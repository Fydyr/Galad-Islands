---
i18n:
  en: "AI System"
  fr: "Système d'IA"
---

# Système d'Intelligence Artificielle (IA)

## Vue d'ensemble

Le système d'IA de Galad Islands est conçu pour offrir un adversaire crédible et des comportements autonomes pour les unités. Il combine des modèles de Machine Learning pour les décisions stratégiques de haut niveau (comme la `BaseAi`) et des logiques plus simples pour les comportements individuels des unités (comme le `KamikazeAiProcessor`).

## IA de la Base (`BaseAi`)

**Fichier** : `src/ia/BaseAI.py`

L'IA de la base est le cerveau stratégique de l'équipe adverse. Elle décide quelle unité produire en fonction de l'état actuel du jeu.

### Architecture

- **Modèle** : `RandomForestRegressor` de Scikit-learn. Ce modèle est un ensemble d'arbres de décision qui prédit une "valeur Q" (une estimation de la récompense future) pour chaque action possible.
- **Fichier modèle** : Le modèle entraîné est sauvegardé dans `src/models/base_ai_unified_final.pkl`.
- **Logique de décision** : Pour prendre une décision, l'IA évalue toutes les actions possibles (produire chaque type d'unité, ou ne rien faire) et choisit celle avec la plus haute valeur Q prédite, tout en vérifiant si elle a assez d'or.

### Vecteur d'état (State Vector)

Le modèle prend en entrée un vecteur décrivant l'état du jeu, combiné à une action possible. La prédiction est la récompense attendue pour cet état-action.

Le vecteur d'état-action est composé des 9 caractéristiques suivantes :

| Index | Caractéristique | Description |
|---|---|---|
| 0 | `gold` | Or disponible pour l'IA. |
| 1 | `base_health_ratio` | Santé de la base de l'IA (ratio de 0.0 à 1.0). |
| 2 | `allied_units` | Nombre d'unités alliées. |
| 3 | `enemy_units` | Nombre d'unités ennemies connues. |
| 4 | `enemy_base_known` | Si la position de la base ennemie est connue (0 ou 1). |
| 5 | `towers_needed` | Indicateur binaire si des tours de défense sont nécessaires. |
| 6 | `enemy_base_health` | Santé de la base ennemie (ratio). |
| 7 | `allied_units_health` | Santé moyenne des unités alliées (ratio). |
| 8 | `action` | L'action envisagée (entier de 0 à 6). |

### Processus d'entraînement

L'entraînement est réalisé par le script `train_unified_base_ai.py`. Il combine plusieurs sources de données pour créer un modèle robuste :

1. **Scénarios Stratégiques (`generate_scenario_examples`)**
    - Des exemples de jeu sont générés à partir de scénarios clés définis manuellement (ex: "Défense prioritaire", "Exploration nécessaire", "Coup de grâce").
    - Chaque scénario associe un état de jeu à une action attendue et une récompense élevée. Les actions incorrectes reçoivent une pénalité.
    - Certains scénarios comme l'exploration et la défense sont surreprésentés pour renforcer ces comportements.
    - **Stratégie en deux phases** : L'entraînement met l'accent sur une stratégie en deux temps.
        1. **Phase d'exploration** : Tant que la base ennemie n'est pas connue (`enemy_base_known = 0`), l'IA est fortement incitée à produire des éclaireurs.
        2. **Phase d'assaut** : Une fois la base localisée (`enemy_base_known = 1`), si l'IA a un avantage économique, elle est récompensée pour la production d'unités lourdes comme le Léviathan, afin de lancer l'assaut final.

2. **Auto-apprentissage (`simulate_self_play_game`)**
    - Des parties complètes sont simulées entre deux instances de l'IA.
    - Chaque décision prise et la récompense obtenue sont enregistrées comme une expérience.
    - Cela permet à l'IA de découvrir des stratégies émergentes dans un contexte de jeu réaliste.

3. **Objectif de Victoire (`generate_victory_scenario`)**
    - Similaire à l'auto-apprentissage, mais avec un bonus de récompense très important pour l'IA qui gagne la partie (en détruisant la base adverse).
    - Cela renforce l'objectif final de la victoire et incite l'IA à prendre des décisions qui y mènent.

Toutes ces données sont ensuite utilisées pour entraîner le `RandomForestRegressor`.

### Démonstration

Le script `demo_base_ai.py` permet de tester les décisions de l'IA dans divers scénarios et de vérifier que son comportement est conforme aux attentes stratégiques.

```python
# Extrait de demo_base_ai.py
scenarios = [
    {
        "name": "Début de partie - Exploration nécessaire",
        "gold": 100,
        "enemy_base_known": 0, # <-- Base ennemie inconnue
        "expected": "Éclaireur"
    },
    {
        "name": "Défense prioritaire - Base très endommagée",
        "gold": 150,
        "base_health_ratio": 0.5, # <-- Santé basse
        "expected": "Maraudeur"
    },
    # ... autres scénarios
]
```

### Création et Entraînement d'une Nouvelle IA de Base

Pour créer ou affiner une nouvelle version de l'IA de la base, le processus implique principalement la modification du script d'entraînement `train_unified_base_ai.py` et potentiellement de la logique de décision à base de règles dans `BaseAi.decide_action_for_training`.

**Étapes clés :**

1. **Définir les comportements souhaités (le "professeur")**
    - La méthode `BaseAi.decide_action_for_training` agit comme un "professeur" pour le modèle de Machine Learning. C'est ici que vous définissez les règles de décision idéales pour l'IA dans divers états du jeu.
    - Si vous souhaitez que l'IA apprenne de nouveaux comportements ou modifie ses priorités (par exemple, privilégier un nouveau type d'unité ou une stratégie de défense différente), vous devez d'abord implémenter ces règles dans cette méthode.
    - Le modèle de Machine Learning apprendra ensuite à imiter et à généraliser ces règles à travers les simulations.

2. **Ajuster les scénarios stratégiques (`generate_scenario_examples`)**
    - Dans `train_unified_base_ai.py`, la fonction `generate_scenario_examples` crée des exemples de jeu basés sur des situations clés.
    - Si vous introduisez de nouvelles unités ou des mécaniques de jeu importantes, il est crucial d'ajouter des scénarios pertinents ici pour guider l'IA vers les bonnes décisions dans ces contextes.
    - Vous pouvez ajuster le `repeat` et `reward_val` pour surpondérer certains comportements jugés plus importants.

3. **Exécuter l'entraînement unifié (`train_unified_base_ai.py`)**
    - Le script `train_unified_base_ai.py` orchestre l'ensemble du processus d'entraînement :
        - Génération d'exemples à partir de scénarios stratégiques.
        - Simulation de parties complètes en auto-apprentissage (`simulate_self_play_game`).
        - Simulation de parties avec un objectif de victoire renforcé (`generate_victory_scenario`).
    - Exécutez le script avec les paramètres souhaités (nombre de scénarios, de parties de self-play, etc.) :

        ```bash
        python train_unified_base_ai.py --n_scenarios 2000 --n_selfplay 1000 --n_victory 500 --n_iterations 5
        ```

    - Le script sauvegardera le modèle entraîné sous `src/models/base_ai_unified_final.pkl`.

4. **Vérifier le comportement de l'IA (`demo_base_ai.py`)**
    - Utilisez le script `demo_base_ai.py` pour tester le nouveau modèle dans une série de scénarios prédéfinis.
    - Assurez-vous que l'IA prend les décisions attendues et que son comportement est conforme à vos attentes stratégiques.
    - Si le comportement n'est pas satisfaisant, retournez à l'étape 1 ou 2 pour affiner les règles et les scénarios d'entraînement.

5. **Intégrer le nouveau modèle dans le jeu**
    - Une fois satisfait du modèle, assurez-vous que la méthode `BaseAi.load_or_train_model()` dans `src/ia/BaseAi.py` est configurée pour charger le fichier `base_ai_unified_final.pkl`. C'est le comportement par défaut si ce fichier existe.
    - La classe `BaseAi` en jeu ne contient plus la logique d'entraînement, elle se contente de charger et d'utiliser le modèle.

Ce processus itératif permet d'affiner progressivement l'intelligence de la base pour qu'elle devienne un adversaire plus sophistiqué et réactif.

## IA des Unités

> 🚧 **Section en cours de rédaction**

En plus de l'IA de la base, certaines unités possèdent leur propre logique de comportement autonome, gérée par des processeurs ECS dédiés.

### IA des Kamikazes (`KamikazeAiProcessor`)

**Fichier** : `src/ia/KamikazeAi.py`

Contrairement à l'IA de la base, l'IA du Kamikaze n'utilise pas de modèle de Machine Learning. Il s'agit d'une **IA procédurale hybride** qui combine des algorithmes classiques pour obtenir un comportement de navigation intelligent et réactif.

Ce processeur gère le comportement des unités Kamikaze :

- **Recherche de cible** : Si la base ennemie n'est pas encore découverte (`KnownBaseProcessor`), le Kamikaze explore des points aléatoires dans le territoire ennemi. Une fois la base trouvée, il identifie en priorité les unités ennemies lourdes à proximité. Si aucune n'est trouvée, il cible la base ennemie.
- **Navigation à long terme (Pathfinding A\*)** : Il calcule un chemin optimal vers sa cible en utilisant l'algorithme A*. Pour éviter que l'unité ne "colle" aux obstacles, le pathfinding est exécuté sur une "carte gonflée" (`inflated_world_map`) où les îles sont artificiellement élargies.

    ```python
    # Extrait de KamikazeAiProcessor.py
    
    # Le chemin est calculé sur une carte où les obstacles sont plus larges
    path = self.astar(self.inflated_world_map, start_grid, goal_grid)
    
    if path:
        # Le chemin est ensuite converti en coordonnées mondiales
        world_path = [(gx * TILE_SIZE + TILE_SIZE / 2, gy * TILE_SIZE + TILE_SIZE / 2) for gx, gy in path]
        self._kamikaze_paths[ent] = {'path': world_path, ...}
    ```

- **Navigation à court terme (Évitement local)** : C'est le cœur de la réactivité de l'IA. À chaque instant, il détecte les dangers immédiats (projectiles, mines) et combine sa direction de chemin avec un "vecteur d'évitement" pour contourner ces dangers de manière fluide.

    ```python
    # Extrait de KamikazeAiProcessor.py

    # 1. Vecteur vers la cible du chemin (waypoint)
    desired_direction_vector = np.array([math.cos(math.radians(desired_direction_angle)), ...])

    # 2. Vecteur d'évitement (pousse l'unité loin des dangers)
    avoidance_vector = np.array([0.0, 0.0])
    for threat_pos in threats:
        # ... calcul du vecteur d'évitement pour chaque menace
        avoidance_vector += avoid_vec * weight

    # 3. Combinaison des deux vecteurs
    final_direction_vector = (1.0 - blend_factor) * desired_direction_vector + blend_factor * avoidance_vector
    ```

- **Recalcul dynamique** : Si son chemin est obstrué par un nouveau danger (comme une mine), il est capable de recalculer entièrement un nouvel itinéraire.

    ```python
    # Extrait de KamikazeAiProcessor.py
    all_dangers = threats + obstacles
    if any(math.hypot(wp[0] - danger.x, wp[1] - danger.y) < 2 * TILE_SIZE for wp in path_to_check for danger in all_dangers):
        # Un danger obstrue le chemin, il faut recalculer
        recalculate_path = True
    ```

- **Action** : Une fois à portée de sa cible finale, l'unité s'autodétruit.
- **Boost Stratégique** : L'IA conserve son boost et l'active spécifiquement lorsqu'elle s'approche de la base ennemie pour maximiser ses chances d'atteindre la cible.

### IA des Eclaireurs (`RapidTroopAIProcessor`)

L'IA des éclaireurs (Scouts ennemis) repose sur une machine à états finis (FSM) et un système de priorités pour choisir l'action la plus pertinente à chaque instant. Elle utilise des règles et des scores pour chaque objectif (pas de machine learning).

**Cycle de décision :**

1. Mise à jour du contexte (santé, position, danger)
2. Évaluation des objectifs (coffre, druide, attaque, base, survie)
3. Sélection de l'objectif prioritaire
4. Changement d'état si besoin (`Idle`, `GoTo`, `Flee`, `Attack`, etc.)
5. Exécution de l'action (déplacement, tir, fuite...)

**Objectifs principaux :**

- Collecter les coffres volants (gain d'or pour acheter des alliés)
- Survivre le plus longtemps
- Attaquer tactiquement à distance sécurisée avec tir continu
- Si un Druide est présent et la santé bonne, harcèlement de base à distance sécurisée

#### Architecture du système

Principaux composants :

- `RapidTroopAIProcessor` : boucle principale, gestion des contrôleurs, événements, overlay debug
- `RapidUnitController` : décisions et exécution pour une unité, actualisation contexte, FSM, coordination, tir continu
- `GoalEvaluator` : évaluation séquentielle par priorités, gestion coordination
- Services auxiliaires : `DangerMapService`, `PathfindingService`, `PredictionService`, `CoordinationService`, `AIContextManager`, `IAEventBus`

#### Évaluation des objectifs (`GoalEvaluator`)

Objectifs par priorité :

- `goto_chest` (100) : coffres visibles + non assignés
- `follow_druid` (90) : santé < 95% + druide présent
- `attack` (80) : unités ennemies stationnaires
- `follow_die` (70) : ennemi < 60 HP + rôle assigné
- `attack_base` (60) : base ennemie + santé > 35%
- `survive` (10) : fallback

Logique séquentielle : priorité maximale : coffres → druide → harcèlement → exécution → attaque base → survie


#### Machine à états finis (FSM)

États : `Idle`, `GoTo`, `Flee`, `Attack`, `FollowDruid`, `FollowToDie`

Transitions globales et locales selon priorité et conditions (danger, santé, navigation, etc.)

#### États détaillés

- **IdleState** : drift vers zone sûre, attend transitions, annule navigation si inactive
- **FleeState** : mouvement vers safest_point, hysteresis, cooldown, interdit si santé > 50%
- **GoToState** : navigation A* vers target, replan, tolérance waypoint
- **AttackState** : anchor system, positions valides autour cible, tir continu
- **FollowToDieState** : poursuite aggressive, ignore danger, tir continu
- **FollowDruid** : approche druide, orbite sécurisée, transition Idle si santé rétablie

#### Système de danger

- Sources dynamiques : projectiles, tempêtes, bandits, unités alliées
- Sources statiques : mines, îles, bords carte

#### Pathfinding pondéré (A*)

- Coûts de tuiles, optimisations (sub-tile factor, blocked margin, recompute distance, waypoint radius)

#### Logique de combat

- Tir continu (`_try_continuous_shoot`) chaque tick, orientation automatique, reset cooldown
- `AttackState` : anchor computation, distance optimale, position aléatoire, ajustement

#### Coordination inter-unités

- Rôles exclusifs (coffres, harcèlement, follow-to-die)
- Services de coordination, event bus, prediction

#### Configuration JSON externe

Exemple :

```json
{
    "danger": {"safe_threshold": 0.45, "flee_threshold": 0.7},
    "weights": {"survive": 4.0, "chest": 3.0, "attack": 1.6}
}
```

#### Seuils critiques

- Santé, temps, distances (voir détails dans `Decisions.md`)

#### Fichiers clés et structure

- `src/ia_troupe_rapide/` : `config.py`, `processors/rapid_ai_processor.py`, `services/*`, `states/*`, `fsm/machine.py`, `integration.py`


#### Points d'optimisation actuels

- **Phase 1** : Stabilisation (tir continu, navigation persistante, coordination rôles rotatifs)
- **Phase 2** : Tuning (seuils danger, distance anchor, poids objectifs)
- **Phase 3** : Advanced (prédiction horizon, micro-positions, load-balance)


### IA des Maraudeurs

**Fichier** : `src/ia/ia_barhamus.py`

#### Architecture et composants

##### Composants principaux

1. **DecisionTreeClassifier** : Modèle d'arbre de décision pour prédire les actions
2. **StandardScaler** : Normalisation des données d'entrée
3. **NearestNeighbors** : Pathfinding intelligent basé sur les positions similaires

##### Vecteur d'état (15 dimensions)

L'IA analyse la situation via un vecteur de 15 dimensions :

1. **Position (2D)** : Coordonnées X,Y normalisées
2. **Santé (1D)** : Ratio santé actuelle/max
3. **Ennemis (3D)** : Nombre, distance au plus proche, force
4. **Obstacles (3D)** : Îles, mines, murs
5. **Tactique (3D)** : Avantage tactique, zone sûre, statut bouclier
6. **État interne (3D)** : Cooldown, temps de survie, stratégie actuelle

##### Actions disponibles (8 types)

0. **Approche agressive** : Fonce vers l'ennemi le plus proche
1. **Attaque** : Engage le combat direct
2. **Patrouille** : Recherche active d'ennemis
3. **Évitement** : Contourne les obstacles dangereux
4. **Bouclier** : Active la protection défensive
5. **Position défensive** : Se place en position stratégique
6. **Retraite** : Fuit vers une zone sûre
7. **Embuscade** : Se positionne pour une attaque surprise

#### Système d'apprentissage

##### Collecte d'expérience

L'IA enregistre chaque décision avec :

- État avant l'action (vecteur 15D)
- Action choisie (0-7)
- Récompense obtenue (-10 à +10)
- État résultant

##### Calcul des récompenses

**Récompenses positives :**

- Santé élevée : +5
- Attaque réussie : +3
- Survie prolongée : +2
- Position tactique : +1

**Pénalités :**

- Dégâts subis : -2 par point
- Échec d'attaque : -1
- Position dangereuse : -3

##### Entraînement du modèle

Le modèle se retraine automatiquement :

- Toutes les 20 expériences
- Quand la performance chute
- Au début de chaque partie

**Pré-entraînement** :

L'IA du Maraudeur peut être pré-entraînée pour améliorer ses performances dès le premier lancement :

```bash
# Entraînement basique (rapide, ~1-2 minutes)
python train_barhamus_ai.py --episodes 100

# Entraînement complet (recommandé, ~5-10 minutes)
python train_barhamus_ai.py --episodes 500 --save-interval 50

# Entraînement intensif (pour production)
python train_barhamus_ai.py --episodes 2000 --save-interval 100
```

Le script génère un modèle pré-entraîné dans `models/barhamus_ai_pretrained.pkl` qui sera chargé automatiquement au lancement du jeu. Cela permet à l'IA de commencer avec des stratégies de base déjà acquises au lieu de partir de zéro.

**Note** : Le pré-entraînement n'est pas obligatoire - l'IA apprendra pendant le jeu si aucun modèle n'existe. Le pré-entraînement améliore simplement les performances initiales.

#### Stratégies adaptatives

L'IA suit 4 stratégies principales qui évoluent selon la performance :

1. **Balanced** : Équilibre entre attaque et défense
2. **Aggressive** : Priorité à l'offensive
3. **Defensive** : Priorité à la survie
4. **Tactical** : Utilise l'environnement et les embuscades

#### Fichiers importants

- `src/ia/ia_barhamus.py` : Implémentation principale
- `tests/test_ia_ml.py` : Tests unitaires
- `models/` : Modèles sauvegardés (créé automatiquement)

#### Performance

Tests effectués montrent :

- ✅ Compilation sans erreurs
- ✅ Analyse d'état 15D fonctionnelle
- ✅ Prédiction d'actions opérationnelle
- ✅ Système d'apprentissage actif
- ✅ Composants scikit-learn initialisés

##### Notes techniques

- Nécessite scikit-learn, numpy
- Sauvegarde automatique des modèles
- Compatible avec l'architecture ECS existante
- Maintient la compatibilité avec les méthodes legacy

#### 🧹 Nettoyage des Modèles de Maraudeurs

##### Utilisation rapide

###### Voir tous les modèles Maraudeur

```bash
python scripts/clean_models.py --marauder --list
```

###### Garder les 5 plus récents (recommandé)

```bash
python scripts/clean_models.py --marauder --keep 5
```

###### Supprimer TOUS les modèles Maraudeur

```bash
python scripts/clean_models.py --marauder --all
```

###### Supprimer les modèles de plus de 7 jours

```bash
python scripts/clean_models.py --marauder --older-than 7
```

##### Exemples d'utilisation

###### Je veux tester l'IA Maraudeur avec un apprentissage frais

```bash
python scripts/clean_models.py --marauder --all
```

L'IA des Maraudeurs recommencera à apprendre depuis zéro.

###### J'ai beaucoup de modèles Maraudeur et je veux faire le ménage

```bash
python scripts/clean_models.py --marauder --keep 10
```

Garde les 10 modèles les plus récents, supprime les autres.

##### Fréquence recommandée

- **Quotidien** : `python scripts/clean_models.py --marauder --keep 5`
- **Hebdomadaire** : `python scripts/clean_models.py --marauder --older-than 7`
- **Avant un test** : `python scripts/clean_models.py --marauder --all`

##### Interface graphique (optionnelle)

 
```bash
# Utilisez le programme compilé (fourni dans les releases)
./MaraudeurAiCleaner          # Linux/macOS
MaraudeurAiCleaner.exe        # Windows

# Ou pour les développeurs avec Python
python tools/maraudeur_ai_cleaner.py
```
 
Permet de lister, supprimer par sélection, ne garder que les N plus récents, ou supprimer les modèles plus anciens que X jours, sans ligne de commande.

Note : l'outil suit automatiquement la langue configurée dans le jeu (définie dans `galad_config.json`). Français par défaut, avec fallback sur l'anglais si la langue n'est pas supportée.

##### Notes importantes

✅ Les fichiers `barhamus_ai_*.pkl` ne sont **PAS** versionnés dans Git  
✅ Tu peux les supprimer sans risque - l'IA les recréera automatiquement  
✅ Chaque Maraudeur crée son propre fichier, d'où l'accumulation rapide  
✅ Supprimer les fichiers réinitialise l'apprentissage de l'IA des Maraudeurs


### IA du Léviathan (`AILeviathanProcessor`)

**Fichier** : `src/processeurs/aiLeviathanProcessor.py`

L'IA du Léviathan est un système d'intelligence artificielle avancé conçu pour contrôler de manière autonome les unités lourdes de type Léviathan. Elle combine un **arbre de décision hiérarchique** pour les décisions tactiques et le **pathfinding A*** pour la navigation stratégique.

**Fichiers associés** :

- `src/ia/leviathan/decision_tree.py` - Arbre de décision
- `src/ia/leviathan/pathfinding.py` - Navigation A*
- `src/components/ai/aiLeviathanComponent.py` - Composant ECS

#### Architecture et Composants

L'IA du Léviathan repose sur une architecture modulaire optimisée pour les performances :

##### 1. Arbre de Décision Hiérarchique (`LeviathanDecisionTree`)

L'arbre de décision implémente un **système de priorités** où les conditions les plus importantes court-circuitent les priorités inférieures. Cela garantit que les comportements critiques de sécurité (évitement d'obstacles) s'exécutent toujours avant les comportements tactiques (combat).

**Priorités de décision** (de la plus haute à la plus basse) :

1. **Évitement d'obstacles** (`AVOID_OBSTACLE`) - Prévient les collisions et les dégâts
   - Îles (bloqueurs absolus, priorité maximale)
   - Tempêtes (marge de sécurité : 200px)
   - Bandits (marge de sécurité : 200px)
   - Mines (marge de sécurité : 150px)

2. **Engagement ennemi** (`ATTACK_ENEMY`) - Élimine les menaces à portée
   - Portée maximale : 350px
   - Engagement opportuniste des unités ennemies

3. **Attaque de base** (`ATTACK_BASE`) - Atteint l'objectif stratégique
   - Portée de bombardement : 400px
   - Tir concentré avec toutes les armes avant

4. **Navigation** (`MOVE_TO_BASE`) - Progression par défaut
   - Déplacement vers la base ennemie via pathfinding A*

##### 2. Pathfinding A* (`Pathfinder`)

Le système de navigation utilise l'algorithme A* pour calculer des chemins optimaux tout en évitant les obstacles :

- **Carte gonflée** : Les obstacles sont artificiellement élargis pour éviter que les unités ne "collent" aux îles
- **Obstacles dynamiques** : Intègre les tempêtes, bandits, mines et unités ennemies dans le calcul de chemin
- **Recalcul intelligent** : Limitation du taux de recalcul (3 secondes minimum) pour optimiser les performances
- **Détection de waypoint** : Supprime les waypoints atteints automatiquement

##### 3. Cache d'Entités

Pour optimiser les performances, l'IA utilise un **système de cache** mis à jour périodiquement (toutes les 30 frames, ~0.5s à 60 FPS) :

- Cache des positions ennemies par équipe
- Cache des tempêtes avec leurs rayons
- Cache des bandits avec leurs rayons
- Détection optimisée des mines par balayage de grille en spirale

#### Vecteur d'État (GameState)

L'IA analyse la situation via un vecteur d'état complet contenant toutes les données de perception :

| Catégorie | Données |
|-----------|---------|
| **Statut de l'unité** | Position (x, y), direction (degrés), santé actuelle/max |
| **Évaluation des menaces** | Distance au plus proche ennemi, angle vers l'ennemi, nombre d'ennemis |
| **Détection d'obstacles** | Île devant (booléen), distances aux tempêtes/bandits/mines |
| **Objectif stratégique** | Position de la base ennemie, distance, angle |

#### Actions Disponibles

L'IA peut exécuter 5 actions tactiques différentes :

##### ATTACK_ENEMY - Combat contre unités ennemies

**Tactiques de combat** :

- **Gestion dynamique de la distance** : Approche/recul selon la portée optimale
  - Distance optimale : 280px (DPS idéal)
  - Distance minimale : 150px (seuil de recul)
  - Distance maximale : 350px (limite d'engagement)
- **Système de ciblage** :
  - Tolérance d'alignement : 50° pour les armes principales
  - Tolérance élargie : 60° pour la capacité spéciale
- **Tir latéral automatique** : Activation lorsque l'ennemi est sur le flanc (60-120°)
- **Arrêt pour tirer** : L'unité s'arrête pour maximiser la précision
- **Utilisation agressive de la capacité spéciale** : Activation automatique dès que disponible

##### ATTACK_BASE - Siège de la base ennemie

**Tactiques de siège** :

- **Approche à la portée de siège optimale** : 320px (équilibre DPS/sécurité)
- **Tir concentré** : Désactivation des canons latéraux pour un bombardement focalisé
- **Utilisation très agressive de la capacité spéciale** : Pour maximiser les dégâts à la base
- **Maintien de distance de sécurité** : Minimum 200px des défenses de la base
- **Bombardement soutenu** : L'unité s'arrête complètement pour tirer

##### AVOID_OBSTACLE - Évitement d'obstacles

**Système d'évitement intelligent** :

- **Balayage multi-directionnel** : Teste les angles de -120° à +120° par incréments de 30°
- **Rotation progressive** : Maximum 45° par frame pour un mouvement fluide
- **Préférence directionnelle** : Privilégie les directions vers la base ennemie
- **Réduction de vitesse en virage** : Ralentit à 60-80% lors de virages serrés
- **Manœuvre de secours** : Marche arrière et demi-tour si toutes les directions sont bloquées

##### MOVE_TO_BASE - Navigation stratégique

**Pathfinding A* avec évitement** :

- **Calcul de chemin optimal** : Utilise A* sur une carte incluant tous les obstacles
- **Navigation par waypoints** : Suit une série de points intermédiaires
- **Rotation fixe** : Rotation de 10° par frame vers le waypoint cible
- **Tolérance de waypoint** : Distance de 2 tuiles pour marquer un waypoint comme atteint
- **Navigation directe en secours** : Si pas de chemin A* disponible, navigation directe avec évitement d'îles

##### IDLE - État de veille

Vitesse de mouvement mise à zéro, l'unité reste immobile.

#### Optimisations de Performance

L'IA du Léviathan intègre de nombreuses optimisations pour fonctionner efficacement :

1. **Cache d'entités** : Mise à jour périodique (30 frames) au lieu de requêtes ECS constantes
2. **Calculs de distance au carré** : Évite les racines carrées coûteuses quand possible
3. **Détection d'îles par cône** : Teste seulement 3 points (centre, gauche, droite) au lieu d'un balayage complet
4. **Détection de mines en spirale** : Sortie anticipée dès qu'une mine proche est trouvée
5. **Limitation de recalcul A*** : Cooldown de 3 secondes entre recalculs de chemin
6. **Cache de cellules bloquées du pathfinder** : Réutilise les données pré-calculées

#### Statistiques et Métriques

Le processeur collecte des statistiques d'utilisation :

```python
statistics = processor.getStatistics()
# Retourne :
# {
#     'total_actions': 1523,
#     'actions_by_type': {
#         'attack_enemy': 456,
#         'attack_base': 234,
#         'avoid_obstacle': 189,
#         'move_to_base': 644
#     }
# }
```

#### Configuration et Ajustement

**Seuils de combat** (dans `LeviathanDecisionTree`) :

- `ENEMY_ATTACK_DISTANCE = 350.0` : Portée maximale d'engagement ennemi
- `BASE_ATTACK_DISTANCE = 400.0` : Portée maximale de bombardement de base

**Seuils d'évitement** (dans `LeviathanDecisionTree`) :

- `STORM_AVOID_DISTANCE = 200.0` : Marge de sécurité pour les tempêtes
- `BANDIT_AVOID_DISTANCE = 200.0` : Marge de sécurité pour les bandits
- `MINE_AVOID_DISTANCE = 150.0` : Marge de sécurité pour les mines

**Cooldown d'action** (dans `AILeviathanComponent`) :

- `action_cooldown = 0.15` : Temps entre les décisions (secondes)

#### Intégration dans le Jeu

Pour activer l'IA sur un Léviathan, il suffit d'ajouter le composant `AILeviathanComponent` à l'entité :

```python
from src.components.ai.aiLeviathanComponent import AILeviathanComponent

# Lors de la création du Léviathan
esper.add_component(entity, AILeviathanComponent(enabled=True))
```

Le processeur `AILeviathanProcessor` doit être ajouté à l'ECS avec accès à la grille de carte :

```python
from src.processeurs.aiLeviathanProcessor import AILeviathanProcessor

leviathan_processor = AILeviathanProcessor()
leviathan_processor.map_grid = world_map  # Nécessaire pour la détection d'obstacles
esper.add_processor(leviathan_processor)
```

#### Points Clés de l'Implémentation

- **Philosophie de conception** : Sécurité d'abord, combat agressif, orientation vers l'objectif
- **Complexité algorithmique** : O(1) pour les décisions, O(n log n) pour le pathfinding A*
- **Indépendance du framerate** : Tous les cooldowns et timings utilisent le temps réel (dt)
- **Compatibilité ECS** : Utilise uniquement les événements et composants ECS, pas de références directes
- **Désactivation pour contrôle joueur** : L'IA se désactive automatiquement si le composant `PlayerSelectedComponent` est présent

### IA des Druides (`DruidAIProcessor`)

**Fichier** : `src/processeurs/ai/DruidAIProcessor.py`

Le Druide est une unité de soutien pilotée par une IA à base de Minimax pour la prise de décision et d'A* pour la navigation. Son rôle est de maintenir les alliés en vie, d'entraver les ennemis avec le lierre, et d'adopter des déplacements prudents.

#### Architecture et boucle de décision

- Perception: construction d'un GameState simplifié via `_build_game_state` (alliés/ennemis proches, santé, cooldowns)
- Décision: appel à `run_minimax(game_state, grid, depth=AI_DEPTH)` pour obtenir la meilleure action
- Action: `_execute_action` traduit l'action en commandes jeu (soin, lierre, déplacement/fuite)
- Navigation: chemin A* via `a_star_pathfinding`, suivi de chemin et gestion d'angle/vitesse

#### Actions supportées

- `HEAL` : rend `DRUID_HEAL_AMOUNT` PV à l’allié ciblé et déclenche le cooldown de soin
- `CAST_IVY` : orientation vers la cible et lancement du projectile de lierre si disponible
- `MOVE_TO_ALLY` / `MOVE_TO_ENEMY` : A* vers la cible pour se positionner
- `FLEE` : calcule un point opposé à l’ennemi proche et A* pour s’en éloigner
- `WAIT` : arrêt et purge du chemin

#### Entrées et paramètres

- Composants requis: `DruidAiComponent`, `SpeDruid`, `Position`, `Velocity`, `Health`, `Team`, `Radius`
- Désactivation automatique si `PlayerSelectedComponent` est présent (contrôle joueur)
- Vision: `ai.vision_range` (dans `DruidAiComponent`)
- Chemin: grille `grid` injectée; tolérance waypoint ≈ `TILE_SIZE/2`

#### Remarques (Druide)

- Le Minimax est évalué périodiquement avec un cooldown (`ai.think_cooldown_current`) pour limiter le coût
- La fuite vise ~10 tuiles de distance dans la direction opposée à la menace
- Les unités « enlacées » (isVinedComponent) sont détectées pour enrichir l’évaluation

#### Vecteur d'état (GameState - Druide)

| Catégorie | Clés | Détails |
|---|---|---|
| druid | `id`, `pos(x,y)`, `health`, `max_health`, `heal_cooldown`, `spec_cooldown` | `heal_cooldown` lu via `RadiusComponent.cooldown`, `spec_cooldown` via `SpeDruid.cooldown` |
| allies[] | `id`, `pos`, `health`, `max_health` | Alliés dans `ai.vision_range` (exclut le Druide lui-même) |
| enemies[] | `id`, `pos`, `health`, `max_health`, `is_vined`, `vine_duration` | Ennemis dans la vision; `is_vined` et durée lierre si présent |

#### Détails décisionnels et heuristiques

- Recherche Minimax avec élagage alpha-bêta: `run_minimax(game_state, grid, depth=AI_DEPTH, alpha=-inf, beta=+inf, is_maximizing=True)`
- Ensemble d'actions évaluées: {HEAL, CAST_IVY, MOVE_TO_ALLY, MOVE_TO_ENEMY, FLEE, WAIT}
- Critères usuels d'évaluation (selon implémentation Minimax): priorité au soin d’alliés fortement blessés, opportunisme lierre si disponible et ennemi dans l’arc

#### Pathfinding et mouvement (A*)

- A* sur `grid` (carte tuilée) avec positions monde en pixels; chemin converti et suivi point par point
- Waypoint atteint si distance < `TILE_SIZE/2`, sinon orientation par `atan2` (axe Y inversé Pygame) et vitesse `vel.maxUpSpeed`
- Sur calcul de fuite: point cible à ~`10 * TILE_SIZE` opposé à l’ennemi le plus proche

#### Timings et cooldowns

- Décision tempo: `ai.think_cooldown_current` réinitialisé à `ai.think_cooldown_max` après chaque réflexion
- Soin: `UNIT_COOLDOWN_DRUID` appliqué via `RadiusComponent.cooldown`
- Lierre: vérification `SpeDruid.can_cast_ivy()` juste avant le tir pour éviter les race conditions

#### Robustesse et erreurs

- Cibles invalides/disparues: exceptions `KeyError` capturées -> purge `ai.current_action` et `ai.current_path`
- Fin de chemin: on saute le premier point (position actuelle), arrêt propre si liste vide


### IA des Architectes (`ArchitectAIProcessor`)

**Fichier** : `src/processeurs/ai/architectAIProcessor.py`

L’Architecte combine Minimax (stratégie) et A* (navigation) pour explorer les îles, construire des tours (attaque/soin) et éviter les menaces. Il maintient des caches pour les îles, mines et chemins, et respecte une réserve d’or minimale.

#### Architecture (Architecte)

- Décision: `ArchitectMinimax.decide(state)` retourne une action stratégique
- Navigation: `SimplePathfinder.findPath(...)` sur la `map_grid`, avec prise en compte d’ennemis comme obstacles souples
- Caches: chemins par entité, groupes d’îles, mines; historique de positions pour détection de blocage
- Économie: lecture/consommation d’or joueur via `PlayerComponent`; réserve d’or configurable (`gold_reserve`)

#### Actions principales (DecisionAction)

- `NAVIGATE_TO_ISLAND` / `CHOOSE_ANOTHER_ISLAND` / `FIND_DISTANT_ISLAND`
- `NAVIGATE_TO_CHEST` / `NAVIGATE_TO_ISLAND_RESOURCE`
- `NAVIGATE_TO_ALLY` / `EVADE_ENEMY` / `GET_UNSTUCK` / `MOVE_RANDOMLY`
- `BUILD_DEFENSE_TOWER` / `BUILD_HEAL_TOWER` (via `createDefenseTower` / `createHealTower`) si or ≥ coût + réserve
- `ACTIVATE_ARCHITECT_ABILITY` (déclenchement, logique d’effet gérée par le processeur des capacités)

#### Entrées et conditions

- Composants requis: `ArchitectAIComponent`, `SpeArchitect`, `Position`, `Velocity`, `Health`, `Team`
- Carte: `map_grid` obligatoire; initialisation lazy du `SimplePathfinder` à la première frame
- Îles: détection par `TileType.is_island_buildable()`, regroupement en clusters; arrêt anticipé si déjà sur une île cible
- Anti-stuck: historique 3s; action `GET_UNSTUCK` quand déplacement < 0.5 tuile

#### Remarques (Architecte)

- Liste « tabou » de cibles d’îles récentes si pathfinding échoue (évite de boucler)
- Recalcule de chemin quand la cible change significativement; suivi waypoint avec tolérance ~1.2 tuile
- S’arrête sur l’île cible et enchaîne une nouvelle recherche/construction

#### GameState (Architecte)

| Catégorie | Clés principales | Détails |
|---|---|---|
| Unité | `current_position`, `current_heading`, `current_hp`, `maximum_hp`, `team_id` | Etat instantané |
| Économie | `player_gold` | Or dispo lu via `PlayerComponent.get_gold()` |
| Hostiles | `closest_foe_dist`, `closest_foe_bearing`, `closest_foe_team_id`, `nearby_foes_count` | Calcul Euclidien + cap Y inversé |
| Alliés | `closest_ally_dist`, `closest_ally_bearing`, `nearby_allies_count`, `total_allies_hp`, `total_allies_max_hp` | Exclut bases des totaux |
| Environnement | `closest_island_dist`, `closest_island_bearing`, `is_on_island`, `closest_chest_dist`, `closest_island_resource_dist`, `is_tower_on_current_island`, `island_groups` | Îles groupées en 8-connexité |
| Menaces | `closest_mine_dist`, `closest_mine_bearing`, `is_stuck` | Mines pré-indexées, stuck sur 3s |
| Spécifique Architecte | `architect_ability_available`, `architect_ability_cooldown`, `build_cooldown_active` | Cooldown build et capacité |

#### Décision et temporisation

- La décision est bloquée par `vetoTimeRemaining` pour limiter la fréquence des re-évaluations
- Les actions de construction déclenchent `build_cooldown_remaining` via `ai_comp.start_build_cooldown()`
- Journalisation ponctuelle des positions/waypoints pour inspection (logger)

#### Pathfinding A* (détails)

- Initialisation lazy de `SimplePathfinder(self.map_grid, TILE_SIZE)`
- Recalcul si nouvelle cible distante de > `2 * TILE_SIZE` de l’ancienne
- Ennemi comme obstacle souple: passage d’une liste `enemy_positions` au pathfinder
- Suivi: waypoint atteint si distance < `1.2 * TILE_SIZE`, sinon orientation progressive (±15° max/frame) et réduction de vitesse en virage
- Échec de pathfinding: ajout de la cible à la « liste tabou » (max 5 récentes) avec timestamp pour éviter les boucles

#### Économie et construction

- Réserve d’or: `gold_reserve = 50` conservés avant de déclencher `BUILD_*`
- Coûts: `UNIT_COST_ATTACK_TOWER`, `UNIT_COST_HEAL_TOWER` (constants gameplay)
- Placement: fonctions `createDefenseTower(...)` / `createHealTower(...)` sur tuiles `TileType.is_island_buildable()`
- Après construction: purge chemin et sélection d’une île d’un autre groupe via clustering DFS 8-connexe

#### Anti-stuck et sécurité

- Historique positions glissant (3s); stuck si déplacement < `0.5 * TILE_SIZE` -> action `GET_UNSTUCK`
- Évasion ennemis: éventail d’angles autour de l’anti-cap (±30°, ±60°), validation par existence de chemin

#### Complexité et performances

- Caches îles/mines/groupes construits à la demande puis réutilisés
- Décision O(1) amorti (Minimax discret côté architecte) et pathfinding O(n log n) typique
- Réduction recalculs par veto, seuils de changement de cible, et liste tabou

---
