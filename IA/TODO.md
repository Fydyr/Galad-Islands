Le but de ce document est de faire une TODO pour le projet IA, à la fin de cette TODO l'ia de la troupe rapide devra être capable de jouer au jeu de manière autonome. Afin de faciliter la compréhension les responsabilités seront écrite dans plusieurs fichiers (#decisions.md, #Info_importante.md, etc...).

# Introduction
- [x] Dans le fichier #decisions.md répondre au questionnement sur les choix d'implémentation de l'IA (algorithme / renforcement, choix des features, combien de niveau de difficulté d'implémentation, etc...)
    - [x] Comparer les algorithmes d’IA adaptés au jeu
    - [x] Définir les niveaux de difficulté
    - [x] Sélectionner les features à utiliser
    - [x] Justifier chaque choix d’implémentation
    - [x] Proposer des stratégies pour la troupe rapide

- [x] Dans le fichier #Info_importante.md lister les informations importantes pour l'implémentation de l'IA (ex: comment fonctionne le jeu, les règles, etc...), ainsi que les failles à utiliser pour que notre unité puisse être la plus performante possible.
    - [x] Décrire le fonctionnement du jeu
    - [x] Lister les règles importantes
    - [x] Identifier les failles exploitables

- [x] Revenir dans ce fichier pour faire les autres sections après avoir pris toutes les décisions et avoir pris en compte de manière complète chaque information utile à l'implémentation de l'IA.

# 1. Préparation & cadrage
- [ ] Mettre en place un dossier `ia_troupe_rapide/` dans `src/` pour regrouper les modules IA (tout sera codé dedans).
- [ ] Recenser les points d’entrée dans le moteur (systèmes, processeurs) où brancher l’IA.
- [ ] Définir les conventions de log/debug (niveau minimal, format des messages, activation via flag).

# 2. Architecture IA & services communs
- [ ] Créer la structure de machine à états finis (FSM) générique.
    - [ ] Définir l’interface `State` (enter/update/exit) et `TransitionCondition`.
    - [ ] Implémenter le gestionnaire de FSM par unité (support multi-instances).
- [ ] Concevoir les services partagés :
    - [ ] Gestionnaire de contexte (positions, objectifs, timers, cooldowns).
    - [ ] Carte de danger (numpy) alimentée par les événements, mines et ennemis.
    - [ ] Service de pathfinding pondéré (nuages = poids x2, zones interdites = inf).
    - [ ] Service de prédiction courte (anticipation déplacement ennemis/projectiles).
- [ ] Préparer un module de configuration (JSON/YAML) pour ajuster facilement les constantes IA.

# 3. Implémentation des états principaux
- [ ] État `Idle` : calcul zone safe, maintien formation légère, transition rapide vers objectif.
- [ ] État `GoTo` : déplacement vers coffre/base/mine ciblée, re-calcul chemin à chaque tick.
- [ ] État `Flee` : fuite immédiate après dégâts, activation invincibilité si PV bas.
- [ ] État `Attack` : positionnement maximal de portée, tir opportuniste, repli si danger.
- [ ] État `JoinDruid` : trajectoire sécurisée vers Druid le plus proche, vérif absence ennemis.
- [ ] État `FollowDruid` : orbite de protection jusqu’à PV max, retour `Idle`.
- [ ] États avancés (`Preshot`, `FollowToDie`) :
    - [ ] Définir triggers précis (fenêtre d’opportunité, défense ennemie faible).
    - [ ] Implémenter logique de tir anticipé et poursuite contrôlée.

# 4. Gestion des objectifs & priorités
- [ ] Implémenter un prioriseur central (survie > coffre > attaque) aligné avec `Decisions.md`.
- [ ] Ajouter un module d’évaluation d’objectifs (score dynamique selon distance, danger, gain).
- [ ] Mettre en place un bus d’événements IA pour signaler apparition de coffres, tempêtes, etc.
- [ ] Gérer les règles spéciales :
    - [ ] Coffre accessible mais mort certaine : accepter le risque si or garanti.
    - [ ] Mines à détruire seulement si Druid safe + ouverture tir base ennemie.
    - [ ] Tempêtes/kraken/bandits : bannir zones concernées.

# 5. Coordination multi-unités
- [ ] Implémenter un gestionnaire de coffres en singleton (assignation unique par Zasper).
- [ ] Prévoir un canal de communication entre unités (partage danger, objectifs).
- [ ] Éviter les collisions alliées : espacement minimal, ajustement trajectoire.
- [ ] Introduire une stratégie de rotation (si plusieurs unités, alterner collecte/harcèlement).

# 6. Micro-gestion & capacités
- [ ] Implémenter l’utilisation contextuelle de l’invincibilité (uniquement fuite PV bas).
- [ ] Ajouter l’évitement précis des projectiles (prédiction trajectoire ennemie longue distance).
- [ ] Optimiser le tir : ajustement de la visée via anticipation mouvement adverses.
- [ ] Gérer les transitions terrain : ralentissement nuages, accélération zones clears.
- [ ] Prévoir la destruction contrôlée de mines (calcul coût/bénéfice avec Druid).

# 7. Intégration moteur & performance
- [ ] Brancher la FSM dans le cycle de mise à jour des unités (processeurs existants).
- [ ] Garantir l’utilisation de NumPy/Numba pour opérations lourdes (matrices danger, pathfinding).
- [ ] Vérifier qu’aucune boucle Python critique ne subsiste (optimiser via vectorisation).
- [ ] Mettre en place un mode debug IA (overlay zones danger, trajectoires, objectifs).
- [ ] Documenter les points d’intégration dans `Decisions.md` ou `dev/`.

# 8. Tests & validation
- [ ] Écrire tests unitaires pour le prioriseur, services (pathfinding, danger map, prédiction).
- [ ] Créer tests d’intégration simulant :
    - [ ] Apparition coffre + concurrence ennemie.
    - [ ] Fuite sous tempête + utilisation invincibilité.
    - [ ] Coopération avec Druid et récupération PV.
    - [ ] Destruction volontaire de mine pour ouvrir tir base.
- [ ] Lancer sessions de jeu automatisées, enregistrer métriques : taux survie, coffres collectés, dégâts infligés.
- [ ] Ajuster la configuration IA jusqu’à atteindre les objectifs.

# 9. Documentation & livraison
- [ ] Mettre à jour `Info_importante.md` si nouvelles découvertes ou optimisations.
- [ ] Compléter `Decisions.md` avec le design final des états et paramètres.
- [ ] Rédiger un `README_IA.md` décrivant l’installation, le fonctionnement, les options.
- [ ] Préparer une note de déploiement (activation IA dans le jeu, flags config).

# 10. Revue finale & maintenance
- [ ] Organiser une session de validation croisée (QA/équipe gameplay).
- [ ] Lister les améliorations futures (esquive missiles avancée, apprentissage léger).
- [ ] Archiver les logs et configs utilisés pour la version finale.
- [ ] Clore ce TODO en cochant toutes les cases et créer un ticket de suivi maintenance IA.