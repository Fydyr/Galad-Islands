#!/usr/bin/env python3
"""
Script de lancement des tests pour Galad Islands
Permet de lancer les tests avec différentes options de configuration
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print('='*60)
    print(f"Commande: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Code de retour: {result.returncode}")

        return result.returncode == 0

    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Lanceur de tests pour Galad Islands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Lancer tous les tests
  python run_tests.py

  # Lancer seulement les tests unitaires
  python run_tests.py --unit

  # Lancer seulement les tests d'intégration
  python run_tests.py --integration

  # Lancer les tests avec couverture
  python run_tests.py --coverage

  # Lancer les tests en mode verbeux
  python run_tests.py --verbose

  # Lancer seulement un fichier de test spécifique
  python run_tests.py --file test_processors.py

  # Lancer les tests de performance
  python run_tests.py --performance

  # Générer un rapport HTML de couverture
  python run_tests.py --coverage --html-report
        """
    )

    parser.add_argument('--unit', action='store_true',
                       help='Lancer seulement les tests unitaires')
    parser.add_argument('--integration', action='store_true',
                       help='Lancer seulement les tests d\'intégration')
    parser.add_argument('--performance', action='store_true',
                       help='Lancer seulement les tests de performance')
    parser.add_argument('--coverage', action='store_true',
                       help='Générer un rapport de couverture')
    parser.add_argument('--html-report', action='store_true',
                       help='Générer un rapport HTML de couverture (implique --coverage)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mode verbeux')
    parser.add_argument('--file', type=str,
                       help='Lancer seulement un fichier de test spécifique')
    parser.add_argument('--fail-fast', action='store_true',
                       help='Arrêter au premier échec')
    parser.add_argument('--no-capture', action='store_true',
                       help='Ne pas capturer la sortie (utile pour debug)')

    args = parser.parse_args()

    # Vérifier que pytest est installé
    try:
        import pytest
    except ImportError:
        print("❌ pytest n'est pas installé. Installez-le avec:")
        print("   pip install pytest pytest-cov pytest-mock")
        sys.exit(1)

    # Construire la commande pytest
    cmd = [sys.executable, '-m', 'pytest']

    # Options de base depuis pyproject.toml
    # Les options sont déjà configurées dans pyproject.toml

    # Filtres par type de test
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.performance:
        cmd.extend(['-m', 'performance'])

    # Fichier spécifique
    if args.file:
        if not args.file.startswith('test_'):
            args.file = f'test_{args.file}'
        if not args.file.endswith('.py'):
            args.file = f'{args.file}.py'
        cmd.append(f'tests/{args.file}')

    # Options de couverture
    if args.coverage or args.html_report:
        cmd.extend(['--cov=src', '--cov-report=term-missing'])
        if args.html_report:
            cmd.append('--cov-report=html:htmlcov')

    # Options générales
    if args.verbose:
        cmd.append('-v')
    if args.fail_fast:
        cmd.append('-x')
    if args.no_capture:
        cmd.append('-s')

    # Lancer les tests
    success = run_command(cmd, "LANCEMENT DES TESTS GALAD ISLANDS")

    # Résumé final
    print(f"\n{'='*60}")
    if success:
        print("✅ TOUS LES TESTS SONT RÉUSSIS!")
        if args.coverage or args.html_report:
            print("📊 Rapport de couverture généré")
            if args.html_report:
                print("🌐 Rapport HTML disponible dans: htmlcov/index.html")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("   Vérifiez la sortie ci-dessus pour les détails")
    print('='*60)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()