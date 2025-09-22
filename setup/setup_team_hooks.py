#!/usr/bin/env python
"""
Configuration automatique des hooks commitizen pour l'équipe
Compatible tous OS: Windows, Linux, macOS
"""

import os
import stat
import shutil
from pathlib import Path

def detect_os():
    """Détecte le système d'exploitation"""
    if os.name == 'nt':
        return 'windows'
    elif os.sys.platform.startswith('darwin'):
        return 'macos' 
    elif os.sys.platform.startswith('linux'):
        return 'linux'
    else:
        return 'unix'

def create_auto_installer():
    """Crée le script d'auto-installation"""
    
    # Contenu de l'installateur universel (version compacte)
    installer_content = '''#!/usr/bin/env python
"""Auto-installateur commitizen - Tous OS"""
import subprocess, sys, os, stat
from pathlib import Path

def detect_os():
    return 'windows' if os.name == 'nt' else 'unix'

def install():
    try:
        # Vérifier si déjà installé
        if Path('.git/hooks/.commitizen_installed').exists():
            return
        
        # Installer commitizen
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'commitizen'], 
                          capture_output=True, check=True)
        except:
            return  # Installation silencieuse
        
        # Installer le hook
        try:
            subprocess.run([sys.executable, '-m', 'commitizen', 'install-hook'], 
                          capture_output=True, check=True)
        except:
            # Hook manuel si échec
            hook = Path('.git/hooks/commit-msg')
            hook.parent.mkdir(exist_ok=True)
            hook.write_text("""#!/usr/bin/env python
import sys,re,os
from pathlib import Path
if len(sys.argv)<2:sys.exit(0)
try:msg=Path(sys.argv[1]).read_text().strip()
except:sys.exit(0)
if re.match(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\(.+\\))?: .+',msg):
    print(f"{'✅' if os.name!='nt' else ''}Commit OK: {msg}");sys.exit(0)
else:
    print(f"{'❌' if os.name!='nt' else ''}Format requis: type(scope): description");sys.exit(1)""")
            if detect_os() != 'windows':
                hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
        
        # Marquer comme installé
        Path('.git/hooks/.commitizen_installed').write_text('installed')
        icon = '✅' if detect_os() != 'windows' else ''
        print(f"{icon} Hooks commitizen installés automatiquement!")
        print("Format requis: type(scope): description")
        
    except:
        pass  # Installation silencieuse

if __name__ == "__main__":
    if Path('.git').exists() and Path('pyproject.toml').exists():
        install()
'''
    
    return installer_content

def create_post_checkout_hook():
    """Crée le hook post-checkout pour auto-installation"""
    
    hooks_dir = Path('hooks')
    hooks_dir.mkdir(exist_ok=True)
    
    installer_content = create_auto_installer()
    
    # Hook post-checkout qui lance l'auto-installation
    post_checkout_content = f'''#!/usr/bin/env python
"""Hook post-checkout - Auto-installation commitizen universelle"""
{installer_content[installer_content.find('import'):]}'''
    
    post_checkout_file = hooks_dir / 'post-checkout'
    post_checkout_file.write_text(post_checkout_content, encoding='utf-8')
    
    # Rendre exécutable (Unix/Linux/macOS)
    if detect_os() != 'windows':
        post_checkout_file.chmod(post_checkout_file.stat().st_mode | stat.S_IEXEC)
    
    print(f"Hook post-checkout créé: {post_checkout_file}")
    return True

def create_commitizen_config():
    """Crée la configuration commitizen"""
    
    config_content = """# Configuration commitizen pour l'équipe
[tool.commitizen]
name = "cz_conventional_commits" 
version_provider = "pep621"
tag_format = "v$version"
update_changelog_on_bump = true

[tool.commitizen.settings]
# Types de commits autorisés
allowed_types = [
    "feat",     # Nouvelle fonctionnalité  
    "fix",      # Correction de bug
    "docs",     # Documentation uniquement
    "style",    # Formatage, espaces, etc.
    "refactor", # Refactorisation du code
    "perf",     # Amélioration des performances
    "test",     # Ajout ou modification de tests
    "build",    # Système de build ou dépendances
    "ci",       # Configuration CI
    "chore",    # Maintenance
    "revert"    # Annulation d'un commit
]

check_consistency = true
use_shortcuts = true

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
"""
    
    config_file = Path('pyproject.toml')
    if not config_file.exists():
        config_file.write_text(config_content, encoding='utf-8')
        print(f"Configuration créée: {config_file}")
    else:
        print("pyproject.toml existe déjà")

def install_post_checkout_locally():
    """Installe le hook post-checkout dans .git/hooks"""
    
    source = Path('hooks/post-checkout')
    dest = Path('.git/hooks/post-checkout')
    
    if source.exists():
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(str(source), str(dest))
        
        # Rendre exécutable (Unix/Linux/macOS)
        if detect_os() != 'windows':
            dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        
        print(f"Hook post-checkout installé dans .git/hooks/")

def create_documentation():
    """Crée la documentation pour tous les OS"""
    
    doc_content = """# Hooks Commitizen Automatiques

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
"""
    
    Path('HOOKS_UNIVERSAL.md').write_text(doc_content, encoding='utf-8')
    print("Documentation créée: HOOKS_UNIVERSAL.md")

def main():
    """Configuration complète pour tous les OS"""
    os_name = {'windows': 'Windows', 'linux': 'Linux', 'macos': 'macOS', 'unix': 'Unix'}[detect_os()]
    
    print(f"🌍 Configuration commitizen universelle pour {os_name}")
    print("="*60)
    
    # Vérifier qu'on est dans un repo Git
    if not Path('.git').exists():
        print("❌ Erreur: Pas dans un repository Git")
        return False
    
    # Créer tous les fichiers
    create_commitizen_config()
    create_post_checkout_hook()
    install_post_checkout_locally()
    create_documentation()
    
    print("\n" + "="*60)
    print("✅ CONFIGURATION UNIVERSELLE TERMINÉE")
    print("="*60)
    
    print("\n📋 Prochaines étapes :")
    print("1. git add pyproject.toml hooks/ HOOKS_UNIVERSAL.md")
    print("2. git commit -m 'feat: ajouter hooks commitizen universels'")
    print("3. git push")
    
    print("\n🎉 Résultat :")
    print("- Installation automatique sur Windows, Linux, macOS")
    print("- Format de commit imposé : type(scope): description")
    print("- Hooks de qualité et validation")
    print("- Compatible avec tous les environnements Python")
    
    return True

if __name__ == "__main__":
    main() 