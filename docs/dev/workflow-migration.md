# Migration des workflows de version

## 🔄 Changement de stratégie

Le projet Galad Islands a migré d'un système de bump de version **centralisé** (GitHub Actions) vers un système **décentralisé** (hooks pre-commit locaux).

## 📊 Comparaison des approches

| Aspect | Ancien (GitHub Actions) | Nouveau (Hooks pre-commit) |
|--------|------------------------|----------------------------|
| **Déclenchement** | Automatique sur push | Automatique au commit local |
| **Latence** | ~2-5 minutes | Instantané |
| **Problèmes de sync** | Fréquents (tags non détectés) | Aucun |
| **Contrôle** | Limité | Total |
| **Offline** | Non | Oui |
| **Rollback** | Difficile | Facile (avant push) |

## ✅ Nouveau workflow recommandé

### 1. Installation (une seule fois)

```bash
# Installation complète de l'environnement de développement
python setup_dev.py

# Installe également les dépendances de développement (requirements-dev.txt)

# Ou installation des hooks uniquement
python setup/install_hooks_with_bump.py
```

### 2. Utilisation quotidienne

```bash
# Développement normal
git add nouvelle_fonctionnalite.py
git commit -m "feat: système de combat naval"
# 🎯 Le hook pre-commit détecte 'feat'
# 🔄 Bump automatique: 0.3.1 → 0.4.0
# ✅ Commit avec bump inclus

# Push avec tags
git push origin main && git push origin --tags
# 🚀 Release automatique se déclenche sur GitHub
```

### 3. Types de commits et bumps

| Type de commit | Bump appliqué | Exemple |
|----------------|---------------|---------|
| `feat: ...` | `minor` | 0.3.1 → 0.4.0 |
| `fix: ...` | `patch` | 0.3.1 → 0.3.2 |
| `perf: ...` | `patch` | 0.3.1 → 0.3.2 |
| `refactor: ...` | `patch` | 0.3.1 → 0.3.2 |
| `docs: ...` | aucun | - |
| `style: ...` | aucun | - |
| `test: ...` | aucun | - |
| `chore: ...` | aucun | - |
| `ci: ...` | aucun | - |

## 🔧 Workflow GitHub Actions (Legacy)

Le workflow `version-bump.yml` est maintenant **désactivé automatiquement** mais reste disponible pour les cas exceptionnels.

### Utilisation manuelle

1. Aller sur GitHub → Actions
2. Sélectionner "Manual Version Bump (Legacy)"
3. Cliquer "Run workflow"
4. Choisir les paramètres :
   - **Type de bump** : `auto`, `patch`, `minor`, `major`
   - **Forcer changelog** : Régénère complètement le changelog

### Quand l'utiliser ?

- 🚨 **Urgence** : Correction critique nécessitant un bump immédiat
- 🔧 **Maintenance** : Réparation d'un changelog corrompu
- 📋 **Migration** : Synchronisation après changement de stratégie
- 👥 **Équipe externe** : Contributeurs sans accès aux hooks

## 🛡️ Avantages du nouveau système

### Pour les développeurs

- ✅ **Immédiat** : Pas d'attente GitHub Actions
- ✅ **Prévisible** : Voir le bump avant push
- ✅ **Contrôlable** : Possibilité d'annuler avant push
- ✅ **Offline** : Fonctionne sans internet

### Pour le projet

- ✅ **Cohérent** : Version toujours synchronisée
- ✅ **Fiable** : Plus de problèmes de détection de tags
- ✅ **Économique** : Moins d'exécutions GitHub Actions
- ✅ **Maintenable** : Code Python plutôt que bash/YAML

## 🔄 Migration pour l'équipe

### Développeurs existants

```bash
# 1. Mise à jour du repository
git pull origin main

# 2. Installation des nouveaux hooks
python setup_dev.py

# 3. Test
python setup/test_hooks.py

# 4. Premier commit avec bump automatique
git commit -m "test: vérification du nouveau système de bump"
```

### Nouveaux développeurs

```bash
# Installation complète en une commande
python setup_dev.py
```

## 📖 Documentation complémentaire

- [Guide de gestion des versions](versioning.md)
- [Configuration des hooks](../../setup/README.md)
- [Guide de contribution](contributing.md)

## 🆘 Support et dépannage

En cas de problème avec le nouveau système :

1. **Vérifier l'installation** : `python setup/test_hooks.py`
2. **Réinstaller les hooks** : `python setup/install_hooks_with_bump.py`
3. **Utiliser le workflow manuel** : GitHub Actions → Manual Version Bump
4. **Demander de l'aide** : Créer une issue avec les logs d'erreur