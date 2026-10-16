"""
Script de test unitaire pour valider l'intégrité de tous les modules du jeu.
"""
import pygame
import os
import sys

# Mode vidéo factice pour test sans écran physique
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
pygame.display.set_mode((1200, 700))

from table import Table
from ball import Ball
from physics import PhysicsEngine
from cue import Cue
from ai import PoolAI
from sound_manager import SoundManager
from game import PoolGame
from ui import UI

print("1. Initialisation des composants...")
table = Table(1200, 700)
sound = SoundManager("assets/sounds")
physics = PhysicsEngine(table, sound)
cue = Cue(table)
ai = PoolAI(table)
game = PoolGame(table, sound)
ui = UI(1200, 700)

print(f"2. Billes initialisées : {len(game.balls)}")
assert len(game.balls) == 16, f"Attendu 16 billes, obtenu {len(game.balls)}"

print("3. Test du calcul de trajectoire de la queue...")
traj = cue.calculate_trajectory(game.cue_ball, game.balls)
print(f"Trajectoire initiale calculée avec succès : {traj['type'] if traj else 'None'}")

print("4. Test de simulation physique (1 tir de casse)...")
game.cue_ball.vel = pygame.Vector2(20.0, 0.0)
game.balls_in_motion = True

for step in range(60):
    physics.update(game.balls, 1.0 / 60.0)

print("5. Test d'évaluation du tour...")
physics.are_all_balls_stopped(game.balls)
game.check_turn_end(physics)

print("6. Test de rendu de l'interface et de la table...")
surf = pygame.Surface((1200, 700))
table.draw(surf)
for b in game.balls:
    b.draw(surf)
cue.draw(surf, game.cue_ball, game.balls)
ui.draw(surf, game, sound, (600, 350))

print("7. Test de l'IA...")
ai.start_turn(game.cue_ball, game.balls, "solids", difficulty="Moyen")
shot = ai.update(0.1, cue, game.cue_ball, game.balls, "solids")

print("TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
