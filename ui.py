"""
Interface utilisateur (HUD) pour 8 Ball Pool :
- Cartouches joueurs avec badges Pleines / Rayées et indicateurs de tour actif
- Mini-râtelier affichant les billes restantes de chaque joueur
- Bannière centrale de notifications et d'arbitrage
- Boutons interactifs : Nouvelle partie, Mode de jeu, Difficulté IA, Son, Aide
- Fenêtre modale des règles et commandes (Touche H ou bouton ?)
- Curseur interactif pour le placement de la bille en main
"""
import pygame
import math
from ball import BALL_COLORS

class UI:
    def __init__(self, screen_w=1200, screen_h=700):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # Polices
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_bold = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_normal = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 12)
        
        # Boutons interactifs
        self.btn_new = pygame.Rect(140, 665, 120, 28)
        self.btn_mode = pygame.Rect(270, 665, 140, 28)
        self.btn_diff = pygame.Rect(420, 665, 110, 28)
        self.btn_mute = pygame.Rect(540, 665, 95, 28)
        self.btn_help = pygame.Rect(645, 665, 80, 28)
        
        self.show_help = False
        
    def handle_click(self, mouse_pos, game, sound):
        """Gère les clics sur les boutons de l'interface."""
        # Clic sur le bouton d'aide
        if self.btn_help.collidepoint(mouse_pos):
            self.show_help = not self.show_help
            return True
            
        if self.show_help:
            # Tout clic ferme l'aide
            self.show_help = False
            return True
            
        # Nouvelle partie
        if self.btn_new.collidepoint(mouse_pos):
            game.reset()
            return True
            
        # Changement de mode
        if self.btn_mode.collidepoint(mouse_pos):
            modes = ["vs_ai", "2_player", "practice"]
            idx = (modes.index(game.mode) + 1) % len(modes)
            game.reset(mode=modes[idx])
            return True
            
        # Changement de difficulté IA
        if self.btn_diff.collidepoint(mouse_pos) and game.mode == "vs_ai":
            diffs = ["Facile", "Moyen", "Pro"]
            idx = (diffs.index(game.ai_difficulty) + 1) % len(diffs)
            game.ai_difficulty = diffs[idx]
            return True
            
        # Couper / Activer le son
        if self.btn_mute.collidepoint(mouse_pos):
            sound.toggle_mute()
            return True
            
        return False

    def draw(self, surface, game, sound, mouse_pos):
        """Dessine tout le HUD supérieur, inférieur, et les bannières."""
        self._draw_header(surface, game)
        self._draw_bottom_bar(surface, game, sound)
        self._draw_ball_in_hand_prompt(surface, game, mouse_pos)
        
        if self.show_help:
            self._draw_help_modal(surface)

    def _draw_header(self, surface, game):
        """Bandeau supérieur avec cartes joueurs et statut du tour."""
        header_rect = pygame.Rect(0, 0, self.screen_w, 105)
        
        # Fond dégradé métallique sombre
        pygame.draw.rect(surface, (14, 18, 24), header_rect)
        pygame.draw.line(surface, (40, 48, 62), (0, 105), (self.screen_w, 105), 2)
        
        # Logo 8 Ball Pool au centre
        title_surf = self.font_title.render("8 BALL POOL", True, (245, 190, 45))
        surface.blit(title_surf, title_surf.get_rect(center=(self.screen_w // 2, 22)))
        
        # Carte Joueur 1 (Gauche)
        self._draw_player_card(
            surface, 
            player_idx=1,
            name="Joueur 1", 
            group=game.p1_group, 
            is_active=(game.current_player == 1 and not game.game_over),
            x=60, y=14, 
            game=game
        )
        
        # Carte Joueur 2 / IA (Droite)
        p2_name = game.get_player_name(2)
        self._draw_player_card(
            surface, 
            player_idx=2,
            name=p2_name, 
            group=game.p2_group, 
            is_active=(game.current_player == 2 and not game.game_over),
            x=self.screen_w - 380, y=14, 
            game=game
        )
        
        # Bannière centrale de statut / message d'arbitrage
        banner_rect = pygame.Rect(self.screen_w // 2 - 250, 48, 500, 42)
        
        if game.game_over:
            bg_color = (25, 80, 40) if game.winner == 1 else (90, 25, 25)
            border_c = (245, 190, 40)
        elif game.foul_message:
            bg_color = (80, 20, 20)
            border_c = (235, 60, 60)
        else:
            bg_color = (22, 28, 38)
            border_c = (60, 75, 100)
            
        pygame.draw.rect(surface, bg_color, banner_rect, border_radius=8)
        pygame.draw.rect(surface, border_c, banner_rect, width=2, border_radius=8)
        
        # Texte du message
        msg_txt = self.font_bold.render(game.turn_message, True, (255, 255, 255))
        surface.blit(msg_txt, msg_txt.get_rect(center=banner_rect.center))

    def _draw_player_card(self, surface, player_idx, name, group, is_active, x, y, game):
        """Affiche le panneau d'un joueur avec ses billes restantes."""
        card_w, card_h = 320, 76
        rect = pygame.Rect(x, y, card_w, card_h)
        
        # Bordure active éclatante
        bg = (24, 30, 42) if is_active else (18, 22, 30)
        pygame.draw.rect(surface, bg, rect, border_radius=10)
        
        border_color = (245, 190, 45) if is_active else (45, 55, 75)
        border_w = 3 if is_active else 1
        pygame.draw.rect(surface, border_color, rect, width=border_w, border_radius=10)
        
        # Avatar circulaire
        avatar_center = (x + 34, y + card_h // 2)
        avatar_bg = (40, 110, 210) if player_idx == 1 else (210, 60, 40)
        pygame.draw.circle(surface, avatar_bg, avatar_center, 22)
        av_txt = self.font_bold.render(f"J{player_idx}" if "IA" not in name else "IA", True, (255, 255, 255))
        surface.blit(av_txt, av_txt.get_rect(center=avatar_center))
        
        # Nom du joueur
        name_txt = self.font_bold.render(name, True, (255, 255, 255) if is_active else (170, 180, 195))
        surface.blit(name_txt, (x + 68, y + 10))
        
        # Badge du groupe (Pleines ou Rayées)
        if group:
            grp_name = "PLEINES (1-7)" if group == "solids" else "RAYÉES (9-15)"
            grp_color = (255, 210, 60) if group == "solids" else (120, 190, 255)
            badge_surf = self.font_small.render(grp_name, True, grp_color)
            surface.blit(badge_surf, (x + 68, y + 30))
            
            # Mini-billes restantes du joueur
            remaining = game.get_remaining_balls(group)
            start_bx = x + 68
            for i, b in enumerate(remaining):
                bx = start_bx + i * 18
                by = y + 54
                b_color = BALL_COLORS.get(b.number, (200, 200, 200))
                pygame.draw.circle(surface, b_color, (bx, by), 6)
                pygame.draw.circle(surface, (255, 255, 255), (bx, by), 6, 1)
        else:
            open_txt = self.font_small.render("Groupe : Table Ouverte", True, (130, 140, 155))
            surface.blit(open_txt, (x + 68, y + 32))

    def _draw_bottom_bar(self, surface, game, sound):
        """Barre d'outils et boutons interactifs en bas de l'écran."""
        # 1. Bouton Nouvelle Partie
        self._draw_btn(surface, self.btn_new, "Rejouer", (40, 130, 80))
        
        # 2. Bouton Mode
        mode_names = {"vs_ai": "Vs Ordinateur", "2_player": "Pass & Play (2J)", "practice": "Entraînement"}
        self._draw_btn(surface, self.btn_mode, mode_names.get(game.mode, "Mode"), (45, 60, 85))
        
        # 3. Bouton Difficulté (uniquement en Vs IA)
        if game.mode == "vs_ai":
            self._draw_btn(surface, self.btn_diff, f"IA: {game.ai_difficulty}", (85, 55, 45))
            
        # 4. Bouton Mute
        mute_txt = "Son : OFF" if sound.muted else "Son : ON"
        mute_bg = (90, 30, 30) if sound.muted else (45, 60, 85)
        self._draw_btn(surface, self.btn_mute, mute_txt, mute_bg)
        
        # 5. Bouton Aide
        self._draw_btn(surface, self.btn_help, "Aide (?)", (55, 70, 95))

    def _draw_btn(self, surface, rect, text, bg_color):
        """Dessine un bouton moderne avec bordure et texte centré."""
        pygame.draw.rect(surface, bg_color, rect, border_radius=6)
        pygame.draw.rect(surface, (180, 195, 215), rect, width=1, border_radius=6)
        txt = self.font_small.render(text, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))

    def _draw_ball_in_hand_prompt(self, surface, game, mouse_pos):
        """Affiche le réticule interactif quand le joueur a bille en main."""
        if not game.ball_in_hand or game.balls_in_motion or game.is_ai_turn():
            return
            
        target_pos = pygame.Vector2(mouse_pos)
        r = Ball.RADIUS
        
        # Vérification si la position de la souris est valide
        is_valid = game.table.is_inside_play_area(target_pos, margin=r + 3.0)
        if is_valid:
            for b in game.balls:
                if b.is_cue or b.is_pocketed or b.is_sinking:
                    continue
                if target_pos.distance_to(b.pos) < r * 2.05:
                    is_valid = False
                    break
                    
        # Halo de placement
        halo_color = (40, 220, 90, 140) if is_valid else (235, 45, 45, 140)
        halo_surf = pygame.Surface((int(r * 4), int(r * 4)), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, halo_color, (int(r * 2), int(r * 2)), int(r))
        pygame.draw.circle(halo_surf, (255, 255, 255), (int(r * 2), int(r * 2)), int(r), 2)
        surface.blit(halo_surf, (int(target_pos.x - r * 2), int(target_pos.y - r * 2)))
        
        # Message d'instruction sous le curseur
        hint = "Cliquez pour déposer la bille blanche" if is_valid else "Emplacement invalide / chevauchement"
        hint_surf = self.font_small.render(hint, True, (255, 255, 255))
        surface.blit(hint_surf, (int(target_pos.x - hint_surf.get_width() // 2), int(target_pos.y + 22)))

    def _draw_help_modal(self, surface):
        """Fenêtre modale d'aide avec commandes et règles du jeu."""
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))
        
        modal_w, modal_h = 680, 480
        rect = pygame.Rect((self.screen_w - modal_w) // 2, (self.screen_h - modal_h) // 2, modal_w, modal_h)
        
        pygame.draw.rect(surface, (20, 25, 35), rect, border_radius=12)
        pygame.draw.rect(surface, (245, 190, 45), rect, width=2, border_radius=12)
        
        # Titre
        t = self.font_title.render("8 BALL POOL - COMMANDES & RÈGLES", True, (245, 190, 45))
        surface.blit(t, t.get_rect(center=(rect.centerx, rect.top + 30)))
        
        lines = [
            ("COMMANDES DU JEU :", True),
            ("• Souris : Orientez le curseur pour viser avec la ligne d'assistance.", False),
            ("• Jauge de gauche : Cliquez et glissez pour régler la force, ou maintenez ESPACE.", False),
            ("• Molette / Flèches Gauche-Droite : Micro-ajustement d'angle de précision.", False),
            ("• Widget en bas à droite : Cliquez sur la bille blanche pour régler l'EFFET (Rétro / Coulé).", False),
            ("• Bille en main : Cliquez n'importe où sur le tapis vert pour placer la blanche.", False),
            ("", False),
            ("RÈGLES OFFICIELLES DU 8 BALL POOL :", True),
            ("• La casse ouvre le jeu. Le premier joueur qui empoche légalement choisit son groupe.", False),
            ("• Groupe PLEINES (1 à 7) ou RAYÉES (9 à 15).", False),
            ("• Toujours toucher en premier une bille de son groupe sous peine de faute.", False),
            ("• En cas de faute : l'adversaire obtient BILLE EN MAIN (placement libre).", False),
            ("• Bille 8 : Après avoir vidé votre groupe, empochez la bille 8 pour GAGNER !", False),
            ("• ATTENTION : Empocher la 8 trop tôt ou faire tomber la blanche en même temps = DÉFAITE !", False),
        ]
        
        cur_y = rect.top + 65
        for text, is_header in lines:
            if is_header:
                s = self.font_bold.render(text, True, (255, 215, 60))
            else:
                s = self.font_normal.render(text, True, (220, 225, 235))
            surface.blit(s, (rect.left + 35, cur_y))
            cur_y += 24
            
        close_txt = self.font_small.render("Cliquez n'importe où pour fermer l'aide", True, (150, 160, 175))
        surface.blit(close_txt, close_txt.get_rect(center=(rect.centerx, rect.bottom - 20)))
