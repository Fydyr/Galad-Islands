# 🧾 Notes de mise à jour

## v1.1.0 (2025-11-26)

### ✨ Nouvelles fonctionnalités

- Support des manettes de jeu (contrôleurs) pour une expérience plus accessible.
- Nouvelle musique d'ambiance et cinématique d'introduction au lancement du jeu.
- Nouveau mode d'affichage du brouillard (tuiles) et améliorations des outils de performance.
- Système de cache pour surfaces et polices : rendu plus fluide et chargements plus rapides.
- Notification de changement de résolution : un message indique quand une résolution nécessite un redémarrage du jeu.
- Limites par type d'unités et par équipe ajoutées pour mieux équilibrer les parties.
- Améliorations de l'IA (Scout, gestion du danger) : meilleur pathfinding et comportement en exploration.
- Bouton global pour activer/désactiver toutes les IA.
- Nouveauté audio : son d'arme lors du tir des unités.
- Nouvelles options de gameplay disponibles dans l'outil de configuration.

### 🐛 Corrections de bugs

- Correction d'un problème de collisions dans certaines situations (impliquant unités et projectiles).
- Mise à jour de la cinématique et de sa musique.
- Mise à jour par défaut des paramètres de résolution et du mode d'affichage du brouillard.
- Amélioration des tuiles d'images (visuel et rendu).
- Application correcte des limites de troupe par équipe et par type d'unité.
- Vérification de l'or avant la construction d'une tour : le jeu empêche désormais le placement si vous n'avez pas assez d'or.
- Amélioration du pathfinding en exploration pour éviter les blocages et mieux gérer les foules.
- Option pour désactiver l'IA du Maraudeur (pratique pour tests ou parties personnalisées).
- Correction du comportement des projectiles des bandits près des bords de la carte.

### 🔧 Améliorations techniques

- Ajout d'un cache pour accélérer le rendu (surfaces et polices) et réduire les temps de chargement.
- Nettoyage de code interne et amélioration de l'outil de configuration.
- Transfert des fonctions de nettoyage des modèles (Maraudeur AI Cleaner) vers l'outil de configuration `Galad Config Tool`.

## v1.0.0

- Version initiale.


## v0.13.0 (2025-11-23)

### ✨ Nouvelles fonctionnalités

- Nouveaux tutoriels in‑game : parcours pas à pas pour les événements, la caméra, la découverte de la base ennemie et plusieurs unités (Éclaireur, Maraudeur, Léviathan, Druide, Kamikaze, Architecte). Les tutoriels sont interactifs et traduits FR/EN.
- Améliorations de l'IA : comportement plus stable et plus fluide du Maraudeur, meilleure gestion des unités de reconnaissance et possibilité d'activer/désactiver l'IA au besoin.
- Son & ambiance : nouveaux effets sonores et un thème musical pour les parties, avec prise en charge améliorée des formats audio.
- Interface : meilleure gestion des résolutions plein écran et affichage amélioré des informations (ex. or des deux équipes en mode IA vs IA).

### 🐛 Corrections de bugs

- Correction des traductions et meilleures prises en charge des accents/UTF‑8.
- Correction du comportement des bandits et protections lors du changement d'unité (empêchements si aucune unité n'est disponible).
- Améliorations et nettoyages du système de tutoriel (boutons inutiles retirés, textes clarifiés).
- Divers correctifs pour la stabilité de l'IA et de l'interface.

### 🔧 Refactorisation

- Nettoyage et tests : améliorations du système de traduction, tests supplémentaires pour les tutoriels et l'audio.
- Packaging : optimisations du processus de build et gestion des dépendances pour des releases plus fiables.


## v0.12.0 (2025-11-14)

### ✨ Nouvelles fonctionnalités

- **🎮 Fenêtre modale de fin de partie** : Nouvelle interface de victoire/défaite avec statistiques détaillées
  - Affichage des statistiques de la partie
  - Option de rejouer directement
  - Interface plus claire et informative

- **🤖 Amélioration de l'IA Scout** : Refonte majeure du système de pathfinding
  - Prise en compte de la vitesse et des objectifs en temps réel
  - Variation d'angle pour les tirs afin d'éviter les collisions entre projectiles
  - **Correction majeure** : L'IA Scout fonctionne désormais correctement pour **les deux équipes**
  - Détection dynamique de la position de la base ennemie (plus de positions codées en dur)

- **⚙️ Gestionnaire de processeurs IA** : Activation/désactivation dynamique
  - Économie de ressources CPU en n'activant que les processeurs nécessaires
  - Meilleure performance globale du jeu

- **📊 Analyse de performance (développeur uniquement)** : Outils de benchmark détaillés
  - Analyse approfondie des résultats de benchmark
  - Identification des goulots d'étranglement

### 🐛 Corrections de bugs

- **🎯 IA de l'Architecte** : L'Architecte place enfin correctement les tours de soin
  - Correction du système de placement des tours
  - Amélioration de la sélection du type de tour

- **🛡️ IA du Maraudeur** : Comportement de combat amélioré
  - Logique de détection des ennemis plus précise
  - Approche tactique optimisée

- **⚡ IA du Léviathan** : Capacité spéciale renforcée
  - Ajout d'une seconde volée pour l'attaque spéciale
  - Meilleure gestion de l'activation des capacités
  - Mise à jour des cooldowns d'attaque

- **🏥 IA des unités blessées** : Logique de survie améliorée
  - Priorité à la retraite en cas de faible santé
  - Recherche de Druide pour soins si disponible

- **🚧 Gestion des obstacles** : Navigation améliorée
  - Meilleure gestion des blocages avec marche arrière prolongée
  - Changement d'angle pour contourner les obstacles
  - Paramètres de navigation optimisés pour réduire les blocages

- **⚖️ Équilibrage stratégique** : Limites d'unités de soutien
  - Plafond pour les Architectes et Druides
  - Évite le spam et maintient l'équilibre du jeu
  - Exclusion correcte des unités de soutien du comptage pour le revenu passif

- **🎯 IA de la Base** : Décisions stratégiques améliorées
  - Démonstration enrichie avec stratégies pour les deux équipes
  - Ajustement des actions en fonction de la connaissance de la base ennemie
  - Empêche le spawn de Léviathan en début de partie

- **🔧 Corrections techniques diverses** :
  - Correction des collisions et du déplacement du Scout
  - Amélioration du chemin de stockage des données pour les versions non compilées
  - Correction de l'importation du package `src`
  - Gestion correcte des temps de recharge avec le processeur de capacités
  - Correction du chargement des sprites au démarrage

### 🔧 Refactorisation

- **Renommage** : "Barhamus" renommé en "Maraudeur" dans tout le code
  - Cohérence avec la terminologie du jeu
  - Mise à jour de tous les fichiers et références

## v0.11.3 (2025-11-04)

### 🐛 Corrections de bugs

- mise à jour du recul et de la direction après une collision (responsable des bugs de collision et de pathfinding)
- **ScoutAi**: améliorer la gestion de la décadence dans DangerMapService et réparation du filtrage des entités dans PredictionService

## v0.11.2 (2025-11-02)

### 🐛 Corrections de bugs

- ajouter la gestion des chemins et d'un import caché pour les modèles pré-entraînés dans BaseAi et BarhamusAI pour la version compilé
- suppresion de la dépendance pygame pour éviter que les outils qui l'importe doivent l'embarquer

## v0.11.1 (2025-11-02)

### 🐛 Corrections de bugs

- corriger la résolution des chemins pour les fichiers de documentation en utilisant get_resource_path
- améliorer la résolution du chemin pour galad_resolutions.json dans les builds développés et compilés
- amélioration de la gestion du dossier des modèles par défaut pour inclure le dossier de données utilisateur en version compilée

## v0.11.0 (2025-11-02) - Pré-release 1.0

> **🎯 Cette version marque la préparation finale avant la sortie de la 1.0 !**  
> Toutes les fonctionnalités principales sont désormais complètes et polies. Le jeu est fonctionnellement complet et prêt pour la production.

### ✨ Nouvelles fonctionnalités

- **🔄 Vérificateur de mises à jour automatique** : Le jeu vérifie désormais les nouvelles versions sur GitHub au démarrage
  - Notification discrète en haut à droite du menu lorsqu'une mise à jour est disponible
  - Système de cache intelligent (maximum 1 vérification par 24 heures)
  - Entièrement configurable dans le menu Options
  - Vérification manuelle disponible à tout moment via le menu Options
  - Désactivation automatique en mode développement

- **🤖 Amélioration de l'entraînement de l'IA Barhamus** : Ajout de nouveaux scénarios d'entraînement
  - Navigation avancée et évitement d'obstacles
  - Prise de décision tactique améliorée
  - Meilleur pathfinding dans les situations complexes

- **🧹 Outil Maraudeur AI Cleaner** : Nouvel outil GUI pour la gestion des modèles d'IA
  - Nettoyage facile des modèles d'IA obsolètes
  - Meilleure organisation des fichiers d'entraînement
  - Fichiers de traduction dédiés pour les outils

- **⚔️ Améliorations de l'IA Scout** : Refonte majeure du comportement du Scout
  - Moins agressif, plus axé sur l'exploration
  - Meilleure recherche de ressources
  - Paramètres de sécurité et logique d'exploration améliorés

- **🏗️ Améliorations de l'IA Architecte** : Gestion de construction plus intelligente
  - Meilleur système de priorités de construction
  - Gestion des ressources améliorée

- **💰 Processeur de revenu passif** : Évite les blocages économiques
  - Génération automatique de ressources pour éviter les impasses
  - Comptage des unités basé sur la santé pour une distribution équitable des revenus

### 🐛 Corrections de bugs

- **🎭 Cohérence du lore** : Mise à jour des noms et classes d'unités dans la boutique pour correspondre au lore du jeu
- **📊 Prêt pour la production** : Réduction des logs au minimum pour la version de release
- **⚡ Système de tempêtes** : Augmentation de la taille visuelle et de la portée des tempêtes pour un meilleur impact
- **🎯 Peaufinage final** : Mise à jour des tests et ajustements de dernière minute pour la stabilité
- **🤖 IA Barhamus** : Mise à jour du modèle pré-entraîné avec de meilleures performances
- **🎯 Service de prédiction** : Exclusion explicite des unités alliées et des navires bandits du ciblage
- **💥 Pathfinding Kamikaze** : Navigation et acquisition de cible améliorées
- **🏠 Positionnement Barhamus** : Meilleure logique de recul et maintien de position près de la base ennemie
- **🧠 Logique de l'IA de base** : Action toujours déterminée dans la prise de décision
- **📝 Commentaires de code** : Migration partielle des commentaires vers l'anglais

### 🔧 Améliorations techniques

- **🌍 Système de traduction** : Les outils ont désormais leurs propres fichiers de traduction dédiés
- **📚 Documentation du code** : Migration en cours des commentaires vers l'anglais
- **🎯 Sélection d'équipe** : Mise à jour des traductions pour correspondre à la terminologie en jeu

---

## v0.10.0 (2025-10-30) - Mise à jour majeure IA & Systèmes

### ✨ Nouvelles fonctionnalités

- **🗺️ Placement dynamique des bases** : Système de positionnement des bases complètement 🔧 Refactorisationisé
  - Gestion flexible des points d'apparition
  - Meilleure intégration avec la génération de carte

- **💥 Améliorations de la fenêtre de crash** : Gestion des erreurs améliorée
  - Messages d'erreur localisés
  - Meilleur retour utilisateur lors des crashes

- **💎 Gestion des ressources** : Système de ressources d'îles amélioré
  - Intervalles d'apparition des ressources ajustés
  - L'IA collecte désormais les ressources des îles
  - Gestion de l'or pour l'IA Architecte

- **🤖 Entraînement IA en deux phases** : Nouveau système d'entraînement stratégique
  - Phase 1 : Exploration et apprentissage de la carte
  - Phase 2 : Assaut et tactiques de combat
  - Constantes de jeu ajustées pour de meilleures performances IA

- **🎓 Pré-entraînement Barhamus** : Nouveau script de pré-entraînement
  - Simulations de combat tactique
  - Meilleures performances de base

- **⚙️ Options de performance** : Nouveaux paramètres graphiques
  - Option de basculement VSync
  - Limiteur de FPS maximum
  - Option pour désactiver l'apprentissage IA du Maraudeur pour de meilleures performances

### 🐛 Corrections de bugs

- **📦 Système de build** : Correction des chemins d'importation des modèles dans les workflows de build
- **📍 Apparition des unités** : Correction des positions d'apparition utilisant les coordonnées des bases alliées et ennemies
- **🎯 Hitboxes des bases** : Centrage des hitboxes pour les bases alliées et ennemies
- **📝 Chemins d'importation** : Correction de divers chemins d'importation de composants IA
- **💰 Économie** : Remplacement de l'or par défaut du joueur par une constante appropriée
- **🗑️ Nettoyage de modèles** : Suppression des fichiers de modèles IA pré-entraînés obsolètes du .gitignore
- **🏝️ Génération d'îles** : Ajustement du taux d'apparition des îles à 0.7%
- **🔍 Pathfinding Scout** : Navigation améliorée (encore en cours de raffinement)
- **🚫 Logique Kamikaze** : Exclusion du Kamikaze lorsque la base ennemie est inconnue
- **🎮 Contrôle joueur** : Désactivation de l'IA pour les unités sélectionnées par le joueur
- **📂 Chemins de fichiers** : Mise à jour des chemins IA Maraudeur pour les versions compilées et non compilées
- **🔄 Pathfinding** : Recalcul du chemin lors de l'assignation de nouveaux objectifs
- **🐍 Python 3.13** : Mise à jour vers Python 3.13 avec ajustements PyInstaller
- **🏗️ Système de build** : Correction des chemins d'archive pour les builds Windows et Linux/Mac

### 🔧 Refactorisation

- remplacement de AIControlledComponent par DruidAiComponent et correction du chemin d'importation d'ArchitectAIComponent
- tri dans les processeurs et composants des IA
- ajout d'un commentaire pour indiquer que la classe AIControlledComponent doit être renommée
- désactivation des logs de débogage dans le processeur IA des troupes rapides
- réajustement des éléments de l'outil de configuration et ajout de messages de changement de langue et redémarrage dans l'outil de configuration

## v0.9.1 (2025-10-28)

### ✨ Nouvelles fonctionnalités

- ajout d'une popup graphique pour signaler les erreurs de crash en jeu
- ajout de la journalisation des performances et mise en cache des chemins dans le processeur IA du Scout
- ajout des tours comme obstacles dans le processeur d'IA Kamikaze
- ajout d'une fenêtre modale de sélection d'équipe pour le mode Joueur vs IA

### 🐛 Corrections de bugs

- ajout de la gestion des collisions pour éviter les positions occupées par d'autres unités
- le message de crash s'affiche bien si le jeu plante maintenant
- correction des IA pour les empecher de tirer n'importe où
- amélioration de la logique d'évitement pour les obstacles dans le processeur IA Kamikaze

### 🔧 Refactorisation

- mise à jour de la version dans le message de rapport de crash
- ajout d'un timer pour le recalcul de chemin par entité dans le processeur IA Kamikaze

## v0.9.0 (2025-10-27)

### ✨ Nouvelles fonctionnalités

- désactiver le brouillard de guerre en mode IA vs IA pour voir tout la carte

### 🐛 Corrections de bugs

- correction du chemin d'importation pour DruidAIProcessor

### 🔧 Refactorisation

- début du 🔧 Refactorisationing et nettoyage des IA

## v0.8.0 (2025-10-27)

### 🤖 Ajout des IA

Cette version marque une avancée majeure dans le développement des intelligences artificielles du jeu. Plusieurs modèles d’IA ont été intégrés, chacun apportant des comportements et des stratégies variées pour enrichir l’expérience de jeu. L’accent a été mis sur l’amélioration du pathfinding, la prise de décision, et l’ajout de fonctionnalités spécifiques à certaines unités. Les IA bénéficient désormais de capacités telles que l’esquive des mines, le tir latéral, et des stratégies de placement de tours plus efficaces. De nombreux tests et ajustements ont permis d’optimiser leur comportement, rendant les parties plus dynamiques et imprévisibles.

Ces ajouts rendent l’IA plus performante, plus réactive et capable de s’adapter à de nombreuses situations de jeu.

### ✨ ✨ Nouvelles fonctionnalités

- **IA** : Intégration de plusieurs modèles d'IA pour enrichir l'expérience de jeu avec des comportements et stratégies variés.
- **IA** : Amélioration du pathfinding, de la prise de décision et ajout de capacités spécifiques (esquive des mines, tir latéral, placement de tours).
- **IA** : Ajout du tir latéral pour les unités.
- **IA** : Intégration de l'IA pour le Léviathan (modèle entraîné sur 100 parties).
- **IA** : L'Architecte peut désormais placer des tours et se déplace correctement vers les îles.
- **IA** : Amélioration de la récupération de l'état de santé et des stratégies de construction de tours.
- **IA** : Intégration de l'IA en jeu avec des méthodes de pathfinding améliorées.
- **IA** : Amélioration de la navigation avec une division des tuiles pour une meilleure précision du pathfinding et ajout de waypoints de débogage.
- **IA** : Implémentation du tir continu pour les unités IA.
- **IA** : Amélioration de la navigation en état de fuite (`FleeState`) grâce à un bonus de position de base sur la carte de danger.
- **IA** : Amélioration de la carte de danger avec le calcul des zones de danger de la base ennemie.
- **IA** : Implémentation d'une portée de tir dynamique et amélioration de la priorisation des attaques.
- **IA** : Ajout de la classe `Barhamus AI` pour l'unité Maraudeur avec gestion du bouclier de mana.
- **IA** : Changement de l'unité de départ de Scout à Maraudeur.
- **IA** : Ajout d'informations de débogage lors de l'entraînement.
- **IA** : Nettoyage amélioré des entités en filtrant les contrôleurs morts ou non existants.
- **IA** : Ajout d'un script de nettoyage automatique des modèles et mise à jour du `.gitignore`.
- **IA** : Ajout de nouvelles fonctionnalités et options.
- **IA** : Suppression du concept de "harcèlement" pour permettre un nombre illimité d'attaquants IA.
- **IA** : Vitesse des unités IA mise à 0 lors de l'attaque pour éviter les mouvements incohérents.
- **IA** : Mise à jour des paramètres de pathfinding et du rendu pour une meilleure navigation.
- **IA** : Ajout de nombreux modèles d'IA, y compris des versions de test et obsolètes pour itération.
- **IA** : Déplacement des fichiers d'IA vers `src` et modification du pathfinding pour un meilleur raisonnement de l'Architecte.
- **IA** : Ajout de la documentation finale pour l'IA.

### 🐞 🐛 Corrections de bugs

- **Dépendances** : Ajout des dépendances manquantes dans le `README.md`.
- **Unités** : Ajout de la vérification du rayon de vision pour le tir des unités.
- **IA** : Rétablissement du processeur IA du Léviathan dans le moteur de jeu.
- **Joueur** : Changement du type d'unité du joueur d'ARCHITECTE à ÉCLAIREUR.
- **Architecte** : Mise à jour de l'exécution des actions pour inclure le composant `SpeArchitect`.
- **IA** : Augmentation de la vitesse de déplacement des unités IA.
- **IA** : Activation de l'utilisation des capacités spéciales.
- **IA** : L'IA cible et attaque désormais la base ennemie ainsi que les unités sur son chemin.
- **IA** : Mise à jour de l'arbre de décision et du pathfinding pour éviter les obstacles.
- **IA** : Remplacement du Q-Learning par un arbre de décision.
- **IA** : Correction des mouvements et amélioration de l'apprentissage (récompenses, ciblage de base).
- **IA** : Correction du processus d'entraînement qui redémarrait de zéro au lieu de reprendre.
- **IA** : L'IA choisit désormais différentes îles pour construire.
- **IA** : Correction de l'angle de l'IA par rapport au chemin choisi.
- **Unités** : Empêchement du tir des unités sur les mines et les alliés.
- **IA** : Ajout du contrôle IA pour les unités Scout de l'équipe alliée.
- **IA** : Amélioration du suivi des coéquipiers blessés en évitant les collisions et les mines.
- **Dépendances** : Mise à jour de `requirements.txt` pour inclure la version de `scikit-learn`.
- **IA** : Mise à jour des imports et des fichiers du modèle `Barhamus AI`.
- **Général** : Ajout et modification de commentaires pour une meilleure compréhension.
- **Général** : Suppression du dossier `sklearn` (inutile et encombrant).
- **Général** : Réparation des explosions de sprites.

### 🧹 🔧 Refactorisation

- **Structure** : Déplacement de fichiers et renommage du processeur du Druide.
- **Assets** : Correction du nom de l'image de la tour de défense ennemie.
- **Code** : Suppression de la traduction inutilisée pour l'Architecte Q-Learning.
- **Code** : Simplification de fonctions, optimisation et mise à jour des commentaires.
- **Code** : Mise à jour des noms de fonctions en `camelCase`.
- **IA** : Suppression de toutes les tentatives d'IA précédentes.
- **IA** : Remplacement de `SKLearn` par un simple `min-max`.
- **IA** : Suppression de l'état `join_druid` (trop similaire à `follow_druid`) et de l'état `preshot` (trop ambitieux).
- **Rendu** : Nettoyage des fichiers de rendu.

## v0.7.1 (2025-10-13)

### 🐞 🐛 Corrections de bugs

- Changement de la manière d'obtenir le numéro de version pour corriger le "vunknown" dans les versions compilées
- Correction de la description du composant de base

## v0.7.0 (2025-10-12)

### ✨ ✨ Nouvelles fonctionnalités

- Ajout du système de récompenses de combat
- Améliorations de performance et système de caméra
- Taille de la map doublée et ajustement de la sensibilité de la caméra avec Ctrl
- Ajout du numéro de version et d'indicateurs de mode développeur
- Ajout de la construction de tours pour l'Architecte
- Ajout du système de vision et du brouillard de guerre avec gestion de la visibilité des unités

### 🐞 🐛 Corrections de bugs

- Les nuages réapparaissent désormais sur la carte, les ressources apparaissent sur les bords des îles, et la fenêtre debug tient sur l'écran
- Correction du tir multiple sur les côtés et l'avant
- Fin de l'inflation des prix des unités dans la faction ennemie
- Le brouillard de guerre est réinitialisé quand on relance une partie et le bouton continuer du menu quitter fonctionne correctement

### 🧹 🔧 Refactorisation

- Amélioration de la lisibilité et de la structure du code des bandits
- Ajout des fonctionnalités bandits et triche de vision illimitée en mode debug
- Externalisation des récompenses de combat à part de la gestion de la vie
- Renommage de FlyingChestManager en FlyingChestProcessor et mise à jour des références dans le code et la documentation
- Remplacement de StormManager par StormProcessor dans le code et la documentation
- Fusion de RecentHitsComponent dans RadiusComponent
- Deuxième phase d'optimisation du jeu notamment le brouillard de guerre et le rendu des sprites et ajout d'un profiler pour analyser les performances du jeu
- Optimisation des collisions avec un hachage spatial et amélioration du rendu des frames
- Correction de l'aide en jeu
- Suppression des boosts globaux d'attaque et de défense dans le code et la documentation
- Suppression des bindings inutilisés

## v0.6.0 (2025-10-06)

### ✨ ✨ Nouvelles fonctionnalités

- Ajout d’un menu en jeu avec options **Reprendre**, **Paramètres** et **Quitter**.

### 🧹 🔧 Refactorisation

- Correction de l’indentation de la clé `spawn_bandits` dans les fichiers de traduction.

---

## v0.5.1 (2025-10-06)

### 🐞 🐛 Corrections de bugs

- Création automatique d’un fichier de configuration avec valeurs par défaut si manquant.  
- Correction du fichier de localisation qui pouvait casser **Galad Settings Tool** sur Windows.  
- Amélioration du chemin d’exécution et des messages d’avertissement dans `galad_config.py`.

---

## v0.5.0 (2025-10-05)

### ✨ ✨ Nouvelles fonctionnalités

- Changement de l’unité de départ : **Druide → Éclaireur**.  
- Ajout de descriptions aux tours dans l’**Action Bar**.  
- **ProjectileCreator** : ajout de projectiles de soin pour les druides.  
- **Système complet de tours de défense** avec projectiles, notifications et capacités spéciales.  
- Implémentation du **système de ressources d’île** (`islandResources`).  
- Ajout du **Kraken Event**, des tentacules inactives et du **Storm Event**.  
- Ajout d’un **menu de debug enrichi** (spawn de bandits, gestion d’événements, ressources, or, etc.).  
- Intégration d’un **gestionnaire de résolutions personnalisées** et création de **Galad Options Tool**.  
- Ajout de nouvelles capacités spéciales : **Leviathan**, **Maraudeur**, **Scout**, **Barhamus**, **Zasper** et **Draupnir** (cooldowns, effets visuels, logique unifiée).  
- Ajout de sprites pour les unités spéciales (Kamikaze, projectiles ennemis, etc.).  
- Intégration de la gestion de l’or, de la boutique et des sélections d’unités.  
- Implémentation du **système d’affichage centralisé** (résolutions, fenêtres).  
- Ajout du fichier `help_en.md` et de traductions supplémentaires pour la fin de partie.

### 🐞 🐛 Corrections de bugs

- Nombreux 🐛 Corrections de bugss sur les collisions, projectiles, mines, événements et affichage.  
- Les projectiles traversent les îles, explosent à l’impact et disparaissent à la limite de la carte.  
- Les mines interagissent désormais correctement avec toutes les factions.  
- Correction du zoom par défaut, des cooldowns d’UI et de l’affichage de l’or.  
- Réduction du taux d’apparition du Kraken et équilibrage du spawn des tempêtes.  
- Ajustement de nombreux fichiers de composants (`bandits`, `storm`, `collision`, `player`, `health`, etc.).  
- Les paramètres audio enregistrés sont désormais pris en compte au lancement du jeu.  
- Correction des traductions (`options.custom_marker`, messages de fin de partie, etc.).  
- Fenêtre à nouveau redimensionnable et ajustement du zoom caméra.

### 🧹 🔧 Refactorisation

- 🔧 Refactorisationisation du système de **BaseManager** (fusionné dans `BaseComponent`).  
- Réorganisation complète des composants pour plus de clarté.  
- 🔧 Refactorisation du **gold management**, intégration dans `playerComponent`.  
- Suppression des anciens composants et du code de test.  
- Nettoyage général du code, constantes gameplay unifiées.  
- Amélioration du **UI handling**, des key bindings et du système d’options.

---

## v0.4.5 (2025-10-02)

### 🐞 🐛 Corrections de bugs

- Correction de l’initialisation de `affected_unit_ids` dans le constructeur.

---

## v0.4.4 (2025-10-02)

### 🐞 🐛 Corrections de bugs

- Les projectiles ne disparaissent plus lorsqu’ils touchent une île.

---

## v0.4.3 (2025-10-02)

### 🐞 🐛 Corrections de bugs

- Les mines ne peuvent plus être détruites par les projectiles.

### 🧹 🔧 Refactorisation

- Intégration du gestionnaire de sprites pour le chargement des images de terrain et ajout de constantes de sprite.

---

## v0.4.2 (2025-10-02)

### 🧹 🔧 Refactorisation

- Centralisation des constantes de **modales**, **santé des bases**, **boutique** et **gameplay**.  
- Ajout d’un système de gestion des sprites avec initialisation et préchargement.  
- 🔧 Refactorisationisation complète de l’architecture **ECS** pour une meilleure maintenance.

---

## v0.4.1 (2025-10-01)

### 🐞 🐛 Corrections de bugs

- Suppression d’un fichier de test après vérification des hooks.

---

## v0.4.0 (2025-10-01)

### ✨ ✨ Nouvelles fonctionnalités

- Implémentation du **système de gestion de bases** et intégration au gameplay.

### 🧹 🔧 Refactorisation

- Modularisation de `game.py` en plusieurs classes.  
- Conversion des fichiers audio de **WAV → OGG** pour qualité et taille optimisées.

---

## v0.2.1 (2025-10-01)

### 🐞 🐛 Corrections de bugs

- Ajout du support du chemin PyInstaller pour les builds Windows.

---

## v0.2.0 (2025-10-01)

### ✨ ✨ Nouvelles fonctionnalités

- Ajout du retour d’entité dans `unitFactory`.

### 🧹 🔧 Refactorisation

- **Options** : désactivation temporaire des résolutions personnalisées.  
- Mise à jour des conseils de résolution pour éviter les erreurs d’affichage.

---

## v0.1.2 (2025-10-01)

### ✨ ✨ Nouvelles fonctionnalités

- Ajout du **logo** dans l’interface principale.  
- Création de la **documentation technique** et début de la **doc utilisateur**.  
- Ajout du **système de boutique**, d’achat d’unités et de gestion de factions via la classe `Team`.  
- Mise en place du **système de localisation** (FR/EN) et des traductions pour tous les menus.  
- Ajout de la **barre de vie**, de la **barre d’action**, et des contrôles améliorés.  
- Intégration du **système de résolution d’écran**, du redimensionnement et de la sauvegarde des paramètres.  
- Ajout des **événements de debug**, de l’aide en jeu (`help.md`), et de nouveaux easter eggs dans le menu.  
- Début du **système de Vignes** pour le druide.  
- Création du **mouvement**, des collisions, des projectiles et des entités de base.

### 🐞 🐛 Corrections de bugs

- Correction de nombreux bugs d’affichage, collisions, audio et configuration.  
- Ajustements sur les traductions, résolutions et paramètres de la fenêtre.  
- Correction du centrage caméra, des modales et de l’aide multilingue.  
- Nettoyage des imports, suppression de fichiers inutiles et correctifs mineurs sur le gameplay.

### 🧹 🔧 Refactorisation

- Externalisation des composants UI (`settings_ui_component.py`).  
- 🔧 Refactorisationisation de la configuration (`settings.py`) et de la caméra (`Camera`).  
- Nettoyage général, renommage cohérent des fichiers et suppression des variables globales.  
- Passage des options Tkinter → modale Pygame.  
- Réorganisation de la documentation et des assets.  
- Amélioration de la structure du code et du rendu des sprites.

### ⚡ Perf

- Suppression automatique des projectiles en bord de carte pour éviter leur persistance.  
- Ajout d’un component dédié aux projectiles pour un traitement plus léger.
