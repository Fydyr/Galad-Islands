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
| `LifetimeProcessor` | 10 | Suppression des entités temporaires |

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
| `flying_chest_collision` | CollisionProcessor | FlyingChestManager | entity, chest |

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