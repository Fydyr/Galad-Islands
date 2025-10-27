# 🧾 Changelog

## v0.8.0 (2025-10-27)

### Feat

- ajout esquive des mines
- **ai**: ajout du tir latéral
- ajout du model d'ia el plus récent
- ajout d'un modèle d'ia ne fonctionnant pas réellement
- ajout de modèles d'ia (qui sont malheureusement obsolète)
- **ai**: ajout d'information sur le print lors de l'entrainement de l'ia
- add model ai for leviathan (100 games simulated)
- add test reward for ai leviathan
- add training ai
- add ai leviathan
- added  better health game_state retrieval, and better tower building strategies
- Architect can place towers
- AI now moves correctly to island
- add more options to AI
- basic AI (not fully implemented)
- added training to AI model
- move ia to src, and modify pathfinding and decisionTree for better architect reasoning.
- removed old ai and added new pathfinding methods
- test new AI
- AI pathfinding training
- upgraded AI (without much success)
- Integration of AI ingame
- basic architect AI
- modify doc
- final ia with doc
- enhance entity cleanup by filtering out dead or non-existent controllers
- maybe last version of ai, detail : - add base position bonus to danger map for improved flee state navigation - 0 speed when AI attack to avoid no sence mouvement - delete "harass" (no max number AI attack)
- enhance danger map with enemy base danger zone calculations
- implement dynamic shooting range and improve attack prioritization for AI units
- save
- update pathfinding settings and rendering for improved AI navigation
- add more debug
- goto normalisé
- ajout des waypoint dans le debug
- division pour l'ia des cases (tiles) en 4 pour une meilleurs précision du pathfinding
- mise en place de debug pour une meilleurs compréhension
- quelques comporrtement bizarre mais légère avancé
- tir continu
- save
- v1
- décision pré code
- configuration.md, requirements.md, druidAiController.py, init.py, positioningBehavior.py, vineBehavior.py, actionEvaluator.py, stateScorer.py, astarNavigator.py,  gameStateAnalyzer.py,
- add automatic model cleanup script and update .gitignore
- ajouter nouvelle fonctionnalité
- ajouter nouvelle fonctionnalité
- Add Barhamus AI class for Maraudeur unit with shield mechanics
- Change starting unit from Scout to Maraudeur
- Implement Barhamus AI with targeting and mana shield mechanics

### Fix

- ajouter des dépendances manquantes dans le README
- ajouter la vérification du rayon de vision pour le tir des unités
- rétablissement du processeur IA Léviathan au moteur de jeu
- change player unit type from ARCHITECT to SCOUT
- update action execution to include SpeArchitect component
- mise à jour de la vitesse de l'ia pour le déplacement (trop lente avant)
- utilisation de la capacité spécial
- **ai**: L'ia va sur la base ennemie et tire dessus ainsi que sur les ennemies
- **ai**: mise à jour de l'arbre de décision
- **ai**: mise à jour du pathfinding pour éviter les obstacles
- **ai**: Retrait du système d'apprentissage par Q-Learning et changement par un arbre de décision
- mise à jour des informations sortie sur le terminal lors de l'arrêt de l'entrainement de l'ia
- mise à jour de l'entrainement de l'ia pour qu'elle apprend plus vite
- **ai**: correction pour le mouvement de l'ia
- mise à jour des rewards et du sysyème pour aller vers la base adverse
- changement de modèle d'ia car non fonctionnel
- mise à jour du model d'ia
- mise à jour sur les rewards
- **ai**: mise à jour des rewards
- mise à jour du reward pour les event + forcer vers la base ennemie
- l'ia ne fonctionnais pas fonctionner pour les alliés + amélioration sur l'entrainement pour entrainer l'ia allié
- mise à jour de l'entrainement de l'ia
- ajout de pathfinding via le A* + ajout de l'ia pour l'unité allié
- modification du fichier de model (recommencer de 0 le model d'ia)
- update ai leviathan model
- update epsilon for ai
- chemin fixé
- **ai**: train ai leviathan
- training ai
- quand on relançais l'entrainement il recommençais de zéro au lieu de reprendre là où il en était et effaçais donc entièrement l'ia
- AI now choosing different islands to build on
- angle of the AI to chosen path and start of building placing
- change ai path
- Added processors to training
- regression of non working ai training
- empêcher le tir des unités sur les mines et les alliés
- ajout du contrôle IA pour les unités Scout dans l'équipe allié et mise à jour des processeurs IA
- ajout et modifications des commentaires
- suppression du dossier sklearn (inutile et encombrant), réparation des explosions de sprites.
- amélioration de l'IA, elle suit son coéquipier quand il est blessé sans prendre de collisions et en évitant les mines
- directions de l'IA
- astarNavigator.py, gameStateAnalyzer.py
- update requirements.txt to include scikit-learn version
- update Barhamus AI model files to latest versions
- update Barhamus AI model files to latest versions
- update Barhamus AI import to new module

### Refactor

- déplacement de fichier
- correction du nom de l'image de la tour de défense ennemi
- remove unused translation for Q-Learning Architect
- simplification de fonction & optimisation
- mise à jour des fonctions en camelCase
- mise à jour des commentaires
- rename file
- removed all previous AI attemps
- removed SKLearn and added simple min-max
- nettoyage des fichiers de rendu
- renommage du processeur du Druid (anciennment un nom générique)
- delete of join_druid bcs too similar with follow_druid delete preshot bcs too ambitious

### Perf

- **ai**: optimisation de l'entrainement de l'ia

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
