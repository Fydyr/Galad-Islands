# Suite de Tests Galad Islands

Cette suite de tests fournit une couverture complète pour faciliter la maintenance et le développement du jeu Galad Islands.

Veuillez noter que certains tests peuvent échouer mais en réalité, le jeu fonctionne correctement. Ces tests sont désactivés et en cours de révision.

## Structure des Tests

```yaml
tests/
├── conftest.py              # Configuration commune et fixtures
├── test_processors.py       # Tests des processeurs ECS
├── test_components.py       # Tests des composants core
├── test_utils.py           # Tests des utilitaires
├── test_integration.py     # Tests d'intégration
├── test_performance.py     # Tests de performance
├── test_AI.py             # Tests IA (existant)
├── test_boutique_unified.py # Tests boutique (existant)
├── test_tips.py           # Tests tips (existant)
scripts/
└── benchmark/             # Dossier contenant les benchmarks
    ├── benchmark.py       # Système de benchmark et profilage
    ├── demo_benchmarks.py # Démos des benchmarks
    └── read_benchmark_csv.py # Lecture des résultats de benchmarks
```

## Installation des Dépendances

```bash
pip install -r requirements-dev.txt
```

Les dépendances de test incluent :

- `pytest` : Framework de test
- `pytest-cov` : Couverture de code
- `pytest-mock` : Mocking pour les tests

## Lancement des Tests

### Commande Simple

```bash
# Lancer tous les tests
python run_tests.py

# Ou directement avec pytest
pytest
```

### Options Avancées

```bash
# Tests unitaires seulement
python run_tests.py --unit

# Tests d'intégration seulement
python run_tests.py --integration

# Tests de performance seulement
python run_tests.py --performance

# Avec couverture de code
python run_tests.py --coverage

# Rapport HTML de couverture
python run_tests.py --coverage --html-report

# Mode verbeux
python run_tests.py --verbose

# Fichier spécifique
python run_tests.py --file test_processors.py

# Arrêter au premier échec
python run_tests.py --fail-fast

# Debug (pas de capture de sortie)
python run_tests.py --no-capture
```

## Types de Tests

### Tests Unitaires (`--unit`)

Tests isolés pour les composants individuels :

- **Composants** : PositionComponent, HealthComponent, TeamComponent, etc.
- **Processeurs** : CombatRewardProcessor, FlyingChestProcessor, etc.
- **Utilitaires** : sprite_utils, version_utils

### Tests d'Intégration (`--integration`)

Tests des interactions entre composants :

- Système de combat complet
- Création et gestion des entités
- Requêtes de composants ECS

### Tests de Performance (`--performance`)

Tests pour identifier les goulots d'étranglement :

- Création d'entités en masse
- Requêtes de composants
- Traitement des récompenses de combat
- Utilisation mémoire

## Fixtures Disponibles

Les fixtures suivantes sont disponibles dans `conftest.py` :

- `pygame_init` : Initialisation de pygame
- `world` : Monde esper propre pour chaque test
- `basic_entity` : Entité basique avec position, santé et équipe
- `enemy_entity` : Entité ennemie
- `mock_sprite` : Sprite mock pour les tests
- `test_surface` : Surface pygame pour les tests de rendu

## Marqueurs Pytest

- `@pytest.mark.unit` : Tests unitaires
- `@pytest.mark.integration` : Tests d'intégration
- `@pytest.mark.performance` : Tests de performance
- `@pytest.mark.slow` : Tests lents (désactivés par défaut)

## Rapports de Couverture

Les rapports de couverture montrent le pourcentage de code couvert par les tests :

```bash
# Rapport terminal
python run_tests.py --coverage

# Rapport HTML (ouvre htmlcov/index.html)
python run_tests.py --coverage --html-report
```

## Tests Existants

La suite inclut les tests existants :

- `test_AI.py` : Tests du système d'IA
- `test_boutique_unified.py` : Tests de la boutique unifiée
- `test_tips.py` : Tests du système de tips traduites
- `benchmark/` : Système de benchmark et profilage des performances

## Bonnes Pratiques

### Écriture de Tests

1. **Nommer les tests clairement** : `test_unit_death_creates_reward_chest`
2. **Utiliser des fixtures** : Réutiliser `world`, `basic_entity`, etc.
3. **Nettoyer après les tests** : esper gère automatiquement le nettoyage
4. **Tester les cas d'erreur** : Unités mortes, composants manquants, etc.

### Exemple de Test

```python
def test_combat_reward_creation(world):
    """Test que la mort d'une unité crée une récompense."""
    # Créer une unité ennemie morte
    entity = esper.create_entity()
    esper.add_component(entity, PositionComponent(100, 100))
    esper.add_component(entity, HealthComponent(0, 100))  # Morte
    esper.add_component(entity, TeamComponent(Team.ENEMY))

    # Créer la récompense
    processor = CombatRewardProcessor()
    processor.create_unit_reward(entity)

    # Vérifier qu'un coffre existe
    chests = [e for e in esper._entities.keys()
              if esper.has_component(e, FlyingChestComponent)]
    assert len(chests) == 1
```

## Maintenance

### Ajouter de Nouveaux Tests

1. Créer un fichier `test_*.py` dans le dossier `tests/`
2. Importer les modules nécessaires
3. Utiliser les fixtures de `conftest.py`
4. Marquer avec `@pytest.mark.unit`, `@pytest.mark.integration`, etc.

### Déboguer les Tests

```bash
# Voir la sortie complète
python run_tests.py --no-capture --verbose

# Arrêter au premier échec
python run_tests.py --fail-fast

# Tester un fichier spécifique
python run_tests.py --file test_processors.py -v
```

## Intégration CI/CD

Pour intégrer dans un pipeline CI/CD :

```yaml
# Exemple GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements-dev.txt
    python run_tests.py --coverage --fail-fast

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./htmlcov/coverage.xml
```

## Métriques Cibles

- **Couverture de code** : > 80%
- **Temps d'exécution** : < 30 secondes pour tous les tests
- **Tests par composant** : Au moins 3 tests par classe importante

## Support

En cas de problème avec les tests :

1. Vérifier que toutes les dépendances sont installées
2. S'assurer que pygame est correctement initialisé
3. Vérifier les imports relatifs depuis le dossier `src/`
4. Consulter les fixtures disponibles dans `conftest.py`