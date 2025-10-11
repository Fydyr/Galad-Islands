---
i18n:
  en: "Special Ability System"
  fr: "Système de capacités spéciales"
---

# Système de capacités spéciales

Le système de capacités spéciales permet aux unités d'avoir des pouvoirs uniques activables avec des cooldowns. Chaque type d'unité possède sa propre capacité spéciale implémentée via des composants `Spe*`.

## Vue d'ensemble

### Architecture des capacités

```text
src/components/special/
├── speScoutComponent.py      # Invincibilité temporaire
├── speMaraudeurComponent.py  # Bouclier de réduction de dégâts
├── speLeviathanComponent.py  # Double attaque
├── speDruidComponent.py      # Lianes immobilisantes
├── speArchitectComponent.py  # Boost de rechargement allié
├── isVinedComponent.py       # Effet d'immobilisation
└── VineComponent.py          # Composant visuel des lianes
```

### Interface commune

Toutes les capacités spéciales partagent une API standard :

```python
class SpeCapacity:
    def can_activate(self) -> bool:
        """Vérifie si la capacité peut être activée."""
        
    def activate(self) -> bool:
        """Active la capacité si possible."""
        
    def update(self, dt: float) -> None:
        """Met à jour les timers de la capacité."""
```

## Capacités par unité

### SpeScout - Invincibilité (Zasper)

**Fichier :** `src/components/special/speScoutComponent.py`

**Effet :** Invincibilité temporaire pour esquiver attaques et mines.

```python
@component
class SpeScout:
    def __init__(self):
        self.is_active: bool = False                    # État d'activation
        self.duration: float = ZASPER_INVINCIBILITY_DURATION  # 3 secondes
        self.timer: float = 0.0                         # Temps restant
        self.cooldown: float = SPECIAL_ABILITY_COOLDOWN # Cooldown standard
        self.cooldown_timer: float = 0.0                # Timer de cooldown
```

**Méthodes spécifiques :**
- `is_invincible() -> bool` : Retourne l'état d'invincibilité

**Intégrations :**
- `CollisionProcessor` vérifie `is_invincible()` avant d'appliquer les dégâts
- `processHealth` ignore les dégâts si l'unité est invincible

### SpeMaraudeur - Bouclier de mana (Barhamus/Maraudeur)

**Fichier :** `src/components/special/speMaraudeurComponent.py`

**Effet :** Réduit les dégâts reçus pendant une durée déterminée.

```python
@component
class SpeMaraudeur:
    def __init__(self):
        self.is_active: bool = False
        self.reduction_min: float = MARAUDEUR_SHIELD_REDUCTION_MIN
        self.reduction_max: float = MARAUDEUR_SHIELD_REDUCTION_MAX  
        self.reduction_value: float = 0.0               # Pourcentage de réduction
        self.duration: float = MARAUDEUR_SHIELD_DURATION
        self.timer: float = 0.0
        self.cooldown: float = SPECIAL_ABILITY_COOLDOWN
        self.cooldown_timer: float = 0.0
```

**Méthodes spécifiques :**
- `apply_damage_reduction(damage: float) -> float` : Applique la réduction
- `is_shielded() -> bool` : Vérifie l'état du bouclier

**Paramètres configurables :**
- Réduction personnalisable entre `reduction_min` et `reduction_max`
- Durée optionnelle lors de l'activation

### SpeArchitect - Boost de rechargement (Architect)

**Fichier :** `src/components/special/speArchitectComponent.py`

**Effet :** Accélère le rechargement des unités alliées dans un rayon.

```python
@component
class SpeArchitect:
    def __init__(self):
        self.is_active: bool = False
        self.available: bool = True                     # Disponibilité
        self.radius: float = 0.0                        # Rayon d'effet
        self.reload_factor: float = 0.0                 # Facteur de division
        self.affected_units: List[int] = []             # Unités affectées
        self.duration: float = 0.0                      # Durée (0 = permanent)
        self.timer: float = 0.0
```

**Activation avec cibles :**
```python
def activate(self, affected_units: List[int], duration: float = 0.0):
    """Active le boost sur les unités spécifiées."""
```

**Fonctionnement :**
- Trouve les unités alliées dans le rayon
- Applique un boost de rechargement (divise les cooldowns)
- Peut être permanent (`duration=0`) ou temporaire

### SpeDruid - Lianes immobilisantes (Druid)

**Fichier :** `src/components/special/speDruidComponent.py`

**Effet :** Lance un projectile qui immobilise la cible avec des lianes.

**Composants associés :**
- `VineComponent` : Visuel des lianes
- `isVinedComponent` : Effet d'immobilisation sur la cible

**Mécanisme :**
1. Activation lance un projectile spécial
2. À l'impact, ajoute `isVinedComponent` à la cible
3. La cible est immobilisée pendant la durée
4. Effet visuel avec `VineComponent`

### SpeLeviathan - Double attaque (Draupnir/Leviathan)

**Fichier :** `src/components/special/speLeviathanComponent.py`

**Effet :** Déclenche une seconde attaque immédiatement après la première.

**Mécanisme :**
- Flag d'activation (`is_active = True`)
- Lors de l'attaque, vérifie le flag
- Si actif, déclenche une seconde salve instantanément
- Consomme le flag (`is_active = False`)

## Constantes de configuration

### Fichier : `src/constants/gameplay.py`

```python
# Cooldowns universels
SPECIAL_ABILITY_COOLDOWN = 15.0         # Cooldown standard (15 secondes)

# SpeScout (Zasper)
ZASPER_INVINCIBILITY_DURATION = 3.0     # Durée d'invincibilité

# SpeMaraudeur (Barhamus/Maraudeur)  
MARAUDEUR_SHIELD_REDUCTION_MIN = 0.2    # 20% réduction minimum
MARAUDEUR_SHIELD_REDUCTION_MAX = 0.5    # 50% réduction maximum
MARAUDEUR_SHIELD_DURATION = 8.0         # Durée du bouclier

# Autres capacités...
```

## Intégration avec les systèmes

### CapacitiesSpecialesProcessor

**Responsabilité :** Mise à jour des timers et gestion des effets spéciaux.

```python
def process(self):
    """Met à jour toutes les capacités spéciales actives."""
    
    # Update des timers pour chaque type de capacité
    for entity, spe_scout in esper.get_components(SpeScout):
        spe_scout.update(dt)
    
    for entity, spe_maraudeur in esper.get_components(SpeMaraudeur):
        spe_maraudeur.update(dt)
        
    # Gestion des effets temporaires (lianes, etc.)
    self._process_vine_effects()
```

### Intégration UI - ActionBar

**Affichage des cooldowns :**

```python
def _draw_special_ability_button(self, surface):
    """Dessine le bouton de capacité spéciale avec cooldown."""
    
    if self.selected_unit.has_special:
        # Récupérer le composant de capacité
        if esper.has_component(entity, SpeScout):
            scout = esper.component_for_entity(entity, SpeScout)
            cooldown_ratio = scout.cooldown_timer / scout.cooldown
            
        # Dessiner le bouton avec overlay de cooldown
        if cooldown_ratio > 0:
            self._draw_cooldown_overlay(surface, cooldown_ratio)
```

### Intégration avec les dégâts

**Dans `processHealth` :**

```python
def apply_damage(entity, damage):
    """Applique les dégâts en tenant compte des capacités."""
    
    # Vérifier invincibilité (SpeScout)
    if esper.has_component(entity, SpeScout):
        scout = esper.component_for_entity(entity, SpeScout)
        if scout.is_invincible():
            return  # Ignorer les dégâts
    
    # Appliquer réduction (SpeMaraudeur)
    if esper.has_component(entity, SpeMaraudeur):
        maraudeur = esper.component_for_entity(entity, SpeMaraudeur)
        if maraudeur.is_shielded():
            damage = maraudeur.apply_damage_reduction(damage)
    
    # Appliquer les dégâts finaux
    health.currentHealth -= damage
```

## Tests et validation

### Exemples de tests unitaires

```python
# Test SpeScout
from src.components.special.speScoutComponent import SpeScout

def test_spe_scout_invincibility():
    scout = SpeScout()
    assert scout.can_activate()
    assert scout.activate() is True
    assert scout.is_invincible()
    
    # Similer le temps qui passe
    scout.update(scout.duration + 0.1)
    assert not scout.is_invincible()
    assert not scout.is_active

# Test SpeMaraudeur
from src.components.special.speMaraudeurComponent import SpeMaraudeur

def test_maraudeur_damage_reduction():
    maraudeur = SpeMaraudeur()
    maraudeur.activate(reduction=0.5)  # 50% de réduction
    
    original_damage = 100
    reduced_damage = maraudeur.apply_damage_reduction(original_damage)
    
    assert reduced_damage == 50
    assert maraudeur.is_shielded()
```

### Tests d'intégration

```python
def test_scout_collision_immunity():
    """Test que le Scout évite les dégâts quand invincible."""
    
    # Créer entité avec SpeScout
    entity = esper.create_entity()
    scout = SpeScout()
    health = HealthComponent(100, 100)
    
    esper.add_component(entity, scout)
    esper.add_component(entity, health)
    
    # Activer invincibilité
    scout.activate()
    
    # Simuler dégâts - ne devrais pas affecter la santé
    apply_damage(entity, 50)
    
    assert health.currentHealth == 100  # Santé inchangée
```

## Bonnes pratiques

### ✅ Recommandations

- **Interface unifiée** : Toutes les capacités implémentent `can_activate()`, `activate()`, `update()`
- **Gestion défensive** : Vérifier `esper.has_component()` avant d'accéder aux capacités
- **Séparation des responsabilités** : Données dans les composants, logique dans les processeurs
- **Configuration centralisée** : Constantes dans `gameplay.py` pour faciliter l'équilibrage
- **Tests exhaustifs** : Couvrir activation, durée, expiration et interactions

### ❌ À éviter

- Logique métier complexe dans les composants
- Modification directe des timers depuis l'extérieur
- Oubli de vérifier les cooldowns avant activation
- États incohérents (`is_active=True` mais `timer=0`)

## Extension du système

### Ajouter une nouvelle capacité

1. **Créer le composant** :

```python
# src/components/special/speNewUnitComponent.py
@component
class SpeNewUnit:
    def __init__(self):
        self.is_active: bool = False
        self.cooldown: float = SPECIAL_ABILITY_COOLDOWN
        self.cooldown_timer: float = 0.0
        # Attributs spécifiques...
    
    def can_activate(self) -> bool:
        return not self.is_active and self.cooldown_timer <= 0
    
    def activate(self) -> bool:
        if self.can_activate():
            self.is_active = True
            self.cooldown_timer = self.cooldown
            return True
        return False
    
    def update(self, dt: float) -> None:
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
```

2. **Intégrer dans le processeur** :

```python
# Dans CapacitiesSpecialesProcessor
for entity, new_capacity in esper.get_components(SpeNewUnit):
    new_capacity.update(dt)
```

3. **Ajouter à l'UI** :

```python
# Dans ActionBar
if esper.has_component(entity, SpeNewUnit):
    capacity = esper.component_for_entity(entity, SpeNewUnit) 
    self._draw_capacity_button(surface, capacity)
```

Cette architecture modulaire permet d'ajouter facilement de nouvelles capacités tout en maintenant la cohérence du système.
