---
i18n:
  en: "AI Processor Manager"
  fr: "Gestionnaire de Processeurs IA"
---

# Gestionnaire de Processeurs IA (AI Processor Manager)

## Vue d'ensemble

Le **AI Processor Manager** est un système d'optimisation qui active et désactive dynamiquement les processeurs d'IA en fonction de la présence d'entités correspondantes dans le jeu. Cette approche évite l'exécution inutile de processeurs IA lorsqu'aucune entité ne nécessite leur traitement, réduisant ainsi l'overhead CPU.

**Fichier** : `src/processeurs/ai/ai_processor_manager.py`

## Problème résolu

### Avant l'AI Manager

Tous les processeurs IA étaient ajoutés à esper au démarrage du jeu et s'exécutaient à chaque frame, même si aucune entité ne nécessitait leur traitement :

```python
# Ancienne approche - TOUS les processeurs toujours actifs
es.add_processor(DruidAiProcessor(...), priority=1)
es.add_processor(RapidTroopAIProcessor(...), priority=2)
es.add_processor(KamikazeAiProcessor(...), priority=6)
# etc.
```

**Impact mesuré** :
- **2.46%** de CPU gaspillé en mode "0 IA" (sans aucune unité IA)
- `rapid_ai` : 1.90% (0.61 ms/frame)
- `druid_ai`, `kamikaze_ai`, `leviathan_ai` : 0.56% combinés

### Après l'AI Manager

Les processeurs sont enregistrés mais **non activés** au démarrage. Ils ne sont ajoutés à esper que lorsque des entités correspondantes apparaissent :

```python
# Nouvelle approche - Activation dynamique
ai_manager = AIProcessorManager(es)
ai_manager.register_ai_processor(DruidAiComponent, druid_ai_processor, priority=1)
ai_manager.register_ai_processor(SpeScout, rapid_ai_processor, priority=2)
# Les processeurs ne sont PAS encore dans esper
```

**Gains mesurés** :
- **-83%** d'overhead IA inutile (2.46% → 0.41%)
- **-100%** pour rapid_ai, druid_ai, kamikaze_ai, leviathan_ai
- **-20%** sur le temps `game_update` (1.66 ms → 1.32 ms)
- **-0.66 ms/frame** économisés

## Architecture

### Classe `AIProcessorManager`

```python
class AIProcessorManager:
    def __init__(self, world):
        """
        Args:
            world: Instance esper.World
        """
        self.registered_processors: Dict[Type, tuple[Any, int, bool]] = {}
        # component_type -> (processor_instance, priority, is_active)
        
        self.entity_counts: Dict[Type, int] = {}
        # Compteur d'entités par type de composant
        
        self._check_interval = 1.0  # Vérifier toutes les secondes
```

### Méthodes principales

#### `register_ai_processor(component_type, processor, priority)`

Enregistre un processeur IA pour activation dynamique.

**Paramètres** :
- `component_type` : Type de composant qui déclenche l'activation (ex: `DruidAiComponent`)
- `processor` : Instance du processeur à gérer
- `priority` : Priorité esper (ordre d'exécution)

**Exemple** :
```python
ai_manager.register_ai_processor(
    DruidAiComponent,           # Type de composant
    self.druid_ai_processor,    # Instance du processeur
    priority=1                  # Priorité esper
)
```

#### `update(dt)`

Met à jour l'état des processeurs (appelé chaque frame depuis `game_update`).

**Fonctionnement** :
- Vérifie périodiquement (toutes les 1 seconde) si des changements sont nécessaires
- Compte les entités pour chaque type de composant enregistré
- Active/désactive les processeurs selon les besoins

**Optimisation** : Le check n'est pas effectué à chaque frame (60 FPS) mais toutes les secondes, réduisant l'overhead du manager lui-même.

#### `force_check()`

Force une vérification immédiate (utile après spawn/suppression d'entités).

**Cas d'usage** :
```python
# Après création massive d'unités
spawn_druid_batch(10)
ai_manager.force_check()  # Active immédiatement DruidAiProcessor
```

#### `_activate_processor(component_type, processor, priority)`

Active un processeur en l'ajoutant à esper.

**Détails d'implémentation** :
```python
esper.add_processor(processor, priority=priority)
self.registered_processors[component_type] = (processor, priority, True)
```

#### `_deactivate_processor(component_type, processor)`

Désactive un processeur en le retirant d'esper.

**Détails d'implémentation** :
```python
# esper.remove_processor() ne fonctionne qu'avec les TYPES, pas les instances
# Manipulation directe de la liste interne
if processor in esper._processors:
    esper._processors.remove(processor)
```

⚠️ **Note technique** : `esper.remove_processor(processor_type)` attend une **classe** (type) et non une **instance**. Pour retirer une instance spécifique, nous manipulons directement `esper._processors`.

#### `get_status()`

Retourne le statut actuel (debug).

**Retour** :
```python
{
    'DruidAiProcessor': {
        'active': True,
        'entity_count': 3,
        'priority': 1
    },
    'RapidTroopAIProcessor': {
        'active': False,
        'entity_count': 0,
        'priority': 2
    }
}
```

## Intégration dans le jeu

### Initialisation (src/game.py)

```python
# Création du manager
self.ai_manager = AIProcessorManager(es)

# Enregistrement des processeurs IA
self.ai_manager.register_ai_processor(DruidAiComponent, self.druid_ai_processor, priority=1)
self.ai_manager.register_ai_processor(SpeScout, self.rapid_ai_processor_ally, priority=2)
self.ai_manager.register_ai_processor(SpeScout, self.rapid_ai_processor_enemy, priority=3)
self.ai_manager.register_ai_processor(KamikazeAiComponent, self.kamikaze_ai_processor, priority=6)
self.ai_manager.register_ai_processor(SpeLeviathan, self.ai_leviathan_processor, priority=9)

# Note: ArchitectAIProcessor n'est PAS géré (signature custom: process(grid))
```

### Update dans la boucle de jeu

```python
def game_update(self, dt):
    # ... autres updates ...
    
    # Update AI Manager (vérifie périodiquement)
    self.ai_manager.update(dt)
    
    # ... processeurs esper (y compris ceux activés dynamiquement) ...
    es.process(dt)
```

## Processeurs gérés

| Processeur | Composant | Priorité | Description |
|------------|-----------|----------|-------------|
| `DruidAiProcessor` | `DruidAiComponent` | 1 | IA Minimax pour Druides |
| `RapidTroopAIProcessor` (allié) | `SpeScout` | 2 | FSM pour Scouts alliés |
| `RapidTroopAIProcessor` (ennemi) | `SpeScout` | 3 | FSM pour Scouts ennemis |
| `KamikazeAiProcessor` | `KamikazeAiComponent` | 6 | IA suicide Kamikaze |
| `AILeviathanProcessor` | `SpeLeviathan` | 9 | IA Leviathan |

### Processeurs non gérés

**ArchitectAIProcessor** : Signature custom `process(self, grid)` au lieu de `process(self, dt)`. Invoqué manuellement dans `game_update`.

```python
# Invocation manuelle nécessaire
if self.architect_ai_processor:
    self.architect_ai_processor.process(self.grid)
```

## Cas d'usage

### Scénario 1 : Démarrage sans IA

```
1. Jeu démarre avec 0 unités IA
2. AI Manager vérifie : entity_counts = {DruidAiComponent: 0, SpeScout: 0, ...}
3. Aucun processeur n'est ajouté à esper
4. Économie : ~2.46% CPU
```

### Scénario 2 : Spawn de Druide

```
1. Joueur construit un Druide
2. Entité créée avec DruidAiComponent
3. AI Manager (au prochain check) : entity_counts[DruidAiComponent] = 1
4. Active DruidAiProcessor avec priority=1
5. Processeur s'exécute normalement
```

### Scénario 3 : Suppression de toutes les unités

```
1. Tous les Scouts sont détruits
2. AI Manager (au prochain check) : entity_counts[SpeScout] = 0
3. Désactive RapidTroopAIProcessor
4. Économie : ~1.90% CPU
```

### Scénario 4 : Cycles rapides spawn/despawn

```python
# Test de stress (extrait de test_ai_processor_manager.py)
for i in range(10):
    entity = esper.create_entity(DruidAiComponent())
    ai_manager.force_check()  # Active
    esper.delete_entity(entity)
    ai_manager.force_check()  # Désactive
# Résultat : Aucune duplication, comportement stable
```

## Benchmarks et validation

### Méthodologie

Benchmarks réalisés avec `scripts/benchmark/benchmark.py` :
- **Avant** : `benchmark_results_20251106_142235.csv`
- **Après** : `benchmark_results_20251106_145449.csv`
- **Paramètres** : 30s, 0 AI teams, profiling activé

### Résultats quantitatifs

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **FPS moyen** | 31.0 | 31.0 | = |
| **Overhead IA total** | 2.46% | 0.41% | **-83%** ✅ |
| **rapid_ai** | 1.90% (0.61 ms) | 0% | **-100%** ✅ |
| **druid_ai** | 0.03% (0.01 ms) | 0% | **-100%** ✅ |
| **kamikaze_ai** | 0.03% (0.01 ms) | 0% | **-100%** ✅ |
| **leviathan_ai** | 0.06% (0.02 ms) | 0% | **-100%** ✅ |
| **game_update** | 1.66 ms/frame | 1.32 ms/frame | **-20%** ✅ |
| **Temps économisé** | - | **-0.66 ms/frame** | - |

### Interprétation

- **FPS identique** : Le goulot d'étranglement reste le rendering (27%) et le code non-profilé (66%)
- **Overhead IA réduit de 83%** : Les processeurs inutiles ne s'exécutent plus
- **game_update 20% plus rapide** : Moins de processeurs = moins de boucles dans esper
- **`other_ai` reste actif (0.41%)** : Processeur non géré (probablement ArchitectAI)

## Tests

**Fichier** : `tests/test_ai_processor_manager.py`

Suite de tests complète (11 tests, 100% pass rate, 89% coverage) :

```python
# Exemples de tests
def test_processor_activation_when_entity_spawns(ai_manager, test_processor):
    """Vérifie l'activation automatique au spawn"""
    entity = esper.create_entity(TestComponent())
    ai_manager.force_check()
    assert test_processor in esper._processors

def test_processor_deactivation_when_all_entities_removed(ai_manager, test_processor):
    """Vérifie la désactivation automatique"""
    entity = esper.create_entity(TestComponent())
    ai_manager.force_check()
    esper.delete_entity(entity)
    ai_manager.force_check()
    assert test_processor not in esper._processors

def test_rapid_spawn_despawn_cycles(ai_manager, test_processor):
    """Test de stress : 10 cycles rapides"""
    for i in range(10):
        entity = esper.create_entity(TestComponent())
        ai_manager.force_check()
        esper.delete_entity(entity)
        ai_manager.force_check()
    assert test_processor not in esper._processors  # Pas de fuite
```

### Découvertes lors des tests

**Problème esper** : `esper.remove_processor(processor)` ne fonctionne pas avec les instances.

```python
# Code source esper
def remove_processor(processor_type: _Type[Processor]) -> None:
    """Remove a Processor from the World, by type."""
    for processor in _processors:
        if type(processor) is processor_type:  # Compare les TYPES
            _processors.remove(processor)
```

**Solution** : Manipulation directe de `esper._processors.remove(processor_instance)`.

## Limitations

1. **Interval de vérification** : 1 seconde de délai maximum avant activation/désactivation
   - Peut être réduit si nécessaire (`self._check_interval = 0.1`)
   - Trade-off : overhead du manager vs réactivité

2. **Processeurs custom** : Ne supporte que les processeurs avec signature `process(dt)`
   - ArchitectAIProcessor exclu (signature `process(grid)`)

3. **Manipulation interne d'esper** : Utilise `esper._processors` (API privée)
   - Risque de casse si esper change son implémentation interne
   - Alternative future : PR sur esper pour `remove_processor(instance)`

## Évolutions futures

### Optimisations possibles

1. **Check adaptatif** : Réduire l'interval quand le jeu est actif, augmenter quand stable
2. **Event-driven** : Hooks sur spawn/delete pour activation immédiate (vs periodic check)
3. **Pooling de processeurs** : Réutiliser les instances au lieu de add/remove

### Extensibilité

```python
# Exemple d'extension future : processeurs conditionnels
ai_manager.register_conditional_processor(
    component_type=DruidAiComponent,
    processor=druid_ai_processor,
    priority=1,
    condition=lambda: game.difficulty >= "Hard"  # N'active que si difficulté élevée
)
```

## Références

- **Implémentation** : `src/processeurs/ai/ai_processor_manager.py`
- **Tests** : `tests/test_ai_processor_manager.py`
- **Intégration** : `src/game.py` (lignes 1118-1140, 1923)
- **Benchmarks** : `scripts/benchmark/benchmark.py`
- **Analyse** : `scripts/benchmark/analyze_benchmark.py`

## Ressources externes

- [esper documentation](https://github.com/benmoran56/esper) - ECS framework
- [Entity-Component-System pattern](https://en.wikipedia.org/wiki/Entity_component_system)
- [Python profiling](https://docs.python.org/3/library/profile.html)
