## v0.6.0 (2025-10-06)

### Feat

- ajouter un menu en jeu avec des options pour reprendre, paramètres et quitter

### Refactor

- corriger l'indentation de la clé 'spawn_bandits' dans les traductions

## v0.5.1 (2025-10-06)

### Fix

- améliorer la gestion des fichiers de configuration manquants en créant un fichier avec des valeurs par défaut
- mise à jour du fichier localisation qui pouvait casser Galad Settings Tool sur Windows
- corriger le chemin d'exécution et améliorer les messages d'avertissement dans galad_config.py

## v0.5.0 (2025-10-05)

### Feat

- Change starting unit from Druid to Scout
- Add descriptions to towers in ActionBar
- **projectileCreator**: added healing to druids
- help_en.md
- ajout de la fonctionnalité de spawn de bandits dans le menu de debug
- création de Galad Options Tool à partir du gestionnaire de résolutions personnalisé
- ajout d'un gestionnaire de résolutions personnalisées et intégration dans les options
- ajout contrôle debug pour ressources d'îles + améliorations UX
- système de debug enrichi avec contrôles d'événements
- added sprite affiliation method to sprite manager and fix tentacle sprites
- Added kraken event with idle tentacles
- **islandResources**: ajout du gestionnaire et du composant pour les ressources d'île
- **sprites**: ajout de l'image du kamikaze ennemi
- **towers**: système complet de tours de défence avec projectiles et notifications
- implémentation complète du système de tours, ajout d'un debug menu et création de fenetre générique à utiliser in game
- ajout des traductions pour les messages de fin de partie et les noms des bases fix: amélioration de la vérification des zones de spawn pour éviter les chevauchements refactor: ajout de la classe pour gérer les types de bases dans BaseManager
- les bases attaquables et gestion de fin de partie
- **event**: add storm event
- réécriture de la capacité spéciale du Lévithan
- ajout du sprite de boule de feu pour les projectiles de la faction ennemi
- fix flying chest management system with spawning and collision handling
- Implement centralized resource management and tile definitions
- implémentation de la capacité spéciale du Leviathan
- implémentation de la capacité spécial du Maraudeur
- implémentation de la capacité spécial du Scout (déjà codé précédamment)
- changement du projectile par une balle et ajout d'une explosion quand touché
- refactorisation du système de capacités spéciales avec nommage cohérent
- ajout des capacités spéciales de Barhamus, Zasper et Draupnir avec gestion des cooldowns et effets visuels (en attente d'approbation pour les implémenter en jeu)
- update unit configurations and improve shop functionality, add mouvement and selection
- ajout de fonctions utilitaires pour la gestion de l'or des joueurs et intégration dans la boutique et l'action bar

### Fix

- tentative de fix le fait que les bandits spawent mid-life (marche pas)
- collisionProcessor.py
- ajout du kamikase dans le help.md + image
- la fenetre est à nouveau redimensionable
- no bullets for druids and architects
- banditsProcessor.py
- merge
- bandit event
- main.py, game.py, eventProcessor.py, banditsProcessor.py
- correction de l'indentation pour la clé 'options.custom_marker' dans les traductions
- event chance and cooldown
- réduction du taux d'apparition du kraken
- **handleHealth**: ajouter protection pour les mines afin d'ignorer les dégâts feat(projectile) : tout ce qui est touché par le projectile a un impact d'explosion refactor(projectile): changement du sprite d'impact d'explosion
- **stormManager**: correction du taux de spawn des tempêtes à 5%
- mise à jour de la logique de distribution d'or dans le modal de débogage pour inclure l'équipe active
- les message de fin de partie ne sont plus hardcodé
- suppression des unités ennemis créé pour les tests
- **storm**: update proba spawn storm
- amélioration de l'affichage de l'or et des coûts dans la boutique avec des symboles monétaires compatibles
- system.md, game.py
- game.py
- repaired vine events according to game design, and added vine sprite
- CapacitiesSpecialesProcessor.py, VineProcessor.py
- le cooldown de la capacité spécial ne s'affichait pas sur l'action bar
- les mines disparait visuellement
- ajuster la position d'ancrage du scout ennemi pour éviter de se retrouver dans la base et plus bouger
- ajouter une équipe neutre aux mines pour permettre des collisions avec toutes les entités
- corriger l'identifiant d'équipe des mines pour permettre les collisions appropriées pour toutes les entités
- définir le facteur de zoom par défaut à ZOOM_MIN dans Camera et lors de l'initialisation de la carte
- la faction ennemi est désormais affecté par les mines
- les projectiles peuvent passer à travers les iles et ne ralentit plus en passant les nuages
- added projectileComponent to all launched projectiles
- les projectiles meurt désormais à la limite de la carte
- unitType wrong name and moved to constants
- unitType correct properties
- le jeu prend en compte du volume audio enregistré au lancement
- la pièce d'or s'affiche sur l'action bar
- speArchitectComponent.py, unitFactory.py, CpacitiesSpecialesProcessor.py, playerControlProcessor.py
- gestion des collisions entre projectiles et mines dans CollisionProcessor
- attackComponent.py, baseComponent.py, canCollideComponent.py, classeComponent.py, eventsComponent.py, healComponent.py, healthComponent.py, playerComponent.py, playerSelectedComponent.py, positionComponent.py, projectileComponent.py, radiusComponent.py, ressourcesComponent.py, spriteComponent.py, teamComponent.py, velocityComponent.py, isVinedComponent.py, speArchitectComponent.py, speBarhamusComponent.py, speDraupnirComponent.py, speDruidComponent.py, speZasperComponant.py, VineComponent.py, banditsComponent.py, flyChestComponent.py, krakenComponent.py, stormComponent, unitFactory.py
- currentSpeed into current_speed
- isVinedComponent.py, speArchitectComponent.py, speBarhamusComponent.py, speDraupnirComponent.py, speDruidComponent.py, speZasperComponent.py, VineComponent.py
- system.md, unitFactory.py, projectileCreator.py, collisionProcessor.py, playerControlProcessor.py

### Refactor

- intégrer le gestionnaire d'affichage pour une gestion centralisée des résolutions et des fenêtres
- suppression des fonctions et callbacks liés aux bâtiments dans la boutique
- déplacement des sprites d'événements, correction de l'emplacement du kamikaze et mise à jour du gestionnaire de sprites
- Démantèlement de BaseManager et intégration dans BaseComponent
- **storm**: update to camelCase
- **player**: refactor gold management and integrate player component in shop
- update sprite
- déplacement du stormComponent
- Suppresion des anciens composants qui étaient conservés au cas où
- restructure component folders to enhance code clarity and maintainability
- retrait de la catégorie bâtiments de la boutique et mise à jour des tests
- input handling and UI components for improved key binding management
- réimplémentation des constantes de gameplay et de l'utilisation du sprite manager

## v0.4.5 (2025-10-02)

### Fix

- corriger l'initialisation de affected_unit_ids dans le constructeur

## v0.4.4 (2025-10-02)

### Fix

- les projectiles ne disparaissent pas quand ils "cognent" une ile

## v0.4.3 (2025-10-02)

### Fix

- les mines sont pas censés être détruites par les projectiles

### Refactor

- intégrer le gestionnaire de sprites pour le chargement des images de terrain et ajouter de nouvelles constantes de sprite

## v0.4.2 (2025-10-02)

### Refactor

- ajouter des constantes pour la boutique et connection avec le nouveau gestionnaire de sprites afin d'améliorer la maintenance et l'interface
- centraliser les constantes de modales et de santé des bases pour une meilleure maintenance
- ajout de constantes de gameplay pour améliorer la maintenance et l'équilibrage
- ajouter un système de gestion des sprites avec initialisation et préchargement
- refactorisation complète de l'architecture ECS

## v0.4.1 (2025-10-01)

### Fix

- remove test file after hook testing

## v0.4.0 (2025-10-01)

### Feat

- implement base management system and integrate into game mechanics

### Refactor

- restructure game.py into modular classes
- **audio**: replace WAV files with OGG format for improved audio quality and space

## v0.2.1 (2025-10-01)

### Fix

- add PyInstaller resource path handling for Windows builds

## v0.2.0 (2025-10-01)

### Feat

- added retrun entity on unitFactory

### Refactor

- **options**: commenter la section de résolution personnalisée pour le retirer tant que c'est pas supporté
- **options**: mettre à jour les conseils de résolution pour éviter les problèmes d'affichage

## v0.1.2 (2025-10-01)

### Feat

- **logo**: ajout du logo sur le haut de l'app
- **documentation**: ajout de nouveaux sprites et logo pour la documentation utilisateur
- **documentation**: création et début de la documentation technique
- **documentation**: Début de documentation utilisateur (généré par Copilot, à revoir évidamment)
- **boutique**: add spawn system and unit type mapping for unit purchases
- **team**: ajout de la classe Team pour gérer les camps (ALLY, ENEMY)
- **boutique**: enhance shop functionality with localization and asset mapping
- added gold per playerComponent, and added return value to unitFactory
- **localization**: ajout de la gestion des langues et mise à jour des labels des boutons dans le menu principal
- **localization**: ajout de traductions pour les éléments de la boutique et mise à jour des descriptions des unités
- **localization**: ajout d'un tooltip pour le bouton de camp et utilisation des traductions pour les noms de camp
- **localization**: ajout de traductions pour les options et messages système en français et anglais
- **docs**: ajout de la gestion multilingue pour les documents d'aide, crédits et scénario
- **localization**: ajout partielle des traductions pour l'interface de la boutique et des unités
- **localization**: ajout du système de localisation avec traductions en français et anglais
- implement enhanced shop system with improved UI and item management
- added unit factory with units
- refactor settings import paths and add projectile component
- **shop**: add tab icons and improve item display logic
- **movement**: améliorer les mouvements avec des contraintes pour ne pas sortir de la map
- implement shop system with enhanced UI and item management
- ajout barre de vie
- added attack handling and entity death
- ajouter la gestion des résolutions dans le menu des options
- ajouter un délai de sauvegarde pour le redimensionnement de la fenêtre
- sauvegarder la résolution dans la configuration lors du redimensionnement
- Collisions on ennemies
- **action-bar**: ajout du type d'action OPEN_SHOP et des configurations d'unités ; implémentation de la fonctionnalité de bascule de la boutique
- ajouter nouvelle fonctionnalité
- ajout de la possibilité de changer la sensibilité de la caméra
- **game**: ajout de l'aide disponible pendant la partie
- ajout d'une fonction qui affiche les informations de debug
- **mapComponent**: ajustement de la taille des éléments de la carte et optimisation du placement
- added sprite to bullet
- **help.md**: ajout des images pour le help.md
- **ui**: implémenter ActionBar pour améliorer l’interaction de jeu
- **main.py**: ajouter de nouvelles astuces (encore) au menu
- **main.py**: ajouter de nouvelles easter egg au menu
- **main.py**: ajouter un système de changement automatique des astuces dans le menu
- **main.py**: ajouter des easter egg au menu
- added player movement
- added movement vector and basic sprite rendering
- Sprite display on screen
- **scénario & help**: ajout de l'intégration de .md pour afficher le contenu via une modale
- Update game.py to start a game loop
- Modify troopsComponent, main and game
- **Vine**: add processor and component for vines for the druid
- add movementProcessor
- preparing main for game start
- add heal.py
- add base.py
- add ressources
- component bullet.py
- add background game

### Fix

- **documentation**: mise à jour des prérequis système et clarification des instructions d'installation
- **boutique**: improve fallback handling for spawn system and unit type mapping
- game.py, spriteComponent.py, collisionProcessor.py
- **menu**: ajouter un titre à la fenêtre principale
- collisionProcessor.py, movementProcessor.py
- **collision**: utilisation des dimensions originales pour les collisions afin d'éviter ques les entités prennent des dégats
- **help.md + vers en**: retraduction du fichier d'aide en anglais + réinsertion des images manquante
- **help**: l'aide en jeu s'ouvrait en français peu importe les paramètres choisis
- **audio**: le jeu se lançait sans tenir compte des paramètres audio enregistrés
- velocityComponent.py, collisionProcessor.py, movementProcessor.py
- collisionProcessor.py, game.py
- **afficher modale**: simplification de la fonction +  fix bug fonction
- projectileCreator.py, playerControlProcessor.py, controls.py
- limiter la taille de zoom et gérer les erreurs de redimensionnement pour "la mort" des entités
- playerControlProcessor.py
- amélioration de la gestion de l'affichage lors du changement de mode de fenêtre
- correction du titre de la section Graphismes à Contrôles dans la modale des options
- ajustement de la gestion de la fenêtre pour Windows
- ajustement de la position de la fenêtre pour les plateformes non-Windows
- correction tips
- help.md, playerControlProcessor.py, controls.py
- functional cooldown
- radiusComponent.py, playerControlProcessor.py
- **settings**: ajustement du taux d'îles génériques et ajout du taux de nuages
- **settings**: correction des taux de mines et d'îles génériques
- scaling of sprite
- **modale**: réglage bug sur l'affichage des images
- images
- modifcations of bullets images
- **camera**: centrage de la map durant le zoom
- **options_window**: appliquer les changements de volume et de mode immédiatement
- **renderingProcessor**: added camera again
- teamComponent.py, projectileCreator.py, playerControlProcessor.py
- **renderingProcessor**: updated sprite and rendering processeur
- **options_window.py**: supprimer une instruction obsolète sur le défilement du menu
- **config.py**: corriger le nom du développeur Cailliau dans la configuration
- correction de l'hyperlien cassé dans le README
- Correction d'une erreur d'orthographe dans les crédits
- **options_window.py**: indentation mal faite
- **options**: ajouter un commentaire sur la nécessité d'interactions dans le fichier de la modale des options
- **game**: nettoyer les entités et processeurs avant de créer de nouveaux lors que on relance le jeu
- **rendering**: Les entités gèrent la caméra, il se déplace plus avec la caméra
- **options**: mettre à jour les messages d'information sur les changements de résolution et d'autres modifications
- **imports**: mise à jour des chemins d'importation pour le module settings
- **main**: améliorer la gestion du mode d'affichage et retirer le bouton 'Windowed'
- **game**: améliorer la gestion de la fenêtre et ajouter des contrôles de caméra
- playerControlProcessor.py, creation of direInProcessor.py
- rendering issue
- playerControlProcessor.py
- playerControlProcessor.py, controls.py, baseComponent.py
- **playerControler**: added src to import
- amélioration affichage / menu responsive
- playerControlProcessor.py, controls.py
- full movement and sprite display
- playerControlProcessor.py, controls.py
- spe barhamus
- game start in menu
- menu
- sprite loading
- game.py import
- **crédits**: changement des crédits via tkinter par une modale
- **menu**: mise à jour chemin pour les son
- **menu**: mise à jour de l'affichage de la modale
- game start in menu
- Components inits
- **afficher_grille**: initialiser le cache de la mer avec une image valide pour éviter les problèmes de type
- **apply_resolution**: validation des résolutions fournies et gestion des erreurs
- **vine**: add is_vined & change the velocity of the troop when he vined
- **vineProcessor**: add statement to the vine
- suppression de fichiers

### Refactor

- **ui**: externalisation des composants UI des options dans settings_ui_component.py
- **settings**: Refactorisation de la gestion de la configuration dans settings.py
- **map**: externalisation de la classe Camera
- **config**: suppression du fichier de configuration qui ne servait à rien
- **boutique**: simplification de l'importation de la localisation en supprimant le fallback
- **menu**: déplacement de fonction et simplification du main
- **action_bar**: utilisation de Team pour le changement de camp et la logique associée
- **boutique**: suppression de l'ancien code des boutiques
- **boutique**: fusion des deux fichiers boutique et implémentation du changement de faction
- **documentation**: tri de la documentation dans un dossier dédié
- **assets**: changement de l'emplacement des images qui était mal rangé dans le code
- **sprite**: gestion manuelle du rendu pour améliorer l’ordre d’affichage et le contrôle
- déplacement fichiers
- rename file
- déplacement fichier + rename dossier
- suppression des variables globales SCREEN_WIDTH/SCREEN_HEIGHT et utilisation des dimensions actuelles dans la gestion de la fenêtre
- nettoyage du code
- changement du mode de fenêtre par défaut en plein écran
- **renderingProcessor.py**: réorganiser le chargement et le redimensionnement des sprites pour éviter que le vaisseau grandit avec le zoom
- **main**: extériorarisation de contantes et suppression de lignes inutile
- **help.md**: remplacer les symboles par des mots pour les contrôles du joueur 2 et de la caméra
- **options_window.py**: supprimer les emojis des titres de section
- **main.py**: correction lié aux astuces
- **options**: supprimer la gestion des résolutions dans la modale des options
- **options**: améliorer la gestion des interactions et la structure du modal des options
- **options**: remplacer la fenêtre Tkinter par une modale Pygame pour les options
- **settings**: déplacement du fichier settings dans le bon dossier
- déplacement fichier et externalisation de fonctions
- déplacement des fichiers
- rename files and folders for greater clarity
- **options**: déplacement des fonction pour les options
- add commentary to the vinecomponent
- rename class

### Perf

- **projectiles**: suppression automatique des projectiles aux bords de la carte pour éviter leur persistance inutile, ajout d'un component pour identifier les projectiles
