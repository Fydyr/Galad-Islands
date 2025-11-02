---
i18n:
  en: "Processors"
  fr: "Processeurs ECS"
---

# Processeurs ECS

Les processeurs contiennent la logique métier du jeu et agissent sur les entités ayant certains composants.

## Liste des processeurs

### Processeurs de base

| Processeur | Priorité | Responsabilité |
|------------|----------|----------------|
| `CollisionProcessor` | 2 | Détection des collisions et gestion des impacts |
| `MovementProcessor` | 3 | Déplacement des entités avec vélocité |
| `PlayerControlProcessor` | 4 | Contrôles joueur et activation des capacités |
| `CapacitiesSpecialesProcessor` | 5 | Mise à jour des cooldowns des capacités |
| `StormProcessor` | X | Gestion des événements tempêtes  |
| `FlyingChestProcessor` | X | Apparition et collecte des coffres volants |
| `LifetimeProcessor` | 10 | Suppression des entités temporaires |
| `PassiveIncomeProcessor` | 10 | Revenu passif anti-blocage (ajoute de l'or si l'équipe n'a plus d'unités) |
| `TowerProcessor` | 15 | Logique des tours défensives (attaque/soin) |

### Processeur de rendu

| Processeur | Description |
|------------|-------------|
| `RenderingProcessor` | Affichage des sprites avec gestion caméra/zoom |

## Détail des processeurs

### CollisionProcessor

**Fichier :** `src/processeurs/collisionProcessor.py`

**Responsabilité :** Détecte et gère les collisions entre entités.

```python
class CollisionProcessor(esper.Processor):
    def __init__(self, graph=None):
        self.graph = graph  # Grille de la carte
    
    def process(self):
        # Détection des collisions entre toutes les entités
        for ent1, (pos1, collision1) in esper.get_components(PositionComponent, CanCollideComponent):
            for ent2, (pos2, collision2) in esper.get_components(PositionComponent, CanCollideComponent):
                if self._entities_collide(ent1, ent2):
                    self._handle_entity_hit(ent1, ent2)
```

**Composants requis :**
- `PositionComponent`
- `CanCollideComponent`

**Actions :**
- Calcule les distances entre entités
- Dispatche l'événement `entities_hit` pour les collisions
- Gère les collisions avec les coffres volants
- Nettoie les mines explosées de la grille

### MovementProcessor

**Fichier :** `src/processeurs/movementProcessor.py`

**Responsabilité :** Déplace les entités selon leur vélocité.

```python
class MovementProcessor(esper.Processor):
    def process(self, dt=0.016):
        for ent, (pos, vel) in esper.get_components(PositionComponent, VelocityComponent):
            # Appliquer le mouvement
            pos.x += vel.currentSpeed * dt * math.cos(pos.direction)
            pos.y += vel.currentSpeed * dt * math.sin(pos.direction)
```

**Composants requis :**
- `PositionComponent`
- `VelocityComponent`

### PlayerControlProcessor

**Fichier :** `src/processeurs/playerControlProcessor.py`

**Responsabilité :** Gère les contrôles du joueur et les capacités spéciales.

**Contrôles gérés :**
- **Clic droit** : Sélection d'unité
- **Espace** : Activation de la capacité spéciale
- **B** : Ouverture de la boutique
- **F3** : Toggle debug
- **T** : Changement de camp (debug)

**Capacités spéciales traitées :**
- `SpeArchitect` : Boost de rechargement des alliés
- `SpeScout` : Invincibilité temporaire  
- `SpeMaraudeur` : Bouclier de mana
- `SpeLeviathan` : Seconde salve de projectiles
- `SpeBreaker` : Frappe puissante

### CapacitiesSpecialesProcessor

**Fichier :** `src/processeurs/CapacitiesSpecialesProcessor.py`

**Responsabilité :** Met à jour les cooldowns et effets des capacités spéciales.

```python
def process(self, dt=0.016):
    # Mise à jour des timers de toutes les capacités
    for ent, spe_comp in esper.get_component(SpeArchitect):
        spe_comp.update(dt)
    
    for ent, spe_comp in esper.get_component(SpeScout):
        spe_comp.update(dt)
    # ... autres capacités
```

### StormProcessor

**Fichier :** `src/processeurs/stormProcessor.py`

**Responsabilité :** Gère les événements tempêtes qui infligent des dégâts aux unités dans leur rayon.

**Configuration :**
- Taille visuelle : 3.0 cases (correspond au sprite 100x100px)
- Rayon de dégâts : 1.5 cases (moitié de la taille visuelle)
- Dégâts : 30 PV toutes les 3 secondes
- Déplacement : 1 case/seconde, changement de direction toutes les 5 secondes
- Chance d'apparition : 5% toutes les 5 secondes
- Durée de vie : 20 secondes par tempête

```python
class StormProcessor(esper.Processor):
    def process(self, dt: float):
        # Mise à jour des tempêtes existantes
        self.updateExistingStorms(dt)
        
        # Vérification de nouvelles apparitions de tempêtes
        if random.random() < self.spawn_chance:
            self.trySpawnStorm()
```

### FlyingChestProcessor

**Fichier :** `src/processeurs/flyingChestProcessor.py`

**Responsabilité :** Gère l'apparition, le comportement et la collecte des coffres volants.

**Configuration :**
- Intervalle d'apparition : 30 secondes
- Récompense en or : 100-200 or par coffre
- Nombre maximum de coffres : Limité par les constantes du jeu
- Durée de vie : Défini par les constantes du jeu

```python
class FlyingChestProcessor(esper.Processor):
    def process(self, dt: float):
        # Mise à jour du timer d'apparition
        self._spawn_timer += dt
        if self._spawn_timer >= FLYING_CHEST_SPAWN_INTERVAL:
            self._spawn_timer = 0.0
            self._try_spawn_chest()
        
        # Mise à jour des coffres existants
        self._update_existing_chests(dt)
```

### LifetimeProcessor

**Fichier :** `src/processeurs/lifetimeProcessor.py`

**Responsabilité :** Supprime les entités temporaires (projectiles, effets).

```python
def process(self, dt=0.016):
    for ent, lifetime in esper.get_component(LifetimeComponent):
        lifetime.duration -= dt
        if lifetime.duration <= 0:
            esper.delete_entity(ent)
```

### PassiveIncomeProcessor

**Fichier :** `src/processeurs/economy/passiveIncomeProcessor.py`

**Responsabilité :** Évite les situations de point mort économiques. Accorde un faible revenu passif à une équipe uniquement lorsqu'elle n'a plus aucune unité sur le terrain, afin de lui permettre de reconstituer un minimum d'or et de relancer la partie.

**Comportement :**

- Ne s'active que si le nombre d'unités d'une équipe est égal à 0 (les bases, tours et projectiles sont exclus du comptage).
- Ajoute par défaut `+1` or toutes les `2.0s` à l'équipe concernée.

**Configuration :**

- `gold_per_tick` (int, défaut: 1) — montant d'or ajouté par intervalle.
- `interval` (float, défaut: 2.0) — intervalle en secondes entre deux ajouts.

**Intégration ECS :**
Ajouté dans `GameEngine._initialize_ecs()` avec priorité `10` (faible impact, après le cœur du gameplay).

```python
from src.processeurs.economy.passiveIncomeProcessor import PassiveIncomeProcessor

# ...
self.passive_income_processor = PassiveIncomeProcessor(gold_per_tick=1, interval=2.0)
es.add_processor(self.passive_income_processor, priority=10)
```

### TowerProcessor

**Fichier :** `src/processeurs/towerProcessor.py`

**Responsabilité :** Gère la logique automatique des tours (détection de cibles, attaque, soin).

> **📖 Documentation complète** : Voir [Système de Tours](../tower-system-implementation.md) pour tous les détails.

**Composants utilisés :**
- `TowerComponent` : Données de base (type, portée, cooldown)
- `DefenseTowerComponent` : Propriétés d'attaque
- `HealTowerComponent` : Propriétés de soin
- `PositionComponent` : Position de la tour
- `TeamComponent` : Équipe de la tour

**Fonctionnalités :**

1. **Gestion du cooldown** : Décrémente le timer entre chaque action
2. **Détection de cibles** :
   - Tours de défense : Cherche ennemis à portée
   - Tours de soin : Cherche alliés blessés à portée
3. **Actions automatiques** :
   - Tours de défense : Crée un projectile vers la cible
   - Tours de soin : Applique des soins sur la cible

```python
def process(self, dt: float):
    for entity, (tower, pos, team) in esper.get_components(
        TowerComponent, PositionComponent, TeamComponent
    ):
        # Mise à jour cooldown
        if tower.current_cooldown > 0:
            tower.current_cooldown -= dt
            continue
        
        # Recherche de cible
        target = self._find_target(entity, tower, pos, team)
        
        # Action selon le type de tour
        if target:
            if tower.tower_type == "defense":
                self._attack_target(entity, target, pos)
            elif tower.tower_type == "heal":
                self._heal_target(entity, target)
            
            tower.current_cooldown = tower.cooldown
```

**Création de tours :** Via `buildingFactory.create_defense_tower()` ou `create_heal_tower()`.

### RenderingProcessor

**Fichier :** `src/processeurs/renderingProcessor.py`

**Responsabilité :** Affiche tous les sprites des entités à l'écran.

**Fonctionnalités :**
- Conversion coordonnées monde → écran via la caméra
- Mise à l'échelle selon le zoom
- Rotation des sprites selon la direction
- Barres de vie pour les unités endommagées
- Gestion des effets visuels (invincibilité, etc.)

```python
def process(self):
    for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
        # Calcul position écran
        screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
        
        # Affichage du sprite avec rotation
        rotated_image = pygame.transform.rotate(image, -pos.direction * 180 / math.pi)
        self.screen.blit(rotated_image, (screen_x, screen_y))
```

## Ordre d'exécution

Les processeurs s'exécutent selon leur priorité (plus petit = priorité plus haute) :

1. **CollisionProcessor** (priorité 2) - Détecte les collisions
2. **MovementProcessor** (priorité 3) - Applique les mouvements  
3. **PlayerControlProcessor** (priorité 4) - Traite les inputs
4. **CapacitiesSpecialesProcessor** (priorité 5) - Met à jour les capacités
5. **LifetimeProcessor** (priorité 10) - Nettoie les entités expirées
6. **PassiveIncomeProcessor** (priorité 10) - Revenu passif si aucune unité

Le `RenderingProcessor` est appelé séparément dans la boucle de rendu.

## Événements

Les processeurs communiquent via le système d'événements d'esper :

| Événement | Émetteur | Récepteur | Données |
|-----------|----------|-----------|---------|
| `entities_hit` | CollisionProcessor | functions.handleHealth | entity1, entity2 |
| `attack_event` | PlayerControlProcessor | functions.createProjectile | attacker, target |
| `special_vine_event` | PlayerControlProcessor | functions.createProjectile | caster |
| `flying_chest_collision` | CollisionProcessor | FlyingChestProcessor | entity, chest |

## Ajout d'un nouveau processeur

1. **Créer la classe** héritant de `esper.Processor`
2. **Implémenter** `process(self, dt=0.016)`
3. **Ajouter** dans `GameEngine._initialize_ecs()`
4. **Définir** la priorité appropriée

```python
# Exemple de nouveau processeur
class ExampleProcessor(esper.Processor):
    def process(self, dt=0.016):
        for ent, (comp1, comp2) in esper.get_components(Component1, Component2):
            # Logique du processeur...
            pass

# Dans GameEngine._initialize_ecs()
self.example_processor = ExampleProcessor()
es.add_processor(self.example_processor, priority=6)
```