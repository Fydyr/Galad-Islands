# Galad Config Tool - Documentation technique

## 📋 Architecture générale

Le **Galad Config Tool** (`tools/galad_config.py`) est un utilitaire Tkinter autonome de 546 lignes qui réplique et étend l'interface d'options du jeu principal. Il fonctionne en lecture/écriture directe des fichiers de configuration JSON.

## 🏗️ Structure du code

### Classes principales

#### `GaladConfigApp(tk.Tk)`
Classe principale héritant de `tk.Tk`, gère l'application complète.

**Méthodes d'initialisation :**
```python
def __init__(self):
    # Initialisation de la fenêtre principale
    # Chargement de la configuration
    # Construction de l'UI
    # Gestion des fichiers manquants avec popups messagebox
```

**Attributs clés :**

- `self.config` : Dict contenant la configuration chargée
- `self.config_path` : Path vers galad_config.json
- `self.resolutions_path` : Path vers galad_resolutions.json
- `self.notebook` : Widget ttk.Notebook pour les onglets

### Configuration et persistance

#### Chargement de configuration

```python
def load_config(self):
    """Charge le fichier galad_config.json avec gestion d'erreurs"""
    try:
        # Lecture JSON avec fallback sur valeurs par défaut
        # Gestion des fichiers manquants avec messagebox.showwarning
        # Création automatique si nécessaire
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur de chargement: {e}")
```

#### Sauvegarde

```python
def save_config(self):
    """Sauvegarde immédiate dans galad_config.json"""
    # Écriture JSON avec indentation
    # Gestion d'erreurs avec messagebox.showerror
```

### Interface utilisateur - Architecture par onglets

#### Onglet Display (`_build_display_tab`)

**Widgets principaux :**
- `ttk.Combobox` pour sélection résolution avec `bind("<<ComboboxSelected>>")`
- `ttk.Checkbutton` pour mode fenêtre avec `command=self._on_windowed_changed`
- `ttk.Scale` pour sensibilité caméra avec `command=self._on_camera_changed`
- `ttk.Combobox` pour langue avec callback immédiat

**Gestion des résolutions :**

```python
def _refresh_resolutions(self):
    """Met à jour la liste des résolutions (builtin + custom)"""
    # Combine résolutions prédéfinies et personnalisées
    # Marque les customs avec text du locale
    # Met à jour le combobox values
```

**Ajout de résolutions :**

```python
def _add_resolution(self):
    """Ajoute une résolution personnalisée"""
    # Validation des entrées largeur/hauteur
    # Évite les doublons
    # Sauvegarde immédiate dans galad_resolutions.json
    # Refresh de l'interface
```

#### Onglet Audio (`_build_audio_tab`)

**Widgets principaux :**

- `ttk.Scale` avec `command=self._on_volume_changed`
- `ttk.Label` pour affichage pourcentage en temps réel

**Mise à jour en temps réel :**

```python
def _on_volume_changed(self, value):
    """Callback slider volume"""
    # Conversion float et mise à jour config
    # Update immédiat du label pourcentage
    # Pas de sauvegarde (fait au clic Apply)
```

#### Onglet Controls (`_build_controls_tab`)

**Architecture scrollable :**

```python
# Canvas + Scrollbar pour navigation fluide
controls_canvas = tk.Canvas(controls_frame)
scrollbar = ttk.Scrollbar(controls_frame, orient="vertical", command=controls_canvas.yview)
scrollable_frame = ttk.Frame(controls_canvas)

# Configuration du scrolling
controls_canvas.configure(yscrollcommand=scrollbar.set)
controls_canvas.bind('<Configure>', lambda e: controls_canvas.configure(scrollregion=controls_canvas.bbox("all")))
```

**Groupes de contrôles :**

```python
control_groups = {
    "Commandes d'unité": ["unit_move_forward", "unit_move_backward", ...],
    "Contrôles caméra": ["camera_move_up", "camera_move_down", ...],
    "Sélection": ["select_all_units", "target_unit", ...],
    "Système": ["toggle_pause", "show_help", ...],
    "Groupes de contrôle": ["assign_group_1", "select_group_1", ...]
}
```

**Widgets dynamiques :**

```python
for group_name, keys in control_groups.items():
    # Création LabelFrame pour chaque groupe
    # Génération ttk.Combobox pour chaque touche
    # Bind sur <<ComboboxSelected>> pour sauvegarde immédiate
    # Utilisation de lambda avec default parameter pour closure
```

#### Onglet Configuration (`_build_config_tab`)

**Sélection de fichiers :**

```python
def _browse_config_file(self):
    """Dialog sélection galad_config.json"""
    filename = filedialog.askopenfilename(
        title="Sélectionner le fichier de configuration",
        filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
        initialdir=str(CONFIG_PATH.parent)
    )
    # Validation du fichier sélectionné
    # Mise à jour des Entry widgets
```

### Localisation et changement de langue

#### Système de traduction extensible

```python
# Import du système de localisation centralisé
from src.settings.localization import get_available_languages, get_current_language, set_language, t

# Menu déroulant extensible pour les langues
self.langs_dict = get_available_languages()  # {"fr": "Français", "en": "English"}
lang_names = list(self.langs_dict.values())  # ["Français", "English"]
self.lang_combo = ttk.Combobox(frm, values=lang_names, state="readonly")
```

#### Ajout d'une nouvelle langue

**Étape 1** - Créer le fichier de traductions :

```python
# assets/locales/spanish.py
TRANSLATIONS = {
    "options.display": "Pantalla",
    "options.audio": "Audio",
    # ... toutes les clés traduites
}
```

**Étape 2** - Mettre à jour le LocalizationManager :

```python
# Dans src/settings/localization.py
language_modules = {
    "fr": "assets.locales.french",
    "en": "assets.locales.english", 
    "es": "assets.locales.spanish"  # Nouveau
}

def get_available_languages(self):
    return {
        "fr": "Français",
        "en": "English",
        "es": "Español"  # Nouveau
    }
```

**Étape 3** - Le tool s'adapte automatiquement :

- Le combobox affiche "Español" dans la liste
- La sélection fonctionne immédiatement
- Aucune modification du code UI nécessaire

#### Mise à jour dynamique de l'UI

```python
def _refresh_ui_texts(self):
    """Met à jour tous les textes de l'interface"""
    try:
        # Parcours récursif de tous les widgets
        # Identification par winfo_name() ou attributs personnalisés
        # Mise à jour des text/title selon le type de widget
        for widget in self.winfo_children():
            self._update_widget_texts(widget)
    except Exception as e:
        messagebox.showwarning("Avertissement", f"Erreur mise à jour UI: {e}")
```

## 🔧 Gestion des fichiers de configuration

### Chemins et résolution

```python
# Utilisation de pathlib pour gestion cross-platform
CONFIG_PATH = Path(__file__).parent.parent / "galad_config.json"
RES_PATH = Path(__file__).parent.parent / "galad_resolutions.json"

# Résolution dynamique via onglet Configuration
def _apply_paths(self):
    """Applique les nouveaux chemins de fichiers"""
    # Validation d'existence des dossiers
    # Mise à jour des paths globaux
    # Rechargement de la configuration
```

### Format des données

#### `galad_config.json`

```python
DEFAULT_CONFIG = {
    "window_mode": "windowed",
    "screen_width": 1920,
    "screen_height": 1080,
    "volume_music": 0.7,
    "camera_sensitivity": 1.5,
    "language": "fr",
    "key_bindings": {
        # Mapping complet des touches par action
        "unit_move_forward": ["z"],
        "camera_move_up": ["up"],
        # ... 40+ bindings
    }
}
```

#### `galad_resolutions.json`

```python
# Format: Array de [width, height]
[
    [1920, 1011],
    [2560, 1440],
    [3840, 2160]
]
```

### Fonctions utilitaires

#### Gestion des résolutions

```python
def load_custom_resolutions():
    """Charge les résolutions personnalisées"""
    # Lecture JSON avec fallback sur liste vide
    # Validation du format [width, height]
    
def save_resolutions_list(res_list):
    """Sauvegarde les résolutions personnalisées"""
    # Écriture JSON avec gestion d'erreurs
    # Popup messagebox.showerror en cas d'échec
```

#### Intégration avec le système de résolutions du jeu

```python
# Le jeu utilise src.settings.resolutions.get_all_resolutions()
# qui combine automatiquement builtin + custom
def get_all_resolutions():
    builtin = [(1920, 1080), (1366, 768), ...]  # Résolutions standard
    custom = load_custom_resolutions()          # Résolutions ajoutées
    return [(w, h, label) for w, h in builtin + custom]
```

## 🚀 Compilation et distribution

### PyInstaller

```bash
pyinstaller --onefile --windowed tools/galad_config.py --name galad-config-tool \
  --add-data "assets/locales:assets/locales" \
  --add-data "src:src"
```

**Paramètres critiques :**

- `--onefile` : Exécutable autonome
- `--windowed` : Pas de console (GUI uniquement)
- `--add-data` : Inclusion des dépendances pour imports dynamiques

### GitHub Actions intégration

```yaml
# Dans .github/workflows/release.yml et manual-release.yml
- name: Build Config Tool
  run: |
    python -m PyInstaller --onefile --windowed tools/galad_config.py 
    --name galad-config-tool 
    --add-data "assets/locales:assets/locales" 
    --add-data "src:src"
    
- name: Create Release Archive
  run: |
    mkdir -p release/
    cp dist/galad-islands release/
    cp dist/galad-config-tool release/
    cp -r assets/ release/
```

## 📊 Flux de données

### Workflow de modification

1. **Chargement** : `load_config()` → `self.config` dict
2. **Interface** : Widgets bindés aux valeurs config
3. **Modification** : Callbacks mettent à jour `self.config`
4. **Persistance** : `save_config()` au clic "Apply"

### Synchronisation avec le jeu

- **Lecture partagée** : Même fichiers JSON
- **Pas de communication runtime** : Config au démarrage du jeu
- **Hot-reload** : Non supporté, redémarrage jeu requis

## 🧪 Gestion d'erreurs et robustesse

### Validation des entrées

```python
# Résolutions : Validation numérique avec try/except
# Chemins de fichiers : Vérification Path.exists()
# JSON : Fallback sur valeurs par défaut si parsing échoue
```

### Messages utilisateur

```python
# Remplacement de tous les print() par messagebox
messagebox.showwarning()  # Avertissements non-bloquants
messagebox.showerror()    # Erreurs critiques
messagebox.showinfo()     # Informations utiles
```

### Fallbacks et récupération

```python
# Configuration corrompue → Régénération avec valeurs par défaut
# Fichiers manquants → Création automatique
# Erreurs de traduction → Fallback sur clés brutes
```

## 🔄 Points d'intégration avec le jeu

### Modules importés

```python
# Configuration management
from src.settings.settings import ConfigManager
from src.settings.resolutions import get_all_resolutions

# Localization
from src.functions.localization import load_language
from assets.locales.french import t as t_fr
from assets.locales.english import t as t_en

# Controls mapping  
from src.settings.controls import DEFAULT_KEY_BINDINGS
```

### Synchronisation des données

- **Lecture** : Tool lit les mêmes fichiers que le jeu
- **Écriture** : Format identique, compatible hot-swap
- **Validation** : Mêmes règles de validation que le système de config du jeu

## 💡 Patterns et bonnes pratiques

### Séparation des responsabilités

- **UI Logic** : Méthodes `_build_*_tab()` 
- **Data Logic** : Méthodes `load_*()` et `save_*()`
- **Event Handling** : Callbacks `_on_*_changed()`

### Performance

- **Lazy Loading** : Résolutions chargées à la demande
- **Batch Updates** : Sauvegarde groupée au lieu d'écriture individuelle
- **UI Threading** : Pas de blocking I/O sur le thread principal

### Maintenabilité

- **Configuration centralisée** : `DEFAULT_CONFIG` dict
- **Traductions externalisées** : Réutilisation des modules du jeu
- **Validation cohérente** : Mêmes règles que le jeu principal