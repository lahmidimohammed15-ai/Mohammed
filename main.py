"""
8 BALL POOL - Jeu complet de billard américain
Point d'entrée principal Pygame.
"""
import pygame
import sys
import os

from table import Table
from ball import Ball
from physics import PhysicsEngine
from cue import Cue
from ai import PoolAI
from sound_manager import SoundManager
from game import PoolGame
from ui import UI

def main():
    # Initialisation Pygame
    pygame.init()
    pygame.mixer.init()
    
    screen_w = 1200
    screen_h = 700
    screen = pygame.display.set_mode((screen_w, screen_h))
    pygame.display.set_caption("8 Ball Pool - Mini Game Billard Américain")
    
    # Création des composants
    table = Table(screen_w, screen_h)
    sound = SoundManager()
    physics = PhysicsEngine(table, sound_manager=sound)
    cue = Cue(table)
    ai = PoolAI(table)
    game = PoolGame(table, sound)
    ui = UI(screen_w, screen_h)
    
    clock = pygame.time.Clock()
    running = True
    ai_turn_started = False
    
    # Viser vers le triangle au départ
    cue.angle = 0.0

    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en secondes (60 FPS max)
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
                
            # Raccourcis clavier
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                elif event.key == pygame.K_h:
                    ui.show_help = not ui.show_help
                elif event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_m:
                    sound.toggle_mute()
                    
            # Clics souris
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Clic sur un bouton de l'interface ?
                if ui.handle_click(mouse_pos, game, sound):
                    continue
                    
                # Placement de la bille blanche en cas de bille en main
                if game.ball_in_hand and not game.balls_in_motion and not game.is_ai_turn():
                    if game.place_ball_in_hand(mouse_pos):
                        continue

            # Transmission des événements à la queue (si le joueur humain a la main)
            if not game.balls_in_motion and not game.is_ai_turn() and not game.game_over and not game.ball_in_hand:
                shot = cue.handle_event(event, game.cue_ball, mouse_pos)
                if shot:
                    physics.reset_shot_stats()
                    game.on_shot_taken()
                    ai_turn_started = False

        # 2. Mise à jour de l'état du jeu
        if game.balls_in_motion:
            physics.update(game.balls, dt)
            # Toutes les billes se sont-elles arrêtées ?
            if physics.are_all_balls_stopped(game.balls):
                game.check_turn_end(physics)
                physics.reset_shot_stats()
                ai_turn_started = False
                
                # Réaligner automatiquement la visée vers la bille la plus proche
                if not game.game_over and game.cue_ball:
                    active = [b for b in game.balls if not b.is_cue and not b.is_pocketed]
                    if active:
                        closest = min(active, key=lambda b: game.cue_ball.pos.distance_to(b.pos))
                        diff = closest.pos - game.cue_ball.pos
                        cue.angle = math.atan2(diff.y, diff.x)
        else:
            # Tour de l'ordinateur (IA)
            if game.is_ai_turn() and not game.game_over:
                if not ai_turn_started:
                    ai.start_turn(game.cue_ball, game.balls, game.p2_group, difficulty=game.ai_difficulty)
                    ai_turn_started = True
                else:
                    shot = ai.update(dt, cue, game.cue_ball, game.balls, game.p2_group)
                    if shot:
                        physics.reset_shot_stats()
                        game.on_shot_taken()
                        ai_turn_started = False
            else:
                cue.update(dt)

        # 3. Rendu graphique
        # Fond sombre luxueux
        screen.fill((12, 14, 18))
        
        # Table de billard
        table.draw(screen)
        
        # Dessin des 16 billes
        for ball in game.balls:
            ball.draw(screen)
            
        # Dessin de la queue de billard et ligne d'aide à la visée (si les billes sont arrêtées)
        if not game.balls_in_motion and not game.game_over and not game.ball_in_hand:
            cue.draw(screen, game.cue_ball, game.balls)
            
        # Interface utilisateur (HUD, scores, bannières, boutons, aide)
        ui.draw(screen, game, sound, mouse_pos)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
