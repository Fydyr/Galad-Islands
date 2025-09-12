#!/usr/bin/env python3
"""
Script de développement pour Galad Islands.

Automatise les tâches courantes de développement comme les tests,
le formatage du code, et la génération de documentation.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def executer_commande(commande, description):
    """
    Exécute une commande et affiche le résultat.
    
    Args:
        commande: Liste des arguments de la commande
        description: Description de l'action
    """
    print(f"🔧 {description}...")
    try:
        resultat = subprocess.run(commande, check=True, capture_output=True, text=True)
        print(f"✅ {description} terminé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de {description}:")
        print(e.stderr)
        return False

def installer_dependances():
    """Installe les dépendances du projet."""
    return executer_commande(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        "Installation des dépendances"
    )

def executer_tests():
    """Exécute tous les tests."""
    return executer_commande(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        "Exécution des tests"
    )

def executer_tests_coverage():
    """Exécute les tests avec coverage."""
    return executer_commande(
        [sys.executable, "-m", "pytest", "--cov=src", "--cov-report=html", "tests/"],
        "Exécution des tests avec coverage"
    )

def formater_code():
    """Formate le code avec Black."""
    return executer_commande(
        [sys.executable, "-m", "black", "src/", "tests/"],
        "Formatage du code"
    )

def verifier_style():
    """Vérifie le style avec Flake8."""
    return executer_commande(
        [sys.executable, "-m", "flake8", "src/", "tests/"],
        "Vérification du style"
    )

def executer_jeu():
    """Lance le jeu."""
    return executer_commande(
        [sys.executable, "main.py"],
        "Lancement du jeu"
    )

def tester_composant(nom_composant):
    """Teste un composant spécifique."""
    return executer_commande(
        [sys.executable, "-m", "pytest", f"tests/components/{nom_composant}/", "-v"],
        f"Tests du composant {nom_composant}"
    )

def verifier_interfaces():
    """Vérifie la compatibilité des interfaces."""
    return executer_commande(
        [sys.executable, "-c", 
         "from src.interfaces import entity_interface, render_interface; print('✅ Interfaces OK')"],
        "Vérification des interfaces"
    )

def status_composants():
    """Affiche le statut des composants du moteur."""
    composants = ["core", "entities", "renderer", "ai", "physics", "world"]
    print("📊 Status des composants du moteur:")
    
    for composant in composants:
        chemin = Path(f"src/components/{composant}")
        if chemin.exists():
            fichiers = list(chemin.glob("*.py"))
            if fichiers:
                print(f"  {composant:12} : ✅ {len(fichiers)} fichiers")
            else:
                print(f"  {composant:12} : 📁 dossier créé")
        else:
            print(f"  {composant:12} : ⏳ à créer")
    
    return True

def nettoyer():
    """Nettoie les fichiers temporaires."""
    patterns_a_supprimer = [
        "**/__pycache__",
        "**/*.pyc", 
        "**/*.pyo",
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        "build/",
        "dist/",
        "*.egg-info/"
    ]
    
    print("🧹 Nettoyage des fichiers temporaires...")
    racine = Path(".")
    
    for pattern in patterns_a_supprimer:
        for chemin in racine.glob(pattern):
            if chemin.is_file():
                chemin.unlink()
                print(f"  Supprimé: {chemin}")
            elif chemin.is_dir():
                import shutil
                shutil.rmtree(chemin)
                print(f"  Supprimé: {chemin}/")
    
    print("✅ Nettoyage terminé")
    return True

def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(description="Script de développement Galad Islands")
    parser.add_argument("--install", action="store_true", help="Installer les dépendances")
    parser.add_argument("--test", action="store_true", help="Exécuter les tests")
    parser.add_argument("--test-component", type=str, help="Tester un composant (core, entities, renderer, ai, physics, world)")
    parser.add_argument("--coverage", action="store_true", help="Exécuter les tests avec coverage")
    parser.add_argument("--format", action="store_true", help="Formater le code")
    parser.add_argument("--lint", action="store_true", help="Vérifier le style")
    parser.add_argument("--run", action="store_true", help="Lancer le jeu")
    parser.add_argument("--clean", action="store_true", help="Nettoyer les fichiers temporaires")
    parser.add_argument("--interfaces", action="store_true", help="Vérifier les interfaces")
    parser.add_argument("--status", action="store_true", help="Statut des composants")
    parser.add_argument("--all", action="store_true", help="Exécuter toutes les vérifications")
    
    args = parser.parse_args()
    
    # Si aucun argument, afficher l'aide
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Vérifier qu'on est dans le bon dossier
    if not Path("src").exists():
        print("❌ Ce script doit être exécuté depuis la racine du projet")
        sys.exit(1)
    
    succes = True
    
    if args.install or args.all:
        succes &= installer_dependances()
    
    if args.format or args.all:
        succes &= formater_code()
    
    if args.lint or args.all:
        succes &= verifier_style()
    
    if args.test or args.all:
        succes &= executer_tests()
    
    if args.test_component:
        succes &= tester_composant(args.test_component)
    
    if args.coverage:
        succes &= executer_tests_coverage()
    
    if args.interfaces or args.all:
        succes &= verifier_interfaces()
    
    if args.status:
        succes &= status_composants()
    
    if args.clean:
        succes &= nettoyer()
    
    if args.run:
        succes &= executer_jeu()
    
    if not succes:
        print("\n❌ Certaines opérations ont échoué")
        sys.exit(1)
    else:
        print("\n✅ Toutes les opérations ont réussi")

if __name__ == "__main__":
    main()