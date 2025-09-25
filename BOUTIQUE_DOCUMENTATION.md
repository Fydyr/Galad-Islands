# 🏪 Système de Boutique - Galad Islands

## Vue d'ensemble

Le système de boutique intégré offre une interface complète pour acheter des unités, bâtiments et améliorations dans Galad Islands. Il est parfaitement intégré avec la barre d'actions existante.

## 🎮 Fonctionnalités

### Interface Utilisateur
- **Interface moderne** avec onglets et navigation intuitive
- **3 catégories** : Unités, Bâtiments, Améliorations
- **Tooltips informatifs** avec détails des items
- **Feedback visuel** pour les achats et erreurs
- **Thème cohérent** avec la barre d'actions

### Système d'Achat
- **Vérification automatique** des ressources (or)
- **Gestion des quantités** pour items limités
- **Callbacks personnalisables** pour chaque achat
- **Synchronisation** avec le système de ressources du jeu

### Intégration
- **Bouton dédié** dans la barre d'actions (touche B)
- **Synchronisation de l'or** bidirectionnelle
- **Gestion des événements** prioritaire
- **Rendu superposé** non-intrusif

## 🚀 Utilisation

### Ouverture/Fermeture
```python
# Ouvrir la boutique
action_bar.shop.open()

# Fermer la boutique  
action_bar.shop.close()

# Basculer l'état
action_bar.shop.toggle()
```

### Contrôles
- **B** : Ouvrir/fermer la boutique
- **1, 2, 3** : Naviguer entre les onglets
- **ESC** : Fermer la boutique
- **Clic** : Acheter un item
- **Survol** : Voir les détails

### Ajout d'Items Personnalisés
```python
# Créer un nouvel item
custom_item = ShopItem(
    id="custom_unit",
    name="Unité Spéciale",
    description="Description détaillée",
    cost=50,
    icon_path="path/to/icon.png",
    category=ShopCategory.UNITS,
    purchase_callback=custom_callback
)

# Ajouter à la boutique
shop.shop_items[ShopCategory.UNITS].append(custom_item)
```

## 📁 Structure des Fichiers

### `boutique.py`
Classes principales :
- `Shop` : Système principal de boutique
- `ShopItem` : Représentation d'un item
- `ShopCategory` : Énumération des catégories
- `UIColors` : Thème graphique

### `action-bar.py` (modifié)
Intégration :
- Ajout du bouton boutique (ActionType.OPEN_SHOP)
- Gestion des événements boutique
- Synchronisation de l'or
- Rendu intégré

## 🎨 Catégories d'Items

### 🎯 Unités
- **Zasper** (10 or) : Scout rapide et polyvalent
- **Barhamus** (20 or) : Guerrier robuste avec bouclier  
- **Draupnir** (40 or) : Léviathan lourd destructeur
- **Druid** (30 or) : Soigneur et support magique
- **Architect** (30 or) : Constructeur de défenses

### 🏗️ Bâtiments  
- **Tour de Défense** (25 or) : Tour d'attaque automatique
- **Tour de Soin** (20 or) : Tour de régénération alliée

### ⚡ Améliorations
- **Boost d'Attaque** (50 or) : +ATK toutes unités (30s)
- **Boost de Défense** (50 or) : +DEF toutes unités (30s)
- **Boost de Vitesse** (40 or) : +SPD toutes unités (20s)
- **Vague de Soin** (60 or) : Soin instantané global
- **Générateur d'Or** (80 or) : +100 pièces d'or

## 🔧 Configuration

### Modification des Prix
```python
# Dans _initialize_items()
units_data = [
    ("zasper", "Zasper", "Description", {'cout_gold': NOUVEAU_PRIX}),
    # ...
]
```

### Nouveaux Callbacks
```python
def custom_purchase_callback():
    # Logique d'achat personnalisée
    print("Item acheté !")
    # Créer l'unité/bâtiment dans le jeu
    return True  # Succès
```

### Thème Personnalisé
```python
# Modifier UIColors dans boutique.py
class UIColors:
    SHOP_BACKGROUND = (20, 20, 30, 240)  # Nouvelle couleur
    PURCHASE_SUCCESS = (80, 200, 80)     # Vert succès
    # ...
```

## 🐛 Debugging

### Messages de Debug
Le système affiche des messages dans la console :
```
Boutique ouverte
Achat d'unité: zasper
Unité zasper créée!
Or insuffisant!
```

### Vérifications Communes
1. **Icônes manquantes** : Icônes de remplacement automatiques
2. **Or insuffisant** : Feedback visuel et sonore
3. **Items limités** : Compteur de quantité affiché

## 🎭 Exemple Complet

```python
import pygame
from action_bar import ActionBar

# Initialisation
pygame.init()
screen = pygame.display.set_mode((1200, 800))
action_bar = ActionBar(1200, 800)

# Donner de l'or au joueur
action_bar.update_player_gold(150)

# Boucle principale
while running:
    for event in pygame.event.get():
        action_bar.handle_event(event)
    
    action_bar.update(dt)
    action_bar.draw(screen)
    pygame.display.flip()
```

## 🎯 Intégration Future

### Extensions Possibles
- **Système de craft** : Combiner des items
- **Promotions temporaires** : Réductions de prix
- **Items débloquables** : Progression du joueur
- **Boutique multi-joueur** : Échanges entre joueurs
- **Statistiques d'achat** : Analytics des ventes

### Callbacks Système Jeu
Les callbacks doivent être connectés au système principal :
```python
def create_unit_in_game(unit_id):
    # Ajouter l'unité au moteur ECS
    entity = world.create_entity(
        Position(mouse_pos),
        UnitComponent(unit_id),
        # ...
    )
    return True
```

---
**Système développé pour Galad Islands - SAE BUT3** 🎮