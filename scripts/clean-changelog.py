#!/usr/bin/env python3
"""
Script to clean up the changelog by removing commits irrelevant to users
"""

import re
from pathlib import Path

def clean_changelog():
    """Cleans the changelog by removing irrelevant commits"""
    
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("❌ CHANGELOG.md not found")
        return False
    
    # Read the content
    content = changelog_path.read_text(encoding='utf-8')
    
    # Types of commits to remove (irrelevant to users)
    excluded_patterns = [
        r'- \*\*ci\*\*:.*',  # ci commits
        r'- \*\*build\*\*:.*',  # build commits
        r'- \*\*chore\*\*:.*',  # chore commits
        r'- \*\*style\*\*:.*',  # style commits (formatting)
        r'- \*\*test\*\*:.*',  # test commits
        r'- .*workflow.*',  # workflows
        r'- .*pipeline.*',  # pipelines
        r'- .*github.*actions.*',  # github actions
        r'- .*requirements.*',  # requirements
        r'- .*dependencies.*',  # dependencies
        r'- .*mkdocs.*',  # mkdocs
        r'- ajuster le workflow.*',  # specific workflows
        r'- ajouter la configuration.*git.*workflow.*',  # git workflow config
        r'- corriger le chemin.*PyInstaller.*métadonnées.*',  # build config
        r'- supprimer le commentaire.*build PyInstaller.*',  # build config
        r'- \*\*readme\*\*: ajout de mkdocs.*',  # technical readme additions
        r'- \*\*requirements\*\*: ajout.*',  # requirements additions
    ]
    
    # Compile the patterns
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in excluded_patterns]
    
    # Remove matching lines
    lines = content.split('\n')
    cleaned_lines = []
    removed_count = 0
    
    for line in lines:
        should_remove = False
        for pattern in compiled_patterns:
            if pattern.search(line):
                should_remove = True
                removed_count += 1
                print(f"🗑️  Removed: {line.strip()}")
                break
        
        if not should_remove:
            cleaned_lines.append(line)
    
    # Clean up empty sections
    final_lines = []
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]
        
        # If it's a section title (### Feat, ### Fix, etc.)
        if line.strip().startswith('###'):
            # Check if there's content after
            j = i + 1
            has_content = False
            while j < len(cleaned_lines) and not cleaned_lines[j].strip().startswith('##'):
                if cleaned_lines[j].strip() and not cleaned_lines[j].strip().startswith('###'):
                    has_content = True
                    break
                j += 1

            # If the section has content, include it
            if has_content:
                final_lines.append(line)
            else:
                print(f"🗑️  Empty section removed: {line.strip()}")
        else:
            final_lines.append(line)
        
        i += 1
    
    # Write the result
    cleaned_content = '\n'.join(final_lines)
    changelog_path.write_text(cleaned_content, encoding='utf-8')
    
    print(f"\n✅ Changelog cleaned!")
    print(f"📊 {removed_count} lines removed")
    print(f"📝 File updated: {changelog_path}")
    
    return True

def main():
    """Main function"""
    print("🧹 Cleaning the changelog...")
    print("Removing commits irrelevant to users")
    print("-" * 60)
    
    if clean_changelog():
        print("\n🎉 Cleaning completed successfully!")
    else:
        print("\n❌ Cleaning failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())