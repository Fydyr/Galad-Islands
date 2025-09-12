# 🏝️ Galad Islands - RTS Naval

**Jeu de stratégie temps réel** basé sur Pygame avec architecture modulaire.

## 🚀 Installation

```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd SAE5A_jeu
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Lancement

```bash
python main.py          # Lancer le jeu
python dev.py --test    # Tests et développement
```

## 🎨 Assets et Sprites

**Dossier sprites** : `assets/sprites/`

```
assets/
├── sprites/
│   ├── units/        # tes guerriers, archers, navires...
│   ├── buildings/    # casernes, tours, châteaux...
│   ├── terrain/      # tiles eau, îles, forêts...
│   └── ui/          # boutons, icônes, curseurs...
├── sounds/          # effets sonores
└── fonts/           # polices personnalisées
```

**Formats recommandés** :
- PNG avec transparence
- Unités : 32x32 ou 64x64 px
- Terrain : 32x32 px (tiles)
- UI : variable selon besoin

## 🏗️ Architecture

### Structure modulaire
```
src/
├── components/      # Composants du moteur
│   ├── core/       # Moteur principal, boucle de jeu
│   ├── entities/   # Système d'entités et unités
│   ├── renderer/   # Rendu, sprites, effets
│   ├── ai/         # IA et pathfinding
│   ├── physics/    # Collisions et mouvements
│   └── world/      # Génération de monde
└── interfaces/     # Communication entre composants
```

### Event Bus
Communication décentralisée entre composants :
```python
# Publier un événement
EventBus.publish("unit_created", unit_data)

# S'abonner à un événement  
EventBus.subscribe("unit_destroyed", callback_function)
```

## �️ Développement

### Performance
- **Target** : 60 FPS stable
- **Optimisation** : Numba + NumPy pour calculs critiques

## 📖 Documentation

- **Assets** : Guide dans `assets/README_ASSETS.md`