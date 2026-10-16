"""
Bille de billard (8 Ball Pool) : graphismes 3D soignés, numérotation, bandes/pleines et état physique.
"""
import pygame
import math

# Couleurs officielles des boules de billard US (1 à 15)
BALL_COLORS = {
    0: (248, 248, 244),   # Bille blanche (Cue ball)
    1: (245, 180, 20),    # Jaune
    2: (30, 90, 210),     # Bleu
    3: (220, 35, 35),     # Rouge
    4: (110, 45, 175),    # Violet
    5: (235, 95, 20),     # Orange
    6: (25, 140, 60),     # Vert
    7: (120, 50, 25),     # Marron / Bordeaux
    8: (18, 18, 20),      # Bille Noire (8-Ball)
    9: (245, 180, 20),    # Jaune rayée
    10: (30, 90, 210),    # Bleu rayée
    11: (220, 35, 35),    # Rouge rayée
    12: (110, 45, 175),   # Violet rayée
    13: (235, 95, 20),    # Orange rayée
    14: (25, 140, 60),    # Vert rayée
    15: (120, 50, 25),    # Marron rayée
}

class Ball:
    RADIUS = 12.5  # Rayon standard adapté à la taille de la table
    MASS = 1.0     # Masse unitaire
    
    def __init__(self, number, pos):
        self.number = number
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        self.radius = Ball.RADIUS
        
        # Propriétés de jeu
        self.is_cue = (number == 0)
        self.is_eight = (number == 8)
        self.is_solid = (1 <= number <= 7)
        self.is_stripe = (9 <= number <= 15)
        
        # États
        self.is_pocketed = False
        self.is_sinking = False
        self.sink_progress = 0.0
        self.sink_target = None
        self.in_hand = False
        
        # Effet (Spin pour la bille blanche)
        self.spin = pygame.Vector2(0, 0)  # (-1..1 en x/y)
        
        # Cache visuel pré-rendu pour 60 FPS constants
        self._sprite = None
        self._generate_sprite()
        
    def _generate_sprite(self):
        """Pré-calcule le sprite avec ombrage 3D, reflet et numéro."""
        diameter = int(self.radius * 2 + 4)
        surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (diameter // 2, diameter // 2)
        r = int(self.radius)
        
        base_color = BALL_COLORS[self.number]
        
        if self.is_cue:
            # Bille blanche pure
            pygame.draw.circle(surface, base_color, center, r)
            # Petit point rouge au centre pour visualiser l'effet
            pygame.draw.circle(surface, (200, 30, 30), center, 2)
        elif self.is_solid or self.is_eight:
            # Bille pleine : cercle plein
            pygame.draw.circle(surface, base_color, center, r)
            self._draw_number_badge(surface, center, r)
        elif self.is_stripe:
            # Bille rayée : fond blanc + bande de couleur équatoriale
            pygame.draw.circle(surface, (245, 245, 240), center, r)
            stripe_rect = pygame.Rect(center[0] - r, center[1] - int(r * 0.55), r * 2, int(r * 1.1))
            # Découpe circulaire pour la bande
            stripe_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(stripe_surf, (255, 255, 255), center, r)
            stripe_color_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.rect(stripe_color_surf, base_color, stripe_rect)
            stripe_color_surf.blit(stripe_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(stripe_color_surf, (0, 0))
            self._draw_number_badge(surface, center, r)
            
        # Reflet spéculaire 3D (lumière venant du haut gauche)
        highlight_pos = (center[0] - int(r * 0.35), center[1] - int(r * 0.35))
        pygame.draw.circle(surface, (255, 255, 255, 160), highlight_pos, int(r * 0.32))
        pygame.draw.circle(surface, (255, 255, 255, 230), highlight_pos, int(r * 0.16))
        
        # Ombrage subtil sur le limbe inférieur
        rim_rect = pygame.Rect(center[0] - r, center[1] - r, r * 2, r * 2)
        pygame.draw.arc(surface, (0, 0, 0, 70), rim_rect, math.pi * 1.0, math.pi * 1.8, 2)
        
        self._sprite = surface
        
    def _draw_number_badge(self, surface, center, r):
        """Dessine le médaillon blanc central avec le numéro de la bille."""
        badge_r = int(r * 0.46)
        pygame.draw.circle(surface, (250, 250, 248), center, badge_r)
        
        # Rendu du numéro
        try:
            font = pygame.font.SysFont("Arial", int(badge_r * 1.45), bold=True)
            text = font.render(str(self.number), True, (15, 15, 15))
            text_rect = text.get_rect(center=center)
            surface.blit(text, text_rect)
        except Exception:
            pass

    def start_sinking(self, pocket_pos):
        """Démarre l'animation de chute dans la poche."""
        self.is_sinking = True
        self.sink_progress = 0.0
        self.sink_target = pygame.Vector2(pocket_pos)
        self.vel = (self.sink_target - self.pos) * 0.15

    def update_sink(self, dt):
        """Met à jour l'animation de descente dans le trou."""
        if not self.is_sinking:
            return
        self.sink_progress += dt * 4.0
        # Mouvement d'aspiration vers le centre de la poche
        if self.sink_target:
            self.pos += (self.sink_target - self.pos) * 0.25
        if self.sink_progress >= 1.0:
            self.is_sinking = False
            self.is_pocketed = True
            self.vel = pygame.Vector2(0, 0)

    def draw(self, surface):
        if self.is_pocketed:
            return
            
        pos_x = int(self.pos.x)
        pos_y = int(self.pos.y)
        
        # 1. Ombre portée sous la bille
        shadow_w = int(self.radius * 2.2)
        shadow_h = int(self.radius * 1.1)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        alpha = 80 if not self.is_sinking else int(80 * (1 - self.sink_progress))
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, alpha), (0, 0, shadow_w, shadow_h))
        surface.blit(shadow_surf, (pos_x - shadow_w // 2, pos_y - shadow_h // 2 + 5))
        
        # 2. Rendu de la bille avec redimensionnement si en train de tomber
        if self._sprite:
            if self.is_sinking:
                scale = max(0.1, 1.0 - self.sink_progress * 0.6)
                new_w = int(self._sprite.get_width() * scale)
                new_h = int(self._sprite.get_height() * scale)
                scaled = pygame.transform.smoothscale(self._sprite, (new_w, new_h))
                surface.blit(scaled, (pos_x - new_w // 2, pos_y - new_h // 2))
            else:
                w = self._sprite.get_width()
                h = self._sprite.get_height()
                surface.blit(self._sprite, (pos_x - w // 2, pos_y - h // 2))
                
        # Si la bille blanche est en main (ball in hand), dessiner un halo lumineux
        if self.in_hand:
            glow_surf = pygame.Surface((int(self.radius * 4), int(self.radius * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 100, 120), (int(self.radius * 2), int(self.radius * 2)), int(self.radius * 1.8), 2)
            surface.blit(glow_surf, (pos_x - int(self.radius * 2), pos_y - int(self.radius * 2)))

    @property
    def speed(self):
        return self.vel.length()
        
    @property
    def is_moving(self):
        return self.vel.length_squared() > 0.05
