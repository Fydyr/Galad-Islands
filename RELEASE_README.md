# Galad Islands - Release

## 🎮 Installation du jeu

1. Décompressez l'archive
2. Assurez-vous que le dossier `assets/` est au même emplacement que l'exécutable `galad-islands`
3. Lancez l'exécutable

## 📁 Structure requise

```
galad-islands/
├── galad-islands (ou galad-islands.exe sur Windows)
├── galad-config-tool (ou galad-config-tool.exe sur Windows)
└── assets/
    ├── image/
    ├── sounds/
    ├── sprites/
    └── ...
```

## ⚙️ Outil de configuration

Cette release inclut **Galad Config Tool**, un utilitaire pour configurer le jeu sans le lancer :

- **Lancement** : Double-clic sur `galad-config-tool` 
- **Fonctions** : Résolutions, audio, contrôles, langue
- **Avantage** : Configuration avant de jouer

### Guide rapide
1. Ouvrir `galad-config-tool`
2. Modifier les paramètres dans les onglets
3. Cliquer "Appliquer"
4. Lancer le jeu

## 🔧 Dépannage

### Erreurs du jeu principal
Si vous rencontrez des erreurs de type "No file found" :
- Le dossier `assets/` est bien présent à côté de l'exécutable
- Vous lancez l'exécutable depuis son répertoire

### Problèmes de configuration
Si l'outil de config ne fonctionne pas :
- Vérifier que `galad_config.json` est accessible en écriture
- Les fichiers de config sont créés automatiquement si manquants
- Messages d'erreur affichés directement dans l'interface

## 📚 Documentation

### 👤 Pour les utilisateurs
- **Guide complet** : `docs/user/galad-config-tool.md` - Utilisation détaillée du tool
- **Guide rapide** : `tools/QUICKSTART.md` - Démarrage en 4 étapes  
- **Interface intuitive** : Messages d'aide intégrés dans l'outil

### 🛠️ Pour les développeurs  
- **Documentation technique** : `docs/dev/galad-config-tool-technical.md` - Architecture et code
- **API documentation** : https://fydyr.github.io/Galad-Islands/
- **Code source** : Organisation modulaire dans `src/`

### 📋 Organisation
- **Index général** : `tools/DOCUMENTATION.md` - Vue d'ensemble
- **Utilisateurs** → Consulter `docs/user/galad-config-tool.md`
- **Développeurs** → Consulter `docs/dev/galad-config-tool-technical.md`

## 🌐 Support

- **Documentation complète** : https://fydyr.github.io/Galad-Islands/
- **Code source** : https://github.com/Fydyr/Galad-Islands
- **Issues** : Rapporter les bugs sur GitHub
