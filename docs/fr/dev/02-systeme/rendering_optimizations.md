# Optimisations du Rendu de Carte - Galad Islands

## Vue d'ensemble

Ce document décrit les optimisations et corrections apportées au système de rendu de la carte dans Galad Islands, en se concentrant sur les problèmes de performance et de précision visuelle.

## Historique des Modifications

### 1. Désactivation de l'Optimisation de Pré-rendu (v1.2.0)

**Date:** Octobre 2025  
**Fichier affecté:** `src/components/globals/mapComponent.py`  
**Problème identifié:** L'optimisation de pré-rendu causait des décalages graphiques et des problèmes d'alignement des éléments.

**Solution implémentée:**

- Désactivation de la fonction `_pre_render_static_map()`
- Retour au rendu tuile par tuile classique
- Suppression du rendu de surface pré-calculée

**Impact:**

- Résolution des problèmes d'alignement graphique
- Rendu plus précis des éléments de la carte
- Performance légèrement réduite mais plus stable

### 2. Correction du Rendu des Bases (v1.2.1)

**Date:** Octobre 2025  
**Fichier affecté:** `src/components/globals/mapComponent.py`  
**Problème identifié:** Les bases (4x4 tuiles) ne se rendaient que si leur coin supérieur gauche était visible, causant des disparitions partielles.

**Solution implémentée:**

- Modification de la logique de rendu des bases dans `afficher_grille()`
- Rendu des bases lorsqu'une tuile de base devient visible, peu importe sa position
- Calcul correct des coordonnées d'écran pour le rendu à la position appropriée
- Marquage de toutes les tuiles de base comme traitées pour éviter les rendus multiples

**Code clé:**

```python
elif val == TileType.ALLY_BASE and (i, j) not in processed_bases:
    # Rendre la base alliée à sa position correcte
    top_left_i, top_left_j = 1, 1
    # Calcul des coordonnées écran et rendu
```

**Impact:**

- Bases toujours visibles même en rendu partiel
- Élimination des disparitions inexpliquées des bases
- Amélioration de l'expérience utilisateur

### 3. Optimisations Futures Planifiées

#### Sprite Batching

- **Objectif:** Regrouper les appels de rendu pour réduire les appels OpenGL
- **Approche:** Collecter tous les sprites dans une liste avant le rendu final
- **Bénéfices attendus:** Amélioration significative des performances sur GPU

#### Découpage Spatial (Spatial Partitioning)

- **Objectif:** Optimiser les vérifications de visibilité
- **Approche:** Utiliser des quadtrees ou des grilles spatiales pour indexer les éléments
- **Bénéfices attendus:** Réduction du temps de calcul des éléments visibles

#### Level of Detail (LOD)

- **Objectif:** Réduire la complexité du rendu à distance
- **Approche:** Rendu simplifié des éléments lointains
- **Bénéfices attendus:** Amélioration des performances à zoom arrière

## Métriques de Performance

### Avant Optimisations

- FPS: ~30 en moyenne avec carte révélée
- Problèmes: Décalages graphiques, bases disparaissant

### Après Corrections

- FPS: Stable, problèmes d'alignement résolus
- Amélioration: Rendu correct des bases, stabilité visuelle

## Architecture du Système de Rendu

### Composants Principaux

1. **mapComponent.py** - Logique de rendu de la carte
2. **cameraComponent.py** - Gestion du viewport et des coordonnées
3. **game.py** - Orchestration du rendu principal

### Flux de Rendu

1. Calcul des tuiles visibles via `camera.get_visible_tiles()`
2. Rendu de la mer en arrière-plan
3. Rendu des éléments (îles, mines, bases) par-dessus
4. Gestion spéciale des bases multi-tuiles

## Recommandations pour les Développeurs

### Tests de Rendu

- Toujours tester le rendu à différents niveaux de zoom
- Vérifier la visibilité des éléments aux bords de l'écran
- Tester avec différentes positions de caméra

### Performance

- Surveiller les FPS pendant les sessions de jeu
- Utiliser les outils de profiling pour identifier les goulots d'étranglement
- Considérer le sprite batching pour les futures optimisations

### Maintenance

- Documenter tout changement affectant le rendu
- Tester les modifications sur différents matériels
- Maintenir la compatibilité avec les anciennes sauvegardes

## Outils de Diagnostic

### Profilage des Performances

Le projet inclut un outil de profilage intégré utilisant `cProfile` :

```bash
python profile_game.py
```

Cet outil analyse les performances en temps réel pendant une session de jeu normale et génère un rapport détaillé des fonctions les plus lentes. Consultez la [documentation de maintenance](../06-maintenance/maintenance.md#profilage-des-performances-avec-cprofile) pour plus de détails.

## Références

- [Pygame Documentation](https://www.pygame.org/docs/)
- [Optimisations de rendu 2D](https://developer.mozilla.org/en-US/docs/Games/Techniques/2D_collision_detection)
- Logs de debug dans `afficher_grille()` pour le diagnostic
