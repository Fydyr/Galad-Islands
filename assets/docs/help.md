# Guide du Joueur - Galad Islands

## Contrôles du Jeu

### Joueur 1
- **Z** : Avancer
- **S** : Reculer
- **Q** : Tourner à gauche
- **D** : Tourner à droite
- **&** : Sélectionner la troupe précédente
- **"** : Sélectionner la prochaine troupe
- **A** : Activer le mode attaque
- **E** : Activer la capacité spéciale
- **CTRL** : Arrêt du vaisseau

### Caméra / Carte
- **Flèches directionnelles** : Déplacer la caméra sur la carte (haut/bas/gauche/droite)
- **Molette de la souris** : Zoom avant/arrière sur la carte
- **Échap** : Quitter la vue carte et revenir au menu

## Guide des Troupes

### Unités de Combat

#### **Zasper** (Scout Léger) - 10 Gold
![Zasper allié](/assets/docs/units/ally/Scout.png)
![Zasper ennemi](/assets/docs/units/enemy/Scout.png)
- **Vitesse** : 5/s 
- **Dégâts** : 10-15
- **Armure** : 60 PV
- **Portée** : 5 cases
- **Rechargement** : 1s
- **Capacité spéciale** : _Manœuvre d'évasion_ - Invincibilité 3s
- **Stratégie** : Idéal pour la reconnaissance et les frappes rapides. Ne tire que vers l'avant.

#### **Barhamus** (Maraudeur Moyen) - 20 Gold
![Barhamus allié](/assets/docs/units/ally/Maraudeur.png)
![Barhamus ennemie](/assets/docs/units/enemy/Maraudeur.png)
- **Vitesse** : 3.5/s
- **Dégâts** : 20-30 (salve) / 10-15 (boulet)
- **Armure** : 130 PV
- **Portée** : 7 cases
- **Rechargement** : 2s
- **Capacité spéciale** : _Bouclier de mana_ - Réduit les dégâts de 20-45%
- **Stratégie** : Équilibré, peut tirer depuis l'avant et les côtés.

#### **Draupnir** (Léviathan Lourd) - 40 Gold
![Draupnir allié](/assets/docs/units/ally/Leviathan.png)
![Draupnir ennemie](/assets/docs/units/enemy/Leviathan.png)
- **Vitesse** : 2/s (Le plus lent)
- **Dégâts** : 40-60 (salve) / 15-20 (boulet)
- **Armure** : 300 PV (Le plus résistant!)
- **Portée** : 10 cases
- **Rechargement** : 4.5s
- **Capacité spéciale** : _Seconde salve_ - Tire immédiatement une 2e salve
- **Stratégie** : Tank puissant avec 3 canons de chaque côté, parfait pour les assauts frontaux.

### Unités de Support

#### **Druid** - 30 Gold
![Druid allié](/assets/docs/units/ally/Druid.png)
![Druid ennemi](/assets/docs/units/enemy/Druid.png)
- **Vitesse** : 4/s
- **Soin** : 20 PV
- **Armure** : 100 PV
- **Portée** : 7 cases
- **Rechargement** : 4s
- **Capacité spéciale** : _Lierre volant_ - Immobilise un ennemi 5s
- **Stratégie** : Support essentiel pour maintenir vos troupes en vie.

#### **Architect** - 30 Gold
![Architect allié](/assets/docs/units/ally/Architect.png)
![Architect ennemie](/assets/docs/units/enemy/Architect.png)
- **Vitesse** : 4/s
- **Armure** : 100 PV
- **Capacité spéciale** : _Rechargement automatique_ - Divise par 2 le cooldown des alliés (rayon 8 cases)
- **Stratégie** : Peut construire des tours sur les îles pour défendre ou soigner.

#### **Kamikase** - 30 Gold
![Kamikase allié](/assets/docs/units/ally/Kamikase.png)
![Kamikase ennemie](/assets/docs/units/enemy/kamikase.png)
- **Vitesse** : 6/s (Le plus rapide!)
- **Dégâts** : instantané (en une fois)
- **Armure** : 60 PV
- **Portée** : 0 case (collision)
- **Stratégie** : Idéal pour les vaisseaux lourd ou pour les tours

## Structures

### Tour de Défense
![Tour de Défense allié](/assets/sprites/buildings/ally/ally-defence-tower.png)
![Tour de Défense ennelie](/assets/sprites/buildings/enemy/enemy-heal-tower.png)
- **Dégâts** : 25
- **Portée** : 8 cases
- **Rechargement** : 10s
- **Armure** : 70 PV
- **Note** : Construite par l'Architect sur les îles

### Tour de Soin
![Tour de Soin allié](/assets/sprites/buildings/ally/ally-heal-tower.png)
![Tour de Soin ennemie](/assets/sprites/buildings/enemy/enemy-attack-tower.png)
- **Soin** : 15 PV
- **Portée** : 5 cases
- **Rechargement** : 10s
- **Armure** : 70 PV
- **Note** : Construite par l'Architect sur les îles

## Événements Aléatoires

### Dangers
- **Tempêtes** (15% chance)
![Tempêtes](/assets/event/tempete.png)
  - Dégâts : 30 toutes les 3s
  - Zone : 4 cases
  - Durée : 20s

- **Vague de bandits** (25% chance)
![Vague de bandits](/assets/event/pirate_ship.png)
  - 1-6 navires ennemis
  - Dégâts : 20
  - Traverse la carte d'ouest en est

- **Kraken** (10% chance)
![Kraken](/assets/event/kraken.png)
  - Dégâts : 70
  - 2-6 tentacules
  - Attaque les îles et détruit tours/ressources

- **Mines volantes**
![Mines](/assets/sprites/terrain/mine.png)
  - Dégâts : 40
  - Placement aléatoire au début de partie

### Bonus
- **Coffres volants** (20% chance)
![chest](/assets/event/chest_close.png)
  - Récompense : 10-20 Gold
  - 2-5 coffres par événement
  - Durée : 20s avant disparition

## Conseils Stratégiques

### Début de Partie
1. Commencez avec 2-3 Zasper pour explorer rapidement
2. Sécurisez les îles proches pour les ressources
3. Placez un Architect sur une île stratégique

### Milieu de Partie
1. Équilibrez votre flotte : scouts, maraudeurs et support
2. Utilisez les Druids pour maintenir vos unités en vie
3. Anticipez les événements aléatoires

### Fin de Partie
1. Rassemblez vos forces pour l'assaut final
2. Les Draupnir sont excellents pour détruire les bases
3. Gardez des unités en défense de votre base

## Objectif
Détruisez la base ennemie tout en protégeant la vôtre!

## Configuration Requise Minimale
- **CPU** : Intel i3 ou équivalent
- **GPU** : Carte graphique intégrée ou GTX 1050
- **RAM** : 4 Go
- **Stockage** : 2 Go
- **OS** : Windows/Linux/Mac

---
*Bon vol et que les vents vous soient favorables!*