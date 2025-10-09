# 📚 Documentation Technique - Galad Islands

## 1. Introduction

### Objectif du document

Cette documentation technique présente l'architecture, l'installation, la configuration et l'exploitation du jeu **Galad Islands**. Elle s'adresse aux développeurs, contributeurs et administrateurs système souhaitant comprendre, installer, configurer ou maintenir le projet.

### Public cible

- **Développeurs** : Comprendre l'architecture et contribuer au code
- **Contributeurs** : Installation et configuration de l'environnement de développement
- **Administrateurs** : Déploiement, supervision et maintenance en production

### Prérequis de lecture

- Connaissances de base en Python 3.9+
- Familiarité avec les concepts de développement logiciel
- Compréhension des environnements virtuels Python

---

## 2. Description du système

### Architecture générale

**Galad Islands** est un jeu de stratégie en temps réel développé en Python utilisant le framework Pygame. Le projet suit une architecture **ECS (Entity-Component-System)** avec la bibliothèque `esper` pour une organisation modulaire et performante du code.

### Composants principaux

#### Moteur de jeu (GameEngine)

- Classe centrale orchestrant tous les systèmes
- Gestion du cycle de jeu (mise à jour, rendu, événements)
- Coordination entre les différents gestionnaires

#### Architecture ECS

```
Entités (Entities) ←→ Composants (Components) ←→ Systèmes/Processeurs (Systems)
```

- **Entités** : Identifiants numériques simples représentant les objets du jeu
- **Composants** : Structures de données pures contenant les propriétés des entités
- **Systèmes** : Logique métier agissant sur les entités selon leurs composants

#### Gestionnaires principaux

- **AudioManager** : Gestion des sons et musique
- **EventManager** : Gestion des événements aléatoires (tempêtes, kraken, coffres)
- **VisionSystem** : Calcul des zones visibles sur la carte
- **ConfigManager** : Gestion centralisée de la configuration

#### Interface utilisateur

- **ActionBar** : Barre d'actions pour les unités
- **Shop** : Système d'achat d'unités
- **DebugModal** : Interface de débogage (mode développeur)

### Technologies utilisées

- **Python 3.9+** : Langage principal
- **Pygame** : Framework graphique et gestion des entrées
- **Esper** : Bibliothèque ECS
- **JSON** : Configuration et sauvegardes
- **TOML** : Métadonnées du projet (pyproject.toml)

---

## 3. Installation

### Prérequis système

#### Configuration minimale

- **OS** : Windows 10+, macOS 10.15+, Linux (Ubuntu 18.04+)
- **CPU** : Intel i3 / AMD équivalent
- **RAM** : 2 GB
- **Stockage** : 500 MB disponible
- **GPU** : Carte graphique compatible OpenGL (intégrée acceptée)

#### Logiciels requis

- **Python 3.9 ou supérieur**
- **Pip** (gestionnaire de paquets Python)
- **Git** (pour le clonage du dépôt)

### Installation étape par étape

#### 1. Clonage du dépôt

```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
```

#### 2. Création de l'environnement virtuel

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Installation des dépendances

```bash
# Dépendances principales
pip install -r requirements.txt

# Dépendances de développement (optionnel)
pip install -r requirements-dev.txt
```

#### 4. Vérification de l'installation

```bash
python main.py
```

### Erreurs d'installation courantes

#### Problème : "ModuleNotFoundError"

**Cause** : Dépendances non installées ou environnement virtuel non activé
**Solution** :

```bash
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

#### Problème : "SDL2 not found"

**Cause** : Bibliothèques système manquantes pour Pygame
**Solutions** :

```bash
# Ubuntu/Debian
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

# macOS
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf

# Windows : réinstaller Pygame
pip uninstall pygame
pip install pygame
```

#### Problème : "Python version too old"

**Cause** : Version Python < 3.9
**Solution** : Mettre à jour Python ou utiliser une version compatible

---

## 4. Configuration

### Fichiers de configuration

#### galad_config.json

Fichier principal de configuration utilisateur créé automatiquement au premier lancement :

```json
{
  "screen_width": 1168,
  "screen_height": 629,
  "window_mode": "fullscreen",
  "volume_master": 0.8,
  "volume_music": 0.5,
  "volume_effects": 0.7,
  "vsync": true,
  "show_fps": false,
  "dev_mode": false,
  "language": "fr",
  "camera_sensitivity": 1.0,
  "camera_fast_multiplier": 2.5
}
```

#### pyproject.toml

Métadonnées du projet (version, dépendances, configuration de build) :

```toml
[project]
name = "galad-islands"
version = "0.6.0"
description = "Jeu de stratégie navale"
readme = "readme.md"
requires-python = ">=3.9"
dependencies = [
    "pygame>=2.5.0",
    "esper>=3.0",
    # ...
]
```

### Variables d'environnement

Le projet n'utilise pas de variables d'environnement externes. Toute la configuration passe par `galad_config.json`.

### Configuration du développement

#### Mode développeur

Activé via `galad_config.json` :

```json
{
  "dev_mode": true
}
```

Fonctionnalités débloquées :

- Menu de débogage (F3)
- Donner de l'or (F5)
- Boutons de développement dans l'interface

#### Configuration Git hooks

```bash
python setup_dev.py
```

Installe automatiquement :

- Pré-commit hooks
- Formatage automatique
- Validation des commits

---

## 5. Exploitation

### Lancement du jeu

#### Mode normal

```bash
python main.py
```

#### Mode développement

```bash
# Avec dev_mode activé dans galad_config.json
python main.py
```

### Arrêt du jeu

- **Normal** : Échap → Quitter
- **Forcé** : Ctrl+C dans le terminal
- **Debug** : Bouton de fermeture de fenêtre

### Logs et débogage

#### Logs console

Le jeu affiche les informations dans la console :

- Chargement de la configuration
- Erreurs de chargement des ressources
- Messages de débogage (si activé)

#### Mode debug intégré

- **F3** : Ouvrir le menu de débogage
- **F5** : Donner 500 pièces d'or (mode dev)
- **F1** : Ouvrir l'aide

### Supervision

#### Métriques de performance

- FPS affichés en haut à droite (si activé)
- Utilisation CPU/RAM via le gestionnaire de tâches système

#### États du jeu

- Nombre d'entités ECS
- État des gestionnaires (audio, événements)
- Configuration active

### Dépannage courant

#### Jeu qui ne démarre pas

1. Vérifier l'environnement virtuel : `source venv/bin/activate`
2. Vérifier les dépendances : `pip list | grep pygame`
3. Supprimer la config : `rm galad_config.json`

#### Problèmes graphiques

1. Désactiver VSync dans la config
2. Changer la résolution
3. Vérifier les pilotes graphiques

#### Problèmes audio

1. Vérifier les volumes dans `galad_config.json`
2. Tester avec `volume_master: 0.0` puis remonter

---

## 6. Maintenance

### Mises à jour

#### Mise à jour du code

```bash
git pull origin main
pip install -r requirements.txt
```

#### Mise à jour des dépendances

```bash
# Vérifier les mises à jour disponibles
pip list --outdated

# Mettre à jour une dépendance spécifique
pip install --upgrade pygame

# Mettre à jour requirements.txt
pip freeze > requirements.txt
```

### Sauvegardes

#### Configuration utilisateur

```bash
cp galad_config.json galad_config_backup.json
```

#### Code source

```bash
# Créer une branche de sauvegarde
git branch backup-$(date +%Y%m%d)

# Ou créer un tag
git tag v0.6.0-backup
```

### Sécurité

#### Bonnes pratiques

- Ne pas commiter `galad_config.json` (déjà dans .gitignore)
- Utiliser des environnements virtuels isolés
- Vérifier les dépendances externes pour les vulnérabilités

#### Nettoyage

```bash
# Supprimer les fichiers temporaires Python
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Nettoyer les sauvegardes de config
find . -name "galad_config_backup.json" -mtime +30 -delete
```

### Monitoring

#### Métriques à surveiller

- Taille du fichier `galad_config.json`
- Présence des fichiers de ressources
- Logs d'erreur dans la console

#### Alertes

- Disparition du fichier de configuration
- Erreurs répétées au lancement
- Performances dégradées (FPS < 25)

---

## 7. Annexes

### Glossaire

- **ECS** : Entity-Component-System, architecture de code
- **Entité** : Objet du jeu représenté par un ID numérique
- **Composant** : Structure de données attachée à une entité
- **Système/Processeur** : Logique agissant sur les entités
- **Tile** : Case élémentaire de la carte de jeu
- **Viewport** : Zone visible de la carte à l'écran

### Scripts et outils

#### Scripts de développement

- `setup_dev.py` : Configuration complète de l'environnement
- `tools/galad_config.py` : Outil de gestion de la configuration
- `scripts/clean-changelog.py` : Nettoyage du changelog

#### Commandes Git utiles

```bash
# Installation des hooks
python setup_dev.py

# Formatage du code
black src/
isort src/

# Tests
python -m pytest tests/
```

### Références externes

- [Documentation Pygame](https://pygame.readthedocs.io/)
- [Guide Esper ECS](https://github.com/benmoran56/esper)
- [PEP 8 - Style Guide Python](https://pep8.org/)
- [Conventional Commits](https://conventionalcommits.org/)

---

## 📖 Explications du code

### Architecture ECS détaillée

#### Composants principaux

##### PositionComponent

```python
@component
class PositionComponent:
    def __init__(self, x=0.0, y=0.0, direction=0.0):
        self.x: float = x
        self.y: float = y
        self.direction: float = direction  # En radians
```

Stocke la position 2D et l'orientation d'une entité.

##### VelocityComponent

```python
@component
class VelocityComponent:
    def __init__(self, speed=0.0, angular_speed=0.0):
        self.speed: float = speed
        self.angular_speed: float = angular_speed
```

Gère le mouvement linéaire et angulaire.

##### HealthComponent

```python
@component
class HealthComponent:
    def __init__(self, max_health=100, current_health=None):
        self.max_health: int = max_health
        self.current_health: int = current_health if current_health is not None else max_health
```

Représente les points de vie d'une unité.

#### Systèmes principaux

##### MovementProcessor

```python
class MovementProcessor(esper.Processor):
    def process(self):
        for entity, (pos, vel) in self.world.get_components(PositionComponent, VelocityComponent):
            # Mise à jour de la position selon la vélocité
            pos.x += vel.speed * math.cos(pos.direction) * self.delta_time
            pos.y += vel.speed * math.sin(pos.direction) * self.delta_time
            pos.direction += vel.angular_speed * self.delta_time
```

Gère le déplacement de toutes les entités mobiles.

##### RenderProcessor

```python
class RenderProcessor(esper.Processor):
    def process(self):
        # Nettoyage de l'écran
        self.screen.fill((0, 0, 50))  # Bleu marine

        # Rendu de toutes les entités visibles
        for entity, (pos, render) in self.world.get_components(PositionComponent, RenderComponent):
            if self.is_visible(pos):
                self.screen.blit(render.sprite, (pos.x, pos.y))
```

Gère l'affichage graphique de toutes les entités.

### Gestionnaire de configuration

```python
class ConfigManager:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.path = config_path
        self.config = deepcopy(DEFAULT_CONFIG)
        self.load_config()

    def load_config(self) -> None:
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Fusion avec la config par défaut
                    for key, value in saved_config.items():
                        if key in self.config:
                            self.config[key] = value
            else:
                self.save_config()
        except Exception as e:
            print(f"Erreur chargement config: {e}")
```

Système de configuration persistant avec valeurs par défaut.

### Système d'événements

Le jeu utilise un système d'événements procéduraux :

- **Tempêtes** : Dégâts de zone toutes les 3 secondes
- **Kraken** : Boss apparaissant aléatoirement avec tentacules
- **Coffres volants** : Récompenses apparaissant périodiquement
- **Mines** : Pièges statiques placés au début

Chaque événement est géré par un `EventManager` spécialisé.

---

*Documentation mise à jour le 9 octobre 2025*</content>
<parameter name="filePath">/home/lieserl/Documents/GitHub/Galad-Islands/docs/dev/documentation-technique.md
