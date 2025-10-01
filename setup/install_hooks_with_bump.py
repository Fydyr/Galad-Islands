#!/usr/bin/env python3
"""
Installation des hooks Git avec bump automatique de version
Peut être importé dans setup_dev.py ou utilisé directement
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_color_print():
    """Retourne les fonctions de print coloré si colorama est disponible"""
    try:
        from colorama import init, Fore, Style
        init()
        
        def success(msg):
            print(Fore.GREEN + "✅ " + msg + Style.RESET_ALL)
        
        def warning(msg):
            print(Fore.YELLOW + "⚠️  " + msg + Style.RESET_ALL)
            
        def info(msg):
            print(Fore.BLUE + "ℹ️  " + msg + Style.RESET_ALL)
            
        def error(msg):
            print(Fore.RED + "❌ " + msg + Style.RESET_ALL)
            
        def title(msg):
            print(Fore.CYAN + Style.BRIGHT + f"🔧 {msg}" + Style.RESET_ALL)
            
        return success, warning, info, error, title
        
    except ImportError:
        def success(msg):
            print(f"✅ {msg}")
        
        def warning(msg):
            print(f"⚠️  {msg}")
            
        def info(msg):
            print(f"ℹ️  {msg}")
            
        def error(msg):
            print(f"❌ {msg}")
            
        def title(msg):
            print(f"🔧 {msg}")
            
        return success, warning, info, error, title

def is_windows():
    """Détecte si on est sur Windows"""
    return os.name == 'nt'

def is_git_repo():
    """Vérifie qu'on est dans un repository Git"""
    return Path('.git').exists()

def is_venv_active():
    """Vérifie si un environnement virtuel est actif"""
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

def check_commitizen():
    """Vérifie que commitizen est installé et accessible"""
    try:
        result = subprocess.run([sys.executable, '-m', 'commitizen', 'version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, None
    except Exception:
        return False, None

def install_commitizen():
    """Installe commitizen si nécessaire"""
    success, warning, info, error, title = get_color_print()
    
    info("Installation de commitizen...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'commitizen'], 
                      check=True, capture_output=True)
        success("Commitizen installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Échec de l'installation de commitizen: {e}")
        return False

def copy_hook(source_hook, target_hook):
    """Copie un hook et le rend exécutable"""
    success, warning, info, error, title = get_color_print()
    
    if not Path(source_hook).exists():
        warning(f"Hook source non trouvé: {source_hook}")
        return False
    
    try:
        # Créer le répertoire .git/hooks s'il n'existe pas
        Path(target_hook).parent.mkdir(parents=True, exist_ok=True)
        
        # Copier le fichier
        shutil.copy2(source_hook, target_hook)
        
        # Rendre exécutable (Unix/Linux/macOS)
        if not is_windows():
            os.chmod(target_hook, 0o755)
        
        success(f"Hook installé: {Path(target_hook).name}")
        return True
        
    except Exception as e:
        error(f"Erreur lors de la copie du hook: {e}")
        return False

def install_hooks_with_bump():
    """Installation principale des hooks avec bump automatique"""
    success, warning, info, error, title = get_color_print()
    
    title("Installation des hooks Git avec bump automatique")
    
    # Vérifications préalables
    if not is_git_repo():
        error("Pas dans un repository Git")
        return False
    
    if not is_venv_active():
        warning("Aucun environnement virtuel détecté")
        warning("Le hook pourrait ne pas fonctionner correctement")
    
    # Vérifier commitizen
    cz_available, cz_version = check_commitizen()
    
    if not cz_available:
        warning("Commitizen non trouvé, tentative d'installation...")
        if not install_commitizen():
            error("Impossible d'installer commitizen")
            return False
        cz_available, cz_version = check_commitizen()
    
    if cz_available:
        success(f"Commitizen v{cz_version} disponible")
    else:
        error("Commitizen non accessible après installation")
        return False
    
    # Installation des hooks
    info("Installation des hooks...")
    
    hooks_installed = 0
    
    # Hook pre-commit (bump automatique)
    if copy_hook("hooks/pre-commit", ".git/hooks/pre-commit"):
        hooks_installed += 1
    
    # Hook commit-msg (validation format - si il existe)
    if Path("hooks/commit-msg").exists():
        if copy_hook("hooks/commit-msg", ".git/hooks/commit-msg"):
            hooks_installed += 1
    elif Path(".git/hooks/commit-msg").exists():
        info("Hook commit-msg existant conservé")
    
    # Hook post-checkout (si il existe)
    if Path("hooks/post-checkout").exists():
        if copy_hook("hooks/post-checkout", ".git/hooks/post-checkout"):
            hooks_installed += 1
    elif Path(".git/hooks/post-checkout").exists():
        info("Hook post-checkout existant conservé")
    
    if hooks_installed > 0:
        success(f"{hooks_installed} hook(s) installé(s)")
        
        # Documentation
        print("\n" + "="*60)
        title("Comment ça marche")
        print("1. Faites vos commits normalement avec des messages conventionnels")
        print("2. Le hook pre-commit détectera automatiquement les commits feat/fix/perf/refactor")
        print("3. Un bump de version sera effectué automatiquement avant le commit")
        print("4. La version et le changelog seront mis à jour")
        print()
        
        title("Types de commits qui déclenchent un bump")
        success("feat: nouvelle fonctionnalité (bump minor)")
        success("fix: correction de bug (bump patch)")
        success("perf: amélioration des performances (bump patch)")
        success("refactor: refactorisation (bump patch)")
        print()
        
        title("Types de commits qui ne déclenchent PAS de bump")
        info("docs: documentation")
        info("style: formatage")
        info("test: tests")
        info("chore: maintenance")
        info("ci: configuration CI")
        print("="*60)
        
        return True
    else:
        error("Aucun hook installé")
        return False

def main():
    """Fonction principale si le script est exécuté directement"""
    try:
        # Changer vers le répertoire racine du projet
        script_dir = Path(__file__).parent
        project_root = script_dir.parent if script_dir.name == 'setup' else script_dir
        os.chdir(project_root)
        
        return install_hooks_with_bump()
        
    except KeyboardInterrupt:
        print("\n⏸️  Installation interrompue par l'utilisateur")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)