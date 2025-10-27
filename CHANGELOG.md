# 🧾 Changelog

## v0.8.0 (2025-10-27)

### 🤖 Ajout des IA

Cette version marque une avancée majeure dans le développement des intelligences artificielles du jeu. Plusieurs modèles d’IA ont été intégrés, chacun apportant des comportements et des stratégies variées pour enrichir l’expérience de jeu. L’accent a été mis sur l’amélioration du pathfinding, la prise de décision, et l’ajout de fonctionnalités spécifiques à certaines unités. Les IA bénéficient désormais de capacités telles que l’esquive des mines, le tir latéral, et des stratégies de placement de tours plus efficaces. De nombreux tests et ajustements ont permis d’optimiser leur comportement, rendant les parties plus dynamiques et imprévisibles.

Ces ajouts rendent l’IA plus performante, plus réactive et capable de s’adapter à de nombreuses situations de jeu.

### ✨ Feat

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

### 🐞 Fix

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

### 🧹 Refactor

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

### 🐞 Fix

- Changement de la manière d'obtenir le numéro de version pour corriger le "vunknown" dans les versions compilées
- Correction de la description du composant de base

## v0.7.0 (2025-10-12)

### ✨ Feat

- Ajout du système de récompenses de combat
- Améliorations de performance et système de caméra
- Taille de la map doublée et ajustement de la sensibilité de la caméra avec Ctrl
- Ajout du numéro de version et d'indicateurs de mode développeur
- Ajout de la construction de tours pour l'Architecte
- Ajout du système de vision et du brouillard de guerre avec gestion de la visibilité des unités

### 🐞 Fix

- Les nuages réapparaissent désormais sur la carte, les ressources apparaissent sur les bords des îles, et la fenêtre debug tient sur l'écran
- Correction du tir multiple sur les côtés et l'avant
- Fin de l'inflation des prix des unités dans la faction ennemie
- Le brouillard de guerre est réinitialisé quand on relance une partie et le bouton continuer du menu quitter fonctionne correctement

### 🧹 Refactor

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

### ✨ Feat

- Ajout d’un menu en jeu avec options **Reprendre**, **Paramètres** et **Quitter**.

### 🧹 Refactor

- Correction de l’indentation de la clé `spawn_bandits` dans les fichiers de traduction.

---

## v0.5.1 (2025-10-06)

### 🐞 Fix

- Création automatique d’un fichier de configuration avec valeurs par défaut si manquant.  
- Correction du fichier de localisation qui pouvait casser **Galad Settings Tool** sur Windows.  
- Amélioration du chemin d’exécution et des messages d’avertissement dans `galad_config.py`.

---

## v0.5.0 (2025-10-05)

### ✨ Feat

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

### 🐞 Fix

- Nombreux correctifs sur les collisions, projectiles, mines, événements et affichage.  
- Les projectiles traversent les îles, explosent à l’impact et disparaissent à la limite de la carte.  
- Les mines interagissent désormais correctement avec toutes les factions.  
- Correction du zoom par défaut, des cooldowns d’UI et de l’affichage de l’or.  
- Réduction du taux d’apparition du Kraken et équilibrage du spawn des tempêtes.  
- Ajustement de nombreux fichiers de composants (`bandits`, `storm`, `collision`, `player`, `health`, etc.).  
- Les paramètres audio enregistrés sont désormais pris en compte au lancement du jeu.  
- Correction des traductions (`options.custom_marker`, messages de fin de partie, etc.).  
- Fenêtre à nouveau redimensionnable et ajustement du zoom caméra.

### 🧹 Refactor

- Refactorisation du système de **BaseManager** (fusionné dans `BaseComponent`).  
- Réorganisation complète des composants pour plus de clarté.  
- Refactor du **gold management**, intégration dans `playerComponent`.  
- Suppression des anciens composants et du code de test.  
- Nettoyage général du code, constantes gameplay unifiées.  
- Amélioration du **UI handling**, des key bindings et du système d’options.

---

## v0.4.5 (2025-10-02)

### 🐞 Fix

- Correction de l’initialisation de `affected_unit_ids` dans le constructeur.

---

## v0.4.4 (2025-10-02)

### 🐞 Fix

- Les projectiles ne disparaissent plus lorsqu’ils touchent une île.

---

## v0.4.3 (2025-10-02)

### 🐞 Fix

- Les mines ne peuvent plus être détruites par les projectiles.

### 🧹 Refactor

- Intégration du gestionnaire de sprites pour le chargement des images de terrain et ajout de constantes de sprite.

---

## v0.4.2 (2025-10-02)

### 🧹 Refactor

- Centralisation des constantes de **modales**, **santé des bases**, **boutique** et **gameplay**.  
- Ajout d’un système de gestion des sprites avec initialisation et préchargement.  
- Refactorisation complète de l’architecture **ECS** pour une meilleure maintenance.

---

## v0.4.1 (2025-10-01)

### 🐞 Fix

- Suppression d’un fichier de test après vérification des hooks.

---

## v0.4.0 (2025-10-01)

### ✨ Feat

- Implémentation du **système de gestion de bases** et intégration au gameplay.

### 🧹 Refactor

- Modularisation de `game.py` en plusieurs classes.  
- Conversion des fichiers audio de **WAV → OGG** pour qualité et taille optimisées.

---

## v0.2.1 (2025-10-01)

### 🐞 Fix

- Ajout du support du chemin PyInstaller pour les builds Windows.

---

## v0.2.0 (2025-10-01)

### ✨ Feat

- Ajout du retour d’entité dans `unitFactory`.

### 🧹 Refactor

- **Options** : désactivation temporaire des résolutions personnalisées.  
- Mise à jour des conseils de résolution pour éviter les erreurs d’affichage.

---

## v0.1.2 (2025-10-01)

### ✨ Feat

- Ajout du **logo** dans l’interface principale.  
- Création de la **documentation technique** et début de la **doc utilisateur**.  
- Ajout du **système de boutique**, d’achat d’unités et de gestion de factions via la classe `Team`.  
- Mise en place du **système de localisation** (FR/EN) et des traductions pour tous les menus.  
- Ajout de la **barre de vie**, de la **barre d’action**, et des contrôles améliorés.  
- Intégration du **système de résolution d’écran**, du redimensionnement et de la sauvegarde des paramètres.  
- Ajout des **événements de debug**, de l’aide en jeu (`help.md`), et de nouveaux easter eggs dans le menu.  
- Début du **système de Vignes** pour le druide.  
- Création du **mouvement**, des collisions, des projectiles et des entités de base.

### 🐞 Fix

- Correction de nombreux bugs d’affichage, collisions, audio et configuration.  
- Ajustements sur les traductions, résolutions et paramètres de la fenêtre.  
- Correction du centrage caméra, des modales et de l’aide multilingue.  
- Nettoyage des imports, suppression de fichiers inutiles et correctifs mineurs sur le gameplay.

### 🧹 Refactor

- Externalisation des composants UI (`settings_ui_component.py`).  
- Refactorisation de la configuration (`settings.py`) et de la caméra (`Camera`).  
- Nettoyage général, renommage cohérent des fichiers et suppression des variables globales.  
- Passage des options Tkinter → modale Pygame.  
- Réorganisation de la documentation et des assets.  
- Amélioration de la structure du code et du rendu des sprites.

### ⚡ Perf

- Suppression automatique des projectiles en bord de carte pour éviter leur persistance.  
- Ajout d’un component dédié aux projectiles pour un traitement plus léger.
