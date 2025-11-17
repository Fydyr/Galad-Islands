# Plan d'amélioration des états de l'IA Scout

Portée : revue des comportements de `src/ia/ia_scout/states` sur la base de l'implémentation actuelle (idle, goto, attack, explore, flee, follow_druid, follow_to_die, preshot). Priorités : **High** = risque gameplay immédiat, **Medium** = manque de finition visible, **Low** = amélioration de confort/nettoyage. Chaque proposition inclut une esquisse de solution pour démarrer rapidement la mise en œuvre.

## Idle (`src/ia/ia_scout/states/idle.py`)
- **Priorité** : Medium
- **Problème** : Les échantillons du danger map provoquent du flottement ; l'unité relance la requête à chaque frame et perd son inertie après avoir atteint une zone sûre.
- **Piste de solution** :
  - Mettre en cache la tuile sûre pendant une courte durée (ex. 0,5 s) pour limiter les oscillations et invalider le cache lors des pics de dégâts ou changement d'objectif.
  - Utiliser `controller.ensure_navigation(... cached_point ...)` pour prolonger le mouvement vers ce point plutôt qu'un `move_towards` direct.
  - Prévoir un repli vers l'objectif d'exploration quand aucun point plus sûr n'est trouvé afin d'éviter les blocages à proximité d'une zone déjà sécurisée.

## GoTo (`src/ia/ia_scout/states/goto.py`)
- **Priorité** : High
- **Problème** : Les invalidations de chemin déclenchent des recalculs complets sans limitation et le rayon de waypoint est constant, ce qui crée du jitter dans les goulots d'étranglement.
- **Piste de solution** :
  - Suivre `last_repath_time` par contrôleur et ignorer les nouvelles demandes pendant ~0,15 s tant qu'aucun drapeau d'obstacle n'est levé.
  - Ajuster dynamiquement le rayon des waypoints selon la densité du terrain (variance de coût dans le cône de navigation) pour permettre aux unités de se faufiler.
  - Autoriser des raccourcis off-mesh en laissant `request_path` accepter des `hint_nodes` fournis par le service de coordination lorsque plusieurs scouts partagent le même but.

## Attack (`src/ia/ia_scout/states/attack.py`)
- **Priorité** : High
- **Problème** : La gestion de l'ancrage échoue dès que l'ennemi se place derrière un obstacle ; l'état continue de tirer même quand `radius_component.cooldown` n'est plus aligné.
- **Piste de solution** :
  - Conserver `context.anchor_position` dans le canal partagé et l'invalider dès que `pathfinding.has_line_of_fire` retourne faux.
  - Ne publier `attack_event` qu'après vérification explicite de munitions/cooldown (ex. `if not controller.weapon_manager.can_fire(entity_id): return`).
  - Ajouter une anticipation : extrapoler la vitesse ennemie depuis l'historique de `context.target_entity` et décaler l'ancrage en conséquence.

## Explore (`src/ia/ia_scout/states/explore.py`)
- **Priorité** : Medium
- **Problème** : Une seule réservation d'assignation crée des boucles d'attente quand la cible est inaccessible ; le planner ne réévalue jamais la fraîcheur des secteurs.
- **Piste de solution** :
  - Détecter les `_handle_blocked_target` répétés pour un même secteur et prévenir le planner via `reserve(..., blacklist=sector)` afin d'en choisir un autre.
  - Faire remonter `record_observation` pour diminuer temporairement la priorité des secteurs récemment scannés, avec un `observation_ttl` pour restaurer leur poids.
  - En absence d'assignation, retomber sur `RapidUnitController.get_support_objective()` afin que le scout escorte un allié plutôt que d'attendre.

## Follow Druid (`src/ia/ia_scout/states/follow_druid.py`)
- **Priorité** : Medium
- **Problème** : Le rayon d'orbite est fixe et ne tient pas compte de la vitesse du druide ; la navigation s'annule/repart sans cesse, produisant un effet yo-yo.
- **Piste de solution** :
  - Remplacer le rayon constant par une distance adaptative en fonction de la vitesse du druide et de la portée des armes du scout (proche à l'arrêt, large en mouvement).
  - Maintenir un petit anneau de waypoints (ex. quatre offsets) autour du druide et le réutiliser tant que la direction ne change pas brutalement.
  - Propager la mort du druide vers le service de coordination afin que les scouts inactifs se redirigent immédiatement vers un nouveau rôle.

## Follow To Die (`src/ia/ia_scout/states/follow_to_die.py`)
- **Priorité** : Medium
- **Problème** : `_target_cache` n'expire jamais ; l'état poursuit indéfiniment la dernière position connue si la cible disparaît et tire sans vérifier la ligne de tir.
- **Piste de solution** :
  - Associer une durée de vie à `_target_cache` (via `controller.settings.target_memory_seconds`) et quitter l'état lorsque la mémoire expire sans contact visuel.
  - Appeler `pathfinding.has_line_of_fire` avant `attack_event` pour éviter de tirer dans les murs ; sinon, demander un chemin de contournement via `controller.request_path`.
  - Moduler la vitesse de poursuite selon les PV restants afin qu'un scout agonisant n'aille pas trop loin (sauf drapeau kamikaze explicite dans l'objectif).

## Preshot (`src/ia/ia_scout/states/preshot.py`)
- **Priorité** : Low
- **Problème** : Fichier de compatibilité laissé vide ; perturbe les mainteneurs et occupe un slot d'état inutile.
- **Piste de solution** :
  - Retirer l'état du FSM dès que les données aval (sauvegardes/scripts) n'y font plus référence, sinon l'associer à une routine de pré-visée légère pour justifier sa présence.
  - Documenter le calendrier de dépréciation dans la docstring du module et le changelog afin de signaler la date de retrait sûre.
