---
i18n:
  en: "Code Architecture"
  fr: "Architecture du code"
---

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

#### RadiusComponent
```python
@component
class RadiusComponent:
    def __init__(self, radius=0.0, angle=0.0, omnidirectional=False, can_shoot_from_side=False, lateral_shooting=False, bullets_front=0, bullets_sides=0, cooldown=0.0, bullet_cooldown=0.0, hit_cooldown_duration=1.0):
        # Paramètres de tir
        self.radius: float = radius
        self.angle: float = angle
        self.omnidirectional: bool = omnidirectional
        self.can_shoot_from_side: bool = can_shoot_from_side
        self.lateral_shooting: bool = lateral_shooting
        self.bullets_front: int = bullets_front
        self.bullets_side: int = bullets_sides
        self.cooldown: float = cooldown
        self.bullet_cooldown: float = bullet_cooldown
        
        # Gestion des collisions répétées (fusionné depuis RecentHitsComponent)
        self.hit_history: dict = {}  # {entity_id: timestamp}
        self.hit_cooldown_duration: float = hit_cooldown_duration
    
    def can_hit(self, entity_id: int) -> bool:
        """Vérifie si cette entité peut infliger des dégâts à l'entité cible."""
        current_time = time.time()
        last_hit_time = self.hit_history.get(entity_id, 0)
        return (current_time - last_hit_time) >= self.hit_cooldown_duration
    
    def record_hit(self, entity_id: int):
        """Enregistre qu'un dégât a été infligé à l'entité cible."""
        self.hit_history[entity_id] = time.time()
    
    def cleanup_old_entries(self):
        """Nettoie les entrées anciennes pour éviter l'accumulation de mémoire."""
        current_time = time.time()
        expired_entries = [
            entity_id for entity_id, timestamp in self.hit_history.items()
            if (current_time - timestamp) > self.hit_cooldown_duration * 2
        ]
        for entity_id in expired_entries:
            del self.hit_history[entity_id]
```

> **🔄 Fusion de composants** : `RadiusComponent` intègre désormais la fonctionnalité de cooldown des collisions précédemment gérée par `RecentHitsComponent` (supprimé).

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

### Composants de bâtiments (buildings/)

Les bâtiments (tours défensives, structures) utilisent des composants dédiés.

> **📖 Documentation complète** : Voir [Système de Tours](tower-system-implementation.md) pour l'implémentation détaillée.

#### TowerComponent
Composant de base pour toutes les tours :
```python
@dataclass
class TowerComponent:
    tower_type: str              # "defense" ou "heal"
    range: float                 # Portée d'action en pixels
    cooldown: float              # Temps entre deux actions (secondes)
    current_cooldown: float = 0.0
    target_entity: Optional[int] = None
```

**Fichier** : `src/components/core/towerComponent.py`

#### DefenseTowerComponent
Composant pour les tours qui attaquent :
```python
@dataclass
class DefenseTowerComponent:
    damage: float        # Dégâts infligés par attaque
    attack_speed: float  # Multiplicateur de vitesse
```

#### HealTowerComponent
Composant pour les tours qui soignent :
```python
@dataclass
class HealTowerComponent:
    heal_amount: float   # Points de vie restaurés
    heal_speed: float    # Multiplicateur de vitesse
```

**Utilisation** :
- Les tours sont créées via `buildingFactory.create_defense_tower()` ou `create_heal_tower()`
- Le `TowerProcessor` gère la détection de cibles et les actions automatiques
- Les tours nécessitent un Architecte pour être construites

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

### Système de Récompenses de Combat

Le système de récompenses génère automatiquement des coffres volants lorsqu'une unité ennemie est éliminée.

#### Mécanisme de Fonctionnement

1. **Détection de Mort** : Dans `processHealth()` (`src/functions/handleHealth.py`), lorsqu'une entité atteint 0 PV :
   - Vérification si c'est une unité (composant `ClasseComponent`)
   - Calcul de la récompense : `coût_unité // 2`
   - Création d'un coffre volant à la position de l'unité morte

2. **Propriétaire des Projectiles** : Les projectiles (`ProjectileComponent`) contiennent désormais un `owner_entity` pour identifier l'attaquant :
   - Défini lors de la création du projectile
   - Permet de distinguer tirs de tours vs unités

3. **Coffres de Récompense** : Créés via `create_reward_chest()` avec :
   - Durée de vie réduite (10s vs 30s pour les coffres normaux)
   - Montant basé sur la valeur de l'unité tuée
   - Collectables par les navires alliés

#### Intégration Technique

- **ProjectileComponent** : Ajout du champ `owner_entity` (optionnel)
- **processHealth()** : Paramètre `attacker_entity` pour identifier le tueur
- **CollisionProcessor** : Passage de l'entité attaquante lors des dégâts
- **FlyingChestComponent** : Réutilisation du système existant de coffres volants

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