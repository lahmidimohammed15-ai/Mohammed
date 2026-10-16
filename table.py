"""
Table de billard 8 Ball Pool : géométrie, bandes, poches, diamants et rendu graphique.
"""
import pygame
import math

class Table:
    def __init__(self, screen_w=1200, screen_h=700):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # Dimensions de la table de jeu (rapport 2:1)
        self.play_w = 920
        self.play_h = 460
        self.cx = screen_w // 2
        self.cy = screen_h // 2 + 25  # Légèrement décalée pour laisser la barre HUD en haut
        
        self.left = self.cx - self.play_w // 2
        self.right = self.cx + self.play_w // 2
        self.top = self.cy - self.play_h // 2
        self.bottom = self.cy + self.play_h // 2
        
        self.rail_width = 46
        self.pocket_radius = 23  # Rayon d'entrée des poches
        self.corner_pocket_radius = 26
        
        # Positions des 6 poches
        self.pockets = [
            {"pos": pygame.Vector2(self.left + 5, self.top + 5), "radius": self.corner_pocket_radius, "type": "corner"},
            {"pos": pygame.Vector2(self.cx, self.top - 2), "radius": self.pocket_radius, "type": "side"},
            {"pos": pygame.Vector2(self.right - 5, self.top + 5), "radius": self.corner_pocket_radius, "type": "corner"},
            {"pos": pygame.Vector2(self.left + 5, self.bottom - 5), "radius": self.corner_pocket_radius, "type": "corner"},
            {"pos": pygame.Vector2(self.cx, self.bottom + 2), "radius": self.pocket_radius, "type": "side"},
            {"pos": pygame.Vector2(self.right - 5, self.bottom - 5), "radius": self.corner_pocket_radius, "type": "corner"},
        ]
        
        # Points d'intérêt sur le tapis
        # Ligne de casse (head string) à 1/4
        self.head_string_x = self.left + self.play_w * 0.25
        # Point de casse (head spot)
        self.head_spot = pygame.Vector2(self.head_string_x, self.cy)
        # Point de mouche pour le triangle (foot spot) à 3/4
        self.foot_spot = pygame.Vector2(self.left + self.play_w * 0.75, self.cy)
        
        # Segments des bandes (cushions) avec mâchoires inclinées pour les poches
        self.cushions = self._build_cushions()
        
        # Pré-génération de la texture du tapis / bois pour des performances optimales
        self.felt_color = (20, 115, 65)        # Vert feutre classique 8 Ball Pool
        self.felt_dark = (14, 90, 50)
        self.wood_color = (64, 32, 16)         # Bois acajou noble
        self.wood_border = (42, 20, 10)
        self.wood_highlight = (92, 50, 26)
        self.cushion_color = (16, 96, 52)      # Bande en caoutchouc vert foncé
        self.cushion_edge = (28, 145, 82)
        
    def _build_cushions(self):
        """Construit les 6 segments de bande avec mâchoires biseautées."""
        cushions = []
        corner_cut = 32
        side_cut = 18
        
        # Bande supérieure gauche
        p1 = pygame.Vector2(self.left + corner_cut, self.top)
        p2 = pygame.Vector2(self.cx - side_cut, self.top)
        cushions.append({"p1": p1, "p2": p2, "normal": pygame.Vector2(0, 1), "type": "rail"})
        
        # Bande supérieure droite
        p1 = pygame.Vector2(self.cx + side_cut, self.top)
        p2 = pygame.Vector2(self.right - corner_cut, self.top)
        cushions.append({"p1": p1, "p2": p2, "normal": pygame.Vector2(0, 1), "type": "rail"})
        
        # Bande inférieure gauche
        p1 = pygame.Vector2(self.left + corner_cut, self.bottom)
        p2 = pygame.Vector2(self.cx - side_cut, self.bottom)
        cushions.append({"p1": p1, "p2": p2, "normal": pygame.Vector2(0, -1), "type": "rail"})
        
        # Bande inférieure droite
        p1 = pygame.Vector2(self.cx + side_cut, self.bottom)
        p2 = pygame.Vector2(self.right - corner_cut, self.bottom)
        cushions.append({"p1": p1, "p2": p2, "normal": pygame.Vector2(0, -1), "type": "rail"})
        
        # Bande latérale gauche
        p1 = pygame.Vector2(self.left, self.top + corner_cut)
        p2 = pygame.Vector2(self.left, self.bottom - corner_cut)
        cushions.append({"p1": p1, "p2": p2, "normal": pygame.Vector2(1, 0), "type": "rail"})
        
        # Bande latérale droite
        p1 = pygame.Vector2(self.right, self.top + corner_cut)
        p2 = pygame.Vector2(self.right, self.bottom - corner_cut)
        cushions.append({"p1": p1, "p2": p2, "normal": pygame.Vector2(-1, 0), "type": "rail"})
        
        # Mâchoires d'angles des poches (pour rebonds réalistes dans l'embouchure)
        jaws = [
            # Poche haut-gauche
            (pygame.Vector2(self.left, self.top + corner_cut), pygame.Vector2(self.left - 12, self.top + 10)),
            (pygame.Vector2(self.left + 10, self.top - 12), pygame.Vector2(self.left + corner_cut, self.top)),
            # Poche haut-milieu
            (pygame.Vector2(self.cx - side_cut, self.top), pygame.Vector2(self.cx - side_cut + 5, self.top - 16)),
            (pygame.Vector2(self.cx + side_cut - 5, self.top - 16), pygame.Vector2(self.cx + side_cut, self.top)),
            # Poche haut-droite
            (pygame.Vector2(self.right - corner_cut, self.top), pygame.Vector2(self.right - 10, self.top - 12)),
            (pygame.Vector2(self.right + 12, self.top + 10), pygame.Vector2(self.right, self.top + corner_cut)),
            # Poche bas-gauche
            (pygame.Vector2(self.left, self.bottom - corner_cut), pygame.Vector2(self.left - 12, self.bottom - 10)),
            (pygame.Vector2(self.left + 10, self.bottom + 12), pygame.Vector2(self.left + corner_cut, self.bottom)),
            # Poche bas-milieu
            (pygame.Vector2(self.cx - side_cut, self.bottom), pygame.Vector2(self.cx - side_cut + 5, self.bottom + 16)),
            (pygame.Vector2(self.cx + side_cut - 5, self.bottom + 16), pygame.Vector2(self.cx + side_cut, self.bottom)),
            # Poche bas-droite
            (pygame.Vector2(self.right - corner_cut, self.bottom), pygame.Vector2(self.right - 10, self.bottom + 12)),
            (pygame.Vector2(self.right + 12, self.bottom - 10), pygame.Vector2(self.right, self.bottom - corner_cut)),
        ]
        for p1, p2 in jaws:
            diff = p2 - p1
            length = diff.length()
            if length > 0.001:
                normal = pygame.Vector2(-diff.y, diff.x).normalize()
                cushions.append({"p1": p1, "p2": p2, "normal": normal, "type": "jaw"})
                
        return cushions
        
    def draw(self, surface):
        """Dessine la table complète : cadre bois, tapis, bandes, diamants, poches."""
        outer_rect = pygame.Rect(
            self.left - self.rail_width,
            self.top - self.rail_width,
            self.play_w + self.rail_width * 2,
            self.play_h + self.rail_width * 2
        )
        
        # 1. Ombre portée sous la table
        shadow_rect = outer_rect.inflate(20, 20).move(0, 10)
        pygame.draw.rect(surface, (12, 14, 18), shadow_rect, border_radius=20)
        
        # 2. Cadre extérieur en bois
        pygame.draw.rect(surface, self.wood_border, outer_rect, border_radius=18)
        inner_wood = outer_rect.inflate(-8, -8)
        pygame.draw.rect(surface, self.wood_color, inner_wood, border_radius=14)
        
        # Liseré doré de finition bois
        gold_trim = outer_rect.inflate(-18, -18)
        pygame.draw.rect(surface, (180, 140, 50), gold_trim, width=2, border_radius=10)
        
        # 3. Diamants / repères de visée sur les bandes (points blancs nacrés)
        self._draw_diamonds(surface)
        
        # 4. Tapis de billard
        felt_rect = pygame.Rect(self.left, self.top, self.play_w, self.play_h)
        # Dégradé feutre subtil (centre plus clair, bords légèrement ombrés)
        pygame.draw.rect(surface, self.felt_color, felt_rect)
        
        # Vignettage intérieur feutre (ombres des bandes sur le tapis)
        pygame.draw.line(surface, (12, 70, 38), (self.left, self.top + 3), (self.right, self.top + 3), 5)
        pygame.draw.line(surface, (12, 70, 38), (self.left + 3, self.top), (self.left + 3, self.bottom), 5)
        
        # 5. Ligne de casse et demi-cercle (D)
        self._draw_table_markings(surface)
        
        # 6. Bandes intérieures (cushions)
        self._draw_cushions(surface)
        
        # 7. Les 6 poches avec contours en cuir et inserts métalliques
        self._draw_pockets(surface)
        
    def _draw_table_markings(self, surface):
        """Trace la ligne de casse, le D, et les points de mouche."""
        line_color = (255, 255, 255, 80)
        
        # Ligne de casse (head string)
        mark_surf = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        pygame.draw.line(mark_surf, (255, 255, 255, 50), 
                         (self.head_string_x, self.top + 25), 
                         (self.head_string_x, self.bottom - 25), 2)
                         
        # Demi-cercle (D-arc) pour placement de départ
        d_radius = 65
        d_rect = pygame.Rect(self.head_string_x - d_radius, self.cy - d_radius, d_radius * 2, d_radius * 2)
        pygame.draw.arc(mark_surf, (255, 255, 255, 50), d_rect, math.pi / 2, 3 * math.pi / 2, 2)
        
        # Point de départ (head spot) et point de mouche (foot spot)
        pygame.draw.circle(mark_surf, (255, 255, 255, 90), (int(self.head_spot.x), int(self.head_spot.y)), 3)
        pygame.draw.circle(mark_surf, (255, 255, 255, 90), (int(self.foot_spot.x), int(self.foot_spot.y)), 3)
        
        surface.blit(mark_surf, (0, 0))

    def _draw_diamonds(self, surface):
        """Dessine les diamants incrustés sur les bords en bois."""
        diamond_color = (240, 230, 200)
        border_c = (50, 40, 30)
        
        # Bandes longues (haut et bas) : 6 diamants
        step_x = self.play_w / 8
        for i in range(1, 8):
            if i == 4:
                continue  # Pas de diamant au niveau de la poche centrale
            dx = self.left + i * step_x
            # Haut
            dy_top = self.top - self.rail_width // 2
            self._draw_single_diamond(surface, dx, dy_top, diamond_color, border_c)
            # Bas
            dy_bot = self.bottom + self.rail_width // 2
            self._draw_single_diamond(surface, dx, dy_bot, diamond_color, border_c)
            
        # Bandes courtes (gauche et droite) : 3 diamants
        step_y = self.play_h / 4
        for j in range(1, 4):
            dy = self.top + j * step_y
            # Gauche
            dx_left = self.left - self.rail_width // 2
            self._draw_single_diamond(surface, dx_left, dy, diamond_color, border_c)
            # Droite
            dx_right = self.right + self.rail_width // 2
            self._draw_single_diamond(surface, dx_right, dy, diamond_color, border_c)
            
    def _draw_single_diamond(self, surface, x, y, color, border):
        size = 3.5
        points = [
            (x, y - size),
            (x + size, y),
            (x, y + size),
            (x - size, y)
        ]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, border, points, 1)

    def _draw_cushions(self, surface):
        """Dessine le relief des bandes en caoutchouc autour du tapis."""
        # On trace les 6 bandes principales
        for c in self.cushions:
            if c["type"] == "rail":
                p1, p2 = c["p1"], c["p2"]
                # Ligne de bordure de bande avec éclairage
                pygame.draw.line(surface, self.cushion_edge, p1, p2, 4)
                
    def _draw_pockets(self, surface):
        """Dessine les 6 poches avec profondeur et fixations en laiton/chrome."""
        for p in self.pockets:
            pos = p["pos"]
            r = p["radius"]
            
            # 1. Enjoliveur métallique de poche
            brass_c = (212, 175, 55)
            brass_dark = (140, 105, 30)
            pygame.draw.circle(surface, brass_dark, (int(pos.x), int(pos.y)), int(r + 6))
            pygame.draw.circle(surface, brass_c, (int(pos.x), int(pos.y)), int(r + 4))
            
            # 2. Trou noir profond de la poche
            pygame.draw.circle(surface, (10, 10, 12), (int(pos.x), int(pos.y)), int(r))
            
            # 3. Ombre intérieure
            pygame.draw.circle(surface, (0, 0, 0), (int(pos.x), int(pos.y)), int(r - 3))
            
            # 4. Reflet subtil sur le rebord en cuir
            inner_rim = pygame.Rect(pos.x - r + 3, pos.y - r + 3, (r - 3) * 2, (r - 3) * 2)
            pygame.draw.arc(surface, (60, 60, 70), inner_rim, math.pi * 0.25, math.pi * 0.85, 2)

    def is_inside_play_area(self, point, margin=15):
        """Vérifie si un point est sur le tapis de jeu (sans toucher les bandes)."""
        return (self.left + margin <= point.x <= self.right - margin and
                self.top + margin <= point.y <= self.bottom - margin)

    def is_in_kitchen(self, point, margin=15):
        """Vérifie si un point est derrière la ligne de casse (D-zone)."""
        return (self.left + margin <= point.x <= self.head_string_x and
                self.top + margin <= point.y <= self.bottom - margin)
