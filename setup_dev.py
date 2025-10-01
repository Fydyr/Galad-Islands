#!/usr/bin/env python3
"""
Script d'installation pour l'environnement de développement Galad Islands.
- Installe Commitizen (pour le versionning et les hooks)
- Installe les dépendances du projet (requirements.txt)

À lancer une seule fois par chaque développeur, jamais en production ni dans le build final.
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

# Vérifier la présence d'un venv
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

try:
    from colorama import Fore, Style
    print(Fore.GREEN + Style.BRIGHT + "✔️  Environnement de développement prêt !" + Style.RESET_ALL)
except ImportError:
    print("✔️  Environnement de développement prêt !")


# Installer les hooks commitizen universels (si les modules existent)
try:
    import setup.install_commitizen_universal as install_cz
    import setup.setup_team_hooks as setup_hooks
    print("\nInstallation des hooks commitizen universels...")
    install_cz.main()
    setup_hooks.main()
except ImportError as e:
    print(f"Avertissement : {e}. Hooks non installés.")

print("- Commitizen installé (commande : cz)")
print("- Dépendances Python installées")
print("- Hooks commitizen installés (si setup_team_hooks.py présent)")
print("- Tu peux maintenant utiliser les hooks et le versionning conventionnel !")
