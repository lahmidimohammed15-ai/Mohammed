"""
Moteur de règles officielles 8 Ball Pool et gestion de partie :
- Placement du triangle réglementaire (bille 8 au centre, coins alternés)
- Arbitrage officiel des fautes (faute blanche, mauvais groupe, bille non touchée)
- Attribution des groupes (Pleines / Rayées)
- Victoire / Défaite (8 empochée légalement ou trop tôt)
- Gestion du tour par tour, bille en main, modes Solo / 2 Joueurs / Contre IA
"""
import pygame
import math
import random
from ball import Ball

class PoolGame:
    def __init__(self, table, sound_manager):
        self.table = table
        self.sound = sound_manager
        
        # Configuration
        self.mode = "vs_ai"  # "vs_ai", "2_player", "practice"
        self.ai_difficulty = "Moyen"
        
        # État des joueurs
        self.current_player = 1  # 1 ou 2
        self.p1_group = None    # "solids" ou "stripes"
        self.p2_group = None    # "stripes" ou "solids"
        self.winner = None
        self.game_over = False
        
        # Statut du tir
        self.is_break_shot = True
        self.balls_in_motion = False
        self.ball_in_hand = False
        self.foul_message = ""
        self.turn_message = "Casse du match ! Cliquez et tirez"
        self.message_timer = 4.0
        
        # Liste des 16 billes
        self.cue_ball = None
        self.balls = []
        self.setup_rack()

    def setup_rack(self):
        """Place les 15 billes en triangle réglementaire et la blanche sur la ligne de casse."""
        self.balls.clear()
        r = Ball.RADIUS
        
        # 1. Bille blanche sur le point de casse
        self.cue_ball = Ball(0, (self.table.head_spot.x, self.table.head_spot.y))
        self.balls.append(self.cue_ball)
        
        # 2. Composition du triangle de 15 billes
        # Solides: 1 à 7, Rayées: 9 à 15, Bille 8 au milieu de la rangée 3
        solids = list(range(1, 8))
        stripes = list(range(9, 16))
        random.shuffle(solids)
        random.shuffle(stripes)
        
        # Agencement standard 1-2-3-4-5
        # Les coins inférieurs doivent avoir une pleine et une rayée
        rack_layout = [
            solids.pop(),                  # Rangée 1 (Sommet)
            stripes.pop(), solids.pop(),    # Rangée 2
            stripes.pop(), 8, solids.pop(), # Rangée 3 (8 au centre !)
            solids.pop(), stripes.pop(), solids.pop(), stripes.pop(), # Rangée 4
            stripes.pop(), solids.pop(), stripes.pop(), solids.pop(), stripes.pop() # Rangée 5
        ]
        
        # Positionnement géométrique du triangle à partir du Foot Spot
        apex = self.table.foot_spot
        dx = r * math.sqrt(3) + 0.3  # Espacement horizontal entre colonnes
        dy = r * 2.0 + 0.3           # Espacement vertical
        
        idx = 0
        for row in range(5):
            row_x = apex.x + row * dx
            start_y = apex.y - (row * dy) / 2.0
            for col in range(row + 1):
                num = rack_layout[idx]
                pos_y = start_y + col * dy
                b = Ball(num, (row_x, pos_y))
                self.balls.append(b)
                idx += 1

    def reset(self, mode=None, ai_diff=None):
        """Redémarre une nouvelle partie."""
        if mode:
            self.mode = mode
        if ai_diff:
            self.ai_difficulty = ai_diff
            
        self.current_player = 1
        self.p1_group = None
        self.p2_group = None
        self.winner = None
        self.game_over = False
        self.is_break_shot = True
        self.balls_in_motion = False
        self.ball_in_hand = False
        self.foul_message = ""
        self.turn_message = "Nouvelle partie ! Joueur 1 à la casse"
        self.message_timer = 4.0
        self.setup_rack()

    def on_shot_taken(self):
        """Appelé dès que la queue frappe la blanche."""
        self.balls_in_motion = True
        self.foul_message = ""
        self.sound.play_cue_hit()

    def check_turn_end(self, physics):
        """Arbitrage complet exécuté quand toutes les billes sont arrêtées."""
        if not self.balls_in_motion:
            return
            
        self.balls_in_motion = False
        pocketed = physics.balls_pocketed
        first_hit = physics.first_ball_hit
        
        cue_pocketed = any(b.is_cue for b in pocketed)
        eight_pocketed = any(b.is_eight for b in pocketed)
        
        # Récupération de la blanche si elle est tombée
        if cue_pocketed:
            self.cue_ball.is_pocketed = False
            self.cue_ball.is_sinking = False
            self.cue_ball.vel = pygame.Vector2(0, 0)
            self.cue_ball.in_hand = True
            
        # Arbitrage de la bille 8
        if eight_pocketed:
            self._handle_eight_ball(cue_pocketed, first_hit)
            return
            
        # Évaluation des fautes
        foul = False
        foul_reason = ""
        
        # Faute 1: Blanche tombée dans une poche
        if cue_pocketed:
            foul = True
            foul_reason = "Faute : Bille blanche empochée !"
            
        # Faute 2: Aucune bille touchée
        elif first_hit is None:
            foul = True
            foul_reason = "Faute : Aucune bille touchée !"
            
        # Faute 3: Mauvaise bille touchée en premier
        elif not self.is_break_shot and self.get_current_group() is not None:
            group = self.get_current_group()
            # Le joueur a-t-il encore des billes de son groupe sur la table ?
            has_remaining = self._player_has_remaining_balls(group)
            
            if has_remaining:
                is_legal_hit = (first_hit.is_solid if group == "solids" else first_hit.is_stripe)
                if not is_legal_hit:
                    foul = True
                    foul_reason = "Faute : Mauvais groupe touché en premier !"
            else:
                # Si plus de billes, la 8 doit être touchée en premier
                if not first_hit.is_eight:
                    foul = True
                    foul_reason = "Faute : Vous devez toucher la bille 8 en premier !"

        # Attribution des groupes si la table était encore ouverte
        if not self.is_break_shot and self.p1_group is None and not foul:
            legal_pots = [b for b in pocketed if not b.is_cue and not b.is_eight]
            if legal_pots:
                first_potted = legal_pots[0]
                assigned = "solids" if first_potted.is_solid else "stripes"
                if self.current_player == 1:
                    self.p1_group = assigned
                    self.p2_group = "stripes" if assigned == "solids" else "solids"
                else:
                    self.p2_group = assigned
                    self.p1_group = "stripes" if assigned == "solids" else "solids"
                self.turn_message = f"Groupes définis ! Joueur {self.current_player} a les {'PLEINES' if assigned == 'solids' else 'RAYÉES'}"

        # Transition de tour
        if foul:
            self.sound.play_foul()
            self.foul_message = foul_reason
            self._switch_turn()
            self.ball_in_hand = True
            self.cue_ball.in_hand = True
            self.turn_message = f"{foul_reason} Bille en main pour {self.get_player_name()}"
        else:
            # Le joueur a-t-il empoché une bille légale de son groupe ?
            current_group = self.get_current_group()
            pocketed_own = False
            
            if current_group is None:
                # Table ouverte : empocher n'importe quelle bille (hors blanche/8) permet de continuer
                pocketed_own = any(not b.is_cue and not b.is_eight for b in pocketed)
            else:
                pocketed_own = any((b.is_solid if current_group == "solids" else b.is_stripe) for b in pocketed)
                
            if pocketed_own:
                self.turn_message = f"Bien joué ! {self.get_player_name()} continue"
            else:
                self._switch_turn()
                self.turn_message = f"À vous de jouer, {self.get_player_name()}"
                
        self.is_break_shot = False

    def _handle_eight_ball(self, cue_pocketed, first_hit):
        """Arbitrage de la bille 8 (Victoire ou Défaite immédiate)."""
        group = self.get_current_group()
        # Si la blanche est tombée en même temps que la 8 -> Perdu
        if cue_pocketed:
            self._end_game(winner=self._get_other_player(), reason="Défaite : Bille blanche et bille 8 empochées !")
            return
            
        # Si le joueur avait encore des billes de son groupe sur la table -> Perdu
        if group is not None and self._player_has_remaining_balls(group):
            self._end_game(winner=self._get_other_player(), reason="Défaite : Bille 8 empochée trop tôt !")
            return
            
        # Si la table était encore ouverte -> Perdu
        if group is None:
            self._end_game(winner=self._get_other_player(), reason="Défaite : Bille 8 empochée sur table ouverte !")
            return
            
        # Si première bille touchée n'était pas la 8 -> Perdu
        if first_hit is None or not first_hit.is_eight:
            self._end_game(winner=self._get_other_player(), reason="Défaite : Faute commise en empochant la bille 8 !")
            return
            
        # VICTOIRE LÉGALE !
        self._end_game(winner=self.current_player, reason=f"VICTOIRE MAGISTRALE DE {self.get_player_name()} !")

    def _end_game(self, winner, reason):
        self.game_over = True
        self.winner = winner
        self.turn_message = reason
        self.sound.play_win()

    def _switch_turn(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def _get_other_player(self):
        return 2 if self.current_player == 1 else 1

    def get_current_group(self):
        return self.p1_group if self.current_player == 1 else self.p2_group

    def get_player_name(self, player_idx=None):
        idx = player_idx if player_idx is not None else self.current_player
        if self.mode == "vs_ai" and idx == 2:
            return f"IA ({self.ai_difficulty})"
        if self.mode == "practice":
            return "Entraînement"
        return f"Joueur {idx}"

    def _player_has_remaining_balls(self, group):
        """Vérifie s'il reste des billes du groupe sur le tapis."""
        for b in self.balls:
            if not b.is_pocketed and not b.is_sinking and not b.is_cue and not b.is_eight:
                if (b.is_solid and group == "solids") or (b.is_stripe and group == "stripes"):
                    return True
        return False

    def get_remaining_balls(self, group):
        """Retourne les billes restantes d'un groupe."""
        if group is None:
            return []
        return [b for b in self.balls if not b.is_pocketed and not b.is_sinking and
                ((b.is_solid and group == "solids") or (b.is_stripe and group == "stripes"))]

    def place_ball_in_hand(self, pos):
        """Permet au joueur de déposer la blanche n'importe où sur le tapis sans chevauchement."""
        target_pos = pygame.Vector2(pos)
        margin = Ball.RADIUS + 3.0
        
        # Vérification des limites du tapis
        if not self.table.is_inside_play_area(target_pos, margin=margin):
            return False
            
        # Vérification de chevauchement avec une autre bille
        for b in self.balls:
            if b.is_cue or b.is_pocketed or b.is_sinking:
                continue
            if target_pos.distance_to(b.pos) < Ball.RADIUS * 2.05:
                return False
                
        # Emplacement valide !
        self.cue_ball.pos = target_pos
        self.cue_ball.vel = pygame.Vector2(0, 0)
        self.cue_ball.in_hand = False
        self.ball_in_hand = False
        self.turn_message = f"Bille placée ! {self.get_player_name()}, à vous de tirer"
        return True

    def is_ai_turn(self):
        return self.mode == "vs_ai" and self.current_player == 2 and not self.game_over
