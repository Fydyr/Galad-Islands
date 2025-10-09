# Interface et barre d'action

## 🎮 Vue d'ensemble de l'interface

### Éléments principaux

L'interface de Galad Islands est conçue pour être intuitive et accessible, avec tous les éléments essentiels visibles en permanence pendant le jeu.

**Disposition de l'écran :**

- **Zone de jeu** : Centre de l'écran (vue de la carte)
- **Barre d'action** : En bas à gauche de l'écran
- **Or** : En bas au centre
- **Informations des unités** : En bas au centre (à côté de l'or)

## 🔧 Barre d'action détaillée

### Informations de ressources

#### Compteur d'or

- **Position** : Centre bas de l'écran
- **Format** : Icône pièce + nombre actuel
- **Couleur** : Doré brillant
- **Mise à jour** : Temps réel

### Boutons d'action rapide

#### Boutique (`B`)

- **Fonction** : Ouvre l'interface d'achat
- **Raccourci** : Touche `B`
- **État** : Toujours disponible

### Informations de sélection

#### Unité sélectionnée

**Panneau d'information (bas à droite)**

- **Nom** : Type d'unité (Scout, Maraudeur, etc.)
- **Statistiques** :
  - Barre de vie (PV actuels/PV maximum)

**Capacités disponibles (bas à gauche)**

- **Icônes** : Capacités spéciales de l'unité
- **Cooldowns** : Temps de recharge restant

#### Gestion de la sélection

- **Focus unique** : L'interface affiche toujours l'unité actuellement ciblée
- **Bascule de faction** : `T` permet de changer la faction prise en compte (développement uniquement)

### États et notifications

#### Indicateurs de cooldown

!!! info
    Les boosts ne sont pas encore implémentés dans le jeu.

**Boosts temporaires**

- **En cooldown** : Icône + temps restant
- **Disponible** : Icône + coût affiché

#### Alertes et warnings

**Notifications système :**

- **Or insuffisant** : Message rouge clignotant

### Workflow optimisé

**Séquence type d'action :**

1. **Vérifier** les ressources disponibles
2. **Sélectionner** les unités concernées
3. **Choisir** l'action (mouvement, attaque, construction)
4. **Confirmer** avec les raccourcis appropriés
5. **Surveiller** l'exécution et les cooldowns

## 🔍 Interface debug et avancée

### Informations développeur

**Mode debug (si activé)**

- **FPS** : Images par seconde dans le coin
- **Coordonnées** : Position du curseur
- **États unités** : Informations détaillées sur sélection
- **Logs système** : Messages de diagnostic

### Commandes console

**Raccourcis développeur :**

- `F3` : Afficher le mode debug

!!! warning "Attention"
    Les commandes développeur peuvent affecter l'équilibre du jeu. Utilisez-les uniquement pour le test ou le débogage.

---

*Maintenant que vous maîtrisez l'interface, explorez les [stratégies de gameplay](gameplay.md) pour dominer vos adversaires !*
