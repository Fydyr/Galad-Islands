## Synthèse narrative

Ce document présente une vue d'ensemble des événements dynamiques, obstacles, buffs, projectiles et stratégies clés du jeu. Il détaille les effets des mines, tempêtes, krakens, bandits et coffres volants, ainsi que les interactions entre unités et les synergies exploitables par l'IA. Les tableaux récapitulent les valeurs essentielles, limites du moteur et combinaisons stratégiques, permettant une compréhension rapide des mécanismes et des opportunités d'optimisation pour le développement d'une IA performante.

## Événements dynamiques
### Tempête

### Kraken

### Mines
**Valeurs précises extraites du code :**
- Dégâts infligés par une mine : **40 PV**
- Santé d'une mine : **1 PV** (détruite en une collision)
- Effet : collision = explosion, dégâts à l'entité qui percute, la mine est détruite

## Collisions et obstacles
**Événement spécial présent dans le code :**
- Dégâts par attaque de bandit : **20 PV**
- Rayon d'effet : **5 x TILE_SIZE**
- Invulnérabilité après spawn : **1.0s**
- Exploitation possible : profiter de l'invulnérabilité pour positionnement agressif
- Projectiles détruits hors limites
- Unités stoppées aux bords
Non présentes dans le code (aucune occurrence détectée)
- Bases : hitbox ~293x262 px, infligent 50 dégâts au contact
- Système de cooldown pour éviter les dégâts continus (1s entre deux impacts sur la même entité)
**Exploitation des mines :**
- Les mines sont neutres (team_id=0), peuvent être utilisées pour piéger les adversaires
- Les mines ne sont pas ciblées par les tours

## Buffs et debuffs
**Bandits :**
- Invulnérabilité 1s après spawn
- Dégâts 20 PV par attaque
- Immobilisation Druid : durée 5s

## Types de projectiles et effets secondaires
- Type : bullet, fireball, tentacle
- Dégâts : variable selon l’origine (ex : tentacule kraken = 1)
- Vie : 1
- Durée de vie : 1.2s
- Effet secondaire : certains projectiles peuvent immobiliser (ex : Druid)

## Règles d’exploitation des coffres
- Coffre volant : spawn toutes les 20s, max 2 actifs
- Or : 60-150
- Durée de vie : 25s
- Animation de chute : 3s
- Stratégie : collecter dès l’apparition, priorité pour les unités rapides ou invincibles

## Situations critiques et réactions IA
- Tempête proche : éviter la zone, prioriser la fuite ou l’utilisation de bouclier/invincibilité
- Coffre en chute : agir vite pour la collecte
# Commentaires sur les synergies, contres et combos
- Architecte + Druid : zone de contrôle + immobilisation
- Maraudeur + Scout : bouclier + invincibilité pour prise de coffre ou percée
- Immobiliser les ennemis dans la zone d’effet Architecte pour maximiser les dégâts

## Unités principales
---
## Synthèse optimisée pour IA

### Table des événements et effets
| Événement      | Dégâts      | Rayon/Zone         | Durée/Timing         | Exploitation/Notes |
|:--------------:|:-----------:|:------------------:|:--------------------:|:------------------:|
| Tempête        | 30          | 5 tuiles           | 5%/5s, durée variable | Éviter, bouclier   |
| Kraken         | 1/tentacule | tuiles spécifiques | event_duration        | Nettoyage auto     |
| Mine           | 40          | 1 tuile (collision)| instantané            | Piège, neutre      |
| Bandit         | 20          | 5 x TILE_SIZE      | invulnérabilité 1s    | Attaque rapide     |
| Coffre volant  | -           | -                  | 20s, max 2, vie 25s   | Collecte rapide    |

### Table des limites moteur
| Élément              | Limite/Constante         |
|:--------------------:|:-----------------------:|
| Ressources d’île     | max 3 actifs            |
| Coffres volants      | max 2 actifs            |
| Mines                | selon carte             |
| Marge collision      | 32 px                   |
| Unités/projectiles   | dépend config/carte     |

### Table des buffs/débuffs
| Effet                | Valeur/Timing           |
|:--------------------:|:-----------------------:|
| Bouclier Maraudeur   | 20-45% réduction, 5s    |
| Invincibilité Scout  | 3s                      |
| Immobilisation Druid | 5s                      |
| Bandit invulnérable  | 1s après spawn          |

### Table des synergies et patterns
| Combo/Synergie           | Effet stratégique                      |
|:------------------------:|:--------------------------------------:|
| Architecte + Druid       | Zone + immobilisation                  |
| Maraudeur + Scout        | Bouclier + invincibilité, percée/coffre|
| Druid vs unités rapides  | Immobilisation                         |
| Maraudeur défense        | Résistance accrue                      |
| Scout invincibilité      | Traversée tempête/coffre               |
| Architecte zone          | Maximiser dégâts immobilisés           |

---

### Zasper (Scout)
- Coût : 10 gold (allié), 12 gold (ennemi)
### Barhamus (Maraudeur)
- Coût : 20 gold (allié), 25 gold (ennemi)
### Draupnir (Leviathan)
- Coût : 40 gold (allié), 45 gold (ennemi)
### Druid
- Coût : 30 gold (allié), 35 gold (ennemi)
### Architect
- Coût : 30 gold (allié), 32 gold (ennemi)
## Tours
- Tour de défense : coût 25 gold (allié), 30 (ennemi), armure 70/80, radius 8/9
## Projectiles
- Vitesse : 10.0 px/frame
## Bases
- Vie : 1000
## Ressources et événements
**Limites moteur et contraintes physiques :**
- Ressources d’île : **max 3 actifs** (`ISLAND_RESOURCE_MAX_COUNT = 3`)
## Terrain
- Modificateur normal : 1.0
## Offsets de spawn ennemis
- Scout : -150
## Autres constantes utiles
- Accélération : 0.2
- Durée effet : 10 s
