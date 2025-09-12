# 🎨 Guide des Assets - Galad Islands

## 📁 Structure des dossiers

```
assets/
├── sprites/           # Tous tes sprites ici !
│   ├── units/        # Guerriers, archers, mages, navires...
│   ├── buildings/    # Casernes, tours, châteaux...
│   ├── terrain/      # Tiles de terrain, eau, forêts...
│   └── ui/           # Boutons, icônes, curseurs...
├── sounds/           # Effets sonores et musiques
└── fonts/            # Polices personnalisées
```

## 🎯 Conventions de nommage

### Units (sprites/units/)
- `warrior_idle.png`, `warrior_walk_1.png`, `warrior_attack_1.png`
- `archer_idle.png`, `archer_shoot.png`
- `ship_sail.png`, `ship_attack.png`

### Buildings (sprites/buildings/)
- `barracks.png`, `tower.png`, `castle.png`
- `house_lvl1.png`, `house_lvl2.png`

### Terrain (sprites/terrain/)
- `grass.png`, `water.png`, `forest.png`, `mountain.png`
- `beach.png`, `rocks.png`

### UI (sprites/ui/)
- `button_normal.png`, `button_hover.png`, `button_pressed.png`
- `icon_sword.png`, `icon_bow.png`
- `cursor_normal.png`, `cursor_attack.png`

## 📏 Formats recommandés

- **Format**: PNG avec transparence
- **Taille units**: 32x32 ou 64x64 pixels
- **Taille buildings**: 64x64 ou 128x128 pixels
- **Taille terrain**: 32x32 pixels (tiles)
- **Taille UI**: Variable selon besoin

## 🔄 Animations

Pour les animations, numéroter les frames :
```
warrior_walk_1.png
warrior_walk_2.png
warrior_walk_3.png
warrior_walk_4.png
```

## 💡 Utilisation dans le code

```python
# Charger un sprite
sprite = pygame.image.load("assets/sprites/units/warrior_idle.png")

# Ou avec le path complet
from pathlib import Path
sprite_path = Path("assets/sprites/units/warrior_idle.png")
sprite = pygame.image.load(sprite_path)
```