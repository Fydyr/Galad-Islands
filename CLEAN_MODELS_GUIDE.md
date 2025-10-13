# 🧹 Guide de Nettoyage des Modèles d'IA

## Utilisation rapide

### Voir tous les fichiers PKL
```bash
python clean_models.py --list
```

### Garder les 15 plus récents (recommandé)
```bash
python clean_models.py --keep 15
```

### Supprimer TOUT (réinitialisation complète)
```bash
python clean_models.py --all
```

### Supprimer les fichiers de plus de 7 jours
```bash
python clean_models.py --older-than 7
```

## Exemples d'utilisation

### Je veux tester l'IA avec un apprentissage frais
```bash
python clean_models.py --all
```
L'IA recommencera à apprendre depuis zéro.

### J'ai beaucoup de fichiers et je veux faire le ménage
```bash
python clean_models.py --keep 20
```
Garde les 20 modèles les plus récents, supprime les autres.

### Je veux supprimer les vieux fichiers automatiquement
```bash
python clean_models.py --older-than 3
```
Supprime tous les fichiers de plus de 3 jours.

## Fréquence recommandée

- **Quotidien** : `python clean_models.py --keep 15`
- **Hebdomadaire** : `python clean_models.py --older-than 7`
- **Avant un test** : `python clean_models.py --all`

## Notes importantes

✅ Les fichiers PKL ne sont **PAS** versionnés dans Git (ajoutés au `.gitignore`)  
✅ Tu peux les supprimer sans risque - l'IA les recréera automatiquement  
✅ Chaque unité crée son propre fichier, d'où l'accumulation rapide  
✅ Supprimer les fichiers réinitialise l'apprentissage de l'IA  
