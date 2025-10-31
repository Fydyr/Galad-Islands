#!/usr/bin/env python3
"""
Script d'installation pour l'environnement de développement Galad Islands.
- Installe Commitizen (pour le versionning et les hooks)
- Installe les dépendances du projet (requirements.txt)

À lancer une seule fois par chaque développeur, jamais in production ni in le build final.
"""

import subprocess
import sys
import os

# Détection d'un environnement virtuel Python
def is_venv():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

def prompt_create_venv():
    print("\nAucun environnement virtuel Python détecté.")
    rep = input("Voulez-vous en créer un maintenant ? [O/n] ").strip().lower()
    if rep in ("", "o", "oui", "y", "yes"):
        venv_dir = "venv"
        print(f"Création de l'environnement virtuel dans ./{venv_dir} ...")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir])
        print(f"✔️  Environnement virtuel créé. Activez-le puis relancez ce script :")
        if os.name == 'nt':
            print(f"  .\\{venv_dir}\\Scripts\\activate")
        else:
            print(f"  source ./{venv_dir}/bin/activate")
        sys.exit(0)
    else:
        print("⚠️  Installation dans l'environnement global (déconseillé)")

# Check la présence d'un venv
if not is_venv():
    prompt_create_venv()

# Utilitaire pour exécuter une commande shell et afficher la sortie

def run(cmd, check=True):
    # Affichage couleur cross-plateforme
    try:
        from colorama import init, Fore, Style
        init()
        print(Fore.BLUE + Style.BRIGHT + f"> {cmd}" + Style.RESET_ALL)
    except ImportError:
        print(f"> {cmd}")
    # shell=True fonctionne sur Windows et Linux
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)


# Upgrade pip (toujours utile)
run(f"{sys.executable} -m pip install --upgrade pip", check=True)

# Installer colorama pour l'affichage couleur cross-plateforme (optionnel)
try:
    import colorama
except ImportError:
    run(f"{sys.executable} -m pip install colorama", check=False)

# Installer Commitizen (local, pas global)
run(f"{sys.executable} -m pip install commitizen", check=True)


# Installer les requirements du projet
req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
if not os.path.exists(req_path):
    req_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "requirements.txt"))
if os.path.exists(req_path):
    run(f"{sys.executable} -m pip install -r {req_path}", check=True)
else:
    print("Avertissement : requirements.txt introuvable.")

# Installer les requirements de développement
req_dev_path = os.path.join(os.path.dirname(__file__), "requirements-dev.txt")
if not os.path.exists(req_dev_path):
    req_dev_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "requirements-dev.txt"))
if os.path.exists(req_dev_path):
    run(f"{sys.executable} -m pip install -r {req_dev_path}", check=True)
else:
    print("Avertissement : requirements-dev.txt introuvable.")

try:
    from colorama import Fore, Style
    print(Fore.GREEN + Style.BRIGHT + "✔️  Environnement de développement prêt !" + Style.RESET_ALL)
except ImportError:
    print("✔️  Environnement de développement prêt !")


# Option pour Clean up l'ancienne installation des hooks avec bump automatique
def clean_old_bump_hooks():
    print("\nNettoyage des anciennes installations de hooks avec bump automatique...")
    try:
        hooks_path = os.path.join(os.getcwd(), ".git", "hooks")
        pre_commit_hook = os.path.join(hooks_path, "pre-commit")
        if os.path.exists(pre_commit_hook):
            os.remove(pre_commit_hook)
            print("✔️  Ancien hook pre-commit supprimé.")
        else:
            print("Aucun ancien hook pre-commit détecté.")
    except Exception as e:
        print(f"Erreur lors de la suppression du hook : {e}")

if __name__ == "__main__":
    print("Voulez-vous nettoyer les anciennes installations de hooks avec bump automatique ? [O/n]")
    response = input().strip().lower()
    if response in ("o", "oui", "y", "yes", ""):
        clean_old_bump_hooks()
        
# Installer les hooks Commitizen universels
try:
    import setup.install_commitizen_universal as install_cz
    import setup.setup_team_hooks as setup_hooks
    print("\nInstallation des hooks Commitizen universels...")
    install_cz.main()
    setup_hooks.main()
except ImportError as e:
    print(f"Avertissement : {e}. Hooks non installés.")

print("\n" + "="*50)
print("✨ ENVIRONNEMENT DE DÉVELOPPEMENT PRÊT !")
print("="*50)
print("✅ Commitizen installé (commande : cz)")
print("✅ Dépendances Python installées")
print("✅ Versionning conventionnel configuré")
print("\n🚀 Tu peux maintenant développer avec Commitizen pour des commits conventionnels !")
