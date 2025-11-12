
# Technical Game Design

## Réalisé par

- Behani Julien
- Fournier Enzo
- Alluin Edouard

---

## Table des matières

1. [Conceptualisation](#conceptualisation) (page 3)
2. [Gameplay & Mécaniques](#gameplay--mécaniques) (page 4)
3. [Système de troupes](#système-de-troupes) (page 5)
4. [Contraintes techniques](#contraintes-techniques) (page 6)
5. [Plateformes cibles](#plateformes-cibles) (page 6)
6. [Performances attendues](#performances-attendues) (page 6)
7. [Moteur de jeu](#moteur-de-jeu) (page 6)
8. [Middleware & Bibliothèques](#middleware--bibliothèques) (page 7)
9. [Contraintes de production](#contraintes-de-production) (page 7)
10. [Structure de données & Architecture](#structure-de-données--architecture) (page 7)
11. [Génération procédurale de la carte](#génération-procédurale-de-la-carte) (page 7)
12. [Gestion du déplacement (implémentation Pygame)](#gestion-du-déplacement-implémentation-pygame) (page 8)
13. [Méthodes de tir (implémentation Pygame)](#méthodes-de-tir-implémentation-pygame) (page 8)
14. [Outils & Debug](#outils--debug) (page 8)
15. [Roadmap technique](#roadmap-technique) (page 8)

---

## Analyse du GDS

### Besoins techniques

---

## 1. Conceptualisation

**Type de jeu :**  
Jeu de stratégie en temps réel (RTS) intégrant deux modes de contrôle :

- **Gestion indirecte** : style RTS classique, gestion des troupes, ressources et stratégie.  
    - Sélection des troupes, choix entre attaque ou défense.
    - IA de chaque bateau adapte sa tactique selon la stratégie demandée.

- **Contrôle direct** : prise de contrôle manuel d’un zeppelin (déplacements clavier, interactions souris).  
    - Architecture flexible permettant de basculer entre les deux modes via un bouton.

**Univers graphique :**  
- Style rétro-fantasy, vue du ciel, graphismes simplifiés mais stylisés.
- Orientation 2D, effets visuels légers (particules, explosions stylisées).

**Public cible :**  
- Joueurs de 12 ans et plus, cœur de cible : adolescents et jeunes adultes.
- Fans de stratégie, rétro gaming et univers fantasy.

---

## 2. Gameplay & mécaniques

### 2.1 Intelligence artificielle (IA)

L’IA ennemie gère :
- Économie (récolte, gestion de ressources)
- Production (création d’unités)
- Tactiques offensives/défensives

**Technologies :**
- Arbres de comportement (behavior trees)
- Machines à états finis (FSM)
- Systèmes heuristiques

### 2.2 Gestion des ressources et événements

- Système de récolte de ressources limitées (îlots)
- Événements aléatoires dynamiques :
    - Coffres volants (gold aléatoire)
    - Tempêtes (dégâts sur unités)
    - Vague de bandits (unités ennemies, dégâts)
    - Kraken (destruction aléatoire de tours/ressources)

> Générateur procédural d’événements en temps réel requis.

### 2.3 Carte de jeu

- Zones d’îlots reliées par espace aérien
- Terrain simplifié avec obstacles tactiques

### 2.4 Physique

- Déplacement des unités
- Collisions projectiles/unités
- Pas de physique réaliste

### 2.5 Contrôles

- RTS classique : achat/placement d’unités (souris)
- Action directe : contrôle manuel d’un zeppelin (clavier ZQSD/flèches + capacités + souris)

### 2.6 Déplacements (IA & manuel)

- Vitesse max, accélération, rotation, friction simulée
- Steering behaviors (seek, flee, arrive, pursuit/evade, obstacle avoidance)
- Contrôle manuel : accélération progressive

### 2.7 Pathfinding & algorithmes d’IA

- Grille de navigation (cellules carrées)
- Algorithmes : A* (heuristique Manhattan/Euclidienne), Min/Max
- Replanification sur événement

### 2.8 Tir & balistique simplifiée

- Types de tir : canon, collision via bounding circles/rects, raycast
- Visée : souris + click (manuel)
- Gestion : cooldown, priorité de cible

---

## 3. Système de troupes

Chaque unité :
- Caractéristiques : coût, vitesse, dégâts, armure, rayon d’action, délai de rechargement
- Capacité spéciale : compétence unique déclenchable
- Système modulaire : héritage Zeppelin, gestion des états temporaires (buff/debuff, cooldowns, invincibilité, boucliers)
- Effets visuels associés

---

## 4. Contraintes techniques

- Carte dynamique avec événements
- Grand nombre d’unités simultanées (optimisation IA + pathfinding)
- Hybridation RTS + Action directe

---

## 5. Plateformes cibles

- Plateforme principale : PC Windows
- Contrôles optimisés clavier/souris
- Pas de version mobile

---

## 6. Performances attendues

- CPU : Intel i3 ou équivalent
- GPU : Carte graphique intégrée ou GTX 1050
- RAM : 4 Go
- Stockage : 2 Go
- FPS : 30 stables en 720p

---

## 7. Moteur de jeu

- **Prioritaire :** Pygame (Python)
    - Avantages : simplicité, rapidité de prototypage, bibliothèques IA
    - Inconvénients : performance limitée
- **Secondaire :** C++ avec SDL/OpenGL
    - Avantages : robustesse, performance
    - Inconvénients : développement complexe

> Stratégie : démarrage sur Pygame, bascule vers C++ si besoin.

---

## 8. Middleware & bibliothèques

- Audio : FMOD ou Wwise
- Pathfinding : A* ou NavMesh
- Physique : moteur natif
- Versioning : Git (GitHub/GitLab)

---

## 9. Contraintes de production

- Textures : 2K max
- Effets spéciaux : spritesheets, particules légères

---

## 10. Structure de données & architecture

### 10.3 Données de carte

- Grille (width × height)
- Cell : type, coût, drapeaux
- Bitmask d’obstacles pour A*
- Graph de navigation : nœuds = ports/îlots/points de passage

### 10.4 Indexation & requêtes spatiales

- Spatial hash / quadtree
- Buckets dynamiques pour projectiles

### 10.5 Persistance & config

- JSON/YAML pour définitions
- Replays optionnels

---

## 11. Génération procédurale de la carte

- Entrées : seed, taille, densité d’îlots, budget navires, niveau menace
- Pipeline :
    - Placement d’îlots (Poisson disk sampling)
    - Couloirs aériens (Voronoï/Delaunay)
    - Événements (bandes d’orage, bandits, kraken, mines)
    - Ressources : distribution pondérée
    - Points d’intérêt : îles
    - Validation : connectivité globale, coût max borné
- Sortie : grille + graph

---

## 12. Gestion du déplacement (implé Pygame)

- Position Vector2, vitesse, angle, hitbox cercle/rect
- Entrées :
    - Manuel : ZQSD/flèches, souris pour viser
    - RTS : clic gauche (achat), clic droit (déplacement)
- Caméra/zoom : transform.smoothscale

---

## 13. Méthodes de tir (implé Pygame)

- Armes : interface tir + cooldown
- Projectiles : affichage et déplacement
- Rayons : raycast, dégâts instantanés, effets visuels persistants
- Effets : explosion area-of-effect, DOT/slow/stun

---

## 14. Outils & debug

- Overlay : coûts A*, chemins, champs d’influence, FPS, compte entités
- Profiler : temps par système
- Cheats : révéler carte, spawn unités, sauter événements

---

## 15. Roadmap technique (proto → alpha)

- Proto core (Pygame) : boucle, rendu, input, entités, collisions, tir canon
- Pathfinding A* + avoidance, sélection/ordres RTS
- Génération carte, ressources, événements basiques
- IA basique, combats de groupe
- Stress-test : 5-10 unités, métriques FPS ; bascule C++ si besoin

