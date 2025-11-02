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

assets/locales/                 # Fichiers de traduction
├── french.py                   # Traductions françaises (jeu)
├── english.py                  # Traductions anglaises (jeu)
├── tools/                      # Traductions des outils GUI
│   ├── clean_models_gui_fr.py  # Nettoyeur de modèles (FR)
│   ├── clean_models_gui_en.py  # Nettoyeur de modèles (EN)
│   ├── galad_config_tool_fr.py # Outil de config (FR)
│   └── galad_config_tool_en.py # Outil de config (EN)
└── [nouvelle_langue].py        # Futures langues
```

## Gestionnaire de localisation

### LocalizationManager (Singleton)

**Fichier :** `src/settings/localization.py`

```python
class LocalizationManager:
    """Gestionnaire singleton pour les traductions."""
    
    def __init__(self):
        self._current_language = "fr"       # Langue par défaut
        self._translations = {}             # Cache des traductions du jeu
        self._tool_translations = {}        # Cache des traductions d'outils
        self._load_translations()           # Chargement initial
    
    def translate(self, key: str, tool: str = None, default: str = None, **kwargs) -> str:
        """Traduit une clé avec paramètres optionnels.
        
        Args:
            key: Clé de traduction (ex: "menu.play" ou "btn.refresh")
            tool: Namespace de l'outil (ex: "clean_models_gui", "galad_config_tool")
            default: Valeur par défaut si la clé n'existe pas
            **kwargs: Paramètres dynamiques pour la traduction
        
        Returns:
            Texte traduit ou clé/default si non trouvé
        """
        # Si un namespace d'outil est spécifié, chercher d'abord dans ses traductions
        if tool:
            tool_catalog = self._load_tool_translations(tool)
            translation = tool_catalog.get(key)
            if translation:
                return translation.format(**kwargs) if kwargs else translation
        
        # Sinon chercher dans les traductions du jeu
        translation = self._translations.get(key, default or key)
        
        # Support des paramètres dynamiques
        if kwargs:
            translation = translation.format(**kwargs)
        
        return translation
    
    def _load_tool_translations(self, tool_name: str) -> dict:
        """Charge les traductions spécifiques à un outil."""
        if tool_name in self._tool_translations:
            return self._tool_translations[tool_name]
        
        try:
            # Essayer de charger le module de l'outil pour la langue actuelle
            lang = self._current_language
            module_name = f"assets.locales.tools.{tool_name}_{lang}"
            tool_module = importlib.import_module(module_name)
            self._tool_translations[tool_name] = tool_module.TRANSLATIONS
        except ImportError:
            # Fallback sur français si la langue n'existe pas
            try:
                module_name = f"assets.locales.tools.{tool_name}_fr"
                tool_module = importlib.import_module(module_name)
                self._tool_translations[tool_name] = tool_module.TRANSLATIONS
            except ImportError:
                # Aucune traduction trouvée
                self._tool_translations[tool_name] = {}
        
        return self._tool_translations[tool_name]
    
    def set_language(self, language_code: str) -> bool:
        """Change la langue et recharge les traductions."""
        if language_code in ["fr", "en"]:
            self._current_language = language_code
            config_manager.set("language", language_code)
            self._load_translations()
            # Invalider le cache des traductions d'outils
            self._tool_translations = {}
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

# Usage dans un outil GUI avec namespace
button_text = t("btn.refresh", tool="clean_models_gui", default="Refresh")
dialog_title = t("dialog.confirm.title", tool="galad_config_tool", default="Confirm")
```

### Traductions pour outils GUI

Les outils GUI (comme `galad-config-tool` ou `MaraudeurAiCleaner`) ont leurs propres traductions séparées du jeu :

```python
# assets/locales/tools/clean_models_gui_fr.py
TRANSLATIONS = {
    "window.title": "Nettoyeur de Modèles Maraudeur",
    "btn.refresh": "Actualiser",
    "btn.choose_folder": "Choisir le dossier…",
    "btn.delete_selected": "Supprimer sélection",
    "status.found_in": "Trouvé {count} fichier(s) modèle dans {path}",
}

# Utilisation dans l'outil
from src.settings.localization import t as game_t

def _t(key: str, default: str = None, **kwargs) -> str:
    return game_t(key, tool='clean_models_gui', default=default, **kwargs)

# Dans l'interface
self.title(self._t("window.title", default="Marauder Models Cleaner"))
```

**Avantages** :
- Séparation claire entre traductions du jeu et des outils
- Les outils suivent automatiquement la langue du jeu
- Fallback automatique sur français puis sur la valeur par défaut
- Pas de pollution des traductions du jeu avec du texte d'outils

## Structure des fichiers de traduction

### Format standard

**Exemple :** `assets/locales/french.py`

```python
# -*- coding: utf-8 -*-
"""
Traductions françaises pour Galad Islands
"""

TRANSLATIONS = {
    # Organisation par catégories avec préfixes
    
    # Menu principal
    "menu.play": "Jouer",
    "menu.options": "Options",
    "menu.quit": "Quitter",
    
    # Interface de jeu
    "game.gold": "Or : {amount}",              # Avec paramètre dynamique
    "game.unit_selected": "Unité sélectionnée : {name}",
    "game.health": "Vie : {current}/{max}",
    
    # Messages système
    "system.loading": "Chargement...",
    "system.error": "Erreur : {message}",
    
    # Raccourcis clavier
    "options.binding.unit_attack": "Attaque principale",
    "options.binding.camera_move_left": "Caméra vers la gauche",
    
    # Tips et conseils
    "tip.0": "Utilisez les capacités spéciales au bon moment !",
    "tip.1": "Les mines d'or vous donnent des ressources supplémentaires.",
    "tip.2": "Explorez la carte pour découvrir des coffres cachés.",
}
```

### Conventions de nommage

| Préfixe | Usage | Exemple |
|---------|-------|---------|
| `menu.` | Menus et navigation | `menu.play`, `menu.options` |
| `game.` | Interface de jeu | `game.gold`, `game.unit_selected` |
| `options.` | Paramètres et configuration | `options.volume`, `options.language` |
| `system.` | Messages système | `system.loading`, `system.error` |
| `tip.` | Conseils et astuces | `tip.0`, `tip.1`, `tip.2` |
| `unit.` | Noms et descriptions d'unités | `unit.zasper`, `unit.druid` |
| `error.` | Messages d'erreur | `error.save_failed`, `error.connection` |

## Utilisation dans le code

### Traduction simple

```python
from src.settings.localization import t

# Dans les menus
button_text = t("menu.play")            # "Jouer" ou "Play"
options_title = t("options.title")      # "Options"

# Dans l'interface de jeu
loading_msg = t("system.loading")       # "Chargement..." ou "Loading..."
```

### Traduction avec paramètres

```python
# Affichage dynamique des ressources
gold_display = t("game.gold", amount=player.gold)
# Résultat : "Or : 150" ou "Gold: 150"

# Informations d'unité
unit_info = t("game.unit_selected", name=unit.name)
# Résultat : "Unité sélectionnée : Zasper"

# Barres de vie
health_text = t("game.health", current=75, max=100)
# Résultat : "Vie : 75/100" ou "Health: 75/100"
```

### Intégration dans l'interface utilisateur

```python
# Dans l'ActionBar
class ActionBar:
    def _draw_gold_display(self, surface):
        gold_text = t("game.gold", amount=self.get_player_gold())
        gold_surface = self.font.render(gold_text, True, UIColors.GOLD)
        surface.blit(gold_surface, self.gold_rect)
    
    def _draw_unit_info(self, surface):
        if self.selected_unit:
            name_text = t("game.unit_selected", name=self.selected_unit.name)
            health_text = t("game.health", 
                          current=self.selected_unit.health,
                          max=self.selected_unit.max_health)
```

### Système de tips aléatoires

```python
from src.settings.localization import get_random_tip, get_all_tips

# Tip aléatoire pour écran de chargement
loading_tip = get_random_tip()

# Toutes les tips pour interface d'aide
all_tips = get_all_tips()
for i, tip in enumerate(all_tips):
    print(f"{i+1}. {tip}")
```

## Ajouter une nouvelle langue

### Étape 1 : Créer le fichier de traduction

Créez un nouveau fichier dans `assets/locales/` :

**Exemple :** `assets/locales/spanish.py`

```python
# -*- coding: utf-8 -*-
"""
Traducciones españolas para Galad Islands
"""

TRANSLATIONS = {
    # Menu principal
    "menu.play": "Jugar",
    "menu.options": "Opciones", 
    "menu.credits": "Créditos",
    "menu.help": "Ayuda",
    "menu.scenario": "Escenario",
    "menu.quit": "Salir",
    
    # Interface de jeu
    "game.gold": "Oro: {amount}",
    "game.unit_selected": "Unidad seleccionada: {name}",
    "game.health": "Vida: {current}/{max}",
    
    # Messages système
    "system.loading": "Cargando...",
    "system.error": "Error: {message}",
    
    # Tips
    "tip.0": "¡Usa las habilidades especiales en el momento adecuado!",
    "tip.1": "Las minas de oro te dan recursos adicionales.",
    
    # Toutes les autres clés doivent être traduites...
}
```

### Étape 2 : Mettre à jour le gestionnaire

Modifiez `src/settings/localization.py` :

```python
def _load_translations(self):
    """Charge les traductions pour la langue actuelle"""
    try:
        # Ajouter la nouvelle langue au mapping
        language_modules = {
            "fr": "assets.locales.french", 
            "en": "assets.locales.english",
            "es": "assets.locales.spanish"  # Nouvelle langue
        }
        
        module_name = language_modules.get(self._current_language, "assets.locales.french")
        translation_module = importlib.import_module(module_name)
        self._translations = translation_module.TRANSLATIONS

def get_available_languages(self):
    """Retourne la liste des langues disponibles"""
    return {
        "fr": "Français",
        "en": "English", 
        "es": "Español"  # Nouvelle langue
    }
```

### Étape 3 : Validation et test

```python
# Script de validation des traductions
def validate_translations():
    """Vérifie que toutes les clés sont traduites."""
    
    from assets.locales import french, english, spanish
    
    fr_keys = set(french.TRANSLATIONS.keys())
    en_keys = set(english.TRANSLATIONS.keys())
    es_keys = set(spanish.TRANSLATIONS.keys())
    
    # Clés manquantes
    missing_en = fr_keys - en_keys
    missing_es = fr_keys - es_keys
    
    if missing_en:
        print(f"Clés manquantes en anglais : {missing_en}")
    
    if missing_es:
        print(f"Clés manquantes en espagnol : {missing_es}")
    
    print(f"Français : {len(fr_keys)} clés")
    print(f"Anglais : {len(en_keys)} clés")
    print(f"Espagnol : {len(es_keys)} clés")
```

## Bonnes pratiques

### Structure et organisation

✅ **À faire :**

- **Préfixes cohérents** pour regrouper les traductions
- **Clés descriptives** en anglais (`unit_attack` plutôt que `ua`)
- **Paramètres nommés** pour les valeurs dynamiques (`{amount}`, `{name}`)
- **Fichiers par langue** avec structure identique
- **Commentaires** pour organiser les sections

❌ **À éviter :**

- Traductions directes dans le code (`"Jouer"` vs `t("menu.play")`)
- Clés trop longues ou peu claires
- Mélange de langues dans un même fichier
- Paramètres non nommés (`{0}`, `{1}` au lieu de `{name}`)

### Gestion des paramètres

```python
# ✅ Bon usage avec paramètres nommés
"game.unit_health": "Vie : {current}/{max}",
"options.volume_label": "Volume {type} : {level}%",

# ❌ À éviter - paramètres positionnels
"game.unit_health": "Vie : {}/{}", 
"options.volume_label": "Volume {} : {}%",
```

### Test et validation

```python
# Script de test pour nouvelle langue
def test_language(lang_code):
    """Test complet d'une langue."""
    
    from src.settings.localization import set_language, t
    
    # Changer vers la nouvelle langue
    set_language(lang_code)
    
    # Tester les traductions essentielles
    essential_keys = [
        "menu.play", "menu.options", "menu.quit",
        "system.loading", "system.error",
        "game.gold", "game.health"
    ]
    
    for key in essential_keys:
        translation = t(key, amount=100, current=75, max=100)
        print(f"{key}: {translation}")
```

## Intégration avec l'UI

Le système de localisation s'intègre parfaitement avec le système UI documenté dans [Interface utilisateur](../02-systeme/api/ui-system.md) :

- **Menu d'options** : Sélection de langue avec persistance automatique
- **ActionBar** : Affichage dynamique des ressources et informations
- **Modales** : Contenu traduit des fenêtres d'aide et crédits
- **Messages système** : Notifications et erreurs localisées

Cette architecture permet d'ajouter facilement de nouvelles langues tout en maintenant la cohérence de l'interface utilisateur.
