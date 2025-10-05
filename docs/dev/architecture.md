# Architecture du code

## Vue d'ensemble de l'architecture ECS

Galad Islands utilise une **architecture ECS (Entity-Component-System)** avec la bibliothèque `esper` pour organiser le code de façon modulaire et performante.

### Principe ECS

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ENTITIES  │    │ COMPONENTS  │    │  SYSTEMS    │
│             │    │             │    │             │
│ ID simples  │◄──►│ Données     │◄──►│ Logique     │
│ (int)       │    │ (Propriétés)│    │ (Comportem.)│
└─────────────┘    └─────────────┘    └─────────────┘
```

- **Entités** : Identifiants numériques simples (int)
- **Composants** : Structures de données pures (dataclasses)
- **Systèmes/Processeurs** : Logique qui agit sur les entités ayant certains composants

## Organisation du code

```
src/
├── components/          # Tous les composants ECS
│   ├── core/           # Composants de base
│   ├── special/        # Capacités spéciales des unités
│   ├── events/         # Composants d'événements
│   └── globals/        # Composants globaux (caméra, carte)
├── processeurs/        # Processeurs ECS (logique)
├── systems/            # Nouveaux systèmes ECS modulaires
├── managers/           # Gestionnaires de haut niveau
├── factory/            # Création d'entités
└── game.py             # Moteur principal
```

## Composants (Components)

Les composants stockent uniquement des **données**, pas de logique.

### Composants de base (core/)

#### PositionComponent
```python
@component
class PositionComponent:
    def __init__(self, x=0.0, y=0.0, direction=0.0):
        self.x: float = x
        self.y: float = y  
        self.direction: float = direction
```

#### HealthComponent
```python
@component
class HealthComponent:
    def __init__(self, currentHealth: int, maxHealth: int):
        self.currentHealth: int = currentHealth
        self.maxHealth: int = maxHealth
```

#### TeamComponent
```python
from src.components.core.team_enum import Team

@component
class TeamComponent:
    def __init__(self, team: Team = Team.ALLY):
        self.team: Team = team
```

#### AttackComponent
```python
@component
class AttackComponent:
    def __init__(self, hitPoints: int):
        self.hitPoints: int = hitPoints
```

### Composants spéciaux (special/)

Les unités avec des capacités ont des composants dédiés :

#### SpeArchitect
```python
@component
class SpeArchitect:
    def __init__(self, is_active=False, radius=0.0, duration=0.0):
        self.is_active: bool = is_active
        self.available: bool = True
        self.radius: float = radius
        self.duration: float = duration
        self.affected_units: List[int] = []
```

### Composants d'événements (events/)

#### FlyingChestComponent
```python
@component
class FlyingChestComponent:
    def __init__(self, gold_value: int = 100):
        self.gold_value: int = gold_value
        self.is_opened: bool = False
```

## Processeurs (Processors)

Les processeurs contiennent la **logique métier** et agissent sur les entités.

### RenderingProcessor
```python
class RenderProcessor(esper.Processor):
    def __init__(self, screen, camera=None):
        super().__init__()
        self.screen = screen
        self.camera = camera

    def process(self):
        # Rendu de toutes les entités avec Position + Sprite
        for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
            # Logique de rendu...
```

### MovementProcessor
```python
class MovementProcessor(esper.Processor):
    def process(self, dt=0.016):
        # Déplace toutes les entités avec Position + Velocity
        for ent, (pos, vel) in esper.get_components(PositionComponent, VelocityComponent):
            pos.x += vel.currentSpeed * dt
            pos.y += vel.currentSpeed * dt
```

### CollisionProcessor
```python
class CollisionProcessor(esper.Processor):
    def process(self):
        # Détecte les collisions entre entités
        for ent1, (pos1, collision1) in esper.get_components(PositionComponent, CanCollideComponent):
            for ent2, (pos2, collision2) in esper.get_components(PositionComponent, CanCollideComponent):
                if self._check_collision(pos1, pos2):
                    self._handle_collision(ent1, ent2)
```

### PlayerControlProcessor
```python
class PlayerControlProcessor(esper.Processor):
    def process(self):
        # Gère les contrôles du joueur et les capacités spéciales
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            # Activer capacité de l'unité sélectionnée...
```

## Systèmes (Systems)

Les nouveaux systèmes modulaires pour séparer la logique :

### SpriteSystem
```python
class SpriteSystem:
    """Gestion des sprites avec cache pour optimiser les performances."""
    
    def __init__(self):
        self._sprite_cache = {}
    
    def get_sprite(self, sprite_id: SpriteID) -> pygame.Surface:
        # Cache des sprites pour éviter les rechargements
```

### CombatSystem
```python
class CombatSystem:
    """Système de combat séparé des processeurs."""
    
    def deal_damage(self, attacker: int, target: int, damage: int) -> bool:
        # Logique de dégâts pure
```

## Gestionnaires (Managers)

Les gestionnaires orchestrent les systèmes de haut niveau :

### BaseComponent (Gestionnaire intégré)
```python
@component
class BaseComponent:
    """Composant de base avec gestionnaire intégré pour les QG."""
    
    @classmethod
    def get_ally_base(cls):
        """Retourne l'entité de base alliée."""
        return cls._ally_base_entity
    
    @classmethod
    def get_enemy_base(cls):
        """Retourne l'entité de base ennemie.""" 
        return cls._enemy_base_entity
    
    @classmethod
    def initialize_bases(cls):
        """Initialise les entités de bases alliée et ennemie."""
        # Logique d'initialisation...
```

Pour en savoir plus, voir la documentation détaillée. [BaseComponent](./modules/components.md#basecomponent---gestionnaire-intégré-des-bases)

### FlyingChestManager
```python
class FlyingChestManager:
    """Gère l'apparition des coffres volants."""
    
    def update(self, dt: float):
        # Logique d'apparition des coffres
```

## Factory (Création d'entités)

### UnitFactory
```python
def UnitFactory(unit: UnitKey, enemy: bool, pos: PositionComponent):
    """Crée une entité complète avec tous ses composants."""
    entity = esper.create_entity()
    
    # Composants de base
    esper.add_component(entity, pos)
    esper.add_component(entity, TeamComponent(Team.ENEMY if enemy else Team.ALLY))
    
    # Composants spécifiques selon le type d'unité
    if unit == UnitKey.ARCHITECT:
        esper.add_component(entity, SpeArchitect(radius=ARCHITECT_RADIUS))
        esper.add_component(entity, HealthComponent(100, 100))
        esper.add_component(entity, AttackComponent(25))
    
    return entity
```

## GameEngine (Moteur principal)

```python
class GameEngine:
    """Moteur principal qui orchestre tous les systèmes."""
    
    def _initialize_ecs(self):
        """Initialise tous les processeurs ECS."""
        self.movement_processor = MovementProcessor()
        self.collision_processor = CollisionProcessor(graph=self.grid)
        self.player_controls = PlayerControlProcessor()
        
        # Ajouter les processeurs avec priorités
        es.add_processor(self.collision_processor, priority=2)
        es.add_processor(self.movement_processor, priority=3)
        es.add_processor(self.player_controls, priority=4)
    
    def run(self):
        """Boucle principale du jeu."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # Traiter tous les processeurs ECS
            es.process(dt)
```

## Flux de données

```
1. Input (clavier/souris) → PlayerControlProcessor
2. PlayerControlProcessor → Modification des composants
3. MovementProcessor → Mise à jour des positions
4. CollisionProcessor → Détection et gestion des collisions
5. RenderingProcessor → Affichage à l'écran
```

## Bonnes pratiques

### ✅ À faire
- **Composants** : Seulement des données, pas de logique
- **Processeurs** : Une responsabilité claire par processeur
- **Type hints** : Toujours typer les propriétés des composants
- **Enums** : Utiliser `Team` et `UnitClass` au lieu d'entiers
- **Vérifications** : Toujours `esper.has_component()` avant `esper.component_for_entity()`

### ❌ À éviter
- Logique métier dans les composants
- Références directes entre entités
- Modifications concurrentes de la même entité
- Processeurs qui dépendent de l'ordre d'exécution

## Exemples d'utilisation

### Créer une unité
```python
# Créer l'entité
entity = esper.create_entity()

# Ajouter les composants
esper.add_component(entity, PositionComponent(100, 200))
esper.add_component(entity, TeamComponent(Team.ALLY))
esper.add_component(entity, HealthComponent(100, 100))
```

### Chercher des entités
```python
# Toutes les entités avec position et santé
for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
    print(f"Entité {ent} à ({pos.x}, {pos.y}) avec {health.currentHealth} PV")
```

### Modifier un composant
```python
if esper.has_component(entity, HealthComponent):
    health = esper.component_for_entity(entity, HealthComponent)
    health.currentHealth -= 10
```

Cette architecture ECS permet une grande flexibilité et des performances optimales pour gérer des centaines d'entités simultanément dans le jeu.