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


### Autres IA (à venir)

Des logiques d'IA pourraient être ajoutées pour d'autres unités, par exemple :

- **Druides** : Soigner automatiquement les alliés les plus blessés à proximité.
- **Lévithans** : Utiliser des attaques de zone contre des groupes d'ennemis.
- **Maraudeurs** : Prioriser les cibles en fonction de leur menace et de leur valeur stratégique.
- **Architectes** : Construire des structures défensives en fonction des menaces détectées.

---
