# Analyse Complète des Décisions d'IA - Troupe Rapide (Scouts Ennemis)

> **Document généré le 20 octobre 2025 | Branche : IA_LAMBERT | Version : Mise à jour complète avec système de priorités et tir continu**

## 1. Vue d'ensemble architecturale

### Principe fondamental
L'IA des éclaireurs ennemis repose sur un **système de machine à états finis (FSM) piloté par un évaluateur d'objectifs basé sur les priorités**. Chaque décision d'action est déterministe, algorithmique (zéro machine learning) et basée sur un système de poids configurables avec évaluation séquentielle.

### Flux général
```
1. Actualisation du contexte (santé, position, danger local)
   ↓
2. Évaluation d'objectif (priorités séquentielles : coffres → druide → attaque → base)
   ↓
3. Sélection de l'objectif avec la plus haute priorité disponible
   ↓
4. Transition de l'état FSM (en fonction de l'objectif et conditions)
   ↓
5. Exécution de l'action correspondante à l'état + tir continu
```

### Objectif global
**collecter** les coffres volants (gain d'or pour acheter des alliés), **Survivre** le plus longtemps, **attaquer** tactiquement à distance sécurisée avec tir continu. Si un Druide est présent et la santé bonne, concentrer sur **harcèlement de base** à distance sécurisée.

---

## 2. Architecture du système

### 2.1 Composants principaux

#### RapidTroopAIProcessor (Processeur Esper global)
- **Rôle** : Boucle principale (10 Hz), met à jour tous les contrôleurs
- **Responsabilités** :
  - Itération scouts ennemis
  - Gestion événements (coffres, tempêtes, mines)
  - Nettoyage entités mortes
  - Collecte debug overlay
  - Accumulateur de temps pour ticks réguliers

#### RapidUnitController (Contrôleur par unité)
- **Rôle** : Décisions et exécution pour une seule unité
- **Responsabilités** :
  - Actualisation contexte
  - Appel évaluateur objectifs
  - Gestion FSM (transitions avec priorités)
  - Coordination inter-unités
  - Commandes mouvement avec navigation persistante
  - Tir continu (_try_continuous_shoot)

#### GoalEvaluator (Évaluateur d'objectifs)
- **Rôle** : Évaluation séquentielle par priorités
- **Responsabilités** :
  - 8 types d'objectifs évalués en ordre décroissant de priorité
  - Sélection du premier objectif valide trouvé
  - Gestion coordination (coffres exclusifs, harcèlement rotatif)

#### Services auxiliaires
- DangerMapService : Carte 2D danger (projectiles, mines, tempêtes)
- PathfindingService : A* pondéré (évite îles, mines, croix pattern)
- PredictionService : Prédiction position ennemis (0.8s horizon)
- CoordinationService : Rôles exclusifs (coffres, follow-to-die, harcèlement rotatif)
- AIContextManager : Cache contexte unitaire avec navigation persistante
- IAEventBus : Bus d'événements pour coffres/tempêtes

---

## 3. Évaluation des objectifs (GoalEvaluator)

### 3.1 Objectifs évalués par priorité
| Priorité | Type | Condition activation | Rôle |
|----------|------|-------------------|------|
| **100** | `goto_chest` | Coffres visibles + non assignés | Collecte exclusive |
| **90** | `follow_druid` | Santé < 95% + druide présent | Soin prioritaire |
| **80** | `attack` | Unités ennemies stationnaires | Harcèlement libre |
| **70** | `follow_die` | Ennemi < 60 HP + rôle assigné | Exécution exclusive |
| **60** | `attack_base` | Base ennemie + santé > 35% | Harcèlement standoff |
| **10** | `survive` | Toujours (fallback) | Fuite/drift |

### 3.2 Logique d'évaluation séquentielle
```python
def evaluate():
    # 1. Priorité maximale : coffres
    chest = _select_chest()  # goto_chest si disponible
  # 2. Gestion druide
  druid = _select_druid_objective()  # suivi prioritaire du druide
    # 3. Harcèlement
    attack = _select_stationary_attack()  # attack si cible immobile
    # 4. Exécution
    follow_die = _select_follow_to_die()  # follow_die si cible faible
    # 5. Attaque base
    base = _select_attack_base()  # attack_base avec position aléatoire
    # 6. Fallback
    return survive  # survie
```

---

## 4. Machine à états finis (FSM)

### 4.1 États disponibles
États : Idle, GoTo, Flee, Attack, FollowDruid, FollowToDie

### 4.2 Transitions globales (priorité décroissante)
| Priorité | Condition | Target | Description |
|----------|-----------|--------|-------------|
| **100** | Danger ≥ seuil + hysteresis | Flee | Fuite avec cooldown sortie |
| **80** | Santé < 95% + druide | FollowDruid | Rapprochement + escorte |
| **70** | Navigation active + propriétaire différent | GoTo | Respect navigation |
| **0** | Dummy | GoTo | Enregistrement état |

### 4.3 Transitions locales par état
#### Idle
- `goto` (50) → GoTo (objectifs goto_*)
- `attack` (40) → Attack (objectifs attack*)

#### GoTo
- `arrived` (10) → Idle (objectif atteint)
- `attack` (20) → Attack (nouvelle cible prioritaire)

#### Attack
- `done` (10) → Idle (cible perdue)
- `follow_die` (15) → FollowToDie (cible faible)

#### FollowToDie
- `done` (5) → Idle (cible tuée)

#### FollowDruid
- `healed` (10) → Idle (santé ≥ 95%)

---

## 5. États détaillés

### 5.1 IdleState
- Drift lent vers zone sûre si danger > safe_threshold
- Attend transitions globales/locales
- Annule navigation si inactive

### 5.2 FleeState
- Mouvement vers safest_point (4.0 tuiles rayon)
- Hysteresis : entrée si danger ≥ 0.7, sortie si < 0.15
- Cooldown 1.0s avant ré-entrée
- Interdit si santé > 50%

### 5.3 GoToState
- Navigation A* vers target avec waypoints
- Replan si distance > 64px
- Tolérance waypoint_radius (32px+)

### 5.4 AttackState
- Anchor system : maintient distance optimale (~90% radius)
- Recherche positions valides autour cible (30° angles)
- Ajustement attack_base si position infranchissable
- Tir continu via _try_continuous_shoot

### 5.5 FollowToDieState
- Poursuite aggressive, ignore danger
- Tir continu
- Rôle exclusif via coordination

### 5.6 FollowDruid
- Approche le druide même à longue distance
- Maintient une orbite sécurisée (< 160px) jusqu'à soin complet
- Transition Idle si santé rétablie

---

## 6. Système de danger

### 6.1 Sources dynamiques (mise à jour/seconde)
| Source | Radius | Intensité | Décroissance |
|--------|--------|-----------|--------------|
| Projectiles | 3.0 tuiles | 2.5 | 2.0/s |
| Tempêtes | 6.0 tuiles | 7.0 | 2.0/s |
| Bandits | 6.0 tuiles | 5.0 | 2.0/s |
| Unités alliées | 3.5 tuiles | 1.2 | 2.0/s |

### 6.2 Sources statiques
- Mines : Croix + (centrale + 4 orthogonales) = ∞
- Îles : Croix + (centrale + 4 orthogonales) = 50.0
- Bords carte : Rayon 1 sous-tuile = ∞

---

## 7. Pathfinding pondéré (A*)

### 7.1 Coûts de tuiles
| Source | Radius | Intensité | Décroissance |
|--------|--------|-----------|--------------|
| Projectiles | 3.0 tuiles | 2.5 | 2.0/s |
| Tempêtes | 6.0 tuiles | 7.0 | 2.0/s |
| Bandits | 6.0 tuiles | 5.0 | 2.0/s |
| Unités alliées | 3.5 tuiles | 1.2 | 2.0/s |

### 7.2 Optimisations
- Sub-tile factor : 2 (résolution ×2)
- Blocked margin : 2 sous-tuiles sécurité
- Recompute distance : 64px
- Waypoint radius : 32px+

---

## 8. Logique de combat

### 8.1 Tir continu (_try_continuous_shoot)
Appelé chaque tick, indépendamment de l'état :
- Vise target_entity ou objective.target_entity
- Orientation automatique
- Tir si cooldown = 0
- Reset cooldown = bullet_cooldown

### 8.2 AttackState specifics
- Anchor computation : 8 directions (45°), coût ∞ filtré
- Distance optimale : 90% radius (120-200px)
- Attack_base : Position aléatoire 0-360°, distance 100px
- Ajustement : Si infranchissable → recherche valide

---

## 9. Coordination inter-unités

### 9.1 Rôles exclusifs
- Coffres : Assignation propriétaire via chest_owner(), libération collecte/coulement/disparition
- Harcèlement : Rotation via assign_rotating_role("harass"), durée 3.0s puis redistribution
- Follow-to-die : Rôle exclusif, autres → survie

### 9.2 Services
- CoordinationService : Gestion rôles + avoidance vectors
- IAEventBus : Événements coffres/tempêtes
- PredictionService : Menaces projectiles

---

## 10. Configuration JSON externe

Structure identique à l'ancienne version :
```json
{
  "danger": {
    "safe_threshold": 0.45,
    "flee_threshold": 0.7
  },
  "weights": {
    "survive": 4.0,
    "chest": 3.0,
    "attack": 1.6
  }
}
```
Chemins recherche inchangés.

---

## 11. Thresholds critiques

### 11.1 Santé
```
flee_health_ratio:         0.35  (35% → fuite possible)
follow_druid_health_ratio: 0.95  (95% → soin terminé)
invincibility_min:         0.25  (25% → critique)
```

### 11.2 Temps
```
tick_frequency:              10 Hz (0.1s)
follow_to_die_window:        3.0s
objective_reconsider_delay:  0.75s
flee_cooldown:               1.0s (anti-oscillation)
state_stuck_timeout:         5.0s (reset objectif)
```

### 11.3 Distances
```
waypoint_reached:       32px+
navigation_tolerance:   24px
near_druid:            128px
follow_to_die_max:     360px
attack_anchor_radius:  120-200px
```

---

## 12. Changements majeurs vs ancienne version

### 12.1 Architecture
- Évaluation : Scoring pondéré → Priorités séquentielles
- Tir : Conditionnel état → Continu tous états
- Navigation : Temporaire → Persistante (survit refresh)

### 12.2 Configurations
- Danger : decay 0.82 → 2.0 (plus rapide)
- Seuils : flee_threshold 1.45 → 0.7 (plus sensible)
- Poids : survive 3.0 → 4.0, chest 4.0 → 3.0

### 12.3 Logique
- Attack_base : Standoff 260px → Position aléatoire
- FSM : Transitions simplifiées avec priorités
- Coordination : + harcèlement rotatif

---

## 13. Fichiers clés et structure
```
src/ia_troupe_rapide/
├── config.py                    # Configuration + dataclasses
├── processors/
│   └── rapid_ai_processor.py   # Processeur + RapidUnitController
├── services/
│   ├── goals.py                 # GoalEvaluator (priorités séquentielles)
│   ├── danger_map.py            # Danger 2D + statiques
│   ├── pathfinding.py           # A* pondéré sub-tile
│   ├── prediction.py            # Prédiction ennemis
│   ├── coordination.py          # Rôles exclusifs + avoidance
│   ├── context.py               # UnitContext + navigation persistante
│   ├── event_bus.py             # Bus événements
│   └── log.py                   # Logging IA
├── states/
│   ├── idle.py, flee.py, goto.py
│   ├── attack.py
│   ├── follow_druid.py
│   ├── follow_to_die.py
│   └── base.py                  # Classe mère états
├── fsm/
│   └── machine.py              # Moteur FSM + transitions
└── integration.py              # Intégration globale
```

---

## 14. Points d'optimisation actuels

### Phase 1 : Stabilisation (courant)
- ✅ Tir continu implémenté
- ✅ Navigation persistante
- ✅ Coordination rôles rotatifs
- ⏳ Test hysteresis fuite (oscillation)

### Phase 2 : Tuning (prochain)
- ⏳ Ajustement seuils danger (0.7 → ?)
- ⏳ Distance anchor attack (120px → ?)
- ⏳ Poids objectifs (survive 4.0 trop haut ?)

### Phase 3 : Advanced (futur)
- ⏳ Prédiction horizon (0.8s → 1.2s)
- ⏳ Micro-positions pattern rotation
- ⏳ Load-balance cibles multiples

---

## Résumé exécutif

L'IA Troupe Rapide a évolué vers un **système hybride priorités + FSM + tir continu** optimisé pour harcèlement efficace et survie. Les changements majeurs incluent l'évaluation séquentielle, la persistance navigation, et le tir indépendant des états.

**Prochaines étapes** : Stabiliser hysteresis fuite, tuner seuils danger, valider distances combat en jeu.

---

**Last Updated: 20 October 2025 | Branch: IA_LAMBERT | Status: Updated with current implementation**