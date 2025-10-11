---
i18n:
  en: "Maintenance"
  fr: "🛠️ Maintenance du projet"
---

# 🛠️ Maintenance du projet

Cette page décrit les bonnes pratiques et procédures pour assurer la pérennité et la qualité du projet **Galad Islands**.

---

## 🚦 Stratégie de maintenance

- **Mises à jour fréquentes** : chaque nouvelle fonctionnalité ou correction de bug doit donner lieu à un commit. Privilégiez de petits commits fréquents pour faciliter le suivi et la restauration.
- **Branches dédiées** : pour toute fonctionnalité majeure, créez une branche dédiée avant de fusionner dans la branche principale.
- **Commits clairs** : les messages de commit doivent être explicites et suivre la [convention de commit](../07-annexes/contributing.md#conventions-de-commit).

---

## 📦 Gestion des dépendances

- Les dépendances sont gérées via le fichier `requirements.txt`. Maintenez-le à jour avec les versions compatibles.
- Avant d’ajouter une nouvelle dépendance, vérifiez sa nécessité et l’absence de conflit avec les dépendances existantes.
- **Utilisez un environnement virtuel** pour isoler les dépendances du projet :

    ```bash
    python -m venv env
    source env/bin/activate  # Sur Windows : env\Scripts\activate
    pip install -r requirements.txt
    ```

    > 💡 Les IDE comme VSCode ou PyCharm peuvent automatiser la création et l’activation de l’environnement virtuel.

!!! info "Mise à jour des dépendances"
    Pour mettre à jour les dépendances, modifiez le fichier [requirements.txt](http://_vscodecontentref_/0) puis exécutez :
    ```bash
    pip install -r requirements.txt
    ```

---

## 💾 Sauvegarde et restauration

- **Sauvegardes régulières** : utilisez Git pour versionner le code source et les ressources.
- **Restauration** : en cas de problème, revenez à une version stable avec :
    ```bash
    git checkout <commit_id>
    # ou pour annuler un commit
    git revert <commit_id>
    ```
- **Configuration** : le fichier [galad_config.json](http://_vscodecontentref_/1) contient la configuration du jeu. Sauvegardez-le ou supprimez-le avant des modifications majeures.

---

## ✅ Bonnes pratiques de maintenance

- **Communiquez** avec l’équipe pour coordonner la maintenance et éviter les conflits.
- **Automatisez** les tâches répétitives avec des scripts ou outils adaptés.
- **Intégration continue** : utilisez des outils de CI pour automatiser tests et déploiements.
- **Documentation à jour** : assurez-vous que la documentation reflète toujours l’état du projet.

---

## 📊 Profilage des performances avec cProfile

Le projet inclut un outil de profilage intégré utilisant `cProfile` pour analyser les performances du jeu en temps réel.

### 🚀 Utilisation du profiler

Pour profiler une session de jeu complète :

```bash
python profile_game.py
```

Le profiler :
- **Enregistre** toutes les performances pendant votre partie
- **Analyse** les fonctions les plus lentes automatiquement
- **Génère** un rapport détaillé des 30 fonctions les plus gourmandes
- **Sauvegarde** les résultats complets dans `profile_results.prof`

### 📈 Interprétation des résultats

Le rapport affiche :
- **`cumulative`** : Temps total passé dans la fonction et ses sous-fonctions
- **`percall`** : Temps moyen par appel de fonction
- **`ncalls`** : Nombre d'appels à la fonction

!!! tip "Conseils d'optimisation"
    - Concentrez-vous sur les fonctions avec le plus haut temps `cumulative`
    - Vérifiez les appels fréquents (haut `ncalls`)
    - Optimisez les boucles et calculs mathématiques intensifs

### 🔧 Analyse avancée

Pour une analyse interactive des résultats sauvegardés :

```bash
python -m pstats profile_results.prof
```

Commandes utiles dans l'interpréteur pstats :
- `sort cumulative` : Trier par temps cumulé
- `sort tottime` : Trier par temps propre à la fonction
- `stats 20` : Afficher les 20 premières fonctions

!!! info "Bonnes pratiques de profilage"
    - Profilez des sessions de jeu réalistes (2-5 minutes)
    - Comparez les résultats avant/après optimisation
    - Utilisez le profilage pour identifier les goulots d'étranglement

---

## 🧪 Suite de Tests et Benchmarks

Le projet inclut une suite complète de tests et de benchmarking pour assurer la qualité du code et le suivi des performances.

### 🧪 Tests Automatisés

Le projet utilise `pytest` pour les tests automatisés avec trois catégories de tests :

#### Catégories de Tests

- **Tests Unitaires** (`--unit`) : Testent les composants et fonctions individuels
- **Tests d'Intégration** (`--integration`) : Testent les interactions entre composants
- **Tests de Performance** (`--performance`) : Testent les performances du système sous charge

#### Exécution des Tests

```bash
# Exécuter tous les tests
python run_tests.py

# Exécuter des catégories spécifiques
python run_tests.py --unit              # Tests unitaires uniquement
python run_tests.py --integration       # Tests d'intégration uniquement
python run_tests.py --performance       # Tests de performance uniquement

# Exécuter avec rapport de couverture
python run_tests.py --coverage

# Exécuter en mode verbeux
python run_tests.py --verbose
```

#### Structure des Tests

```
tests/
├── conftest.py              # Fixtures communes et configuration
├── test_components.py       # Tests unitaires des composants ECS
├── test_processors.py       # Tests unitaires des processeurs ECS
├── test_utils.py           # Tests unitaires des fonctions utilitaires
├── test_integration.py     # Tests d'intégration
├── test_performance.py     # Tests de performance
└── run_tests.py           # Script d'exécution des tests
```

### 📊 Benchmarking de Performance

Le projet inclut un programme de benchmarking dédié pour mesurer les performances réelles.

#### Types de Benchmarks

- **Création d'Entités** : Mesure la vitesse de création d'entités ECS (~160k ops/sec)
- **Requêtes de Composants** : Mesure les performances des requêtes de composants
- **Spawn d'Unités** : Simule la création et le spawn d'unités
- **Simulation de Combat** : Teste les performances du système de combat
- **Simulation Complète** : Vraie fenêtre pygame avec mesure FPS (~31 FPS)

#### Exécution des Benchmarks

```bash
# Exécuter tous les benchmarks (10 secondes chacun)
python benchmark.py

# Exécuter seulement le benchmark de simulation complète
python benchmark.py --full-game-only --duration 30

# Exécuter avec durée personnalisée et sauvegarder les résultats
python benchmark.py --duration 5 --output benchmark_results.json

# Exécuter le script de démonstration
python demo_benchmarks.py
```

#### Résultats des Benchmarks

Métriques de performance typiques :

- **Création d'Entités** : 160 000+ opérations/seconde
- **Simulation Complète** : 30+ FPS avec vraie fenêtre pygame
- **Utilisation Mémoire** : Gestion mémoire ECS efficace
- **Requêtes de Composants** : Recherches rapides entité-composant

#### Interprétation des Résultats

```text
🔹 ENTITY_CREATION:
   ⏱️  Durée: 10.00s
   🔢 Opérations: 1,618,947
   ⚡ Ops/sec: 161,895
   💾 Mémoire: 0.00 MB

🔹 FULL_GAME_SIMULATION:
   ⏱️  Durée: 10.03s
   🔢 Opérations: 312
   ⚡ Ops/sec: 31
   💾 Mémoire: 0.00 MB
```

!!! tip "Bonnes Pratiques de Benchmarking"
    - Exécutez les benchmarks sur du matériel dédié pour des résultats cohérents
    - Comparez les résultats avant/après optimisations de performance
    - Utilisez `--full-game-only` pour des tests de performance réalistes
    - Surveillez les métriques FPS pour la validation des performances de jeu

!!! info "Intégration à la Maintenance"
    - Exécutez les tests avant toute modification majeure
    - Utilisez les benchmarks pour valider les améliorations de performance
    - Incluez les résultats de benchmark dans les tests de régression de performance
    - Automatisez l'exécution des benchmarks dans les pipelines CI/CD

---

> Pour toute question ou suggestion, n’hésitez pas à ouvrir une issue ou une pull request sur le dépôt GitHub.
