# 🎨 Guide des Assets - Galad Islands

## 📁 Structure actuelle des assets

```
assets/
├── logo.png                    # Logo du jeu
├── sprites/                    # Tous les sprites du jeu
│   ├── units/                 # Unités par faction
│   │   ├── ally/              # Unités alliées
│   │   │   ├── Zasper.png     # Unité rapide, évasion
│   │   │   ├── Barhamus.png   # Unité équilibrée, bouclier
│   │   │   ├── Draupnir.png   # Unité lourde, double salve
│   │   │   ├── Druid.png      # Unité de soin, lierre
│   │   │   └── Architect.png  # Unité de support, buff
│   │   └── enemy/             # Unités ennemies (mêmes types)
│   │       ├── Zasper.png, Barhamus.png, etc.
│   ├── buildings/             # Bâtiments et structures
│   │   ├── generic-tour.png   # Tour générique
│   │   ├── ally/              # Bâtiments alliés
│   │   │   ├── ally-defence-tower.png
│   │   │   └── ally-heal-tower.png
│   │   └── enemy/             # Bâtiments ennemis
│   │       ├── enemy-attack-tower.png
│   │       └── enemy-heal-tower.png
│   ├── terrain/               # Éléments de terrain
│   │   ├── background.png     # Fond d'écran
│   │   ├── ally_island.png    # Île base alliée
│   │   ├── enemy_island.png   # Île base ennemie
│   │   ├── generic_island.png # Île neutre
│   │   └── mine.png          # Mine de ressources
│   ├── weather/               # Effets météo
│   │   └── tempete.png       # Tempête
│   └── ui/                   # Interface utilisateur (vide)
├── event/                     # Sprites d'événements
│   ├── kraken.png            # Kraken et tentacules
│   ├── tentacule_kraken.png
│   ├── pirate_ship.png       # Navire pirate
│   ├── chest_open.png        # Coffres au trésor
│   ├── chest_close.png
│   ├── ball_explosion.png    # Effets d'explosion
│   └── impact_explosion.png
├── sounds/                   # Effets sonores (vide)
└── fonts/                    # Polices personnalisées (vide)
```

## � Assets disponibles par catégorie

### ⚔️ Unités (ally/ et enemy/)
- **Zasper** : Unité rapide avec capacité d'évasion (3s)
- **Barhamus** : Unité équilibrée avec bouclier magique
- **Draupnir** : Unité lourde avec double salve
- **Druid** : Unité de soin avec capacité lierre (5s)
- **Architect** : Unité de support avec buff rechargement

### 🏰 Bâtiments
- **Tours défensives** : ally-defence-tower.png / enemy-attack-tower.png
- **Tours de soin** : ally-heal-tower.png / enemy-heal-tower.png
- **Tour générique** : generic-tour.png

### 🌍 Terrain et îles
- **Bases** : ally_island.png, enemy_island.png (1000 armure chacune)
- **Îles neutres** : generic_island.png (50-150 gold)
- **Mines** : mine.png (ressources)
- **Fond** : background.png

### 🌩️ Événements aléatoires
- **Tempêtes** : tempete.png (30 dégâts, 20s durée)
- **Kraken** : kraken.png + tentacule_kraken.png (70 dégâts, 2-6 tentacules)
- **Pirates** : pirate_ship.png (1-6 unités, 20 dégâts chacune)
- **Coffres** : chest_open.png, chest_close.png (10-20 gold, 2-5 coffres)
- **Explosions** : ball_explosion.png, impact_explosion.png

## � Utilisation dans le code

### Chargement des sprites par faction
```python
# Unités alliées
zasper_ally = pygame.image.load("assets/sprites/units/ally/Zasper.png")
druid_ally = pygame.image.load("assets/sprites/units/ally/Druid.png")

# Unités ennemies
zasper_enemy = pygame.image.load("assets/sprites/units/enemy/Zasper.png")

# Terrain
background = pygame.image.load("assets/sprites/terrain/background.png")
ally_base = pygame.image.load("assets/sprites/terrain/ally_island.png")

# Événements
kraken = pygame.image.load("assets/event/kraken.png")
tempete = pygame.image.load("assets/sprites/weather/tempete.png")
```

### Gestionnaire d'assets (recommandé)
```python
from pathlib import Path

class AssetManager:
    def __init__(self):
        self.assets_path = Path("assets")
        self.sprites = {}
        self.load_all_sprites()
    
    def load_sprite(self, path: str, name: str):
        """Charge un sprite et le stocke."""
        full_path = self.assets_path / path
        self.sprites[name] = pygame.image.load(full_path)
    
    def get_unit_sprite(self, unit_type: str, faction: str):
        """Récupère le sprite d'une unité selon sa faction."""
        return self.sprites[f"{unit_type}_{faction}"]
    
    def load_all_sprites(self):
        """Charge tous les sprites disponibles."""
        # Unités
        for faction in ["ally", "enemy"]:
            for unit in ["Zasper", "Barhamus", "Draupnir", "Druid", "Architect"]:
                self.load_sprite(f"sprites/units/{faction}/{unit}.png", f"{unit}_{faction}")
        
        # Terrain
        for terrain in ["background", "ally_island", "enemy_island", "generic_island", "mine"]:
            self.load_sprite(f"sprites/terrain/{terrain}.png", terrain)
        
        # Événements
        for event in ["kraken", "pirate_ship", "tempete"]:
            if event == "tempete":
                self.load_sprite(f"sprites/weather/{event}.png", event)
            else:
                self.load_sprite(f"event/{event}.png", event)

# Utilisation
assets = AssetManager()
zasper_sprite = assets.get_unit_sprite("Zasper", "ally")
background_sprite = assets.sprites["background"]
```

## 📋 Todo - Assets manquants

### UI à créer
- Boutons (normal, hover, pressed)
- Icônes d'unités pour l'interface
- Curseurs (normal, attaque, sélection)
- Barres de vie et mana
- Minimap

### Sons à ajouter
- Effets sonores d'attaque par unité
- Sons d'explosion et d'impact
- Musique de fond
- Sons d'interface (clic, hover)

### Polices
- Police principale pour l'UI
- Police pour les dégâts flottants

---

## 🎯 Prêt pour le développement !

Tous les sprites principaux sont disponibles et organisés par faction. Le système peut maintenant être implémenté avec les vrais assets ! 🚀