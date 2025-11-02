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
├── MaraudeurAiCleaner (ou MaraudeurAiCleaner.exe sur Windows)
└── models/ (créé automatiquement si nécessaire)
```

## ⚙️ Outils inclus

Cette release inclut plusieurs utilitaires pour améliorer votre expérience :

### Galad Config Tool
Configurez le jeu sans le lancer :

- **Lancement** : Double-clic sur `galad-config-tool` 
- **Fonctions** : Résolutions, audio, contrôles, langue
- **Avantage** : Configuration avant de jouer

#### Guide rapide
1. Ouvrir `galad-config-tool`
2. Modifier les paramètres dans les onglets
3. Cliquer "Appliquer"
4. Lancer le jeu

### Maraudeur AI Cleaner
Gérez les modèles d'apprentissage de l'IA des Maraudeurs :

- **Lancement** : Double-clic sur `MaraudeurAiCleaner`
- **Fonctions** : 
  - Visualiser les modèles existants
  - Supprimer les modèles sélectionnés
  - Garder uniquement les N plus récents
  - Supprimer les modèles plus vieux que X jours
  - Ouvrir le dossier des modèles
- **Langue** : Suit automatiquement la langue du jeu (FR/EN)

**Note** : Supprimer les modèles est sans risque - l'IA les recréera automatiquement lors du prochain jeu.

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

- **Guide pour l'utilisateur** : `docs/user/galad-config-tool.md` - Utilisation détaillée du tool

## 🌐 Support

- **Documentation complète** : https://fydyr.github.io/Galad-Islands/
- **Code source** : https://github.com/Fydyr/Galad-Islands
- **Issues** : Rapporter les bugs sur GitHub
