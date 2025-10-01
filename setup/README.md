# Scripts de configuration - Galad Islands

Ce dossier contient les scripts de configuration pour l'environnement de développement.

## 📋 Scripts disponibles

### `setup_dev.py` - Script principal
Script d'installation principal pour l'environnement de développement.

```bash
python setup_dev.py
```

**Installe automatiquement :**
- Environnement virtuel Python (si nécessaire)
- Commitizen pour la gestion des versions
- Dépendances du projet (requirements.txt)
- Hooks Git avec bump automatique de version

### `install_hooks_with_bump.py` - Installation des hooks
Script spécialisé pour l'installation des hooks Git avec bump automatique.

```bash
python setup/install_hooks_with_bump.py
```

**Fonctionnalités :**
- ✅ Installation automatique des hooks pre-commit, commit-msg, post-checkout
- ✅ Vérification de commitizen
- ✅ Installation de commitizen si nécessaire
- ✅ Documentation intégrée
- ✅ Support Windows/Linux/macOS

### `test_hooks.py` - Tests de vérification
Script de test pour vérifier l'installation des hooks.

```bash
python setup/test_hooks.py
```

**Vérifie :**
- ✅ Présence des hooks installés
- ✅ Permissions d'exécution (Unix)
- ✅ Disponibilité de commitizen
- ✅ État du repository Git

### `install_hooks_with_bump.sh` - Version bash (legacy)
Version bash du script d'installation (conservée pour compatibilité).

```bash
./setup/install_hooks_with_bump.sh
```

## 🚀 Installation rapide

Pour une installation complète de l'environnement de développement :

```bash
# Installation complète
python setup_dev.py

# Ou installation manuelle des hooks uniquement
python setup/install_hooks_with_bump.py

# Test de l'installation
python setup/test_hooks.py
```

## 🔧 Système de bump automatique

Une fois installé, le système fonctionne automatiquement :

1. **Commit normal** : `git commit -m "feat: nouvelle fonctionnalité"`
2. **Hook pre-commit s'exécute** : Détecte le type `feat`
3. **Bump automatique** : Version 0.3.1 → 0.4.0
4. **Changelog mis à jour** : Nouvelles entrées ajoutées
5. **Push** : `git push origin main && git push origin --tags`

### Types de commits qui déclenchent un bump

| Type | Description | Bump |
|------|-------------|------|
| `feat` | Nouvelle fonctionnalité | `minor` |
| `fix` | Correction de bug | `patch` |
| `perf` | Amélioration performances | `patch` |
| `refactor` | Refactorisation | `patch` |

### Types de commits sans bump

| Type | Description |
|------|-------------|
| `docs` | Documentation |
| `style` | Formatage |
| `test` | Tests |
| `chore` | Maintenance |
| `ci` | Configuration CI |

## 📖 Documentation

Pour plus de détails, consultez :
- [Guide de gestion des versions](../docs/dev/version-management.md)
- [Guide de contribution](../docs/dev/contributing.md)