# Interface et barre d'action

## 🎮 Vue d'ensemble de l'interface

### Éléments principaux

L'interface de Galad Islands est conçue pour être intuitive et accessible, avec tous les éléments essentiels visibles en permanence pendant le jeu.

**Disposition de l'écran :**
- **Zone de jeu** : Centre de l'écran (vue de la carte)
- **Barre d'action** : Partie inférieure
- **Informations** : Coin supérieur droit
- **Minimap** : Coin inférieur droit (quand disponible)

## 🔧 Barre d'action détaillée

### Informations de ressources

#### Compteur d'or
- **Position** : Coin supérieur gauche de la barre
- **Format** : Icône pièce + nombre actuel
- **Couleur** : Doré brillant
- **Mise à jour** : Temps réel

#### Revenus actuels
- **Affichage** : "+X or/seconde" à côté du compteur
- **Code couleur** :
  - Vert : Revenus positifs
  - Rouge : Dépenses supérieures aux revenus
  - Blanc : Revenus neutres

### Boutons d'action rapide

#### Boutique (`B`)
- **Icône** : Symbole de panier ou pièce
- **Fonction** : Ouvre l'interface d'achat
- **Raccourci** : Touche `B`
- **État** : Toujours disponible

#### Boosts temporaires

**Boost d'Attaque (`Q`)**
- **Icône** : Épée rouge avec particules
- **Coût** : 50 pièces d'or
- **Durée** : 30 secondes
- **Cooldown** : 60 secondes
- **Effet visuel** : Aura rouge autour des unités

**Boost de Défense (`E`)**
- **Icône** : Bouclier bleu avec particules  
- **Coût** : 50 pièces d'or
- **Durée** : 30 secondes
- **Cooldown** : 60 secondes
- **Effet visuel** : Aura bleue autour des unités

#### Capacités spéciales

**Téléportation d'urgence**
- **Raccourci** : `T`
- **Coût** : 100 pièces d'or
- **Fonction** : Téléporte l'unité sélectionnée vers votre base
- **Conditions** : Une unité sélectionnée, cooldown de 45 secondes

### Informations de sélection

#### Unité sélectionnée

**Panneau d'information (bas gauche)**
- **Portrait** : Image de l'unité
- **Nom** : Type d'unité (Zasper, Barhamus, etc.)
- **Statistiques** :
  - Barre de vie (PV actuels/PV maximum)
  - Niveau d'expérience (si applicable)
  - État actuel (En mouvement, Au combat, Inactif)

**Capacités disponibles**
- **Icônes** : Capacités spéciales de l'unité
- **Cooldowns** : Temps de recharge restant
- **Coûts** : Or nécessaire pour activer

#### Gestion de la sélection

- **Focus unique** : L'interface affiche toujours l'unité actuellement ciblée
- **Raccourcis de groupe** : Utilisez `Ctrl + Maj + (1-9)` puis `Ctrl + (1-9)` pour basculer rapidement
- **Bascule de faction** : `T` permet de changer la faction prise en compte

### États et notifications

#### Indicateurs de cooldown

**Boosts temporaires**
- **Actif** : Icône brillante + compte à rebours
- **En cooldown** : Icône grisée + temps restant
- **Disponible** : Icône normale + coût affiché

#### Alertes et warnings

**Notifications système :**
- **Or insuffisant** : Message rouge clignotant
- **Unité détruite** : Flash rouge à l'écran
- **Nouvelle technologie** : Notification dorée
- **Territoire capturé** : Message de confirmation vert

## ⌨️ Raccourcis de l'interface

### Navigation rapide

| Raccourci | Action | Détails |
|-----------|---------|---------|
| `Espace` | Centrer sur la base | Retour rapide à votre position de départ |
| `H` | Centrer sur l'Architect | Localise votre constructeur |
| `F` | Suivre unité sélectionnée | La caméra suit automatiquement |
| `G` | Afficher la grille | Montre les limites des îles |

### Raccourcis de production

| Raccourci | Unité | Coût | Pré-requis |
|-----------|--------|------|------------|
| `1` | Zasper | 50 or | Boutique ouverte |
| `2` | Barhamus | 100 or | Boutique ouverte |
| `3` | Draupnir | 300 or | Boutique ouverte |
| `4` | Druid | 150 or | Boutique ouverte |
| `5` | Architect | 200 or | Boutique ouverte |

### Raccourcis de construction

| Raccourci | Bâtiment | Coût | Pré-requis |
|-----------|----------|------|------------|
| `Shift + 1` | Tour de Défense | 100 or | Architect sur île |
| `Shift + 2` | Tour de Soin | 125 or | Architect sur île |
| `Shift + 3` | Générateur d'Or | 200 or | Architect sur mine |
| `Shift + 4` | Entrepôt | 150 or | Architect sur île |

## 📱 Interface responsive

### Adaptations selon la résolution

**1920x1080 (Full HD)**
- Interface complète avec tous les détails
- Portraits d'unités en haute résolution
- Informations détaillées visibles

**1366x768 (Standard)**
- Interface compacte mais fonctionnelle
- Textes légèrement réduits
- Éléments essentiels conservés

**1024x768 (Minimum)**
- Interface simplifiée
- Raccourcis privilégiés sur les clics
- Informations condensées

### Personnalisation

#### Options d'affichage

**Transparence de l'interface**
- **Opaque** : Visibilité maximale (par défaut)
- **Semi-transparente** : Vue sur la carte améliorée
- **Minimale** : Seuls les éléments essentiels

**Taille des éléments**
- **Grande** : Accessibilité améliorée
- **Normale** : Équilibre standard
- **Petite** : Plus d'espace pour la carte

## 🎯 Conseils d'optimisation

### Utilisation efficace

!!! tip "Maîtrise de l'interface"
    **Pour devenir plus efficace :**
    
    1. **Mémorisez** les raccourcis les plus utilisés (`B`, `Q`, `E`)
  2. **Enregistrez** vos unités clés dans des groupes (`Ctrl + Maj + numéro`)
    3. **Surveillez** constamment vos ressources et cooldowns
    4. **Personnalisez** l'interface selon vos préférences

### Workflow optimisé

**Séquence type d'action :**
1. **Vérifier** les ressources disponibles
2. **Sélectionner** les unités concernées
3. **Choisir** l'action (mouvement, attaque, construction)
4. **Confirmer** avec les raccourcis appropriés
5. **Surveiller** l'exécution et les cooldowns

### Gestion des urgences

**Réactions rapides :**
- **Attaque surprise** → `Q` (boost attaque) + sélection toutes unités
- **Défense critique** → `E` (boost défense) + regroupement  
- **Unité en danger** → `T` (téléportation d'urgence)
- **Ressources faibles** → Focus sur économie + construction générateurs

## 🔍 Interface debug et avancée

### Informations développeur

**Mode debug (si activé)**
- **FPS** : Images par seconde dans le coin
- **Coordonnées** : Position du curseur
- **États unités** : Informations détaillées sur sélection
- **Logs système** : Messages de diagnostic

### Commandes console

**Raccourcis développeur :**
- `F12` : Toggle mode debug
- `F11` : Plein écran
- `F10` : Capture d'écran
- `F9` : Reload interface

!!! warning "Attention"
    Les commandes développeur peuvent affecter l'équilibre du jeu. Utilisez-les uniquement pour le test ou le débogage.

---

*Maintenant que vous maîtrisez l'interface, explorez les [stratégies avancées](strategy.md) pour dominer vos adversaires !*