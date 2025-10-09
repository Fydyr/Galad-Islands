# Configuration développement

## Ce qu'il faut pour développer Galad Islands

### Prérequis minimum
- **Python 3.9+** 
- **4 GB RAM** minimum (8 GB recommandés)
- **2 GB d'espace disque**

### Installation rapide

#### Linux (Ubuntu/Debian)
```bash
sudo apt install python3 python3-pip python3-venv
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

#### Windows
- Installer Python 3.9+ depuis python.org
- Visual C++ Redistributable 2019+

#### macOS
```bash
brew install python@3.9
brew install sdl2 sdl2_image sdl2_mixer
```

### Setup du projet

```bash
# Cloner le projet
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Lancer le jeu
python main.py
```

### Dépendances Python principales

```txt
# requirements.txt (version de production)
pygame>=2.1.2
esper>=2.0
numpy>=1.21.0
Pillow>=8.3.0
pyyaml>=6.0
requests>=2.26.0

# requirements-dev.txt (développement)
pytest>=6.2.0
pytest-cov>=2.12.0
black>=21.7.0
flake8>=3.9.0
mypy>=0.910
sphinx>=4.1.0
```


# Vérifier que tout fonctionne
```
python -c "import pygame, esper; print('✅ Setup OK')"
```

C'est tout ! Si ça marche, tu peux développer.