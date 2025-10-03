# Capacités spéciales (Spe*) — documentation technique
```py
from src.components.properties.ability.speScoutComponent import SpeScout

def test_spe_scout_activate_and_expire():
    s = SpeScout()
    assert s.can_activate()
    assert s.activate() is True
    assert s.is_invincible()
    s.update(s.duration + 0.1)
    assert not s.is_invincible()

---
# Capacités spéciales (Spe*) — documentation technique

Cette page décrit les capacités spéciales implémentées dans le jeu (composants `Spe*`).
Pour chaque capacité : objectif, forme des données (attributs), API publique, cycle de vie, interactions avec les systèmes
(collision, santé, UI) et suggestions de tests.

## Sommaire

- [SpeScout](#spescout)
- [SpeMaraudeur](#spemaraudeur)
- [SpeLeviathan](#speleviathan)
- [SpeDruid](#spedruid)
- [SpeArchitect](#spearchitect)


## SpeScout {#spescout}

### But

Fournir une courte période d'invincibilité (en secondes) pour esquiver des attaques ou des mines.

### Données (exemple)

```py
is_active: bool
duration: float  # durée en secondes
timer: float     # temps restant d'effet
cooldown: float  # cooldown standard
cooldown_timer: float
```

### API

- `can_activate()` -> bool
- `activate()` -> bool
- `update(dt)`
- `is_invincible()` -> bool

### Comportement

- `activate()` met `is_active=True`, `timer=duration`, `cooldown_timer=cooldown`.
- `update(dt)` décrémente `cooldown_timer` et, si `is_active`, décrémente `timer` et coupe `is_active` quand `timer <= 0`.
- `is_invincible()` renvoie l'état `is_active`.

### Interactions

- `CollisionProcessor._handle_entity_hit` doit vérifier `SpeScout.is_invincible()` et ignorer la collision/dégâts si True.
- `functions.processHealth` devrait aussi vérifier l'invincibilité avant d'appliquer des dégâts (double-sûreté).

### Tests recommandés

- activation possible quand `cooldown_timer == 0`
- active pendant `duration` puis expire
- aucune perte de vie pendant l'invincibilité


## SpeMaraudeur {#spemaraudeur}

### But

Réduire une fraction des dégâts reçus pendant une durée donnée.

### Données (exemple)

```py
is_active: bool
reduction_value: float  # fraction (0.0..1.0) appliquée aux dégâts
duration: float
timer: float
cooldown: float
cooldown_timer: float
```

### API

- `can_activate()` -> bool
- `activate()` -> bool
- `update(dt)`
- `apply_damage_reduction(damage: float) -> float`
- `is_shielded()` -> bool

### Comportement

- `apply_damage_reduction` réduit `damage` par `reduction_value` si `is_active` True.
- `activate()` règle `is_active` et `timer` et démarre `cooldown_timer`.
- `update(dt)` décrémente `timer` et `cooldown_timer`.

### Interactions

- `functions.processHealth` appelle `apply_damage_reduction` avant de soustraire la vie.
- L'UI lit `cooldown_timer` pour afficher le cooldown dans l'ActionBar.

### Tests recommandés

- réduction appliquée uniquement quand actif
- cooldown empêchant double activation
- interaction avec Scout: un Scout invincible ne devrait pas déclencher la réduction (la logique d'annulation de dégâts vient avant)

### Notes d'implémentation

- Protéger `apply_damage_reduction` avec try/except dans `processHealth` pour éviter des exceptions qui interrompraient l'application des dégâts (défensive).


## SpeLeviathan {#speleviathan}

### But

Doubler (ou relancer) une attaque instantanément après la première salve si la capacité est active.

### Données & API

- `is_active`, `duration` (souvent 1 shot — utilisé comme un flag)
- `can_activate()`, `activate()`, `update(dt)`

### Comportement

- Lors de `trigger_selected_attack`, le code vérifie `SpeLeviathan.is_active` et, si True, déclenche un second `attack_event` immédiatement puis désactive le flag.

### Interactions

- Pas d'interaction directe avec `processHealth` (capacité offensive) ; elle se résout en dispatch d'`attack_event` (projectiles) et sera visible dans `CollisionProcessor`.

### Tests

- activer et vérifier qu'une seconde salve est émise
- vérifier que l'effet est consommé (`is_active -> False`) après usage


## SpeDruid {#spedruid}

### But

Lancer un projectile particulier (ou appliquer un effet) qui immobilise ou entrave une unité ennemie pendant un temps.

### Données & API (exemple)

- `is_active: bool`
- `available: bool`
- `cooldown`, `cooldown_timer`
- `target_id: Optional[int]`
- `immobilization_duration`, `remaining_duration`
- méthodes: `can_cast_ivy()`, `cast(target_pos)` ou `activate(target)`

### Comportement

- On sélectionne une cible (ou position), on lance un projectile spécial.
- À l'impact, le projectile applique `is_vined` / `VineComponent` à la cible, avec `remaining_duration`.
- `CapacitiesSpecialesProcessor` doit aussi gérer le countdown de l'immobilisation et retirer le composant.

### Interactions

- Ajoute/retire dynamiquement un composant (ex: `VineComponent`) sur l'entité cible.
- Doit coopérer proprement avec `CollisionProcessor` (projectile) et `LifetimeProcessor` (durée de l'effet visuel/explosion).

### Tests

- lancer projectile, vérifier ajout du composant et sa suppression après durée
- vérifier cooldown / availability


## SpeArchitect {#spearchitect}

### But

Appliquer un buff de recharge automatique sur les alliés proches (ou recharger leurs munitions), généralement pendant une durée.

### Données & API (exemple)

- `is_active`, `available`, `cooldown`, `cooldown_timer`
- `radius: float`
- `activate(affected_units: list[int], duration: float)`
- `timer` / `remaining_duration`

### Comportement

- À l'activation, on trouve les unités alliées dans le rayon, on applique un buff (par ex: réduire leur `RadiusComponent.cooldown` ou augmenter reload rate) et on démarre `timer`.
- À expiration, on retire l'effet.

### Interactions

- Interagit avec `RadiusComponent` (lecture/écriture de `cooldown` ou d'un multiplicateur), et avec l'UI si on veut afficher le buff.

### Tests

- activer et vérifier que les unités cibles ont leur cadence modifiée
- vérifier expiration et cleanup


## Bonnes pratiques pour toutes les capacités

- Standardiser une interface minimale (`can_activate`, `activate`, `update`) permet à `GameEngine` et à l'UI d'interagir de manière uniforme.
- Toujours protéger les appels provenant d'un composant optionnel (ex: `if esper.has_component(entity, SpeMaraudeur): ...`).
- Garder les effets purs côté composants (données) et la logique lourde (création de projectiles, modifications globales) dans des systèmes/processors.
- Utiliser `logging` au niveau DEBUG pour traces détaillées (activation, expiry, dégâts appliqués) et éviter `print`.
- Documenter clairement les invariants (p.ex. `cooldown_timer >= 0`, `timer >= 0`).


## Exemples de tests unitaires (pytest)

```py
from src.components.properties.ability.speScoutComponent import SpeScout

def test_spe_scout_activate_and_expire():
    s = SpeScout()
    assert s.can_activate()
    assert s.activate() is True
    assert s.is_invincible()
    s.update(s.duration + 0.1)
    assert not s.is_invincible()

# SpeMaraudeur behaviour
from src.components.properties.ability.speMaraudeurComponent import SpeMaraudeur

def test_maraudeur_reduction():
    m = SpeMaraudeur()
    assert m.can_activate()
    m.activate()
    reduced = m.apply_damage_reduction(100)
    assert reduced < 100
```


## Notes de maintenance

- Si on ajoute de nouvelles capacités, créer le composant `SpeNew` avec l'API minimale et documenter le comportement ici.
- Si on introduit un `ManaComponent`, mettre à jour `activate()` pour vérifier et consommer la ressource.


Fin.
- Si on ajoute de nouvelles capacités, créer le composant `SpeNew` avec l'API minimale et documenter le comportement ici.
- Si on introduit un `ManaComponent`, mettre à jour `activate()` pour vérifier et consommer la ressource.


Fin.
