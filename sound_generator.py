"""
Générateur d'effets sonores réalistes pour le jeu de billard (8 Ball Pool).
Génère des fichiers WAV en pur Python sans dépendances externes.
"""
import math
import struct
import wave
import os

def generate_wave(filename, duration, sample_rate, wave_func):
    """Génère un fichier WAV 16-bit mono."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    num_samples = int(duration * sample_rate)
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            sample = wave_func(t, duration)
            sample = max(-1.0, min(1.0, sample))
            int_sample = int(sample * 32767)
            frames.extend(struct.pack('<h', int_sample))
            
        wav.writeframes(frames)
    print(f"Généré: {filename}")

def cue_hit_func(t, duration):
    """Coup de queue sec avec résonance bois/cuir."""
    # Transitoire sec (bruit blanc amorti) + résonance bois ~400Hz et ~1200Hz
    decay = math.exp(-t * 45)
    body = math.sin(2 * math.pi * 380 * t) * 0.6 + math.sin(2 * math.pi * 1150 * t) * 0.4
    noise = (math.sin(t * 89234.123) % 1.0 - 0.5) * 1.5 * math.exp(-t * 90)
    return (body * 0.5 + noise * 0.5) * decay

def ball_hit_func(t, duration):
    """Choc sec et cristallin de deux boules de billard (résine phénolique)."""
    # Deux pics très nets: ~2200Hz et ~4800Hz avec décroissance très rapide
    decay = math.exp(-t * 60)
    h1 = math.sin(2 * math.pi * 2100 * t) * 0.7
    h2 = math.sin(2 * math.pi * 4600 * t) * 0.35
    h3 = math.sin(2 * math.pi * 9200 * t) * 0.15 * math.exp(-t * 120)
    click = (math.sin(t * 99123.4) % 1.0 - 0.5) * 1.0 * math.exp(-t * 180)
    return (h1 + h2 + h3 + click) * decay

def rail_hit_func(t, duration):
    """Rebond sourd et élastique sur la bande en caoutchouc."""
    decay = math.exp(-t * 28)
    body = math.sin(2 * math.pi * 160 * t) * 0.8 + math.sin(2 * math.pi * 320 * t) * 0.3
    thump = math.sin(2 * math.pi * 90 * (t ** 0.8)) * 0.5
    return (body + thump) * decay * 0.9

def pocket_drop_func(t, duration):
    """Bruit d'une bille qui tombe dans la poche en cuir/filet."""
    decay = math.exp(-t * 15)
    # Double bruit: impact sur le bord puis chute dans le filet
    t1 = t
    t2 = max(0.0, t - 0.05)
    sound1 = math.sin(2 * math.pi * 240 * t1) * math.exp(-t1 * 30)
    sound2 = (math.sin(2 * math.pi * 140 * t2) + math.sin(2 * math.pi * 95 * t2) * 0.6) * math.exp(-t2 * 12)
    return (sound1 * 0.6 + sound2 * 0.8) * decay

def foul_func(t, duration):
    """Son d'erreur / faute (accord mineur descendant)."""
    decay = math.exp(-t * 4)
    f1 = 280 if t < 0.15 else 210
    tone = math.sin(2 * math.pi * f1 * t) * 0.6 + math.sin(2 * math.pi * (f1 * 1.2) * t) * 0.3
    return tone * decay

def win_func(t, duration):
    """Son de victoire (accord majeur ascendant et éclatant)."""
    decay = math.exp(-t * 2)
    step = int(t * 8)
    freqs = [440, 554, 659, 880, 1108, 1318]
    f = freqs[min(step, len(freqs)-1)]
    tone = math.sin(2 * math.pi * f * t) * 0.6 + math.sin(2 * math.pi * f * 2 * t) * 0.2
    return tone * decay

def create_all_sounds(output_dir="assets/sounds"):
    sr = 44100
    generate_wave(os.path.join(output_dir, "cue_hit.wav"), 0.2, sr, cue_hit_func)
    generate_wave(os.path.join(output_dir, "ball_hit.wav"), 0.18, sr, ball_hit_func)
    generate_wave(os.path.join(output_dir, "rail_hit.wav"), 0.25, sr, rail_hit_func)
    generate_wave(os.path.join(output_dir, "pocket.wav"), 0.4, sr, pocket_drop_func)
    generate_wave(os.path.join(output_dir, "foul.wav"), 0.5, sr, foul_func)
    generate_wave(os.path.join(output_dir, "win.wav"), 0.9, sr, win_func)
    print("Tous les sons ont été générés avec succès !")

if __name__ == "__main__":
    create_all_sounds()
