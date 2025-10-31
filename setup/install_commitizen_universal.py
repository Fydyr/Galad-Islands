#!/usr/bin/env python
"""
Automatic commitizen installation - Compatible with all OSes
Windows, Linux, macOS
"""

import subprocess
import sys
import os
import stat
from pathlib import Path

def detect_os():
    """Detects the operating system"""
    if os.name == 'nt':
        return 'windows'
    elif sys.platform.startswith('darwin'):
        return 'macos'
    elif sys.platform.startswith('linux'):
        return 'linux'
    else:
        return 'unix'

def get_os_info():
    """Returns OS info with appropriate emojis"""
    os_type = detect_os()
    
    os_info = {
        'windows': {'name': 'Windows', 'icon': '', 'shell': True},
        'linux': {'name': 'Linux', 'icon': '🐧', 'shell': False},
        'macos': {'name': 'macOS', 'icon': '🍎', 'shell': False},
        'unix': {'name': 'Unix', 'icon': '🖥️', 'shell': False}
    }
    
    return os_info.get(os_type, os_info['unix'])

def run_command(cmd, description, shell=False):
    """Executes a command with multi-OS error handling"""
    os_info = get_os_info()
    icon = os_info['icon']
    
    print(f"{icon} {description}...")
    
    try:
        if isinstance(cmd, str) and shell:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=shell)
        
        success_icon = "" if detect_os() == 'windows' else "✅"
        print(f"{success_icon} {description} - OK")
        
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        error_icon = "" if detect_os() == 'windows' else "❌"
        print(f"{error_icon} {description} - Error")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def find_python_executable():
    """Trouve le bon exécutable Python selon l'OS"""
    os_type = detect_os()
    
    if os_type == 'windows':
        candidates = ['py', 'python', 'python3']
    else:
        candidates = ['python3', 'python']
    
    for candidate in candidates:
        try:
            result = subprocess.run([candidate, '--version'], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                return candidate
        except:
            continue
    
    return sys.executable

def install_commitizen():
    """Installe commitizen sur all OS"""
    python_cmd = find_python_executable()
    
    # Check sidéjà installé
    try:
        result = subprocess.run([python_cmd, '-m', 'commitizen', '--version'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            success_icon = "" if detect_os() == 'windows' else "✅"
            print(f"{success_icon} commitizen déjà installé: {result.stdout.strip()}")
            return True
    except:
        pass
    
    # Installer commitizen
    os_info = get_os_info()
    cmd = [python_cmd, '-m', 'pip', 'install', 'commitizen']
    return run_command(cmd, f"Installation commitizen sur {os_info['name']}")

def create_commitizen_config():
    """creates la configuration commitizen universelle"""
    
    config_content = """[tool.commitizen]
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
    "test",     # add ou modification de tests
    "build",    # Système de build ou dépendances
    "ci",       # Configuration CI
    "chore",    # Maintenance
    "revert"    # Annulation d'un commit
]

# Validation stricte
check_consistency = true
use_shortcuts = true

[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"
"""
    
    config_file = Path('pyproject.toml')
    
    if config_file.exists():
        # Check siconfig commitizen existe déjà
        content = config_file.read_text(encoding='utf-8')
        if '[tool.commitizen]' not in content:
            content += '\n' + config_content
            config_file.write_text(content, encoding='utf-8')
            print("Configuration ajoutée à pyproject.toml existant")
        else:
            print("Configuration commitizen déjà présente")
    else:
        # Create nouveau file
        config_file.write_text(config_content, encoding='utf-8')
        print("Configuration créée: pyproject.toml")
    
    return True

def install_hook_universal():
    """Installe le hook commit-msg sur all OS"""
    python_cmd = find_python_executable()
    
    # Essayer l'installation automatique commitizen
    cmd = [python_cmd, '-m', 'commitizen', 'install-hook']
    if run_command(cmd, "Installation du hook commit-msg via commitizen"):
        return True
    
    # Si échec, installation manuelle universelle
    print("Installation manuelle du hook...")
    return create_universal_hook()

def create_universal_hook():
    """creates le hook manuellement pour all OS"""
    
    hook_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hook commit-msg universel - Compatible Windows/Linux/macOS
Validation des conventions de commit (Conventional Commits)
"""

import sys
import os
import re
from pathlib import Path

def is_windows():
    """Détecte Windows"""
    return os.name == 'nt'

def validate_commit_msg():
    """Valide le message de commit selon les conventions"""
    
    # Check les arguments
    if len(sys.argv) < 2:
        return True
    
    msg_file = Path(sys.argv[1])
    if not msg_file.exists():
        return True
    
    # Lire le message avec gestion d'encodage
    try:
        message = msg_file.read_text(encoding='utf-8').strip()
    except UnicodeDecodeError:
        try:
            message = msg_file.read_text(encoding='cp1252').strip()
        except:
            message = msg_file.read_text().strip()
    
    # Ignorer les messages vides et les merges
    if not message or message.startswith('Merge'):
        return True
    
    # Prendre seulement la première ligne
    first_line = message.split('\\n')[0].strip()
    
    # Pattern pour conventional commits
    pattern = r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\(.+\\))?: .+'
    
    if re.match(pattern, first_line):
        # Message de succès adapté à l'OS
        if is_windows():
            print(f"Commit valide: {first_line}")
        else:
            print(f"✅ Commit valide: {first_line}")
        return True
    else:
        # Messages d'error adaptés à l'OS
        if is_windows():
            print(f"Format invalide: {first_line}")
            print("Format requis: type(scope): description")
            print("Types autorises: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert")
        else:
            print(f"❌ Format invalide: {first_line}")
            print("📝 Format requis: type(scope): description")
            print("🏷️  Types autorisés: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert")
        
        print("\\nExemples valides:")
        print("  feat: Add nouvelle fonctionnalité")
        print("  fix(auth): corriger bug de connexion")  
        print("  ci: configurer pipeline")
        print("  docs: mettre à jour README")
        
        return False

if __name__ == "__main__":
    sys.exit(0 if validate_commit_msg() else 1)
'''
    
    # Create le dossier hooks
    hooks_dir = Path('.git/hooks')
    hooks_dir.mkdir(exist_ok=True)
    
    # Create le hook
    hook_file = hooks_dir / 'commit-msg'
    hook_file.write_text(hook_content, encoding='utf-8')
    
    # Rendre exécutable (Unix/Linux/macOS seulement)
    if detect_os() != 'windows':
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
    
    success_icon = "" if detect_os() == 'windows' else "✅"
    print(f"{success_icon} Hook commit-msg créé manuellement")
    return True

def test_installation():
    """Teste l'installation sur all OS"""
    python_cmd = find_python_executable()
    os_info = get_os_info()
    
    print(f"{os_info['icon']} Test sur {os_info['name']}...")
    
    # Tester commitizen
    try:
        result = subprocess.run([python_cmd, '-m', 'commitizen', '--help'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            success_icon = "" if detect_os() == 'windows' else "✅"
            print(f"{success_icon} commitizen fonctionne")
        else:
            warning_icon = "" if detect_os() == 'windows' else "⚠️"
            print(f"{warning_icon} commitizen installé mais problème mineur")
    except:
        warning_icon = "" if detect_os() == 'windows' else "⚠️"
        print(f"{warning_icon} Impossible de tester commitizen")
    
    # Check le hook
    hook_file = Path('.git/hooks/commit-msg')
    if hook_file.exists():
        success_icon = "" if detect_os() == 'windows' else "✅"
        print(f"{success_icon} Hook commit-msg installé")
        
        # Check les permissions (Unix seulement)
        if detect_os() != 'windows':
            is_executable = hook_file.stat().st_mode & stat.S_IEXEC
            if is_executable:
                print("✅ Hook exécutable")
            else:
                print("⚠️  Hook non exécutable, correction...")
                hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
    else:
        warning_icon = "" if detect_os() == 'windows' else "⚠️"
        print(f"{warning_icon} Hook commit-msg manquant")

def show_universal_usage():
    """Affiche les instructions pour all OS"""
    os_info = get_os_info()
    python_cmd = find_python_executable()
    
    separator = "=" * 60
    print(f"\\n{separator}")
    print(f"{os_info['icon']} INSTALLATION TERMINÉE SUR {os_info['name'].upper()}")
    print(separator)
    
    print("\\nUtilisation:")
    print("1. Commit interactif (recommandé):")
    print(f"   {python_cmd} -m commitizen commit")
    
    print("\\n2. Commit direct (validé automatiquement):")
    print("   git commit -m 'feat: nouvelle fonctionnalité'")
    print("   git commit -m 'fix(auth): corriger bug'")
    print("   git commit -m 'ci: configurer pipeline'")
    
    print("\\nTypes autorisés:")
    print("   feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert")
    
    print("\\nCommandes utiles:")
    print(f"   {python_cmd} -m commitizen --help")
    print(f"   {python_cmd} -m commitizen bump")
    print(f"   {python_cmd} -m commitizen changelog")

def main():
    """Installation universelle pour all OS"""
    os_info = get_os_info()
    
    print(f"{os_info['icon']} Installation commitizen sur {os_info['name']}")
    print("="*60)
    
    # Check qu'on est in un repo Git
    if not Path('.git').exists():
        error_icon = "" if detect_os() == 'windows' else "❌"
        print(f"{error_icon} Erreur: Pas dans un repository Git")
        return False
    
    success = True
    
    # 1. Installer commitizen
    if not install_commitizen():
        success = False
    
    # 2. Create la configuration
    if success:
        create_commitizen_config()
    
    # 3. Installer le hook
    if success and not install_hook_universal():
        success = False
    
    # 4. Tester l'installation
    if success:
        test_installation()
        show_universal_usage()
    else:
        error_icon = "" if detect_os() == 'windows' else "❌"
        print(f"\\n{error_icon} Installation échouée")
        print("Solution manuelle:")
        print("1. pip install commitizen")
        print("2. Créer pyproject.toml avec la config")
        print("3. python -m commitizen install-hook")
    
    return success

if __name__ == "__main__":
    main()