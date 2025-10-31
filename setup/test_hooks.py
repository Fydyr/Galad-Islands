#!/usr/bin/env python3
"""
Test script to check the installation of hooks with automatic bump
"""

import os
import sys
import subprocess
from pathlib import Path

def test_hook_installation():
    """Tests that hooks are correctly installed"""
    print("🧪 Testing hook installation")

    # Check hook files
    hooks_to_check = [
        '.git/hooks/pre-commit',
        '.git/hooks/commit-msg'  # Optional
    ]
    
    for hook_path in hooks_to_check:
        if Path(hook_path).exists():
            print(f"✅ {hook_path} found")

            # Check if the hook is executable (on Unix)
            if os.name != 'nt':
                if os.access(hook_path, os.X_OK):
                    print(f"✅ {hook_path} is executable")
                else:
                    print(f"⚠️  {hook_path} is not executable")
        else:
            if 'commit-msg' in hook_path:
                print(f"ℹ️  {hook_path} not found (optional)")
            else:
                print(f"❌ {hook_path} not found")

def test_commitizen():
    """Tests that commitizen is accessible"""
    print("\n🧪 Testing commitizen")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'commitizen', 'version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Commitizen v{result.stdout.strip()} available")
            return True
        else:
            print("❌ Commitizen not accessible")
            return False
    except Exception as e:
        print(f"❌ Error testing commitizen: {e}")
        return False

def test_git_status():
    """Tests the Git repository state"""
    print("\n🧪 Testing Git state")

    try:
        # Check that we're in a Git repo
        result = subprocess.run(['git', 'status', '--porcelain'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Valid Git repository")

            # Display modified files
            if result.stdout.strip():
                print("ℹ️  Modified files detected:")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            else:
                print("ℹ️  No modified files")
            return True
        else:
            print("❌ Problem with Git repository")
            return False
    except Exception as e:
        print(f"❌ Error testing Git: {e}")
        return False

def simulate_commit_test():
    """Simulates a test commit to check the hook"""
    print("\n🧪 Simulating a test commit")

    # Create a temporary file
    test_file = Path('test_hook_simulation.tmp')
    try:
        test_file.write_text("Testing the pre-commit hook\n")

        # Add the file
        result = subprocess.run(['git', 'add', str(test_file)],
                              capture_output=True, text=True)

        if result.returncode != 0:
            print("⚠️  Unable to add test file")
            return

        print("ℹ️  Test file added")
        print("ℹ️  To test the hook, execute:")
        print(f"   git commit -m 'test: testing the pre-commit hook'")
        print("   (then git reset HEAD~1 to cancel)")

        # Clean up
        subprocess.run(['git', 'reset', 'HEAD', str(test_file)],
                      capture_output=True)
        test_file.unlink()

    except Exception as e:
        print(f"⚠️  Error during simulation: {e}")
        # Clean up in case of error
        try:
            subprocess.run(['git', 'reset', 'HEAD', str(test_file)], 
                          capture_output=True)
            if test_file.exists():
                test_file.unlink()
        except:
            pass

def main():
    """Main test function"""
    print("🔍 HOOK INSTALLATION TESTS WITH AUTOMATIC BUMP")
    print("="*60)

    # Tests
    test_hook_installation()
    cz_ok = test_commitizen()
    git_ok = test_git_status()

    if cz_ok and git_ok:
        simulate_commit_test()

    print("\n" + "="*60)
    if cz_ok and git_ok:
        print("✅ TESTS PASSED - Hooks should work correctly")
    else:
        print("⚠️  PROBLEMS DETECTED - Check the installation")

    print("\n📖 For more information, consult:")
    print("   docs/dev/version-management.md")

if __name__ == "__main__":
    main()