---
i18n:
  en: "Vision System and Fog of War"
  fr: "Système de Vision et Brouillard de Guerre"
---

# Système de Vision et Brouillard de Guerre

## Vue d'ensemble

Le **Système de Vision** gère la visibilité des unités et applique un brouillard de guerre immersif inspiré de Civilization. Il contrôle quelles parties de la carte sont visibles pour chaque équipe et rend les zones non explorées avec des sprites de nuages variés.

## Architecture

### VisionSystem (Classe principale)

```python
class VisionSystem:
    def __init__(self):
        self.visible_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Par équipe
        self.explored_tiles: dict[int, Set[Tuple[int, int]]] = {}  # Par équipe
        self.current_team = 1  # Équipe actuelle
        self.cloud_image = None  # Image des nuages chargée dynamiquement
```

### États de visibilité

- **Visible** : Tuiles actuellement dans le champ de vision des unités de l'équipe
- **Exploré** : Tuiles déjà vues au moins une fois (persistent)
- **Non découvert** : Tuiles jamais vues, couvertes de nuages

## Fonctionnalités principales

### 1. Gestion multi-équipes

- Chaque équipe maintient ses propres ensembles de tuiles visibles et explorées
- Changement automatique lors du switch d'équipe dans l'interface
- Séparation complète des données de visibilité

### 2. Calcul de visibilité

```python
def update_visibility(self, current_team: Optional[int] = None):
    """Met à jour les zones visibles pour l'équipe actuelle."""
    # Parcourt toutes les unités de l'équipe avec VisionComponent
    # Calcule les tuiles dans leur portée de vision
    # Met à jour visible_tiles et explored_tiles
```

### 3. Rendu du brouillard

#### Nuages pour zones non découvertes

- Sprites de nuages 2x plus gros que les tuiles
- Centrés sur chaque tuile pour un effet de chevauchement naturel
- Découpes variées de l'image source pour plus de diversité
- Alpha blending à 160 pour une transparence optimale

#### Brouillard léger pour zones explorées

- Couleur noire semi-transparente (alpha 40)
- Appliqué aux tuiles déjà vues mais hors de portée

### 4. Optimisations de performance

- Chargement différé de l'image cloud (après initialisation Pygame)
- Utilisation du SpriteManager pour la gestion centralisée des assets
- Calcul déterministe des découpes pour éviter les calculs aléatoires coûteux

## Composants associés

### VisionComponent

```python
@dataclass
class VisionComponent:
    range: float  # Portée de vision en unités de grille
```

- Attaché à toutes les unités et bâtiments
- Valeurs définies dans `constants/gameplay.py`
- Portées typiques : 4-8 unités de grille selon le type d'unité

### Intégration dans le rendu

Le système s'intègre dans `GameRenderer._render_fog_of_war()` :

```python
def _render_fog_of_war(self, window, camera):
    vision_system.update_visibility(current_team)
    fog_rects = vision_system.get_visibility_overlay(camera)
    # Rendu des rectangles de brouillard
```

## Constantes de configuration

```python
# Dans constants/gameplay.py
BASE_VISION_RANGE = 8.0      # Vision des bases
UNIT_VISION_SCOUT = 6.0      # Vision des éclaireurs
UNIT_VISION_MARAUDEUR = 5.0  # Vision des maraudeurs
# ... autres unités
```

## Interface utilisateur

### Cercle de vision

- Cercle blanc affiché uniquement autour de l'unité sélectionnée
- Diamètre proportionnel à la portée de vision
- Épaisseur configurable (2 pixels par défaut)

### Contrôles

- Changement d'équipe : Met automatiquement à jour la visibilité
- Sélection d'unité : Affiche le cercle de vision correspondant

## Optimisations et performances

### Gestion mémoire

- Images mises en cache par le SpriteManager
- Découpes créées à la demande et non stockées
- Ensembles de tuiles par équipe pour éviter les conflits

### Performance de rendu

- Un sprite par tuile non visible (optimisé pour les GPUs modernes)
- Calcul de visibilité uniquement lors des changements d'équipe
- Clipping automatique des sprites hors écran

## Débogage

### Messages de debug

- "Cloud requested but cloud_image is None" : Image non chargée
- Comptage des cercles de vision rendus par équipe

### Outils de développement

- Vision étendue disponible en mode debug
- Possibilité de révéler toute la carte temporairement

## Évolutions futures

### Améliorations possibles

- Animation des nuages pour plus d'immersion
- Effets de particules pour les transitions de visibilité
- Ligne de vue (line-of-sight) plus sophistiquée
- Brouillard dynamique réagissant aux événements

### Intégration

- Support des bâtiments avec vision étendue
- Capacités spéciales affectant la visibilité
- Effets météorologiques impactant le brouillard</content>
<parameter name="filePath">/home/lieserl/Documents/GitHub/Galad-Islands/docs/dev/modules/vision-system.md
