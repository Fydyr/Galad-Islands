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

## 📊 Système de Benchmark et Profilage des Performances

Le projet inclut un système complet de benchmarking et de profilage pour analyser les performances du jeu en temps réel et identifier les goulots d'étranglement.

### 🚀 Types de Benchmarks Disponibles

#### 🎮 Simulation Complète de Jeu

Teste les performances dans des conditions réelles de jeu :

```bash
# Benchmark rapide avec 1 équipe IA
python benchmark.py --full-game-only --num-ai 1

# Test intensif avec 2 équipes IA
python benchmark.py --full-game-only --num-ai 2 --duration 30

# Avec profilage détaillé activé
python benchmark.py --full-game-only --num-ai 2 --profile

# Avec export des résultats en CSV
python benchmark.py --full-game-only --num-ai 2 --profile --export-csv
```

### ⚙️ Options de Benchmark pour la reproductibilité

Lors des simulations complètes, le framerate peut être affecté par le système, le pilote graphique ou les paramètres du jeu. Pour éviter le vsync ou le plafonnement involontaire lors du profilage, le script de benchmark propose de surcharger ces réglages :

```bash
# Désactiver le vsync et autoriser un framerate non limité (utile pour un profilage CPU pur)
python benchmark.py --full-game-only --no-vsync --max-fps 0 --profile --export-csv

# Forcer une limite max de FPS lors du benchmark (0 = illimité)
python benchmark.py --full-game-only --max-fps 120 --profile --export-csv
```

Notes :

- `--no-vsync` définit la configuration `vsync` du jeu sur `false` pour cette exécution de benchmark et laisse le `GameEngine` créer la fenêtre en conséquence.
- `--max-fps` permet d'appliquer une limite supérieure au rendu (0 = illimité).


#### 🧠 Benchmark Maraudeur (Apprentissage IA)

Compare l'impact de l'apprentissage machine sur les performances :

```bash
# Comparaison ML activé vs désactivé avec export CSV
python benchmark.py --maraudeur-benchmark --export-csv
```

Ce benchmark compare :

- **Configuration par défaut** : Apprentissage ML désactivé (config standard)
- **Configuration ML** : Apprentissage activé pour mesurer l'impact

#### 🔧 Benchmarks Techniques

Tests ciblés sur des composants spécifiques :

```bash
# Tous les benchmarks techniques
python benchmark.py

# Benchmarks individuels disponibles :
# - Création d'entités ECS (~160k ops/sec)
# - Requêtes de composants
# - Spawn d'unités avec progression
# - Système de combat
```

### 📈 Profilage Détaillé avec GameProfiler

Le système intègre un profiler personnalisé qui mesure les performances de chaque système du jeu :

#### Sections Profilées Automatiquement

- **game_update** : Mise à jour logique du jeu
- **rendering** : Rendu graphique
- **display_flip** : Mise à jour de l'affichage
- **IA par type** : maraudeur_ai, druid_ai, architect_ai, etc.

#### Interprétation des Résultats de Profilage

```text
⚡ TOP SYSTÈMES LES PLUS COÛTEUX:
• game_update: 26.0%      ← Logique principale du jeu
• rendering: 20.0%        ← Rendu graphique
• display_flip: 2.3%      ← Mise à jour écran
• rapid_ai: 2.1%          ← IA des unités rapides
• leviathan_ai: 0.1%      ← IA des Léviathans
```

### � Export et Analyse des Données

#### Export CSV avec Informations Système

Le système peut exporter les résultats en CSV avec :

```bash
# Export automatique des métriques système
python benchmark.py --full-game-only --profile --export-csv
```

**Contenu du CSV exporté :**

- Informations système (OS, CPU, mémoire)
- Métriques de performance (FPS, frames, durée)
- Statistiques détaillées par IA
- Analyse des systèmes les plus coûteux

#### Lecture des Résultats

```bash
# Lire le dernier fichier CSV généré
python read_benchmark_csv.py --latest

# Afficher tous les fichiers disponibles
python read_benchmark_csv.py --all
```

### 🎯 Utilisation Pratique

#### Pour le Développement

```bash
# Test rapide des performances actuelles
python benchmark.py --full-game-only --num-ai 1

# Analyse approfondie avec export pour documentation
python benchmark.py --full-game-only --num-ai 2 --profile --export-csv
```

#### Pour l'Optimisation

```bash
# Mesurer l'impact de l'IA Maraudeur
python benchmark.py --maraudeur-benchmark --export-csv

# Comparer avant/après optimisation
python benchmark.py --profile --export-csv
```

#### Pour les Tests de Performance

```bash
# Test de charge avec spawn progressif
python benchmark.py --full-game-only --num-ai 2 --duration 60
```

### 🧪 Suite de Tests Automatisés

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

```text
tests/
├── conftest.py              # Fixtures communes et configuration
├── test_components.py       # Tests unitaires des composants ECS
├── test_processors.py       # Tests unitaires des processeurs ECS
├── test_utils.py           # Tests unitaires des fonctions utilitaires
├── test_integration.py     # Tests d'intégration
├── test_performance.py     # Tests de performance
└── run_tests.py           # Script d'exécution des tests
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
