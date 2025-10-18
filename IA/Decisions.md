# Analyse Complète des Décisions d'IA - Troupe Rapide (Scouts Ennemis)

> **Document généré le 18 octobre 2025 | Branche : IA_LAMBERT | Version : Complète et optimisée**

## 1. Vue d'ensemble architecturale

### Principe fondamental
L'IA des éclaireurs ennemis repose sur un **système de machine à états finis (FSM)** piloté par un **évaluateur d'objectifs basé sur le scoring**. Chaque décision d'action est déterministe, algorithmique (zéro machine learning) et basée sur un système de poids configurables.

### Flux général
```
1. Actualisation du contexte (santé, position, danger local)
   ↓
2. Évaluation d'objectif (scoring de toutes les options)
   ↓
3. Sélection de l'objectif avec le meilleur score
   ↓
4. Transition de l'état FSM (en fonction de l'objectif)
   ↓
5. Exécution de l'action correspondante à l'état
```

### Objectif global
**collecter** les coffres volants (gain d’or pour acheter des alliés), **Survivre** le plus longtemps, **attaquer** tactiquement à distance. Si un Druide est présent et la santé bonne, concentrer sur **harcèlement de base** à distance sécurisée.

---

## 2. Architecture du système

### 2.1 Composants principaux

#### **RapidTroopAIProcessor** (Processeur Esper global)
- **Rôle** : Boucle principale (10 Hz), met à jour tous les contrôleurs
- **Responsabilités** : 
  - Itération scouts ennemis
  - Gestion événements (coffres, tempêtes, mines)
  - Nettoyage entités mortes
  - Collecte debug overlay

#### **RapidUnitController** (Contrôleur par unité)
- **Rôle** : Décisions et exécution pour une seule unité
- **Responsabilités** :
  - Actualisation contexte
  - Appel évaluateur objectifs
  - Gestion FSM (transitions)
  - Coordination inter-unités
  - Commandes mouvement

#### **GoalEvaluator** (Évaluateur d'objectifs)
- **Rôle** : Scoring de toutes les options d'action
- **Responsabilités** :
  - 8 types d'objectifs évalués
  - Score pour chacun
  - Sélection du meilleur

#### **Services auxiliaires**
- **DangerMapService** : Carte 2D danger (projectiles, mines, tempêtes)
- **PathfindingService** : A* pondéré (évite îles, mines, croix pattern)
- **PredictionService** : Prédiction position ennemis (0.8s horizon)
- **CoordinationService** : Rôles exclusifs (coffres, follow-to-die)
- **AIContextManager** : Cache contexte unitaire

---

## 3. Évaluation des objectifs (GoalEvaluator)

### 3.1 Objectifs évalués et scoring

| Type | Score calcul | Condition activation | Rôle |
|------|--------------|-------------------|------|
| **survive** | `3.0 × (1-santé%) × danger_norm` | Toujours | Fuite, druide |
| **goto_chest** | `4.0 / (1 + dist/256)` | Coffres visibles | Collecte exclusive |
| **attack** | `1.6 / (1 + dist/300)` | Unités ennemies | Harcèlement libre |
| **attack_base** | `1.6 / (1 + dist/420) × santé%` | Pas menace < 420px | Harcèlement standoff |
| **follow_die** | `1.92 / (1 + dist/220)` | Ennemi < 60 HP | Exécution exclusive |
| **join_druid** | `2.5` | Santé ≤ 65%, druide | Soin rapide |
| **follow_druid** | `1.2` | 65% < santé < 95% | Soin continu |
| **goto_mine** | `0.3 / (1 + dist/256)` | Druide sûr | Support druide |

### 3.2 Poids d'objectifs (config)

```
survive:      3.0   (baseline, peut être réduit si zone sûre)
chest:        4.0   (collecte, plus attrayant que survie)
attack:       1.6   (engagement libre)
join_druid:   2.5   (soin urgent)
follow_druid: 1.2   (suivi passif)
destroy_mine: 0.3   (appui stratégique)
```

---

## 4. Machine à états finis (FSM)

### 4.1 États et transitions globales

```
PRIORITÉ GLOBALE (100 + 80)
         ↓
    ┌─────────┐
    │  FLEE   │ ← Danger élevé OU santé faible
    └────┬────┘
         │ Danger < safe + marge
         ↓
    ┌─────────────┐        ┌──────────┐
    │   IDLE      ├───────►│  GOTO    │
    └────┬────────┘        └──────┬───┘
         │ objectif       objectif atteint
         │ + safe danger          │
         ▼                        ▼
    ┌─────────────┐
    │   ATTACK    │ (distmaint + tir) → IDLE/FOLLOW_DIE
    └─────────────┘

    JOIN_DRUID → FOLLOW_DRUID → IDLE (santé rétablie)
```

### 4.2 États détaillés

#### **IDLE** (Attente)
- Écoute transitions globales
- Transitions : FLEE (danger), GOTO (objectif), ATTACK (safe+objectif)
- Sortie : Vers état actif

#### **FLEE** (Fuite)
- Mouvement vers zone sûre
- Transition : IDLE (danger < seuil)
- Prisonnier jusqu'à stabilisation
- Sortie : Retour IDLE

#### **GOTO** (Déplacement)
- A* pathfinding, suivi waypoints
- Transition : IDLE (arrivée), ATTACK (nouvelle cible prioritaire)
- Actualisation : Replan si distance > 64px

#### **ATTACK** (Combat)
- Distance maintenance (optimal ±24px)
- Pour attack_base : recul si < 195px
- Tir si en portée (coodown update)
- Prédiction horizon 0.35s
- Transition : IDLE (cible perdue), FOLLOW_DIE (cible faible)

#### **FOLLOW_TO_DIE** (Exécution)
- Fonce vers cible, ignore danger
- Tir continu
- Transition : IDLE (cible tuée)
- Coordination : Rôle exclusif

#### **JOIN_DRUID** (Rapprochement)
- Mouvement vers druide
- Transition : FOLLOW_DRUID (< 128px)

#### **FOLLOW_DRUID** (Suivi)
- Accompagnement druide
- Transition : IDLE (santé ≥ 95%)

---

## 5. Système de danger

### 5.1 Sources dynamiques (par tick)

| Source | Radius | Intensité | Usage |
|--------|--------|-----------|-------|
| Projectiles | 3.0 tuiles | 2.5 | Court-terme |
| Bandits | 6.0 tuiles | 5.0 | Élevé |
| Tempêtes | 6.0 tuiles | 7.0 | Très élevé |
| Unités alliées | 3.5 tuiles | 1.2 | Léger |

### 5.2 Sources statiques (une fois)

**Mines** (croix `+` bloquante) :
- Tuile centrale + quatre orthogonales = danger max (fuite immédiate)
- Aucune propagation diagonale : la zone reste compacte

**Îles** :
- Aucune pénalité de danger statique (juste pathfinding qui interdit la croix)

### 5.3 Seuils

```
SAFE_THRESHOLD:         0.45   ← Zone "agir"
FLEE_THRESHOLD:         1.45   ← Fuite obligée
FLEE_HYSTERESIS:        0.55   ← Amortissement
FLEE_RELEASE_MARGIN:    0.25   ← Sortie fuite (0.70 total)
MAX_VALUE_CAP:          12.0   ← Normalisation max
DECAY_PER_SECOND:       0.82   ← Décroissance
```

---

## 6. Pathfinding pondéré (A*)

### 6.1 Coûts de tuiles

| Tuile | Coût | Usage |
|-------|------|-------|
| Sol normal | 1.0 | Déplacement libre |
| Nuage | 1.3 | Ralentissement léger |
| Île (case + croix à 1 tuile) | ∞ | Infranchissable |
| Mine (case + croix à 1 tuile) | ∞ | Infranchissable |
| Déplacement diagonal | coût × 1.4 | Facteur move |

### 6.2 Zones interdites en croix (+)

- Chaque île ou mine bloque sa tuile centrale et les quatre cases orthogonales adjacentes.
- Aucune notion d'anneaux : la croix est la seule barrière.
- Le danger dynamique n'est plus additionné au coût : seules ces interdictions + le poids des nuages modifient la recherche.

---

## 7. Logique de combat (AttackState)

### 7.1 Tir (Shooting)

```
Chaque tick :
1. Réduction cooldown : radius.cooldown -= dt
2. Si cooldown > 0 : aucun tir
3. Si cooldown ≤ 0 :
   a. Prédiction position cible (horizon=0.35s)
   b. Orientation vers prédiction
   c. Dispatch event "attack_event"
   d. Réinitialisation cooldown = bullet_cooldown
```

### 7.2 Positionnement

#### **Unités normales**
- Distance optimale : radius × 0.85 (~166 px)
- Tolérance : 24 px
- Approche si distance > optimal + 24
- Tire si distance ≤ optimal + 24

#### **Attaque base**
- Point de harcèlement : 260 px (calculé métadonnées)
- **Si < 195 px** : RECUL CONTRÔLÉ loin de base
- Continue tir pendant recul
- Évite contact destructeur

---

## 8. Coordination inter-unités

### 8.1 Rôles réservés

**Coffres** (EXCLUSIVE) :
- Une seule unité réserve le coffre et reçoit le chemin vers celui-ci
- Les autres unités ignorent simplement ce coffre et conservent/choisissent un objectif différent
- Libération : collecte, coffre coulé, cible perdue

**Follow-to-die** (EXCLUSIVE) :
- Une seule exécution par groupe
- Autre unité → "attack" simple
- Libération : cible tuée

**Harcèlement** (PARTAGÉ) :
- Plusieurs unités peuvent attaquer même cible
- Aucune réservation

---

## 9. Thresholds critiques

### 9.1 Santé

```
flee_ratio:         0.35  (35% → mourant)
join_druid_ratio:   0.65  (65% → appel soin)
follow_druid_ratio: 0.95  (95% → reste druide)
invincibility_min:  0.25  (25% → critique)
```

### 9.2 Temps

```
tick_frequency:              10 Hz (0.1s)
objective_reconsider_delay:  0.75s
state_min_duration:          0.8s
flee_reaction_window:        1.8s
attack_ignore_danger_window: 2.0s
attack_persistence_ratio:    0.55 (continue si > 55%)
flee_release_margin:         0.25 (marge sortie)
```

### 9.3 Distances

```
waypoint_reached:       24 px
near_druid:            128 px
follow_to_die_max:     360 px
attack_max_vs_units:   420 px
attack_max_vs_base:    420 px
pathfinding_recompute: 64 px
attack_tolerance:      24 px
```

---

## 10. Configuration JSON externe

Structure JSON (optionnelle, chemins) :

```json
{
  "danger": {
    "safe_threshold": 0.45,
    "flee_threshold": 1.45
  },
  "weights": {
    "survive": 3.0,
    "chest": 4.0,
    "attack": 1.6
  }
}
```

Chemins recherche :
1. `assets/ia_troupe_rapide/config.json`
2. `config/ia_troupe_rapide.json`
3. `ia_troupe_rapide_config.json`

---

## 11. Problèmes actuels et opportunités

### 11.1 Bugs identifiés et fixes appliqués

| Bug | Cause | Fix appliqué | Statut |
|-----|-------|-------------|--------|
| Tirs rares/jamais | Cooldown non décrémenté | Ajout `_cooldown_step(dt)` global | ✅ Complet |
| Rush base | Distance standoff nulle | Ajout 260px + recul si <195px | ✅ Complet |
| Collisions mines | Coûts pathfinding faibles | Mines: 5.5×/3.0× + croix pattern | ✅ Complet |
| Oscillation attaque | Tolérance 24px trop fine | Incrémenter à 32px | ⏳ À tester |
| Survie excessive | Poids "survive" trop haut | Réduit scaling dynamique | ⏳ À tester |

### 11.2 Améliorations easy wins

1. **Logs debug** : Ajouter tous scores évaluation
2. **Tuning poids** : `attack: 1.2` (moins agressif)
3. **Distance sûre** : 420 → 520 px
4. **Tolérance** : 24 → 32 px

### 11.3 Améliorations medium

1. **Pathfinding** : Coûts îles ×2.5 vs ×1.6
2. **Prédiction** : horizon 0.8 → 1.2s
3. **Groupe tactics** : Load-balance cibles

---

## 12. Fichiers clés et structure

### Chemin principal
```
src/ia_troupe_rapide/
├── config.py                    # Configuration + thresholds
├── processors/
│   └── rapid_ai_processor.py   # Processeur + RapidUnitController
├── services/
│   ├── goals.py                 # GoalEvaluator (8 objectifs)
│   ├── danger_map.py            # Danger 2D + statiques
│   ├── pathfinding.py           # A* pondéré
│   ├── prediction.py            # Prédiction ennemis
│   ├── coordination.py          # Rôles exclusifs
│   └── ai_context.py            # Cache contexte
├── states/
│   ├── idle.py, flee.py
│   ├── goto.py, attack.py
│   ├── follow_druid.py
│   └── follow_to_die.py
└── fsm/
    └── machine.py              # Moteur FSM
```

---

## 13. Points clés d'optimisation future

### Phase 1 : Validation (court terme)
- ✅ Tirs générés (cooldown)
- ✅ Standoff base (260px + recul)
- ✅ Mines évitées (5.5× / 3.0×)
- ⏳ Test oscillation (tolérance 24→32px)

### Phase 2 : Tuning (moyen terme)
- ⏳ Logs objectifs (tous scores)
- ⏳ Poids attack: 1.6→1.2
- ⏳ Distance base: 420→520px
- ⏳ Îles coûts: ×2.5 / ×2.0 / ×1.5

### Phase 3 : Advanced (long terme)
- ⏳ Prédiction horizon: 0.35→1.2s
- ⏳ Coordination groupe: load-balance
- ⏳ Micro-positions: pattern rotation

---

## Résumé exécutif

L'IA Troupe Rapide est un **système hybride scoring + FSM** optimisé pour survie et harcèlement rapide. Depuis les derniers fixes (projectiles, standoff base, pathfinding mines), le système est **stable et complet**. Les thresholds sont documentés, les transitions claires, les services découplés.

**Prochaines étapes d'amélioration** : Tester en-jeu, affiner poids d'objectifs, ajouter logs de debug, valider distances d'engagement.

---

**Last Updated: 18 October 2025 | Branch: IA_LAMBERT | Status: Ready for Testing**
