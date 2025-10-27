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

### Knockback centralisé (recul lors des collisions avec terrain/îles)

L'effet de recul ("knockback") appliqué lorsqu'une entité percute un élément non franchissable (île, base, obstacle fixe) est géré au niveau du `CollisionProcessor`. Cela permet d'assurer un comportement cohérent pour toutes les entités (unités, projectiles, coffres volants, etc.) et d'éviter la duplication de la logique dans plusieurs processeurs ou AIs.

Comportement principal :

- Lorsqu'une collision avec un tile non-passable est détectée, le `CollisionProcessor` appelle le helper `apply_knockback(entity, position, velocity, magnitude=..., stun_duration=...)`.
- Le helper applique :
    - un déplacement de recul sur la position de l'entité (recul dans la direction opposée au vecteur de collision) proportionnel à `magnitude` ;
    - met `velocity.currentSpeed = 0` (interrompt le mouvement instantanément) ;
    - si le composant `VelocityComponent` possède un champ `stun_timer`, il est positionné à `stun_duration` pour empêcher le mouvement pendant cette durée ;
    - crée éventuellement un événement `entities_knocked_back` pour que d'autres processeurs puissent réagir (son, effet visuel, dégâts, etc.).

Paramètres et réglages :

- `magnitude` (float) : distance de recul en unités de jeu (par défaut ≈ 30.0). Ajuster selon la sensation désirée.
- `stun_duration` (float) : durée en secondes pendant laquelle l'entité est incapacitée (par défaut ≈ 0.6). Réduisez si vous voulez un gameplay plus réactif.
- Ces valeurs sont définies dans le helper et peuvent être exposées via la configuration (par exemple dans `galad_config.json` ou un module `src/settings.py`) si nécessaire.

Conséquences pour d'autres systèmes :

- `PhysicsSystem` / `MovementProcessor` doit décrémenter `stun_timer` à chaque frame et empêcher la translation tant que `stun_timer > 0`.
- Les AIs (ex. `KamikazeAiProcessor`) doivent respecter l'état de `stun_timer` et ne pas forcer un mouvement tant que l'entité est étourdie.
- Vérifier `IslandResourceManager` et `FlyingChestProcessor` pour retirer toute logique locale de knockback afin d'éviter les doubles applications.

Exemple (pseudo-code) du helper dans `CollisionProcessor` :

```python
def apply_knockback(self, entity, pos, vel, magnitude=30.0, stun_duration=0.6):
        # calcule vecteur opposé à la direction de la collision
        dx = math.cos(pos.direction) * magnitude
        dy = math.sin(pos.direction) * magnitude
        pos.x -= dx
        pos.y -= dy
        vel.currentSpeed = 0
        if hasattr(vel, 'stun_timer'):
                vel.stun_timer = stun_duration
        # dispatch event si besoin
        self.world.publish('entities_knocked_back', entity=entity, magnitude=magnitude)

```

Tests associés :

- Un test d'intégration `tests/test_knockback.py` vérifie que l'appel à `apply_knockback` :
    - recule bien la position de l'entité ;
    - met `currentSpeed` à 0 ;
    - initialise `stun_timer` > 0 si le champ existe.

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