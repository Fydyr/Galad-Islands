---
i18n:
  en: "Development Requirements"
  fr: "Configuration développement"
---

# Configuration développement

## Ce qu'il faut pour développer Galad Islands

### Prérequis minimum
- **Python 3.9+** 
- **2 GB RAM** minimum (4 GB recommandés)
- **500 MB d'espace disque**

### Installation rapide

#### Linux (Ubuntu/Debian)
```bash
sudo apt install python3 python3-pip python3-venv
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

#### Windows
- Installer Python 3.9+ depuis python.org

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
esper==3.4
llvmlite==0.44.0
numba==0.61.2
numpy==2.2.6
pygame==2.6.1
Pillow==10.4.0
tomli==1.2.0

# requirements-dev.txt (développement)
markdown==3.9.0
tkhtmlview==0.3.1
commitizen==4.9.1
mkdocs==1.5.2
mkdocs-material==9.1.15
mkdocs-static-i18n==1.2.3
```


# Vérifier que tout fonctionne
```
python -c "import pygame, esper; print('✅ Setup OK')"
```

C'est tout ! Si ça marche, tu peux développer.