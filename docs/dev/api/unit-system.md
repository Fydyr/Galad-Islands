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

- Fonction : `UnitFactory(unit_type, enemy: bool, pos: PositionComponent)`

- Comportement : instancie l'entité et lui attache les composants pertinents (health, attack, sprite, team, canCollide, SpeXxx si applicable).

- Exemple : `UnitType.MARAUDEUR` → ajoute `SpeMaraudeur()` lors de la création.

- Valeurs (PV, attaque, vitesse, cooldown) : définies dans `src/constants/gameplay.py`.

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

1. `CollisionProcessor` détecte les collisions (AABB sur `SpriteComponent.original_*`) et appelle `_handle_entity_hit(e1, e2)`.
2. `_handle_entity_hit` :

   - sauvegarde l'état utile (positions, si projectile, ...)
   - dispatch : `esper.dispatch_event('entities_hit', e1, e2)`
   - après le dispatch, gère destruction de mine / explosions selon l'existence des entités

3. Handler configuré : `functions.handleHealth.entitiesHit`

   - lit `AttackComponent.hitPoints` et appelle `processHealth(target, damage)`

4. `processHealth(entity, damage)`

   - récupère `HealthComponent`
   - si `SpeMaraudeur` présent : applique `apply_damage_reduction`
   - si `SpeScout` et `is_invincible()` : annule le dégât
   - décrémente `health.currentHealth` et supprime l'entité si ≤ 0

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

- Système de combat
- IA et comportements
- Factory pattern (déjà rédigé ?)

---

*Cette documentation sera complétée prochainement.*