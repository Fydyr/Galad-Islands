# IA Barhamus avec Machine Learning (scikit-learn)

## Vue d'ensemble

Ce document décrit la nouvelle implémentation de l'IA pour les unités Barhamus (Maraudeur Zeppelin) utilisant l'apprentissage automatique avec scikit-learn.

## Architecture

### Composants principaux

1. **DecisionTreeClassifier** : Modèle d'arbre de décision pour prédire les actions
2. **StandardScaler** : Normalisation des données d'entrée
3. **NearestNeighbors** : Pathfinding intelligent basé sur les positions similaires

### Vecteur d'état (15 dimensions)

L'IA analyse la situation via un vecteur de 15 dimensions :

1. **Position (2D)** : Coordonnées X,Y normalisées
2. **Santé (1D)** : Ratio santé actuelle/max
3. **Ennemis (3D)** : Nombre, distance au plus proche, force
4. **Obstacles (3D)** : Îles, mines, murs
5. **Tactique (3D)** : Avantage tactique, zone sûre, statut bouclier
6. **État interne (3D)** : Cooldown, temps de survie, stratégie actuelle

### Actions disponibles (8 types)

0. **Approche agressive** : Fonce vers l'ennemi le plus proche
1. **Attaque** : Engage le combat direct
2. **Patrouille** : Recherche active d'ennemis
3. **Évitement** : Contourne les obstacles dangereux
4. **Bouclier** : Active la protection défensive
5. **Position défensive** : Se place en position stratégique
6. **Retraite** : Fuit vers une zone sûre
7. **Embuscade** : Se positionne pour une attaque surprise

## Système d'apprentissage

### Collecte d'expérience

L'IA enregistre chaque décision avec :
- État avant l'action (vecteur 15D)
- Action choisie (0-7)
- Récompense obtenue (-10 à +10)
- État résultant

### Calcul des récompenses

**Récompenses positives :**
- Santé élevée : +5
- Attaque réussie : +3
- Survie prolongée : +2
- Position tactique : +1

**Pénalités :**
- Dégâts subis : -2 par point
- Échec d'attaque : -1
- Position dangereuse : -3

### Entraînement du modèle

Le modèle se retraine automatiquement :
- Toutes les 20 expériences
- Quand la performance chute
- Au début de chaque partie

## Stratégies adaptatives

L'IA suit 4 stratégies principales qui évoluent selon la performance :

1. **Balanced** : Équilibre entre attaque et défense
2. **Aggressive** : Priorité à l'offensive
3. **Defensive** : Priorité à la survie
4. **Tactical** : Utilise l'environnement et les embuscades

## Avantages par rapport au système précédent

### Ancien système (règles fixes)
- Comportement prévisible
- Réactions limitées aux situations
- Pas d'adaptation à l'adversaire

### Nouveau système (ML)
- Apprend de ses erreurs
- S'adapte au style de jeu du joueur  
- Stratégies évolutives
- Meilleure utilisation de l'environnement

## Fichiers importants

- `src/ia/ia_barhamus2.py` : Implémentation principale
- `test_ia_ml.py` : Tests unitaires
- `models/` : Modèles sauvegardés (créé automatiquement)

## Performance

Tests effectués montrent :
- ✅ Compilation sans erreurs
- ✅ Analyse d'état 15D fonctionnelle
- ✅ Prédiction d'actions opérationnelle
- ✅ Système d'apprentissage actif
- ✅ Composants scikit-learn initialisés

## Utilisation dans le jeu

Pour utiliser cette IA, remplacer l'import dans le système de jeu :

```python
# Ancien
from src.ia.ia_barhamus import BarhamusAI

# Nouveau  
from src.ia.ia_barhamus2 import BarhamusAI
```

## Notes techniques

- Nécessite scikit-learn, numpy
- Sauvegarde automatique des modèles
- Compatible avec l'architecture ECS existante
- Maintient la compatibilité avec les méthodes legacy

---

*Développé pour améliorer l'expérience de jeu avec des adversaires IA plus intelligents et adaptatifs.*