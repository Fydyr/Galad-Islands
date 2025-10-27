---
i18n:
  en: "API - Unit System"
  fr: "API - Système d'unités"
---

# API - Système d'unités

> 🚧 **Section en cours de rédaction**

Cette page décrit le modèle d'entités pour les unités, l'API des capacités spéciales, le flux de dégâts (collision → dispatch → application) et les bonnes pratiques de débogage et de test.

---

## 🧩 Principes généraux

- Architecture : ECS (Esper-like)

  - entité = id numérique (int)
  - composants = dataclasses attachées via `esper.add_component(entity, Component(...))`
  - processeurs = classes héritant de `esper.Processor` et exécutées via `es.process()`

- Composants clefs pour une unité

  - `PositionComponent` : { x, y, direction }
  - `SpriteComponent` : rendu (image, taille, surface)
  - `TeamComponent` : { team_id }
  - `VelocityComponent` : { currentSpeed, terrain_modifier, ... }
  - `RadiusComponent` : { bullet_cooldown, ... }
  - `AttackComponent` : { hitPoints }
  - `HealthComponent` : { currentHealth, maxHealth }
  - `CanCollideComponent` : drapeau de collision
  - `Spe*` : composants de capacités spéciales (SpeScout, SpeMaraudeur, ...)

Vous pouvez en savoir plus sur les capacités spéciales dans la [documentation dédiée](../modules/special-capacity-system.md).

---

## ⚙️ Factory — création des unités

La `UnitFactory` est le point central pour la création des entités d'unités. Elle garantit que chaque unité est instanciée avec le bon ensemble de composants en fonction de son type.

- **Fonction** : `UnitFactory(unit_type: UnitType, enemy: bool, pos: PositionComponent)`

- **Comportement** : Instancie l'entité et lui attache les composants pertinents (santé, attaque, sprite, équipe, `CanCollide`, `SpeXxx` si applicable). La factory lit les statistiques des unités (PV, dégâts, vitesse) depuis `src/constants/gameplay.py`.

- **Exemple** : `UnitType.MARAUDER` → ajoute `SpeMaraudeur()` lors de la création.

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

---

## ✨ Capacités spéciales — contrat & API

Chaque capacité spéciale est encapsulée dans un composant `SpeXxx`. Le code (GameEngine/UI/processors) attend une API légère et uniforme.

> Voir la documentation détaillée des capacités : [Système de capacités spéciales](../modules/special-capacity-system.md)

### Contrat recommandé

- Attributs (selon capacité)

  - `is_active: bool`
  - `duration: float`
  - `timer: float`
  - `cooldown: float`
  - `cooldown_timer: float`

- Méthodes conseillées

  - `can_activate()` -> bool
  - `activate()` -> bool
  - `update(dt)`
  - éventuelles méthodes spécifiques (ex : `apply_damage_reduction(damage)`, `is_invincible()`)

### Implementations courantes

- `SpeScout` : invincibilité temporaire (`is_invincible()`)
- `SpeMaraudeur` : bouclier qui réduit les dégâts (`apply_damage_reduction`, `is_shielded()`)
- `SpeLeviathan`, `SpeDruid`, `SpeArchitect` : autres comportements (voir composants respectifs)

---

## 🔁 Cycle de mise à jour

- `CapacitiesSpecialesProcessor.process(dt)` appelle `update(dt)` sur chaque composant `Spe*`.
- L'UI (ActionBar) lit `cooldown_timer` pour afficher le cooldown via `GameEngine._build_unit_info` / `_update_unit_info`.

---

## 💥 Chaîne de dégâts (collision → application)

Le système de combat est piloté par les événements, à partir de la détection de collision.

1.  **`CollisionProcessor`** : Détecte les collisions (AABB sur `SpriteComponent.original_*`) et appelle `_handle_entity_hit(e1, e2)`.
2.  **`_handle_entity_hit`** :
    - Sauvegarde l'état utile (positions, si projectile, ...).
    - Dispatche un événement : `esper.dispatch_event('entities_hit', e1, e2)`.
    - Après le dispatch, gère la destruction des mines/explosions en fonction de l'existence de l'entité.
3.  **Handler configuré** : `functions.handleHealth.entitiesHit` est enregistré pour écouter l'événement `entities_hit`.
    - Il lit `AttackComponent.hitPoints` de l'attaquant et appelle `processHealth(target, damage)`.
4.  **`processHealth(entity, damage)`** :
    - Récupère le `HealthComponent` de la cible.
    - Si `SpeMaraudeur` est présent et actif, il applique `apply_damage_reduction`.
    - Si `SpeScout` est présent et `is_invincible()`, il annule les dégâts.
    - Décrémente `health.currentHealth` et supprime l'entité si la santé est ≤ 0.


---

## ⚠️ Points d'attention

- Cohérence des noms : `HealthComponent` utilise `currentHealth` / `maxHealth` (camelCase)
- Protéger les appels sur composants optionnels avec `esper.has_component(...)`
- Éviter que des handlers ré-dispatchent `entities_hit` pour la même paire (boucle)
- Mine lifecycle : entité (HP=1, Attack=40, Team=0) + nettoyage de la grille (`graph[y][x] = 0`) par `CollisionProcessor`

---

## 🐛 Debugging recommandé

- Préférer `logging` à `print` et utiliser des niveaux (DEBUG/INFO/WARN)
- Traces utiles :

  - `CollisionProcessor._handle_entity_hit(e1,e2)` (composants clés)
  - `functions.handleHealth.entitiesHit` / `processHealth` (health avant/après, Spe* présents)
  - vérifier `esper.entity_exists(entity)` après dispatch

---

## ✅ Tests à automatiser

- Tests unitaires (monde esper minimal) :

  - mine vs unité normale → mine morte, unité -40 PV, grille = 0
  - mine vs Scout invincible → mine intacte, unité pas touchée
  - projectile vs mine → projectile détruit, mine intacte
  - Maraudeur bouclier → dégâts réduits correctement

---

## 💡 Recommandations futures

- Remplacer `print` par `logging` (niveau DEBUG)
- Standardiser l'API des capacités via une base commune (`BaseSpecialAbility`)
- Ajouter `ManaComponent` si besoin de coût en ressource pour certaines capacités

---

## À venir

- IA et comportements

---

*Cette documentation sera complétée prochainement.*