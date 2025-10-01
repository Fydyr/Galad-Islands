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
