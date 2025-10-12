---
i18n:
  en: "Configuration Development"
  fr: "Configuration Development"
---

# Configuration Development

## What you need to develop Galad Islands

### Minimum Prerequisites

- **Python 3.9+** 
- **2 GB RAM** Minimum (4 GB recommended)
- **500 MB disk space**

### Quick Installation

#### Linux (Ubuntu/Debian)
```bash
sudo apt install python3 python3-pip python3-venv
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

#### Windows
- Install Python 3.9+ from python.org

#### macOS
```bash
brew install python@3.9
brew install sdl2 sdl2_image sdl2_mixer
```

### Project Setup

```bash
# Clone the Project
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands

# Create Virtual Environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install Dependencies
pip install -r requirements.txt
# Install Development Dependencies
pip install -r requirements-dev.txt

# Launch the game
python main.py
```

### Main Python Dependencies

```txt
# requirements.txt (Production version)
esper==3.4
llvmlite==0.44.0
numba==0.61.2
numpy==2.2.6
pygame==2.6.1
Pillow==10.4.0
tomli==1.2.0

# requirements-dev.txt (Development)
markdown==3.9.0
tkhtmlview==0.3.1
commitizen==4.9.1
mkdocs==1.5.2
mkdocs-material==9.1.15
mkdocs-static-i18n==1.2.3
```


# Verify everything works
```
python -c "import pygame, esper; print('✅ Setup OK')"
```

That's it! If it works, you can develop.