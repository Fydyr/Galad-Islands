# Déploiement en production

## Compilation pour la production

### Méthode 1 : Exécutable autonome (recommandée)

```bash
# Installation de PyInstaller
pip install pyinstaller

# Compilation en fichier unique
pyinstaller --onefile --windowed \
    --add-data "assets:assets" \
    --add-data "galad_config.json:." \
    --name "GaladIslands" \
    main.py

# L'exécutable se trouve dans dist/GaladIslands
# Penser à copier les dossiers d'assets nécessaires
```

### Méthode 2 : Distribution Python

```bash
# Préparer l'environnement
python3 -m venv venv_prod
source venv_prod/bin/activate
pip install -r requirements.txt

# Créer un script de lancement
cat > start_game.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./venv_prod/bin/python main.py
EOF
chmod +x start_game.sh
```

## Structure du package de production

```
galad-islands-prod/
├── GaladIslands.exe        # Exécutable (Windows)
├── GaladIslands            # Exécutable (Linux/Mac)
├── assets/                 # Ressources du jeu
├── README.txt              # Instructions
└── galad_config.json       # Configuration, il se crée automatiquement si absent
```

## Instructions de déploiement

### Pour les utilisateurs finaux

1. **Télécharger** le package complet
2. **Extraire** dans un dossier
3. **Lancer** l'exécutable `GaladIslands`
