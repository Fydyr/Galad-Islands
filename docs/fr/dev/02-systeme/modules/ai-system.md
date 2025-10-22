---
i18n:
  en: "AI System"
  fr: "Système d'IA"
---

# Système d'Intelligence Artificielle (IA)

## Vue d'ensemble

Le système d'IA de Galad Islands est conçu pour offrir un adversaire crédible et des comportements autonomes pour les unités. Il combine des modèles de Machine Learning pour les décisions stratégiques de haut niveau (comme la `BaseAi`) et des logiques plus simples pour les comportements individuels des unités (comme le `KamikazeAiProcessor`).

## IA de la Base (`BaseAi`)

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

1.  **Scénarios Stratégiques (`generate_scenario_examples`)**
    - Des exemples de jeu sont générés à partir de scénarios clés définis manuellement (ex: "Défense prioritaire", "Exploration nécessaire", "Coup de grâce").
    - Chaque scénario associe un état de jeu à une action attendue et une récompense élevée. Les actions incorrectes reçoivent une pénalité.
    - Certains scénarios comme l'exploration et la défense sont surreprésentés pour renforcer ces comportements.

2.  **Auto-apprentissage (`simulate_self_play_game`)**
    - Des parties complètes sont simulées entre deux instances de l'IA.
    - Chaque décision prise et la récompense obtenue sont enregistrées comme une expérience.
    - Cela permet à l'IA de découvrir des stratégies émergentes dans un contexte de jeu réaliste.

3.  **Objectif de Victoire (`generate_victory_scenario`)**
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

## IA des Unités

> 🚧 **Section en cours de rédaction**

En plus de l'IA de la base, certaines unités possèdent leur propre logique de comportement autonome, gérée par des processeurs ECS dédiés.

### IA des Kamikazes (`KamikazeAiProcessor`)

**Fichier** : `src/processeurs/KamikazeAiProcessor.py`

Ce processeur gère le comportement des unités Kamikaze :
- **Recherche de cible** : Il identifie la base ennemie comme cible prioritaire.
- **Navigation** : Il calcule une trajectoire directe vers la cible.
- **Action** : Une fois à portée, l'unité s'autodétruit pour infliger des dégâts à la base.

### Autres IA (à venir)

Des logiques d'IA pourraient être ajoutées pour d'autres unités, par exemple :
- **Druides** : Soigner automatiquement les alliés les plus blessés à proximité.
- **Éclaireurs** : Explorer de manière autonome les zones inconnues de la carte.

---

*Cette documentation sera complétée au fur et à mesure de l'implémentation de nouvelles IA.*