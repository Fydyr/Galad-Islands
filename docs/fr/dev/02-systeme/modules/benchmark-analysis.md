---
i18n:
  en: "Benchmark Analysis Tool"
  fr: "Outil d'Analyse de Benchmarks"
---

# Outil d'Analyse de Benchmarks

## Vue d'ensemble

L'**outil d'analyse de benchmarks** (`analyze_benchmark.py`) est un script qui parse et analyse les résultats CSV des benchmarks de performance de Galad Islands. Il fournit une vue détaillée des métriques de performance, identifie les goulots d'étranglement et propose des recommandations d'optimisation.

**Fichier** : `scripts/benchmark/analyze_benchmark.py`

## Fonctionnalités

### Analyse automatique

- **Détection automatique** : Trouve le fichier CSV le plus récent si aucun n'est spécifié
- **Métriques système** : CPU, RAM, OS, fréquence processeur
- **Performances globales** : FPS moyen, durée du test, nombre de frames
- **Budget temps** : Comparaison avec la cible 60 FPS
- **Profiling détaillé** : Temps par fonction, appels par frame
- **Activité IA** : Détection des processeurs IA actifs
- **Recommandations** : Suggestions d'optimisation basées sur les métriques

## Utilisation

### Analyse du dernier benchmark

```bash
python3 scripts/benchmark/analyze_benchmark.py
```

Détecte automatiquement le fichier `benchmark_results_*.csv` le plus récent.

### Analyse d'un benchmark spécifique

```bash
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_145449.csv
```

### Depuis le répertoire racine

```bash
cd /home/user/Galad-Islands
python3 scripts/benchmark/analyze_benchmark.py
```

## Format de sortie

### Exemple complet

```text
📊 ANALYSE DU BENCHMARK GALAD ISLANDS
======================================================================

💻 SYSTÈME:
  OS: Linux 6.17.7-3-cachyos
  Python: 3.13.7
  CPU: 8 cores physiques / 16 logiques
  Fréquence CPU: 3600 MHz (max: 4465 MHz)
  RAM: 14.97 GB total / 5.69 GB disponible
  Usage CPU: 5.7%
  Usage RAM: 62.0%

⚡ PERFORMANCES GLOBALES:
  Durée test: 30.0s
  FPS moyen: 31.0 FPS
  Total frames: 929 frames
  Type: full_game_simulation_0_ai

⏱️  BUDGET TEMPS:
  Budget @60 FPS: 16.67 ms/frame
  Budget actuel @31.0 FPS: 32.31 ms/frame
  ⚠️  Dépassement: +15.64 ms/frame (93.8%)

🔥 TOP CONSOMMATEURS CPU (% du temps total):
   1. rendering             27.03% █████████████        ( 8.74 ms/frame)
   2. game_update            4.10% ██                   ( 1.32 ms/frame)
   3. display_flip           2.50% █                    ( 0.81 ms/frame)
   4. other_ai               0.41%                      ( 0.13 ms/frame)
        Autres/Non profilé  65.96%

⏱️  TEMPS MOYENS PAR APPEL:
   1. rendering              8.736 ms/call |   929 appels (1.0/frame) |   8.12s total
   2. game_update            1.324 ms/call |   929 appels (1.0/frame) |   1.23s total
   3. display_flip           0.808 ms/call |   929 appels (1.0/frame) |   0.75s total
   4. other_ai               0.067 ms/call |  1858 appels (2.0/frame) |   0.12s total

🤖 ACTIVITÉ IA:
  ✅ Aucune IA active (mode full_game_simulation_0_ai)

💡 RECOMMANDATIONS:
  📊 Rendering normal (27.0%)
  ⚠️  FPS sous la cible (31.0/60) - optimisation nécessaire

======================================================================
```

## Sections d'analyse

### 1. Informations système (💻 SYSTÈME)

Affiche les spécifications matérielles et logicielles :

- **OS** : Système d'exploitation et version kernel
- **Python** : Version de l'interpréteur
- **CPU** : Nombre de cores physiques/logiques, fréquence actuelle/max
- **RAM** : Mémoire totale et disponible
- **Usage CPU/RAM** : Utilisation au moment du test

**Source** : Colonnes `os`, `python_version`, `cpu_count`, `cpu_freq_mhz`, etc.

### 2. Performances globales (⚡ PERFORMANCES)

Résumé des performances du test :

- **Durée test** : Temps total du benchmark (ex: 30.0s)
- **FPS moyen** : Frames par seconde moyens sur toute la durée
- **Total frames** : Nombre de frames rendues
- **Type** : Type de test (ex: `full_game_simulation_0_ai`)

**Calcul FPS** : `total_frames / duration`

### 3. Budget temps (⏱️ BUDGET TEMPS)

Compare le temps disponible par frame avec la cible 60 FPS :

- **Budget @60 FPS** : 16.67 ms/frame (cible)
- **Budget actuel** : Temps réel disponible par frame
- **Dépassement** : Écart absolu et pourcentage

**Exemple** :
```text
Budget actuel @31.0 FPS: 32.31 ms/frame
⚠️  Dépassement: +15.64 ms/frame (93.8%)
```

Indique que le jeu prend **93.8% de temps en plus** que la cible 60 FPS.

### 4. Top consommateurs CPU (🔥 TOP CONSOMMATEURS)

Liste les fonctions profilées par ordre de consommation CPU :

**Format** :
```text
1. rendering             27.03% █████████████        ( 8.74 ms/frame)
2. game_update            4.10% ██                   ( 1.32 ms/frame)
```

- **Pourcentage** : Part du temps total de test
- **Barre graphique** : Visualisation proportionnelle
- **ms/frame** : Temps moyen par frame

**Code non-profilé** : La ligne "Autres/Non profilé" représente le temps Python/pygame/système non capturé par cProfile (GC, overhead, I/O, etc.).

### 5. Temps moyens par appel (⏱️ TEMPS MOYENS)

Détails pour chaque fonction profilée :

**Format** :
```text
1. rendering  8.736 ms/call | 929 appels (1.0/frame) | 8.12s total
```

- **ms/call** : Temps moyen par appel
- **Appels** : Nombre total d'appels
- **appels/frame** : Fréquence (1.0 = une fois par frame, 2.0 = deux fois)
- **Total** : Temps cumulé sur tout le test

**Utilité** : Identifier les fonctions appelées trop fréquemment ou trop coûteuses.

### 6. Activité IA (🤖 ACTIVITÉ IA)

Détecte les processeurs IA actifs et leur impact :

**Mode 0 IA (aucune unité IA)** :
```text
✅ Aucune IA active (mode full_game_simulation_0_ai)
```

**Mode avec IA** :
```text
🤖 IA active détectée:
  - rapid_ai: 1.90% (0.61 ms/frame)
  - druid_ai: 0.03% (0.01 ms/frame)
```

**Détection** : Parse les colonnes avec suffixes `_ai` et vérifie si `test_type` contient `_0_ai`.

### 7. Recommandations (💡 RECOMMANDATIONS)

Suggestions automatiques basées sur les métriques :

| Condition | Recommandation |
|-----------|---------------|
| `rendering` < 20% | ✅ Rendering optimal |
| `rendering` 20-30% | 📊 Rendering normal |
| `rendering` > 30% | ⚠️ Rendering coûteux |
| `game_update` > 10% | ⚠️ Game update coûteux - optimiser la logique |
| FPS < 30 | 🚨 FPS très bas - jeu non jouable |
| FPS 30-45 | ⚠️ FPS sous la cible - optimisation nécessaire |
| FPS 45-55 | 📊 FPS acceptable - optimisation possible |
| FPS >= 55 | ✅ FPS excellent |

## Analyse comparative (avant/après)

### Workflow recommandé

1. **Benchmark AVANT** l'optimisation :

```bash
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
```

2. **Noter le nom du CSV** généré (ex: `benchmark_results_20251106_142235.csv`)

3. **Implémenter l'optimisation**

4. **Benchmark APRÈS** l'optimisation :

```bash
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
```

5. **Comparer les résultats** :

```bash
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_142235.csv > avant.txt
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_145449.csv > apres.txt
diff -y avant.txt apres.txt
```

### Exemple : Validation de l'AI Manager

**AVANT** (`benchmark_results_20251106_142235.csv`) :

```text
FPS moyen: 31.0 FPS
rapid_ai               1.90% (0.61 ms/frame)
druid_ai               0.03% (0.01 ms/frame)
kamikaze_ai            0.03% (0.01 ms/frame)
leviathan_ai           0.06% (0.02 ms/frame)
game_update            5.13% (1.66 ms/frame)
```

**APRÈS** (`benchmark_results_20251106_145449.csv`) :

```text
FPS moyen: 31.0 FPS
rapid_ai               (absent - désactivé ✅)
druid_ai               (absent - désactivé ✅)
kamikaze_ai            (absent - désactivé ✅)
leviathan_ai           (absent - désactivé ✅)
game_update            4.10% (1.32 ms/frame) ⬇️ -20%
```

**Gains mesurés** :

- Overhead IA : 2.46% → 0.41% (**-83%**)
- game_update : 1.66 ms → 1.32 ms (**-20%**)
- Temps économisé : **0.66 ms/frame**

## Structure du CSV source

Le script attend un CSV avec les colonnes suivantes (générées par `benchmark.py`) :

### Colonnes système

- `timestamp` : Date/heure du benchmark
- `os` : Système d'exploitation
- `python_version` : Version Python
- `cpu_count` : Nombre de cores logiques
- `physical_cpu_count` : Nombre de cores physiques
- `cpu_freq_mhz` : Fréquence CPU actuelle (MHz)
- `cpu_freq_max_mhz` : Fréquence CPU maximale (MHz)
- `total_ram_gb` : RAM totale (GB)
- `available_ram_gb` : RAM disponible (GB)
- `cpu_percent` : Usage CPU (%)
- `ram_percent` : Usage RAM (%)

### Colonnes de performance

- `test_type` : Type de test (ex: `full_game_simulation_0_ai`)
- `duration` : Durée du test (secondes)
- `avg_fps` : FPS moyen
- `total_frames` : Nombre total de frames

### Colonnes de profiling

Pour chaque fonction profilée (ex: `rendering`, `game_update`, `rapid_ai`) :

- `<function>_time` : Temps total (secondes)
- `<function>_calls` : Nombre d'appels
- `<function>_time_per_call` : Temps moyen par appel (ms)

**Exemple** :

```csv
rendering_time,rendering_calls,rendering_time_per_call
8.12,929,8.736
```

## Code source (extraits)

### Détection automatique du dernier CSV

```python
def find_latest_benchmark(directory="."):
    """Trouve le fichier CSV de benchmark le plus récent."""
    csv_files = glob.glob(os.path.join(directory, "benchmark_results_*.csv"))
    if not csv_files:
        return None
    latest = max(csv_files, key=os.path.getmtime)
    return latest
```

### Calcul du budget temps

```python
def analyze_performance(data):
    """Analyse les métriques de performance."""
    avg_fps = data.get('avg_fps', 0)
    target_fps = 60
    target_budget_ms = 1000 / target_fps  # 16.67 ms
    
    if avg_fps > 0:
        current_budget_ms = 1000 / avg_fps
        overshoot_ms = current_budget_ms - target_budget_ms
        overshoot_pct = (overshoot_ms / target_budget_ms) * 100
    
    return {
        'target_budget_ms': target_budget_ms,
        'current_budget_ms': current_budget_ms,
        'overshoot_ms': overshoot_ms,
        'overshoot_pct': overshoot_pct
    }
```

### Extraction des fonctions profilées

```python
def extract_profiled_functions(data):
    """Extrait les fonctions profilées du CSV."""
    profiled = {}
    
    for col in data.keys():
        if col.endswith('_time'):
            func_name = col.replace('_time', '')
            time_s = data.get(f'{func_name}_time', 0)
            calls = data.get(f'{func_name}_calls', 0)
            time_per_call_ms = data.get(f'{func_name}_time_per_call', 0)
            
            profiled[func_name] = {
                'time': time_s,
                'calls': calls,
                'time_per_call': time_per_call_ms
            }
    
    return profiled
```

### Génération des recommandations

```python
def generate_recommendations(data, profiled, avg_fps):
    """Génère des recommandations d'optimisation."""
    recommendations = []
    
    # Analyse du rendering
    rendering_pct = profiled.get('rendering', {}).get('percent', 0)
    if rendering_pct < 20:
        recommendations.append("✅ Rendering optimal")
    elif rendering_pct < 30:
        recommendations.append("📊 Rendering normal")
    else:
        recommendations.append(f"⚠️  Rendering coûteux ({rendering_pct:.1f}%)")
    
    # Analyse du game_update
    game_update_pct = profiled.get('game_update', {}).get('percent', 0)
    if game_update_pct > 10:
        recommendations.append(f"⚠️  Game update coûteux ({game_update_pct:.1f}%) - optimiser la logique")
    
    # Analyse des FPS
    if avg_fps < 30:
        recommendations.append(f"🚨 FPS très bas ({avg_fps:.1f}) - jeu non jouable")
    elif avg_fps < 45:
        recommendations.append(f"⚠️  FPS sous la cible ({avg_fps:.1f}/60) - optimisation nécessaire")
    elif avg_fps < 55:
        recommendations.append(f"📊 FPS acceptable ({avg_fps:.1f}/60) - optimisation possible")
    else:
        recommendations.append(f"✅ FPS excellent ({avg_fps:.1f}/60)")
    
    return recommendations
```

## Cas d'usage

### 1. Diagnostic de performance

**Objectif** : Identifier pourquoi le jeu est lent.

**Commande** :

```bash
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --profile --export-csv
python3 scripts/benchmark/analyze_benchmark.py
```

**Résultat** :

```text
🔥 TOP CONSOMMATEURS CPU:
   1. rendering             43.76% (21.74 ms/frame)  ← GOULOT D'ÉTRANGLEMENT
   2. game_update           15.53% ( 7.72 ms/frame)
```

**Action** : Optimiser le rendering (voir `docs/fr/dev/02-systeme/rendering_optimizations.md`).

### 2. Validation d'optimisation

**Objectif** : Prouver qu'une optimisation fonctionne.

**Workflow** :

```bash
# AVANT
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
# Note le CSV : benchmark_results_20251106_142235.csv

# IMPLÉMENTATION de l'optimisation (ex: AI Manager)

# APRÈS
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --num-ai 0 --profile --export-csv
# Note le CSV : benchmark_results_20251106_145449.csv

# COMPARAISON
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_142235.csv | grep -E "(rapid_ai|game_update)"
python3 scripts/benchmark/analyze_benchmark.py benchmark_results_20251106_145449.csv | grep -E "(rapid_ai|game_update)"
```

**Résultat** :

```text
AVANT:  rapid_ai 1.90%, game_update 5.13%
APRÈS:  rapid_ai (absent), game_update 4.10%
GAIN:   -1.90% overhead IA, -20% game_update
```

### 3. Régression testing

**Objectif** : Détecter les régressions de performance.

**Workflow** :

```bash
# Test de référence
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --profile --export-csv -o baseline.json
cp benchmark_results_*.csv baseline.csv

# Après changements
git checkout feature/new-feature
python3 scripts/benchmark/benchmark.py -d 30 --full-game-only --profile --export-csv -o current.json

# Comparaison
python3 scripts/benchmark/analyze_benchmark.py baseline.csv > baseline_report.txt
python3 scripts/benchmark/analyze_benchmark.py  # Auto-détecte le plus récent
diff baseline_report.txt <(python3 scripts/benchmark/analyze_benchmark.py)
```

**Détection** : Si FPS baisse de plus de 5%, investiguer.

### 4. Profilage ciblé

**Objectif** : Analyser une fonction spécifique.

**Commande** :

```bash
python3 scripts/benchmark/analyze_benchmark.py | grep -A 2 "game_update"
```

**Résultat** :

```text
2. game_update            4.10% ██                   ( 1.32 ms/frame)
   game_update            1.324 ms/call |   929 appels (1.0/frame) |   1.23s total
```

**Interprétation** :

- `1.0/frame` : Appelé une fois par frame (normal)
- `1.32 ms/frame` : Temps raisonnable
- `4.10%` : Part faible du temps total (bon)

## Limitations

### 1. Dépendance au profiling

Le script analyse uniquement les fonctions **profilées** dans `benchmark.py`. Les fonctions non décorées avec `@profile_function` n'apparaissent pas.

**Solution** : Ajouter `@profile_function` aux fonctions critiques.

### 2. Code non-profilé

Le pourcentage "Autres/Non profilé" est souvent élevé (60-70%) car il inclut :

- Overhead Python (GC, interpréteur)
- Pygame internals (non profilés)
- Appels système (I/O, sleep)
- Fonctions non décorées

**Limitation** : Impossible d'optimiser sans profiling plus profond (ex: cProfile complet).

### 3. Variance des benchmarks

Les résultats peuvent varier selon :

- **Charge système** : Autres processus en arrière-plan
- **Fréquence CPU** : Throttling thermique, mode économie d'énergie
- **Aléa du jeu** : Seed aléatoire, spawns variables

**Solution** : Répéter les benchmarks 3 fois, prendre la médiane.

### 4. Granularité temporelle

L'analyse moyenne les performances sur toute la durée. Les pics/drops temporaires ne sont pas visibles.

**Solution future** : Générer des graphiques frame-by-frame (CSV avec timestamp par frame).

## Évolutions futures

### 1. Graphiques visuels

```python
# Exemple avec matplotlib
import matplotlib.pyplot as plt

def plot_benchmark(csv_file):
    data = pd.read_csv(csv_file)
    plt.figure(figsize=(10, 6))
    plt.bar(data['function'], data['percent'])
    plt.xlabel('Fonction')
    plt.ylabel('% CPU')
    plt.title('Profil CPU')
    plt.savefig('benchmark_plot.png')
```

### 2. Export JSON structuré

```python
def export_json(analysis):
    with open('benchmark_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
```

**Utilité** : Intégration CI/CD, monitoring automatique.

### 3. Mode diff

```bash
python3 scripts/benchmark/analyze_benchmark.py --diff baseline.csv current.csv
```

**Sortie** :

```text
📊 COMPARAISON AVANT/APRÈS
  FPS:         31.0 → 31.0 (=)
  rapid_ai:    1.90% → 0% (-100% ✅)
  game_update: 5.13% → 4.10% (-20% ✅)
```

### 4. Alertes de seuil

```python
def check_thresholds(avg_fps, rendering_pct):
    if avg_fps < 30:
        print("🚨 ALERTE: FPS critique!")
        sys.exit(1)
    if rendering_pct > 40:
        print("⚠️  WARNING: Rendering trop coûteux")
        sys.exit(1)
```

**Utilité** : CI/CD rejection si performances dégradées.

## Références

- **Script principal** : `scripts/benchmark/analyze_benchmark.py`
- **Générateur de CSV** : `scripts/benchmark/benchmark.py`
- **Documentation benchmark** : `docs/fr/dev/05-exploitation/operations.md`
- **AI Processor Manager** : `docs/fr/dev/02-systeme/modules/ai-processor-manager.md`

## Ressources externes

- [cProfile documentation](https://docs.python.org/3/library/profile.html)
- [CSV format specification](https://docs.python.org/3/library/csv.html)
- [Performance analysis best practices](https://docs.python.org/3/howto/profiling.html)
