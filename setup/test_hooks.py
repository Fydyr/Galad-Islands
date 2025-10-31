#!/usr/bin/env python3
"""
Script de test pour Check l'installation des hooks avec bump automatique
"""

import os
import sys
import subprocess
from pathlib import Path

def test_hook_installation():
    """Teste que les hooks sont correctement installés"""
    print("🧪 Test de l'installation des hooks")
    
    # Check les fichiers de hooks
    hooks_to_check = [
        '.git/hooks/pre-commit',
        '.git/hooks/commit-msg'  # Optionnel
    ]
    
    for hook_path in hooks_to_check:
        if Path(hook_path).exists():
            print(f"✅ {hook_path} trouvé")
            
            # Check quele hook est exécutable (sur Unix)
            if os.name != 'nt':
                if os.access(hook_path, os.X_OK):
                    print(f"✅ {hook_path} est exécutable")
                else:
                    print(f"⚠️  {hook_path} n'est pas exécutable")
        else:
            if 'commit-msg' in hook_path:
                print(f"ℹ️  {hook_path} non trouvé (optionnel)")
            else:
                print(f"❌ {hook_path} non trouvé")

def test_commitizen():
    """Teste que commitizen est accessible"""
    print("\n🧪 Test de commitizen")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'commitizen', 'version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Commitizen v{result.stdout.strip()} disponible")
            return True
        else:
            print("❌ Commitizen non accessible")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du test de commitizen: {e}")
        return False

def test_git_status():
    """Teste l'état du repository Git"""
    print("\n🧪 Test de l'état Git")
    
    try:
        # Check qu'on est in un repo Git
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Repository Git valide")
            
            # Afficher les fichiers modifiés
            if result.stdout.strip():
                print("ℹ️  Fichiers modifiés détectés:")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("ℹ️  Aucun fichier modifié")
            return True
        else:
            print("❌ Problème avec le repository Git")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du test Git: {e}")
        return False

def simulate_commit_test():
    """Simule un test de commit pour Check le hook"""
    print("\n🧪 Simulation d'un commit de test")
    
    # Create un file temporaire
    test_file = Path('test_hook_simulation.tmp')
    try:
        test_file.write_text("Test du hook pre-commit\n")
        
        # Add the file
        result = subprocess.run(['git', 'add', str(test_file)], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("⚠️  Impossible d'ajouter le fichier de test")
            return
        
        print("ℹ️  Fichier de test ajouté")
        print("ℹ️  Pour tester le hook, exécutez:")
        print(f"   git commit -m 'test: test du hook pre-commit'")
        print("   (puis git reset HEAD~1 pour annuler)")
        
        # Clean up
        subprocess.run(['git', 'reset', 'HEAD', str(test_file)], 
                      capture_output=True)
        test_file.unlink()
        
    except Exception as e:
        print(f"⚠️  Erreur lors de la simulation: {e}")
        # Clean up in case of error
        try:
            subprocess.run(['git', 'reset', 'HEAD', str(test_file)], 
                          capture_output=True)
            if test_file.exists():
                test_file.unlink()
        except:
            pass

def main():
    """Main function de test"""
    print("🔍 TESTS D'INSTALLATION DES HOOKS AVEC BUMP AUTOMATIQUE")
    print("="*60)
    
    # Tests
    test_hook_installation()
    cz_ok = test_commitizen()
    git_ok = test_git_status()
    
    if cz_ok and git_ok:
        simulate_commit_test()
    
    print("\n" + "="*60)
    if cz_ok and git_ok:
        print("✅ TESTS RÉUSSIS - Les hooks devraient fonctionner correctement")
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS - Vérifiez l'installation")
    
    print("\n📖 Pour plus d'informations, consultez:")
    print("   docs/dev/version-management.md")

if __name__ == "__main__":
    main()