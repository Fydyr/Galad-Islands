---
i18n:
  en: "Localization"
  fr: "Système de localisation"
---

# Système de localisation

Le système de localisation de Galad Islands permet de supporter plusieurs langues avec une architecture modulaire et extensible.

## Vue d'ensemble

### Architecture du système

```text
src/settings/localization.py    # Gestionnaire principal
├── LocalizationManager         # Classe singleton
├── Fonctions utilitaires       # t(), set_language(), etc.
└── Intégration config          # Persistance des préférences

assets/locales/                 # Structure modulaire
├── french.py                   # Compatibilité - charge assets.locales.french
├── english.py                  # Compatibilité - charge assets.locales.english
├── fr/                         # Traductions françaises modulaires
│   ├── __init__.py            # Chargement automatique
│   ├── navigation.py          # Menus, modes de jeu, sélection d'équipe
│   ├── game.py                # Interface de jeu, victoire/défaite, modales
│   ├── options.py             # Tous les paramètres et configuration
│   ├── shops.py               # Interface boutique et objets
│   ├── help.py                # Conseils, infobulles et aide
│   ├── actionbar.py           # Éléments de la barre d'action
│   ├── units.py               # Noms d'unités, classes et descriptions
│   ├── teams.py               # Noms d'équipes et descriptions
│   ├── debug.py               # Éléments d'interface de débogage
│   ├── controls.py            # Paramètres de contrôle et raccourcis
│   ├── system.py              # Messages système et notifications
│   ├── tutorial.py            # Contenu du tutoriel et guidage
│   └── gameplay.py            # Éléments de gameplay principaux
├── en/                         # Traductions anglaises modulaires
│   └── [structure identique]   # Même organisation
└── [nouvelle_langue]/          # Futures langues
```

### Organisation modulaire

La nouvelle structure modulaire organise les traductions en catégories logiques, facilitant la maintenance et réduisant la taille des fichiers. Chaque catégorie est un module Python séparé qui est chargé automatiquement.

### Avantages

- **Maintenance facilitée** : Chaque catégorie peut être mise à jour indépendamment
- **Meilleure organisation** : Les traductions liées sont groupées ensemble
- **Taille de fichier réduite** : Les fichiers plus petits sont plus faciles à gérer
- **Chargement automatique** : Aucune gestion manuelle des imports requise

### Format des catégories

**Exemple :** `assets/locales/fr/navigation.py`

```python
# -*- coding: utf-8 -*-
"""
Traductions de navigation pour Galad Islands
"""

TRANSLATIONS = {
    # Menu principal
    "menu.play": "Jouer",
    "menu.options": "Options",
    "menu.quit": "Quitter",

    # Modes de jeu
    "gamemode.select_mode_title": "Mode de jeu",
    "gamemode.select_mode_message": "Sélectionnez un mode de jeu",
    "gamemode.player_vs_ai": "Joueur vs IA",
    "gamemode.ai_vs_ai": "IA vs IA (Spectateur)",

    # Sélection d'équipe
    "team_selection.title": "Choisissez votre équipe",
    "team_selection.message": "Sélectionnez votre côté de départ :",
    "team_selection.team1": "La Flotte de l'Aube",
    "team_selection.team2": "La Légion des Abysses",
}
```

### Chargement automatique

Le système utilise des fichiers `__init__.py` pour charger automatiquement tous les modules de catégorie dans chaque répertoire de langue.

**Exemple :** `assets/locales/fr/__init__.py`

```python
# -*- coding: utf-8 -*-
"""
Traductions françaises pour Galad Islands - Module de chargement automatique
"""

import importlib
import os

TRANSLATIONS = {}

# Charger automatiquement tous les modules de catégorie dans ce répertoire
current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith('.py') and filename not in ['__init__.py', '__pycache__']:
        module_name = filename[:-3]  # Supprimer l'extension .py
        try:
            category_module = importlib.import_module(f'assets.locales.fr.{module_name}')
            TRANSLATIONS.update(category_module.TRANSLATIONS)
        except ImportError:
            continue  # Ignorer les modules qui ne peuvent pas être chargés
```

## Gestionnaire de localisation

### LocalizationManager (Singleton)

**Fichier :** `src/settings/localization.py`

```python
class LocalizationManager:
    """Gestionnaire singleton pour les traductions."""
    
    def __init__(self):
        self._current_language = "fr"       # Langue par défaut
        self._translations = {}             # Cache des traductions
        self._load_translations()           # Chargement initial
    
    def translate(self, key: str, default: str = None, **kwargs) -> str:
        """Traduit une clé avec paramètres optionnels.
        
        Args:
            key: Clé de traduction (ex: "menu.play")
            default: Valeur par défaut si la clé n'existe pas
            **kwargs: Paramètres dynamiques pour la traduction
        
        Returns:
            Texte traduit ou clé/default si non trouvé
        """
        translation = self._translations.get(key, default or key)
        
        # Support des paramètres dynamiques
        if kwargs:
            translation = translation.format(**kwargs)
        
        return translation
    
    def _load_translations(self):
        """Charge les traductions pour la langue actuelle"""
        try:
            # Mapping des langues vers les modules modulaires
            language_modules = {
                "fr": "assets.locales.french", 
                "en": "assets.locales.english"
            }
            
            module_name = language_modules.get(self._current_language, "assets.locales.french")
            translation_module = importlib.import_module(module_name)
            self._translations = translation_module.TRANSLATIONS

    def set_language(self, language_code: str) -> bool:
        """Change la langue et recharge les traductions."""
        if language_code in ["fr", "en"]:
            self._current_language = language_code
            config_manager.set("language", language_code)
            self._load_translations()
            return True
        return False
```

### Fonctions utilitaires globales

```python
# Importation simple depuis n'importe où
from src.settings.localization import t, set_language, get_current_language

# Usage dans le code du jeu
title = t("menu.play")                           # "Jouer" ou "Play"
volume_text = t("options.volume_music_label", volume=75)  # Avec paramètres
```

## Ajouter une nouvelle langue

### Aperçu du processus

L'ajout d'une nouvelle langue suit ces étapes :

1. **Créer la structure modulaire** : Copier un répertoire de langue existant
2. **Traduire les catégories** : Traduire chaque fichier de catégorie
3. **Créer le module de chargement automatique** : `__init__.py`
4. **Créer le fichier de compatibilité** : Fichier racine pour la compatibilité
5. **Mettre à jour le gestionnaire** : Ajouter la nouvelle langue
6. **Validation et test** : Vérifier que toutes les clés sont traduites

### Étape 1 : Créer la structure modulaire

Copiez le répertoire d'une langue existante :

```bash
cp -r assets/locales/fr assets/locales/es
```

### Étape 2 : Traduire les catégories

Traduisez chaque fichier de catégorie. Commencez par `navigation.py` :

**`assets/locales/es/navigation.py`**

```python
# -*- coding: utf-8 -*-
"""
Traducciones de navegación para Galad Islands
"""

TRANSLATIONS = {
    # Menú principal
    "menu.play": "Jugar",
    "menu.options": "Opciones",
    "menu.quit": "Salir",

    # Modos de juego
    "gamemode.select_mode_title": "Modo de juego",
    "gamemode.select_mode_message": "Selecciona un modo de juego",
    "gamemode.player_vs_ai": "Jugador vs IA",
    "gamemode.ai_vs_ai": "IA vs IA (Espectador)",

    # Selección de equipo
    "team_selection.title": "Elige tu equipo",
    "team_selection.message": "Selecciona tu lado inicial:",
    "team_selection.team1": "La Flota del Alba",
    "team_selection.team2": "La Legión del Abismo",
}
```

Répétez pour toutes les catégories : `game.py`, `options.py`, `shops.py`, etc.

### Étape 3 : Créer le module de chargement automatique `__init__.py`

Créez le fichier `__init__.py` pour le chargement automatique :

**`assets/locales/es/__init__.py`**

```python
# -*- coding: utf-8 -*-
"""
Traducciones españolas para Galad Islands - Módulo de carga automática
"""

import importlib
import os

TRANSLATIONS = {}

# Cargar automáticamente todos los módulos de categoría en este directorio
current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith('.py') and filename not in ['__init__.py', '__pycache__']:
        module_name = filename[:-3]  # Remover extensión .py
        try:
            category_module = importlib.import_module(f'assets.locales.es.{module_name}')
            TRANSLATIONS.update(category_module.TRANSLATIONS)
        except ImportError:
            continue  # Ignorar módulos que no se puedan cargar
```

### Étape 4 : Créer le fichier de compatibilité

Créez le fichier racine de compatibilité :

**`assets/locales/spanish.py`**

```python
# -*- coding: utf-8 -*-
"""
Traducciones españolas para Galad Islands (compatibilidad)
"""

# Cargar traducciones modulares
from assets.locales.es import TRANSLATIONS as _ES_CATEGORIES

# Diccionario principal de traducciones para compatibilidad
TRANSLATIONS = {}
TRANSLATIONS.update(_ES_CATEGORIES)
```

### Étape 5 : Mettre à jour le gestionnaire

Modifiez `src/settings/localization.py` pour supporter la nouvelle langue :

```python
def _load_translations(self):
    """Carga las traducciones para el idioma actual"""
    try:
        # Mapeo de idiomas hacia módulos modulares
        language_modules = {
            "fr": "assets.locales.french", 
            "en": "assets.locales.english",
            "es": "assets.locales.spanish"  # Nuevo idioma
        }
        
        module_name = language_modules.get(self._current_language, "assets.locales.french")
        translation_module = importlib.import_module(module_name)
        self._translations = translation_module.TRANSLATIONS

def get_available_languages(self):
    """Devuelve la lista de idiomas disponibles"""
    return {
        "fr": "Français",
        "en": "English", 
        "es": "Español"  # Nuevo idioma
    }
```

### Étape 6 : Validation et test

```python
# Script de validación de traducciones
def validate_translations():
    """Verifica que todas las claves estén traducidas."""
    
    from assets.locales import french, english, spanish
    
    fr_keys = set(french.TRANSLATIONS.keys())
    en_keys = set(english.TRANSLATIONS.keys())
    es_keys = set(spanish.TRANSLATIONS.keys())
    
    # Claves faltantes
    missing_en = fr_keys - en_keys
    missing_es = fr_keys - es_keys
    
    if missing_en:
        print(f"Claves faltantes en inglés: {missing_en}")
    
    if missing_es:
        print(f"Claves faltantes en español: {missing_es}")
    
    print(f"Francés: {len(fr_keys)} claves")
    print(f"Inglés: {len(en_keys)} claves")
    print(f"Español: {len(es_keys)} claves")
```

**Avantages de l'approche modulaire :**

- **Configuration plus rapide** : Copier la structure existante au lieu de créer un fichier monolithique
- **Maintenance plus facile** : Traduire une catégorie à la fois
- **Meilleure organisation** : Les traductions liées restent ensemble
- **Chargement automatique** : Pas besoin de mettre à jour manuellement les listes d'imports
