"""
Queue de billard et système de visée assistée inspiré de 8 Ball Pool (Miniclip) :
- Traçage du rayon de visée précis
- Bille fantôme (Ghost Ball) au point d'impact
- Lignes directrices de déviation (bille visée et bille blanche)
- Détection et illumination de la poche ciblée
- Queue en bois noble avec recul selon la puissance
- Jauge de puissance verticale interactive
- Sélecteur d'effet (Spin / Anglais / Rétro / Coulé)
"""
import pygame
import math

class Cue:
    def __init__(self, table):
        self.table = table
        self.angle = 0.0          # Angle en radians
        self.power = 0.0          # 0.0 à 1.0
        self.max_impulse = 28.0   # Vitesse maximale transmise
        
        # Effet sur la blanche (-1.0 à 1.0)
        self.spin_x = 0.0
        self.spin_y = 0.0
        
        # États d'interaction
        self.is_aiming = True
        self.is_charging = False
        self.is_striking = False
        self.strike_progress = 0.0
        
        # Dimensions de la jauge de puissance
        self.gauge_rect = pygame.Rect(35, 180, 28, 320)
        self.dragging_gauge = False
        
        # Dimensions du sélecteur de spin
        self.spin_center = pygame.Vector2(1135, 625)
        self.spin_radius = 42
        self.dragging_spin = False
        
        # Longueur de la queue
        self.length = 280
        self.tip_dist = 18        # Distance au repos de la bille blanche
        self.pull_back = 0.0      # Recul actuel en pixels (0 à 100)

    def handle_event(self, event, cue_ball, mouse_pos):
        """Gère la visée, le tir, la jauge et le réglage de l'effet."""
        if cue_ball is None or cue_ball.is_pocketed or cue_ball.is_sinking or cue_ball.in_hand:
            return None

        # 1. Clic sur le sélecteur d'effet
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dist_spin = (pygame.Vector2(mouse_pos) - self.spin_center).length()
            if dist_spin <= self.spin_radius:
                self.dragging_spin = True
                self._update_spin_from_mouse(mouse_pos)
                return None
                
            # Clic sur la jauge de puissance
            gauge_hit_rect = self.gauge_rect.inflate(25, 20)
            if gauge_hit_rect.collidepoint(mouse_pos):
                self.dragging_gauge = True
                self._update_power_from_mouse(mouse_pos)
                return None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_spin:
                self.dragging_spin = False
                return None
            if self.dragging_gauge:
                self.dragging_gauge = False
                # Déclenche le tir si de la puissance a été armée
                if self.power > 0.04:
                    return self.shoot(cue_ball)
                return None

        # Glissement de la souris
        if event.type == pygame.MOUSEMOTION:
            if self.dragging_spin:
                self._update_spin_from_mouse(mouse_pos)
                return None
            elif self.dragging_gauge:
                self._update_power_from_mouse(mouse_pos)
                return None
            elif not self.is_striking:
                # Visée naturelle à la souris vers le curseur
                m_vec = pygame.Vector2(mouse_pos) - cue_ball.pos
                if m_vec.length_squared() > 100 and not self.is_charging:
                    # L'angle pointe depuis la blanche vers la cible
                    self.angle = math.atan2(m_vec.y, m_vec.x)

        # Molette de la souris pour micro-ajustement de l'angle
        if event.type == pygame.MOUSEWHEEL:
            self.angle += event.y * 0.015

        # Touches du clavier : flèches pour micro-ajustement et Espace pour tir
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.angle -= 0.01
            elif event.key == pygame.K_RIGHT:
                self.angle += 0.01
            elif event.key == pygame.K_SPACE:
                self.is_charging = True
                
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if self.power > 0.04:
                    return self.shoot(cue_ball)
                self.is_charging = False
                self.power = 0.0

        return None

    def update(self, dt):
        """Met à jour l'animation de charge ou de frappe."""
        if self.is_charging:
            # Remplissage progressif de la jauge avec la barre d'espace
            self.power = min(1.0, self.power + dt * 0.9)
            
        self.pull_back = self.power * 85.0
        
        if self.is_striking:
            self.strike_progress += dt * 8.0
            if self.strike_progress >= 1.0:
                self.is_striking = False
                self.strike_progress = 0.0
                self.power = 0.0

    def shoot(self, cue_ball):
        """Déclenche la frappe de la bille blanche."""
        impulse_mag = self.power * self.max_impulse
        shot_dir = pygame.Vector2(math.cos(self.angle), math.sin(self.angle))
        
        cue_ball.vel = shot_dir * impulse_mag
        cue_ball.spin = pygame.Vector2(self.spin_x, self.spin_y)
        
        shot_info = {
            "power": self.power,
            "angle": self.angle,
            "spin": (self.spin_x, self.spin_y)
        }
        
        self.power = 0.0
        self.is_charging = False
        self.is_striking = True
        self.strike_progress = 0.0
        return shot_info

    def _update_power_from_mouse(self, mouse_pos):
        # 0 en haut, 1 en bas de la jauge
        rel_y = mouse_pos[1] - self.gauge_rect.top
        fraction = max(0.0, min(1.0, rel_y / self.gauge_rect.height))
        self.power = fraction

    def _update_spin_from_mouse(self, mouse_pos):
        offset = pygame.Vector2(mouse_pos) - self.spin_center
        max_r = self.spin_radius - 8
        dist = offset.length()
        if dist > max_r:
            offset = offset.normalize() * max_r
        self.spin_x = offset.x / max_r
        # Inverser Y pour que le haut soit topspin (+1) et le bas rétro (-1)
        self.spin_y = -offset.y / max_r

    def calculate_trajectory(self, cue_ball, balls):
        """Calcule les trajectoires de visée (ligne directe, bille fantôme, déviation)."""
        if cue_ball is None or cue_ball.is_pocketed or cue_ball.is_sinking:
            return None
            
        start_pos = cue_ball.pos
        aim_dir = pygame.Vector2(math.cos(self.angle), math.sin(self.angle))
        r = cue_ball.radius
        
        closest_hit = None
        closest_dist = 999999.0
        
        # 1. Recherche d'intersection avec une bille cible
        for b in balls:
            if b.is_cue or b.is_pocketed or b.is_sinking:
                continue
            to_ball = b.pos - start_pos
            proj = to_ball.dot(aim_dir)
            if proj <= 0:
                continue  # Bille derrière
                
            perp_sq = to_ball.length_squared() - proj * proj
            min_dist = r + b.radius
            if perp_sq < min_dist * min_dist:
                offset_sq = min_dist * min_dist - perp_sq
                hit_dist = proj - math.sqrt(max(0.0, offset_sq))
                if 0 < hit_dist < closest_dist:
                    closest_dist = hit_dist
                    ghost_pos = start_pos + aim_dir * hit_dist
                    col_normal = (b.pos - ghost_pos).normalize()
                    
                    # Déviation de la bille visée
                    target_dir = col_normal
                    
                    # Déviation de la bille blanche (tangente)
                    tangent_dir = aim_dir - (aim_dir.dot(col_normal)) * col_normal
                    if tangent_dir.length_squared() > 0.001:
                        tangent_dir = tangent_dir.normalize()
                    else:
                        tangent_dir = pygame.Vector2(0, 0)
                        
                    closest_hit = {
                        "type": "ball",
                        "target_ball": b,
                        "ghost_pos": ghost_pos,
                        "target_dir": target_dir,
                        "cue_deflect": tangent_dir,
                        "hit_pos": ghost_pos
                    }
                    
        # 2. Si aucune bille ou si la bande est plus proche
        cushion_hit = self._raycast_cushions(start_pos, aim_dir, r)
        if cushion_hit and cushion_hit["dist"] < closest_dist:
            closest_hit = cushion_hit
            
        return closest_hit

    def _raycast_cushions(self, origin, direction, radius):
        """Détecte l'intersection du rayon de visée avec les bandes de la table."""
        best_hit = None
        min_t = 999999.0
        
        for cushion in self.table.cushions:
            p1 = cushion["p1"]
            p2 = cushion["p2"]
            seg = p2 - p1
            seg_len = seg.length()
            if seg_len < 0.001:
                continue
            normal = cushion["normal"]
            
            # Décalage de la bande par le rayon de la bille
            offset_p1 = p1 + normal * radius
            offset_p2 = p2 + normal * radius
            offset_seg = offset_p2 - offset_p1
            
            # Intersection de deux lignes
            denom = direction.x * offset_seg.y - direction.y * offset_seg.x
            if abs(denom) < 0.0001:
                continue
                
            dx = offset_p1.x - origin.x
            dy = offset_p1.y - origin.y
            t = (dx * offset_seg.y - dy * offset_seg.x) / denom
            u = (dx * direction.y - dy * direction.x) / denom
            
            if t > 0 and 0 <= u <= 1 and t < min_t:
                min_t = t
                hit_pos = origin + direction * t
                # Direction du rebond réfléchi
                reflect_dir = direction - 2.0 * (direction.dot(normal)) * normal
                best_hit = {
                    "type": "cushion",
                    "dist": t,
                    "hit_pos": hit_pos,
                    "reflect_dir": reflect_dir.normalize()
                }
                
        return best_hit

    def draw(self, surface, cue_ball, balls):
        """Dessine la queue, le viseur Miniclip 8 Ball Pool, la jauge et le widget de spin."""
        if cue_ball is None or cue_ball.is_pocketed or cue_ball.is_sinking or cue_ball.in_hand:
            return

        # 1. Dessin de la visée assistée (Guideline)
        trajectory = self.calculate_trajectory(cue_ball, balls)
        if trajectory:
            self._draw_guidelines(surface, cue_ball, trajectory)

        # 2. Dessin de la queue de billard
        self._draw_cue_stick(surface, cue_ball)
        
        # 3. Jauge de puissance verticale (style 8 Ball Pool)
        self._draw_power_gauge(surface)
        
        # 4. Sélecteur de spin
        self._draw_spin_widget(surface)

    def _draw_guidelines(self, surface, cue_ball, traj):
        """Trace les lignes directrices de visée style 8 Ball Pool."""
        guide_surf = pygame.Surface((self.table.screen_w, self.table.screen_h), pygame.SRCALPHA)
        start_pos = cue_ball.pos
        hit_pos = traj["hit_pos"]
        
        # Ligne de visée principale (blanche lumineuse semi-transparente)
        pygame.draw.line(guide_surf, (255, 255, 255, 180), start_pos, hit_pos, 2)
        
        if traj["type"] == "ball":
            ghost = traj["ghost_pos"]
            target_ball = traj["target_ball"]
            target_dir = traj["target_dir"]
            cue_deflect = traj["cue_deflect"]
            
            # Bille fantôme (Ghost ball)
            pygame.draw.circle(guide_surf, (255, 255, 255, 60), (int(ghost.x), int(ghost.y)), int(cue_ball.radius))
            pygame.draw.circle(guide_surf, (255, 255, 255, 190), (int(ghost.x), int(ghost.y)), int(cue_ball.radius), 2)
            
            # Ligne de déviation de la bille cible
            target_end = target_ball.pos + target_dir * 180.0
            pygame.draw.line(guide_surf, (255, 230, 80, 220), target_ball.pos, target_end, 2)
            # Flèche au bout
            arrow_p1 = target_end - target_dir * 8 + pygame.Vector2(-target_dir.y, target_dir.x) * 5
            arrow_p2 = target_end - target_dir * 8 - pygame.Vector2(-target_dir.y, target_dir.x) * 5
            pygame.draw.polygon(guide_surf, (255, 230, 80, 220), [target_end, arrow_p1, arrow_p2])
            
            # Ligne de déviation naturelle de la blanche (tangente)
            if cue_deflect.length_squared() > 0.01:
                cue_end = ghost + cue_deflect * 85.0
                pygame.draw.line(guide_surf, (255, 255, 255, 140), ghost, cue_end, 2)
                
            # Vérifier si la trajectoire vise directement une poche (illumination)
            for pocket in self.table.pockets:
                to_pocket = pocket["pos"] - target_ball.pos
                if to_pocket.dot(target_dir) > 0:
                    cross = abs(to_pocket.x * target_dir.y - to_pocket.y * target_dir.x)
                    if cross < pocket["radius"] * 0.9 and to_pocket.length() < 300:
                        # Halo doré sur la poche visée
                        pygame.draw.circle(guide_surf, (255, 215, 0, 110), 
                                           (int(pocket["pos"].x), int(pocket["pos"].y)), 
                                           int(pocket["radius"] + 8), 3)

        elif traj["type"] == "cushion":
            # Rebond sur la bande
            reflect_dir = traj["reflect_dir"]
            bounce_end = hit_pos + reflect_dir * 90.0
            pygame.draw.line(guide_surf, (255, 255, 255, 140), hit_pos, bounce_end, 2)

        surface.blit(guide_surf, (0, 0))

    def _draw_cue_stick(self, surface, cue_ball):
        """Dessine la queue de billard en bois noble avec dégradé et virole."""
        # La queue est alignée à l'opposé de la direction de tir
        opp_angle = self.angle + math.pi
        stick_dir = pygame.Vector2(math.cos(opp_angle), math.sin(opp_angle))
        perp_dir = pygame.Vector2(-stick_dir.y, stick_dir.x)
        
        # Position du nez de la queue
        dist = self.tip_dist + cue_ball.radius + self.pull_back
        tip_pos = cue_ball.pos + stick_dir * dist
        butt_pos = tip_pos + stick_dir * self.length
        
        # Dimensions effilées de la queue
        w_tip = 3.5
        w_butt = 8.0
        
        p_tip1 = tip_pos + perp_dir * w_tip
        p_tip2 = tip_pos - perp_dir * w_tip
        p_butt1 = butt_pos + perp_dir * w_butt
        p_butt2 = butt_pos - perp_dir * w_butt
        
        # Corps principal en érable blond
        pygame.draw.polygon(surface, (215, 175, 120), [p_tip1, p_tip2, p_butt2, p_butt1])
        
        # Poignée arrière texturée en bois sombre / cuir noir
        grip_start = tip_pos + stick_dir * (self.length * 0.55)
        p_grip1 = grip_start + perp_dir * (w_tip + (w_butt - w_tip) * 0.55)
        p_grip2 = grip_start - perp_dir * (w_tip + (w_butt - w_tip) * 0.55)
        pygame.draw.polygon(surface, (35, 30, 30), [p_grip1, p_grip2, p_butt2, p_butt1])
        
        # Liserés dorés décoratifs
        gold_c = (212, 175, 55)
        pygame.draw.line(surface, gold_c, p_grip1, p_grip2, 2)
        
        # Virole blanche à la pointe
        ferrule_pos = tip_pos + stick_dir * 10
        p_f1 = ferrule_pos + perp_dir * (w_tip + 0.3)
        p_f2 = ferrule_pos - perp_dir * (w_tip + 0.3)
        pygame.draw.polygon(surface, (240, 240, 245), [p_tip1, p_tip2, p_f2, p_f1])
        
        # Embout bleu craie (procéder en cuir avec craie bleue)
        chalk_pos = tip_pos - stick_dir * 3
        p_c1 = chalk_pos + perp_dir * (w_tip - 0.5)
        p_c2 = chalk_pos - perp_dir * (w_tip - 0.5)
        pygame.draw.polygon(surface, (30, 110, 210), [tip_pos, p_tip1, p_c1, p_c2, p_tip2])

    def _draw_power_gauge(self, surface):
        """Jauge de puissance verticale authentique sur le côté gauche."""
        rect = self.gauge_rect
        
        # Fond sombre avec bordure dorée
        pygame.draw.rect(surface, (20, 24, 30), rect.inflate(10, 10), border_radius=8)
        pygame.draw.rect(surface, (180, 140, 50), rect.inflate(10, 10), width=2, border_radius=8)
        
        # Fond interne
        pygame.draw.rect(surface, (10, 12, 15), rect, border_radius=5)
        
        # Remplissage dégradé selon le niveau de puissance (du haut vers le bas)
        fill_h = int(rect.height * self.power)
        if fill_h > 0:
            fill_rect = pygame.Rect(rect.left, rect.top, rect.width, fill_h)
            # Dégradé couleur : vert -> jaune -> orange -> rouge
            if self.power < 0.33:
                bar_color = (40, 210, 90)
            elif self.power < 0.66:
                bar_color = (245, 190, 30)
            else:
                bar_color = (235, 45, 45)
            pygame.draw.rect(surface, bar_color, fill_rect, border_radius=5)
            
        # Curseur de réglage horizontal
        slider_y = rect.top + fill_h
        pygame.draw.rect(surface, (255, 255, 255), (rect.left - 4, slider_y - 3, rect.width + 8, 6), border_radius=3)
        
        # Label de puissance
        try:
            font = pygame.font.SysFont("Arial", 12, bold=True)
            txt = font.render(f"{int(self.power * 100)}%", True, (240, 240, 240))
            txt_rect = txt.get_rect(center=(rect.centerx, rect.bottom + 18))
            surface.blit(txt, txt_rect)
            
            title = font.render("FORCE", True, (180, 180, 180))
            surface.blit(title, title.get_rect(center=(rect.centerx, rect.top - 16)))
        except Exception:
            pass

    def _draw_spin_widget(self, surface):
        """Widget circulaire de sélection d'effet (Spin / Anglais)."""
        center = (int(self.spin_center.x), int(self.spin_center.y))
        r = self.spin_radius
        
        # Cadre extérieur
        pygame.draw.circle(surface, (25, 30, 40), center, r + 6)
        pygame.draw.circle(surface, (180, 140, 50), center, r + 6, 2)
        
        # Bille blanche du widget
        pygame.draw.circle(surface, (245, 245, 240), center, r)
        
        # Réticule de visée fin
        pygame.draw.line(surface, (210, 210, 215), (center[0] - r + 4, center[1]), (center[0] + r - 4, center[1]), 1)
        pygame.draw.line(surface, (210, 210, 215), (center[0], center[1] - r + 4), (center[0], center[1] + r - 4), 1)
        
        # Point rouge représentant l'impact de la craie (effet)
        max_r = r - 8
        dot_x = int(center[0] + self.spin_x * max_r)
        # Inversion pour affichage
        dot_y = int(center[1] - self.spin_y * max_r)
        
        pygame.draw.circle(surface, (220, 30, 30), (dot_x, dot_y), 5)
        pygame.draw.circle(surface, (255, 255, 255), (dot_x, dot_y), 5, 1)
        
        # Titre
        try:
            font = pygame.font.SysFont("Arial", 11, bold=True)
            txt = font.render("EFFET / SPIN", True, (220, 220, 220))
            surface.blit(txt, txt.get_rect(center=(center[0], center[1] - r - 14)))
        except Exception:
            pass
