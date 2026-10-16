"""
Intelligence Artificielle pour 8 Ball Pool :
- Évaluation géométrique des trajectoires bille -> poche
- Calcul des angles de coupe (cut angles) et détection des obstacles
- Placement stratégique de la bille blanche en cas de bille en main (Ball in hand)
- 3 niveaux de difficulté (Facile, Moyen, Pro)
- Animation fluide de visée et tir humanisé
"""
import pygame
import math
import random

class PoolAI:
    def __init__(self, table):
        self.table = table
        self.difficulty = "Moyen"  # "Facile", "Moyen", "Pro"
        
        # États du cycle de décision
        self.state = "IDLE"  # "THINKING", "ROTATING", "CHARGING", "READY_TO_SHOOT"
        self.timer = 0.0
        
        # Paramètres de tir calculés
        self.target_angle = 0.0
        self.target_power = 0.5
        self.chosen_target = None
        
    def start_turn(self, cue_ball, balls, ai_group, difficulty="Moyen"):
        """Initialise la réflexion de l'IA pour son tour."""
        self.difficulty = difficulty
        self.state = "THINKING"
        self.timer = 0.8 + random.uniform(0.2, 0.6)  # Pause naturelle de réflexion
        self.chosen_target = None

    def update(self, dt, cue, cue_ball, balls, ai_group):
        """Met à jour la machine à états de l'IA."""
        if self.state == "IDLE":
            return None
            
        self.timer -= dt
        
        if self.state == "THINKING":
            if self.timer <= 0:
                # Si bille en main, placer la blanche idéalement
                if cue_ball.in_hand:
                    self._place_ball_in_hand(cue_ball, balls, ai_group)
                    cue_ball.in_hand = False
                    
                # Calcul du meilleur tir
                best_shot = self._find_best_shot(cue_ball, balls, ai_group)
                if best_shot:
                    self.target_angle = best_shot["angle"]
                    self.target_power = best_shot["power"]
                else:
                    # Coup de sécurité si aucun tir direct n'est possible
                    self.target_angle, self.target_power = self._fallback_shot(cue_ball, balls, ai_group)
                    
                # Bruit selon la difficulté
                noise_map = {"Facile": 0.045, "Moyen": 0.016, "Pro": 0.003}
                noise = random.gauss(0, noise_map.get(self.difficulty, 0.015))
                self.target_angle += noise
                
                self.state = "ROTATING"
                self.timer = 1.2
                
        elif self.state == "ROTATING":
            # Rotation progressive de la queue vers la cible
            diff = (self.target_angle - cue.angle + math.pi) % (2 * math.pi) - math.pi
            cue.angle += diff * min(1.0, dt * 6.0)
            if abs(diff) < 0.02 or self.timer <= 0:
                cue.angle = self.target_angle
                self.state = "CHARGING"
                self.timer = 0.8
                
        elif self.state == "CHARGING":
            # Recul progressif de la queue
            cue.power = min(self.target_power, cue.power + dt * 1.4)
            if cue.power >= self.target_power or self.timer <= 0:
                self.state = "IDLE"
                # Exécution du tir !
                return cue.shoot(cue_ball)
                
        return None

    def _find_best_shot(self, cue_ball, balls, ai_group):
        """Évalue tous les tirs possibles et retourne le meilleur candidat."""
        legal_balls = self._get_legal_targets(balls, ai_group)
        if not legal_balls:
            return None
            
        r = cue_ball.radius
        best_candidate = None
        best_score = -999999.0
        
        for b in legal_balls:
            for pocket in self.table.pockets:
                p_pos = pocket["pos"]
                to_pocket = p_pos - b.pos
                dist_pocket = to_pocket.length()
                if dist_pocket < 0.001:
                    continue
                dir_pocket = to_pocket / dist_pocket
                
                # Position fantôme de la blanche pour pousser la bille dans la poche
                ghost_pos = b.pos - dir_pocket * (r * 2.0)
                
                # Vérifier si la position fantôme est sur la table
                if not self.table.is_inside_play_area(ghost_pos, margin=r):
                    continue
                    
                # Vérifier la ligne blanche -> ghost_pos
                to_ghost = ghost_pos - cue_ball.pos
                dist_cue = to_ghost.length()
                if dist_cue < 0.001:
                    continue
                dir_cue = to_ghost / dist_cue
                
                # Angle de coupe (Cut angle)
                cos_cut = dir_cue.dot(dir_pocket)
                if cos_cut < 0.15:  # Coupe trop fermée (> 81°)
                    continue
                    
                # Vérification des obstacles
                # Obstacle 1: entre bille cible et poche
                if self._is_path_blocked(b.pos, p_pos, balls, ignore=[b]):
                    continue
                    
                # Obstacle 2: entre blanche et bille fantôme
                if self._is_path_blocked(cue_ball.pos, ghost_pos, balls, ignore=[cue_ball, b]):
                    continue
                    
                # Score heuristique
                score = 1000.0
                score += cos_cut * 850.0               # Prime énorme aux tirs droits
                score -= dist_pocket * 0.7             # Pénalité distance poche
                score -= dist_cue * 0.45               # Pénalité distance blanche
                
                if pocket["type"] == "side":
                    # Les poches latérales demandent un angle plus direct
                    if cos_cut < 0.45:
                        score -= 250.0
                        
                if score > best_score:
                    best_score = score
                    # Calcul de la puissance requise
                    total_dist = dist_cue + dist_pocket
                    power = min(0.95, max(0.28, total_dist / 900.0 + (1.0 - cos_cut) * 0.25))
                    shot_angle = math.atan2(dir_cue.y, dir_cue.x)
                    best_candidate = {
                        "target_ball": b,
                        "pocket": pocket,
                        "angle": shot_angle,
                        "power": power,
                        "score": score
                    }
                    
        return best_candidate

    def _fallback_shot(self, cue_ball, balls, ai_group):
        """Tir de sécurité pour simplement toucher une bille légale et éviter la faute."""
        legal_balls = self._get_legal_targets(balls, ai_group)
        if not legal_balls:
            legal_balls = [b for b in balls if not b.is_cue and not b.is_pocketed]
            
        closest_b = None
        min_dist = 999999.0
        for b in legal_balls:
            d = cue_ball.pos.distance_to(b.pos)
            if d < min_dist:
                min_dist = d
                closest_b = b
                
        if closest_b:
            diff = closest_b.pos - cue_ball.pos
            angle = math.atan2(diff.y, diff.x)
            return angle, 0.45
        return 0.0, 0.4

    def _place_ball_in_hand(self, cue_ball, balls, ai_group):
        """Place stratégiquement la bille blanche en cas de faute adverse."""
        legal_balls = self._get_legal_targets(balls, ai_group)
        if not legal_balls:
            cue_ball.pos = pygame.Vector2(self.table.head_spot)
            return
            
        # Chercher une bille proche d'une poche et se placer directement derrière
        for b in legal_balls:
            for pocket in self.table.pockets:
                to_pocket = pocket["pos"] - b.pos
                d_pocket = to_pocket.length()
                if d_pocket < 220 and not self._is_path_blocked(b.pos, pocket["pos"], balls, ignore=[b]):
                    dir_pocket = to_pocket / d_pocket
                    # Placement à 120px derrière la bille
                    candidate_pos = b.pos - dir_pocket * 140.0
                    if self.table.is_inside_play_area(candidate_pos, margin=25):
                        # Vérifier qu'aucune bille ne chevauche
                        overlap = any(candidate_pos.distance_to(other.pos) < 30.0 
                                     for other in balls if not other.is_cue and not other.is_pocketed)
                        if not overlap:
                            cue_ball.pos = candidate_pos
                            return
                            
        # Position par défaut : Head spot
        cue_ball.pos = pygame.Vector2(self.table.head_spot)

    def _get_legal_targets(self, balls, ai_group):
        """Retourne la liste des billes que l'IA a le droit de viser."""
        active = [b for b in balls if not b.is_cue and not b.is_pocketed and not b.is_sinking]
        
        if ai_group is None:
            # Table ouverte : toutes sauf la 8
            non_8 = [b for b in active if not b.is_eight]
            return non_8 if non_8 else active
            
        group_balls = [b for b in active if (b.is_solid if ai_group == "solids" else b.is_stripe)]
        if group_balls:
            return group_balls
            
        # Toutes les billes du groupe sont empochées : la 8 est la cible légale
        eight = [b for b in active if b.is_eight]
        return eight

    def _is_path_blocked(self, p1, p2, balls, ignore=None):
        """Vérifie si une autre bille obstrue le segment p1 -> p2."""
        if ignore is None:
            ignore = []
        path_vec = p2 - p1
        path_len = path_vec.length()
        if path_len < 0.001:
            return False
            
        path_dir = path_vec / path_len
        r_sum = Ball.RADIUS * 1.85  # Marge de sécurité
        
        for b in balls:
            if b in ignore or b.is_pocketed or b.is_sinking:
                continue
            to_ball = b.pos - p1
            proj = to_ball.dot(path_dir)
            if 0 < proj < path_len:
                perp_sq = to_ball.length_squared() - proj * proj
                if perp_sq < r_sum * r_sum:
                    return True
        return False
