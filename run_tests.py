#!/usr/bin/env python3
"""
Test launcher script for Galad Islands
Allows running tests with different configuration options
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Executes a command and displays the result."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print('='*60)
    print(f"Command: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")

        return result.returncode == 0

    except Exception as e:
        print(f"Execution error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Lanceur de tests pour Galad Islands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Run all tests
  python run_tests.py

  # Run only unit tests
  python run_tests.py --unit

  # Run only integration tests
  python run_tests.py --integration

  # Run tests with coverage
  python run_tests.py --coverage

  # Run tests in verbose mode
  python run_tests.py --verbose

  # Run only a specific test file
  python run_tests.py --file test_processors.py

  # Run performance tests
  python run_tests.py --performance

  # Generate an HTML coverage report
  python run_tests.py --coverage --html-report
        """
    )

    parser.add_argument('--unit', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--performance', action='store_true',
                       help='Run only performance tests')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate a coverage report')
    parser.add_argument('--html-report', action='store_true',
                       help='Generate an HTML coverage report (implies --coverage)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose mode')
    parser.add_argument('--file', type=str,
                       help='Run only a specific test file')
    parser.add_argument('--fail-fast', action='store_true',
                       help='Stop at the first failure')
    parser.add_argument('--no-capture', action='store_true',
                       help='Do not capture output (useful for debugging)')

    args = parser.parse_args()

    # Check quepytest est installé
    try:
        import pytest
    except ImportError:
        print("❌ pytest is not installed. Install it with:")
        print("   pip install pytest pytest-cov pytest-mock")
        sys.exit(1)

    # Build the pytest command
    cmd = [sys.executable, '-m', 'pytest']

    # Base options from pyproject.toml
    # The options are already configured in pyproject.toml

    # Filters by test type
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.performance:
        cmd.extend(['-m', 'performance'])

    # Specific file
    if args.file:
        if not args.file.startswith('test_'):
            args.file = f'test_{args.file}'
        if not args.file.endswith('.py'):
            args.file = f'{args.file}.py'
        cmd.append(f'tests/{args.file}')

    # Options of coverage
    if args.coverage or args.html_report:
        cmd.extend(['--cov=src', '--cov-report=term-missing'])
        if args.html_report:
            cmd.append('--cov-report=html:htmlcov')

    # Options general
    if args.verbose:
        cmd.append('-v')
    if args.fail_fast:
        cmd.append('-x')
    if args.no_capture:
        cmd.append('-s')

    # Run the tests
    success = run_command(cmd, "LANCEMENT DES TESTS GALAD ISLANDS")

    # final summary
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