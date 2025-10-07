# Décisions d'implémentation IA - Troupe rapide

## Objectif principal
Survivre le plus longtemps possible, récupérer les coffres volants, infliger des dégâts sans prendre de risques inutiles. Si un Druid est près de la base et que la vie est à 100%, se sacrifier pour permettre de tirer sur la base ennemie à distance.
Priorisation des objectifs :
- Survie avant tout (éviter la mort)
- Coffres pour maximiser l'argent et permettre le respawn d'unités
- Dégâts : opportunistes, toucher une unité puis fuir suffit

## Type d'IA
100% algorithmique, aucune utilisation de machine learning. Les algorithmes doivent être fiables et déterministes.

## Algorithmes envisagés
L’architecture choisie pour l’IA est une machine à états finis (FSM). Chaque unité rapide (Zasper) suivra des états clairs : fuir, aller au coffre, attaquer, rejoindre Druid, etc. Les transitions entre états sont déterminées par des conditions simples et prioritaires. Aucun machine learning ni renforcement, uniquement du script pur pour garantir fiabilité et performance.

### États FSM prévus pour Zasper
- **Idle** : Va vers une zone safe (calculée via une matrice de danger), contrôle de map si plusieurs unités.
- **GoTo** : Se dirige vers un objectif (coffre, base, mine, etc.).
- **Flee** : Dès qu’un dégât est reçu (hors bombe), demi-tour rapide et recherche d’un chemin safe. Utilise l’invisibilité si disponible.
- **Attack** : Attaque la base ennemie à distance maximale si pas de coffre et vie pleine ou base attaquée.
- **JoinDruid** : Va vers le Druid le plus proche sans ennemis autour si vie basse.
- **FollowDruid** : Suit le Druid jusqu’à récupération complète de la vie, puis repasse en Idle.
- **Preshot** : Tente de tirer en avance sur la position future d’un ennemi pour fuir avant riposte (à affiner).
- **FollowToDie** : Suit un ennemi en tirant jusqu’à sa mort (à affiner).

### Conditions de transition principales
- **Idle → GoTo** : Un objectif apparaît (coffre visible, base à attaquer, etc.).
- **Idle → Flee** : Dégât reçu (hors bombe).
- **Idle → JoinDruid** : Vie basse.
- **GoTo → Flee** : Dégât reçu.
- **GoTo → Attack** : Objectif atteint ou pas de coffre disponible.
- **Flee → Idle** : Zone safe atteinte.
- **JoinDruid → FollowDruid** : Druid atteint.
- **FollowDruid → Idle** : Vie à 100%.
- **Attack → Idle** : Objectif terminé ou danger détecté.
- **Preshot/FollowToDie** : Transitions à définir selon opportunité et contexte (à affiner).

### Priorités d’état (si plusieurs conditions réunies)
1. Survie (Flee, JoinDruid, FollowDruid)
2. Money (GoTo coffre)
3. Attaque (Attack, mines, preshot, followToDie)

### Gestion des mines et événements
Transitions et priorités identiques : toujours privilégier la survie, puis le coffre, puis l’attaque.

### Utilisation de la capacité spéciale (invisibilité)
Activée automatiquement en Flee si disponible pour traverser les mines ou zones dangereuses.

## Difficulté
Une seule IA, la plus forte possible. Pas de niveaux de difficulté.

## Features à prendre en compte
### Sélection et justification des features
#### Réponses aux questions de sélection

1. **Vitesse de déplacement** : Oui, essentielle pour être la première à récupérer les items, rester dynamique et difficile à toucher tant que l’on bouge.
2. **Invincibilité** : À utiliser uniquement pour fuir quand on a peu de PV, afin de sortir plus vite du danger.
3. **Détection et collecte des coffres** : La survie est prioritaire, mais l’or permet le respawn : si on est sûr d’obtenir l’or même en mourant, on prend le risque, sinon priorité à la survie.
4. **Évitement des mines/tempêtes** : Mines esquivées sauf si un Druid est safe et la destruction de la mine permet de tirer sur la base ennemie ; tempêtes et autres événements toujours évités.
5. **Pathfinding et nuages** : Les nuages ne sont pas évités mais ont un poids plus lourd dans le calcul du chemin ; le poids doit être cohérent avec le ralentissement (ex : si nuage = 0.5 vitesse, alors coût x2).
6. **Gestion des priorités** : Voir la section “Priorités d’état” : survie > coffre > attaque.
7. **Coordination multi-unités** : Oui, un singleton (ou équivalent) attribue chaque coffre à une seule unité rapide ; pas besoin de coordination pour le reste pour l’instant.
8. **Buffs/débuffs** : Non utilisé, pas pertinent pour la troupe rapide.
9. **Gestion des cooldowns** : Non, pas d’impact sur la prise de décision pour le moment.
10. **Anticipation des mouvements ennemis** : Oui, nécessaire pour viser précisément, éviter les projectiles et optimiser les déplacements.

#### Justification des choix d’implémentation
Les réponses ci-dessus sont déjà justifiées dans la partie “Priorités d’état” et dans les explications précédentes. Chaque feature retenue l’est pour maximiser la performance, la survie et la capacité à remplir les objectifs principaux de la troupe rapide.
Pour garantir une IA optimale, voici les questions à se poser pour chaque feature :

1. La vitesse de déplacement de la troupe rapide est-elle essentielle pour atteindre les objectifs ? Pourquoi ?
2. L’invincibilité (capacité spéciale) doit-elle être utilisée systématiquement ou seulement dans certains cas ? Lesquels ?
3. La détection et la collecte des coffres sont-elles prioritaires par rapport à l’attaque ou à la survie ?
4. L’IA doit-elle éviter activement les mines et les tempêtes, ou peut-elle prendre des risques calculés ?
5. Le pathfinding doit-il intégrer l’évitement des nuages (ralentissement) ou se concentrer sur la rapidité d’accès aux objectifs ?
6. Comment l’IA doit-elle gérer les priorités entre survie, collecte de coffres et attaque ?
7. Faut-il coordonner plusieurs unités rapides pour éviter qu’elles poursuivent le même objectif ? Comment ?
8. L’utilisation des buffs/débuffs (bouclier, soin) doit-elle être automatisée ou contextuelle ?
9. La gestion des cooldowns (capacités, attaques) doit-elle influencer la prise de décision ?
10. L’IA doit-elle anticiper les mouvements ennemis ou se concentrer sur la réaction immédiate ?

Pour chaque feature retenue, justifier le choix :

- **Vitesse élevée** : Permet d’atteindre les coffres avant l’ennemi et d’éviter les zones dangereuses rapidement, ce qui maximise la survie et la collecte.
- **Invincibilité** : Utilisée pour traverser les mines ou fuir une tempête, elle garantit la survie dans les situations critiques.
- **Détection et collecte des coffres** : Objectif prioritaire pour maximiser l’argent et le respawn d’unités.
- **Évitement des mines/tempêtes** : Réduit les risques de mort instantanée, augmente la durée de vie de l’unité.
- **Pathfinding optimal** : Évite les obstacles et les zones à risque, améliore la réactivité et la sécurité.
- **Gestion des priorités** : Assure que l’IA prend toujours la meilleure décision selon le contexte (survie > coffre > attaque).
- **Coordination multi-unités** : Optimise la répartition des objectifs, évite les doublons et maximise l’efficacité collective.
- **Utilisation des buffs/débuffs** : Automatisée pour garantir une réaction rapide en cas de danger ou d’opportunité.
- **Gestion des cooldowns** : Influence le timing des actions et évite les pertes d’opportunité.
- **Anticipation des mouvements ennemis** : Permet d’éviter les pièges et d’optimiser les attaques ou les esquives.

**À compléter : Pour chaque feature, répondre aux questions ci-dessus et adapter la justification selon la stratégie choisie.**
## Micro/Macro gestion
Gestion fine des déplacements : orientation, avancer/reculer, arrêt, calcul de chemin optimal (éviter obstacles, nuages, événements), liaison du chemin au contrôle du vaisseau. Esquive des missiles à envisager pour une version ultérieure.
Déplacement : éviter les nuages si possible (ralentissement), mais priorité aux coffres et objectifs.

## Apprentissage
Aucun apprentissage en cours de partie.

## Exploitation de failles
Pas de faille connue, mais possibilité de prédire la position future des ennemis ou projectiles pour esquiver ou viser.

## Adaptation au joueur
Aucune adaptation au style du joueur humain.

## Performance
Temps de calcul et réactivité critiques (jeu en temps réel).

## Modularité
L'IA doit être modulaire pour faciliter l'ajout de nouveaux comportements.

## Outils/Bibliothèques
Privilégier les bibliothèques optimisées (NumPy, etc.), pas de préférence stricte.

## Testabilité
Tests unitaires et logs (activables via une variable debug) à prévoir tout au long du développement.
Niveau de logs : très limité, uniquement changement d'objectif, position cible, prédictions, etc.

## Priorité
Priorité à la qualité du comportement plutôt qu'à la rapidité de développement.

## Contrôle d'unités
Gestion multi-unités : l’IA peut gérer plusieurs troupes rapides (Zasper). Pour les coffres, un singleton attribue à chaque apparition du coffre l’unité la plus adaptée parmi les Zasper disponibles, afin d’éviter que plusieurs unités poursuivent le même objectif.

## Scénarios de victoire/défaite
Non pertinent (pas de machine learning).

## Gestion des événements
Gestion active des événements aléatoires (tempêtes, coffres, etc.).
Marge de sécurité pour prédiction d'événements : à définir selon la taille de l'événement, mais fuite immédiate hors zone à risque.

## Style de jeu
Agressif mais conservateur : embêter l’ennemi, accumuler de l’argent, profiter de la vitesse, éviter la mort sauf si le gain est garanti.
Pas de routine différente selon la phase de partie : comportement identique du début à la fin.
Pas de comportement spécifique selon le type d’ennemi.
Interaction avec alliés : uniquement avec Druid si vie basse.
Pas de patrouille ou d’attente passive : toujours en action (attaque, coffre, gêne, destruction de mines selon conditions).

## Risques techniques
Aucun identifié à ce stade.

## Bonus
Les fonctions doivent être ciblées et optimisées pour chaque sous-tâche.
Utilisation des capacités spéciales : invisibilité uniquement pour traverser les mines si vie basse et rejoindre Druid.
Système de cooldown : cooldown dur de 2 secondes entre chaque tâche/action.
