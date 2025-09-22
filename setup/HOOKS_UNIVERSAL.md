# Hooks Commitizen Automatiques

## 🌍 Compatible avec tous les OS
- ✅ Windows
- ✅ Linux  
- ✅ macOS

## 🚀 Installation automatique

Les hooks commitizen sont **installés automatiquement** lors de :
- `git clone` du repository
- `git checkout` d'une branche
- `git pull`

**Aucune action manuelle requise !**

## 📝 Format de commit requis

```
type(scope): description
```

### Types autorisés
- **feat**: Nouvelle fonctionnalité
- **fix**: Correction de bug
- **docs**: Documentation
- **style**: Formatage
- **refactor**: Refactorisation
- **perf**: Performance
- **test**: Tests
- **build**: Build
- **ci**: CI/CD
- **chore**: Maintenance
- **revert**: Annulation

### ✅ Exemples valides
```bash
git commit -m "feat: ajouter système de login"
git commit -m "fix(auth): corriger bug de session"
git commit -m "docs: mettre à jour README"
git commit -m "ci: ajouter pipeline"
```

## 🛠️ Commandes utiles

```bash
# Commit interactif (recommandé)
python -m commitizen commit

# Générer changelog
python -m commitizen changelog

# Version bump
python -m commitizen bump

# Contourner temporairement (déconseillé)
git commit --no-verify
```

## 🔧 Résolution de problèmes

### Installation manuelle (si l'auto-installation échoue)
```bash
# Installer commitizen
pip install commitizen

# Installer les hooks
python -m commitizen install-hook
```

### Vérifier l'installation
```bash
python -m commitizen --version
ls -la .git/hooks/commit-msg
```

## 📚 Plus d'infos
- [Commitizen](https://commitizen-tools.github.io/commitizen/)
- [Conventional Commits](https://www.conventionalcommits.org/)
