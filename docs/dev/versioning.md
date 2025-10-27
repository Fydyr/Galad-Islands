# Gestion des versions

## 🎯 Objectif

Ce document explique comment gérer les versions du projet Galad Islands avec un système de gestion manuelle des versions.

> **💡 Info : Migration du workflow de version**
>
> Le projet a récemment migré d'un système de bump automatique (hooks pre-commit locaux) vers une gestion manuelle des versions.
>
> 📖 **[Consultez le guide de migration](workflow-migration.md)** pour comprendre les changements et les avantages du nouveau système.

## 🚀 Nouveau : Gestion manuelle des versions

Le système de bump automatique via hook pre-commit a été supprimé. Désormais, les versions doivent être gérées manuellement par les développeurs.

### Comment gérer les versions manuellement

1. **Activer l'environnement virtuel** :

   ```bash
   source venv/bin/activate  # Unix/Linux/macOS
   # ou
   venv\Scripts\activate     # Windows
   ```

2. **S'assurer d'être à jour** :

   ```bash
   git checkout main && git pull origin main
   ```

3. **Effectuer le bump** :

   ```bash
   python -m commitizen bump --increment patch --yes --changelog
   ```

4. **Pousser les changements** :

   ```bash
   git push origin main && git push origin --tags
   ```

### Types de commits et leur impact

- ✅ **feat**: nouvelle fonctionnalité → bump **minor**
- ✅ **fix**: correction de bug → bump **patch**
- ✅ **perf**: amélioration performances → bump **patch**
- ✅ **refactor**: refactorisation → bump **patch**
- ❌ **docs**, **style**, **test**, **chore**, **ci** : pas de bump

## 🔄 Workflow recommandé

1. **Installation initiale** : `python setup_dev.py` (une seule fois)
2. **Développement normal** : Commits avec messages conventionnels
3. **Bump manuel** : Utiliser Commitizen pour gérer les versions
4. **Push avec tags** : `git push origin main && git push origin --tags`

## 🚫 Suppression des hooks pre-commit

> **⚠️ Attention : Hooks supprimés**
>
> Le système de bump automatique via hooks pre-commit a été **désactivé**. Les versions doivent désormais être gérées manuellement.
>
> - ✅ **Nouveau** : Gestion manuelle des versions
> - 🔄 **Legacy** : Les hooks ne sont plus installés par défaut
>

## 🎯 Avantages de cette approche

- ✅ **Contrôle total** : Vous décidez quand faire une release
- ✅ **Pas de problème de sync** : Tags créés et poussés ensemble
- ✅ **Changelog cohérent** : Généré localement avec tout l'historique
- ✅ **Confirmation** : Possibilité de vérifier avant publication
- ✅ **Rollback facile** : Annulation possible avant push

## 🔍 Dépannage

### Installation et tests

```bash
# Réinstaller Commitizen
python -m pip install commitizen

# Vérifier Commitizen
python -m commitizen version
```

### Problèmes courants

```bash
# Environnement virtuel non activé
source venv/bin/activate  # Unix/Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

