# Boutique Unifiée Galad Islands

## Vue d'ensemble

La `UnifiedShop` (boutique unifiée) remplace les deux anciens fichiers `boutique.py` et `boutique2.py` en un seul système flexible qui peut gérer à la fois les boutiques alliées et ennemies.

## Caractéristiques principales

### 🎨 **Thèmes visuels adaptatifs**
- **Faction alliée** : Thème bleu avec des tons froids
- **Faction ennemie** : Thème rouge avec des tons chauds
- Changement automatique des couleurs selon la faction

### 🔄 **Changement de faction dynamique**
- Basculement instantané entre les factions
- Rechargement automatique des items selon la faction
- Conservation des paramètres (or du joueur, position, etc.)

### 🛍️ **Items contextuels**
- **Alliés** : Zasper, Barhamus, Draupnir, Druid, Architect + tours de défense/soin
- **Ennemis** : Scout, Warrior, Brute, Shaman, Engineer + tours d'attaque/soin
- Descriptions traduites avec statistiques localisées

### 🌐 **Localisation complète**
- Support français/anglais
- Titres, descriptions et messages d'erreur traduits
- Statistiques des items localisées (`Vie:`, `ATK:`, etc.)

## Utilisation

### Création d'une boutique

```python
from src.ui.boutique_unified import UnifiedShop, ShopFaction

# Boutique alliée
ally_shop = UnifiedShop(screen_width, screen_height, ShopFaction.ALLY)

# Boutique ennemie
enemy_shop = UnifiedShop(screen_width, screen_height, ShopFaction.ENEMY)
```

### Changement de faction

```python
# Basculer vers la faction ennemie
shop.switch_faction(ShopFaction.ENEMY)

# Retour à la faction alliée
shop.switch_faction(ShopFaction.ALLY)
```

### Intégration dans la boucle de jeu

```python
def game_loop():
    shop = UnifiedShop(800, 600, ShopFaction.ALLY)
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            # Transmettre les événements à la boutique
            shop.handle_event(event)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    shop.toggle()  # Ouvrir/fermer
                elif event.key == pygame.K_f:
                    # Changer de faction
                    new_faction = ShopFaction.ENEMY if shop.faction == ShopFaction.ALLY else ShopFaction.ALLY
                    shop.switch_faction(new_faction)
        
        # Mise à jour
        shop.update(dt)
        shop.set_player_gold(player_gold)  # Synchroniser l'or
        
        # Rendu
        screen.fill((30, 30, 40))
        shop.draw(screen)
        pygame.display.flip()
```

## API

### Méthodes principales

| Méthode | Description |
|---------|-------------|
| `__init__(width, height, faction)` | Constructeur avec faction optionnelle |
| `switch_faction(faction)` | Change la faction et recharge les items |
| `open()` / `close()` / `toggle()` | Contrôle de l'état d'ouverture |
| `handle_event(event)` | Gestion des événements pygame |
| `update(dt)` | Mise à jour logique (timers, animations) |
| `draw(surface)` | Rendu graphique |
| `set_player_gold(amount)` | Définit l'or du joueur |

### Propriétés utiles

| Propriété | Type | Description |
|-----------|------|-------------|
| `faction` | `ShopFaction` | Faction actuelle (ALLY/ENEMY) |
| `theme` | `AllyTheme`/`EnemyTheme` | Thème de couleurs actuel |
| `is_open` | `bool` | État d'ouverture de la boutique |
| `player_gold` | `int` | Or disponible du joueur |
| `current_category` | `ShopCategory` | Catégorie sélectionnée |

## Contrôles

### Clavier
- **Échap** : Fermer la boutique
- **1** : Catégorie Unités
- **2** : Catégorie Bâtiments
- **F** : Changer de faction (en mode test)

### Souris
- **Clic sur item** : Acheter
- **Survol** : Aperçu/highlight
- **Clic onglet** : Changer de catégorie
- **Clic extérieur** : Fermer la boutique

## Migration depuis les anciens fichiers

### Remplacement de `boutique.py`
```python
# Ancien code
from src.ui.boutique import Shop
shop = Shop(width, height)

# Nouveau code
from src.ui.boutique_unified import UnifiedShop, ShopFaction
shop = UnifiedShop(width, height, ShopFaction.ALLY)
```

### Remplacement de `boutique2.py`
```python
# Ancien code
from src.ui.boutique2 import Shop
enemy_shop = Shop(width, height)

# Nouveau code  
from src.ui.boutique_unified import UnifiedShop, ShopFaction
enemy_shop = UnifiedShop(width, height, ShopFaction.ENEMY)
```

## Avantages de la solution unifiée

### ✅ **Maintenance simplifiée**
- Un seul fichier à maintenir au lieu de deux
- Pas de duplication de code
- Corrections/améliorations appliquées automatiquement aux deux factions

### ✅ **Flexibilité**
- Changement de faction à chaud
- Ajout facile de nouvelles factions
- Thèmes modulaires et extensibles

### ✅ **Cohérence**
- Interface identique pour toutes les factions
- Comportement uniformisé
- Expérience utilisateur cohérente

### ✅ **Performance**
- Chargement optimisé des ressources
- Gestion mémoire améliorée
- Code plus efficace

## Tests

Exécuter les tests de base :

```bash
python test_boutique_unified.py
```

Le fichier de test vérifie :
- Création des boutiques alliée/ennemie
- Changement de faction
- Chargement des items
- Fonctions de base (ouvrir/fermer, or)

## Prochaines étapes

1. **Supprimer les anciens fichiers** `boutique.py` et `boutique2.py`
2. **Mettre à jour les imports** dans le jeu principal
3. **Tester l'intégration** complète
4. **Ajouter de nouvelles factions** si nécessaire (neutres, pirates, etc.)

---

*La boutique unifiée Galad Islands - Un système moderne, flexible et maintenable ! 🏪*