# 🎱 8 Ball Pool - Mini Jeu de Billard Américain

Un jeu de billard complet, fluide et réaliste inspiré du célèbre **8 Ball Pool** (Miniclip), développé en **Python (Pygame)** avec une version web instantanée en **HTML5 Canvas**.

---

## 🚀 Comment Lancer le Jeu

### Option 1 : Double-clic direct (Le plus simple)
Double-cliquez simplement sur le fichier **`Lancer_Billard.bat`** situé dans ce dossier.

### Option 2 : En ligne de commande
Dans un terminal PowerShell ou CMD :
```bash
py main.py
# ou
python main.py
```

### Option 3 : Version Web instantanée dans le navigateur
Double-cliquez sur **`index.html`** pour jouer directement dans votre navigateur web préféré (Chrome, Edge, Firefox) sans aucune installation !

---

## 🎮 Commandes et Contrôles

| Action | Commande |
|---|---|
| **Viser** | Déplacez simplement la **Souris** autour de la bille blanche |
| **Ajustement d'angle fin** | **Molette de la souris** ou **Flèches Gauche / Droite** |
| **Tirer / Doser la force** | Glissez le curseur sur la **jauge de gauche (FORCE)** ou maintenez la touche **ESPACE** |
| **Régler l'effet (Spin)** | Cliquez dans la bille en bas à droite (**Rétro / Coulé / Effet latéral**) |
| **Bille en main (Faute adverse)** | Cliquez n'importe où sur le tapis vert pour déposer la blanche |
| **Nouvelle partie** | Touche **R** ou clic sur le bouton *Rejouer* |
| **Activer / Couper le son** | Touche **M** ou bouton *Son : ON/OFF* |
| **Menu d'aide & Règles** | Touche **H** ou bouton *Aide (?)* |

---

## 🏆 Règles Officielles du 8 Ball Pool

1. **La Casse** : Le match démarre avec les 15 billes en triangle réglementaire (la bille 8 noire au centre).
2. **Attribution des groupes** : La table reste ouverte jusqu'à ce qu'un joueur empoche légalement une bille après la casse. Les deux groupes sont :
   - **Pleines** (*Solids*) : billes 1 à 7
   - **Rayées** (*Stripes*) : billes 9 à 15
3. **Fautes et Bille en main** :
   - Empocher la bille blanche (scratch).
   - Ne toucher aucune bille avec la blanche.
   - Toucher une bille du camp adverse en premier.
   - *Pénalité* : L'adversaire récupère la **Bille en Main** et peut la placer librement n'importe où sur la table !
4. **La Bille 8 (Noire)** :
   - Vous devez vider toutes les billes de votre groupe avant de pouvoir viser la 8.
   - Empocher la 8 légalement = **VICTOIRE** !
   - Empocher la 8 trop tôt ou faire tomber la blanche en même temps = **DÉFAITE IMMÉDIATE** !

---

## ✨ Fonctionnalités Avancées

- **Visée Assistée Style 8 Ball Pool** :
  - Ligne de visée dynamique vers la bille cible.
  - Bille fantôme (*Ghost Ball*) matérialisant le point d'impact exact.
  - Ligne de déviation de la bille visée et trajectoire tangente de la blanche.
  - Éclairage doré sur la poche visée.
- **Moteur Physique avec Sub-stepping** : 10 sous-pas par image pour éviter tout passage à travers les bandes même à vitesse maximale.
- **Effets de Spin Réalistes** :
  - **Rétro (*Backspin*)** : la bille blanche recule après l'impact.
  - **Coulé (*Topspin*)** : la bille blanche suit la cible.
  - **Effets latéraux (*English*)** : modifie l'angle de rebond sur les bandes.
- **Intelligence Artificielle Complète** :
  - Calcule les angles de coupe (*cut angles*) et vérifie les trajectoires sans obstacle.
  - 3 modes de difficulté : **Facile**, **Moyen** et **Pro**.
- **Effets Sonores Synthétisés** : Chocs secs en résine phénolique, rebonds feutrés sur bande en caoutchouc, rentrée dans le filet de poche et jingles de victoire.
