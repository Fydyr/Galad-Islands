# Modules - Gestionnaires

Cette section documente les différents gestionnaires (managers) du système, qui centralisent la gestion des ressources et comportements du jeu.

## Gestionnaires disponibles

### Sprite Manager

Le **Sprite Manager** est un système centralisé de gestion des sprites qui remplace l'utilisation directe des chemins de fichiers par un système basé sur des IDs.

**Caractéristiques principales :**
- Enregistrement centralisé de tous les sprites du jeu
- Mise en cache automatique pour améliorer les performances
- API simple basée sur des énumérations (SpriteID)
- Fonctions utilitaires pour créer facilement des composants sprite
- Support complet pour unités, projectiles, effets, bâtiments, événements et UI

**Documentation complète :** [Sprite Manager](sprite-manager.md)

## À venir

- Gestionnaire audio
- Gestionnaire d'affichage  
- Gestionnaires de ressources avancés
- Patterns utilisés