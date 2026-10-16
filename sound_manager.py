"""
Gestionnaire sonore pour le billard : chargement des bruitages WAV et gestion du volume.
"""
import pygame
import os

class SoundManager:
    def __init__(self, sound_dir="assets/sounds"):
        self.muted = False
        self.sounds = {}
        
        # Initialisation du mixer audio de Pygame
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
        except Exception as e:
            print("Erreur initialisation mixer audio:", e)

        # Chargement des effets
        sound_files = {
            "cue": "cue_hit.wav",
            "ball": "ball_hit.wav",
            "rail": "rail_hit.wav",
            "pocket": "pocket.wav",
            "foul": "foul.wav",
            "win": "win.wav"
        }
        
        for name, fname in sound_files.items():
            path = os.path.join(sound_dir, fname)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Impossible de charger {fname}:", e)
            else:
                print(f"Fichier son absent: {path}")

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted

    def play_cue_hit(self, volume=1.0):
        if not self.muted and "cue" in self.sounds:
            snd = self.sounds["cue"]
            snd.set_volume(min(1.0, max(0.1, volume)))
            snd.play()

    def play_ball_hit(self, volume=1.0):
        if not self.muted and "ball" in self.sounds:
            snd = self.sounds["ball"]
            snd.set_volume(min(1.0, max(0.1, volume)))
            snd.play()

    def play_rail_hit(self, volume=1.0):
        if not self.muted and "rail" in self.sounds:
            snd = self.sounds["rail"]
            snd.set_volume(min(1.0, max(0.1, volume * 0.8)))
            snd.play()

    def play_pocket(self):
        if not self.muted and "pocket" in self.sounds:
            snd = self.sounds["pocket"]
            snd.set_volume(0.9)
            snd.play()

    def play_foul(self):
        if not self.muted and "foul" in self.sounds:
            snd = self.sounds["foul"]
            snd.set_volume(0.85)
            snd.play()

    def play_win(self):
        if not self.muted and "win" in self.sounds:
            snd = self.sounds["win"]
            snd.set_volume(0.95)
            snd.play()
