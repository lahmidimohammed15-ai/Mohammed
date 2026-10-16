"""
Moteur physique pour billard (8 Ball Pool) :
- Sous-échantillonnage temporel (sub-stepping) pour une physique sans tunnel
- Collisions élastiques bille-bille et bille-bande avec restitution d'énergie
- Frottement de roulement réaliste
- Effets (Topspin, Backspin/Rétro, Sidespin)
- Détection des poches et capture
- Détection des premiers contacts pour arbitrage des fautes
"""
import pygame
import math

class PhysicsEngine:
    SUB_STEPS = 10
    RESTITUTION_BALL = 0.97      # Rebond entre billes
    RESTITUTION_CUSHION = 0.90   # Rebond sur bande caoutchouc
    ROLLING_FRICTION = 0.992     # Décélération par sous-pas
    LINEAR_DRAG = 0.008          # Frottement sec
    MIN_SPEED = 0.12             # Seuil d'arrêt complet
    
    def __init__(self, table, sound_manager=None):
        self.table = table
        self.sound = sound_manager
        
        # Données du tir en cours
        self.first_ball_hit = None
        self.balls_pocketed = []
        self.cushion_hit_after_contact = False
        self.cue_ball_contact_occurred = False
        
    def reset_shot_stats(self):
        """Réinitialise les statistiques du tir pour l'arbitrage."""
        self.first_ball_hit = None
        self.balls_pocketed = []
        self.cushion_hit_after_contact = False
        self.cue_ball_contact_occurred = False

    def update(self, balls, dt=1.0/60.0):
        """Exécute une frame physique découpée en plusieurs sous-pas."""
        sub_dt = dt / self.SUB_STEPS
        
        # Mettre à jour l'animation de chute dans les poches
        for ball in balls:
            if ball.is_sinking:
                ball.update_sink(dt)

        # Sous-échantillonnage pour la physique
        for _ in range(self.SUB_STEPS):
            self._sub_step(balls, sub_dt)

    def _sub_step(self, balls, dt):
        active_balls = [b for b in balls if not b.is_pocketed and not b.is_sinking and not b.in_hand]
        
        # 1. Mise à jour de la position et frottement
        for ball in active_balls:
            if ball.is_moving:
                ball.pos += ball.vel * (dt * 60.0)
                # Décélération
                ball.vel *= self.ROLLING_FRICTION
                speed = ball.vel.length()
                if speed > 0:
                    new_speed = max(0.0, speed - self.LINEAR_DRAG)
                    if new_speed < self.MIN_SPEED:
                        ball.vel = pygame.Vector2(0, 0)
                    else:
                        ball.vel = ball.vel * (new_speed / speed)

        # 2. Détection de chute dans les poches
        for ball in active_balls:
            for pocket in self.table.pockets:
                dist = ball.pos.distance_to(pocket["pos"])
                capture_radius = pocket["radius"] + 2.0
                if dist < capture_radius:
                    ball.start_sinking(pocket["pos"])
                    self.balls_pocketed.append(ball)
                    if self.sound:
                        self.sound.play_pocket()
                    break

        # Re-filtrer les billes encore en jeu
        active_balls = [b for b in active_balls if not b.is_sinking]

        # 3. Collisions bille-bille
        n = len(active_balls)
        for i in range(n):
            b1 = active_balls[i]
            for j in range(i + 1, n):
                b2 = active_balls[j]
                self._resolve_ball_collision(b1, b2)

        # 4. Collisions bille-bandes
        for ball in active_balls:
            self._resolve_cushion_collisions(ball)

    def _resolve_ball_collision(self, b1, b2):
        delta = b2.pos - b1.pos
        dist_sq = delta.length_squared()
        min_dist = b1.radius + b2.radius
        min_dist_sq = min_dist * min_dist
        
        if dist_sq < min_dist_sq and dist_sq > 0.0001:
            dist = math.sqrt(dist_sq)
            normal = delta / dist
            
            # Vitesse relative le long de la normale
            rel_vel = b1.vel - b2.vel
            vel_along_normal = rel_vel.dot(normal)
            
            # Les billes s'approchent-elles ?
            if vel_along_normal > 0:
                # Arbitrage du premier impact de la blanche
                if b1.is_cue and not self.cue_ball_contact_occurred:
                    self.first_ball_hit = b2
                    self.cue_ball_contact_occurred = True
                    self._apply_cue_spin(b1, normal)
                elif b2.is_cue and not self.cue_ball_contact_occurred:
                    self.first_ball_hit = b1
                    self.cue_ball_contact_occurred = True
                    self._apply_cue_spin(b2, -normal)

                # Impulsion élastique
                impulse = (1.0 + self.RESTITUTION_BALL) * vel_along_normal / 2.0
                b1.vel -= impulse * normal
                b2.vel += impulse * normal
                
                # Effet sonore proportionnel à la violence du choc
                if self.sound:
                    impact_speed = abs(vel_along_normal)
                    vol = min(1.0, max(0.15, impact_speed / 12.0))
                    self.sound.play_ball_hit(vol)
                    
            # Séparation géométrique (anti-chevauchement)
            overlap = 0.5 * (min_dist - dist)
            b1.pos -= normal * overlap
            b2.pos += normal * overlap

    def _apply_cue_spin(self, cue_ball, hit_normal):
        """Applique l'effet rétro (backspin) ou coulé (topspin) au moment du choc."""
        spin = cue_ball.spin
        if spin.length_squared() > 0.01:
            # spin.y : -1 = backspin (rétro), +1 = topspin (coulé)
            # spin.x : -1 = effet gauche, +1 = effet droite
            tangent = pygame.Vector2(-hit_normal.y, hit_normal.x)
            
            # Rétro / Coulé selon l'axe d'impact
            draw_impulse = -hit_normal * (spin.y * 2.8)
            side_impulse = tangent * (spin.x * 1.5)
            cue_ball.vel += draw_impulse + side_impulse
            
            # Consommer une partie du spin après le premier choc
            cue_ball.spin *= 0.3

    def _resolve_cushion_collisions(self, ball):
        """Résout les rebonds contre les bandes segmentées."""
        for cushion in self.table.cushions:
            p1 = cushion["p1"]
            p2 = cushion["p2"]
            seg_vec = p2 - p1
            seg_len = seg_vec.length()
            if seg_len < 0.001:
                continue
                
            seg_dir = seg_vec / seg_len
            ball_to_p1 = ball.pos - p1
            projection = ball_to_p1.dot(seg_dir)
            projection = max(0.0, min(seg_len, projection))
            
            closest_pt = p1 + seg_dir * projection
            dist_vec = ball.pos - closest_pt
            dist = dist_vec.length()
            
            if dist < ball.radius and dist > 0.0001:
                normal = dist_vec / dist
                # Vitesse le long de la normale
                vn = ball.vel.dot(normal)
                if vn < 0:
                    # Rebond
                    ball.vel -= (1.0 + self.RESTITUTION_CUSHION) * vn * normal
                    ball.vel *= 0.98  # Frottement tangentiel bande
                    
                    if self.cue_ball_contact_occurred:
                        self.cushion_hit_after_contact = True
                        
                    if self.sound:
                        vol = min(1.0, max(0.12, abs(vn) / 10.0))
                        self.sound.play_rail_hit(vol)
                        
                # Correction de position
                ball.pos = closest_pt + normal * ball.radius

    def are_all_balls_stopped(self, balls):
        """Indique si toutes les billes sont parfaitement immobiles."""
        for b in balls:
            if b.is_sinking or b.is_moving:
                return False
        return True
