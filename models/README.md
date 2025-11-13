# 🧠 Dossier des Modèles d'IA

Ce dossier contient les modèles d'apprentissage automatique sauvegardés pour les unités Barhamus (Maraudeur Zeppelin).

## 📁 Fichiers PKL

Chaque fichier `barhamus_ai_<ID>.pkl` contient :
- Le modèle DecisionTree entraîné
- Le scaler pour normaliser les données
- Les 100 dernières expériences
- Les statistiques de performance par stratégie
- L'état d'entraînement du modèle

## 🧹 Nettoyage des fichiers

Les fichiers PKL s'accumulent au fil du temps car chaque unité crée son propre fichier. Tu n'as **pas besoin de tous les garder** !

### Utilisation du script de nettoyage

Depuis la racine du projet, utilise le script `clean_models.py` :

```bash
# Lister tous les fichiers PKL
python clean_models.py --list

# Supprimer TOUS les fichiers PKL (réinitialisation complète)
python clean_models.py --all

# Garder seulement les 10 fichiers les plus récents
python clean_models.py --keep 10

# Supprimer les fichiers de plus de 7 jours
python clean_models.py --older-than 7
```

### Quand nettoyer ?

**Supprime les vieux fichiers PKL si :**
- Tu veux réinitialiser l'apprentissage de l'IA
- Le dossier `models/` devient trop gros
- Tu veux tester l'IA avec un apprentissage frais

**Garde les fichiers PKL si :**
- Tu veux que l'IA conserve son apprentissage entre les parties
- Tu veux comparer les performances avant/après modifications

## ⚙️ Pourquoi les fichiers PKL ne sont pas versionnés ?

Les fichiers `.pkl` sont ajoutés au `.gitignore` car :
- Ils sont générés automatiquement pendant le jeu
- Ils sont spécifiques à chaque session de jeu
- Ils peuvent devenir incompatibles après des modifications du code
- Chaque développeur devrait générer ses propres modèles

## 🎯 Recommandation

Pour un usage quotidien, exécute régulièrement :

```bash
python clean_models.py --keep 20
```

Cela garde les 20 modèles les plus récents et supprime les anciens.
