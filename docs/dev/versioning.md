# Gestion des versions

## 🎯 Objectif

Ce document explique comment gérer les versions du projet Galad Islands avec un système de bump automatique via les hooks Git.

> **💡 Info : Migration du workflow de version**
> 
> Le projet a récemment migré d'un système de bump centralisé (GitHub Actions) vers un système décentralisé (hooks pre-commit locaux). 
> 
> 📖 **[Consultez le guide de migration](workflow-migration.md)** pour comprendre les changements et les avantages du nouveau système.

## 🚀 Nouveau : Bump automatique avec hooks pre-commit

Le système de bump automatique via hook pre-commit est maintenant la méthode recommandée. Il bumpe automatiquement la version lors des commits éligibles.

### Installation du hook

```bash
# Installation automatique (recommandé)
python setup/install_hooks_with_bump.py

# Ou via setup_dev.py (installation complète, y compris les dépendances de développement)
python setup_dev.py

# Ou installation manuelle
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit  # Unix/Linux/macOS uniquement
```

### Comment ça fonctionne

1. **Vous faites un commit normal** : `git commit -m "feat: nouvelle fonctionnalité"`
2. **Le hook pre-commit s'exécute** : Détecte que c'est un commit `feat`
3. **Bump automatique** : Version passe de 0.3.1 → 0.4.0
4. **Changelog mis à jour** : Nouveau changelog généré
5. **Commit final** : Votre commit + bump inclus

### Types de commits qui déclenchent un bump

- ✅ **feat**: nouvelle fonctionnalité → bump **minor**
- ✅ **fix**: correction de bug → bump **patch**
- ✅ **perf**: amélioration performances → bump **patch**
- ✅ **refactor**: refactorisation → bump **patch**

### Types de commits qui NE déclenchent PAS de bump

- ❌ **docs**: documentation uniquement
- ❌ **style**: formatage, espaces
- ❌ **test**: ajout/modification de tests
- ❌ **chore**: maintenance
- ❌ **ci**: configuration CI

## 🛠️ Méthodes disponibles

### Option 1 : Hooks pre-commit automatiques (Recommandé)

```bash
# Installation du système automatique
python setup_dev.py

# Ou installation des hooks uniquement
python setup/install_hooks_with_bump.py

# Test de l'installation
python setup/test_hooks.py

# Utilisation : commits normaux avec bump automatique
git commit -m "feat: nouvelle fonctionnalité"  # → bump minor automatique
```

Le système automatique :

- ✅ Multi-plateforme (Windows, Linux, macOS)
- ✅ Détection automatique des commits éligibles
- ✅ Bump de version instantané
- ✅ Changelog mis à jour automatiquement
- ✅ Pas d'intervention manuelle nécessaire
- ✅ Fonctionne avec l'environnement virtuel

### Option 2 : Commandes manuelles

```bash
# 1. Activer l'environnement virtuel
source venv/bin/activate

# 2. S'assurer d'être à jour
git checkout main && git pull origin main

# 3. Effectuer le bump
python -m commitizen bump --increment patch --yes --changelog

# 4. Pousser les changements
git push origin main && git push origin --tags
```

### Option 3 : Scripts de fallback (cas particuliers)

```bash
# Si les hooks ne fonctionnent pas, bump manuel avec Python
python -c "
import subprocess, sys
subprocess.run([sys.executable, '-m', 'commitizen', 'bump', '--yes', '--changelog'])
"

# Ou commandes commitizen directes
python -m commitizen bump --increment patch --yes --changelog
python -m commitizen bump --increment minor --yes --changelog
python -m commitizen bump --increment major --yes --changelog
```

## 🔄 Workflow recommandé

1. **Installation initiale** : `python setup_dev.py` (une seule fois)
2. **Développement normal** : Commits avec messages conventionnels
3. **Bump automatique** : Le hook pre-commit gère tout automatiquement
4. **Push avec tags** : `git push origin main && git push origin --tags`

## 🚫 Workflow GitHub Actions (Déprécié)

> **⚠️ Attention : Workflow déprécié**
> 
> Le workflow automatique GitHub Actions `version-bump.yml` a été **désactivé** et remplacé par les hooks pre-commit locaux.
> 
> - ✅ **Nouveau** : Bump automatique via hooks pre-commit
> - 🔄 **Legacy** : Workflow manuel uniquement (cas exceptionnels)
> 
> 📖 **[Voir le guide de migration](workflow-migration.md)** pour plus de détails sur cette transition.

Le workflow `version-bump.yml` reste disponible en mode **manuel uniquement** pour les cas exceptionnels (urgences, maintenance, etc.).

## 🎯 Avantages de cette approche

- ✅ **Contrôle total** : Vous décidez quand faire une release
- ✅ **Pas de problème de sync** : Tags créés et poussés ensemble
- ✅ **Changelog cohérent** : Généré localement avec tout l'historique
- ✅ **Confirmation** : Possibilité de vérifier avant publication
- ✅ **Rollback facile** : Annulation possible avant push

## 🔍 Dépannage

### Installation et tests

```bash
# Réinstaller les hooks
python setup/install_hooks_with_bump.py

# Tester l'installation
python setup/test_hooks.py

# Vérifier commitizen
python -m commitizen version
```

### Problèmes courants

```bash
# Environnement virtuel non activé
source venv/bin/activate  # Unix/Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Vérifier les hooks installés
ls -la .git/hooks/pre-commit
```

### Conflit avec le workflow GitHub

- Le workflow ne devrait plus se déclencher après un bump manuel
- Si problème, désactivez temporairement le workflow dans `.github/workflows/version-bump.yml`

## 📚 Documentation complémentaire

- 🔄 **[Guide de migration des workflows](workflow-migration.md)** - Transition vers les hooks pre-commit
- 🛠️ **[Configuration des hooks](../setup/README.md)** - Scripts d'installation et tests
- 👥 **[Guide de contribution](contributing.md)** - Conventions de commit et processus