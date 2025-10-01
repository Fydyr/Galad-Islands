#!/usr/bin/env python3
"""
Script pour nettoyer le changelog en supprimant les commits non pertinents pour les utilisateurs
"""

import re
from pathlib import Path

def clean_changelog():
    """Nettoie le changelog en supprimant les commits non pertinents"""
    
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("❌ CHANGELOG.md non trouvé")
        return False
    
    # Lire le contenu
    content = changelog_path.read_text(encoding='utf-8')
    
    # Types de commits à supprimer (non pertinents pour les utilisateurs)
    excluded_patterns = [
        r'- \*\*ci\*\*:.*',  # commits ci
        r'- \*\*build\*\*:.*',  # commits build
        r'- \*\*chore\*\*:.*',  # commits chore
        r'- \*\*style\*\*:.*',  # commits style (formatage)
        r'- \*\*test\*\*:.*',  # commits test
        r'- .*workflow.*',  # workflows
        r'- .*pipeline.*',  # pipelines
        r'- .*github.*actions.*',  # github actions
        r'- .*requirements.*',  # requirements
        r'- .*dependencies.*',  # dependencies
        r'- .*mkdocs.*',  # mkdocs
        r'- ajuster le workflow.*',  # workflows spécifiques
        r'- ajouter la configuration.*git.*workflow.*',  # config git workflow
        r'- corriger le chemin.*PyInstaller.*métadonnées.*',  # config build
        r'- supprimer le commentaire.*build PyInstaller.*',  # config build
        r'- \*\*readme\*\*: ajout de mkdocs.*',  # ajouts techniques readme
        r'- \*\*requirements\*\*: ajout.*',  # ajouts requirements
    ]
    
    # Compiler les patterns
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in excluded_patterns]
    
    # Supprimer les lignes correspondantes
    lines = content.split('\n')
    cleaned_lines = []
    removed_count = 0
    
    for line in lines:
        should_remove = False
        for pattern in compiled_patterns:
            if pattern.search(line):
                should_remove = True
                removed_count += 1
                print(f"🗑️  Supprimé: {line.strip()}")
                break
        
        if not should_remove:
            cleaned_lines.append(line)
    
    # Nettoyer les sections vides
    final_lines = []
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]
        
        # Si c'est un titre de section (### Feat, ### Fix, etc.)
        if line.strip().startswith('###'):
            # Vérifier s'il y a du contenu après
            j = i + 1
            has_content = False
            while j < len(cleaned_lines) and not cleaned_lines[j].strip().startswith('##'):
                if cleaned_lines[j].strip() and not cleaned_lines[j].strip().startswith('###'):
                    has_content = True
                    break
                j += 1
            
            # Si la section a du contenu, l'inclure
            if has_content:
                final_lines.append(line)
            else:
                print(f"🗑️  Section vide supprimée: {line.strip()}")
        else:
            final_lines.append(line)
        
        i += 1
    
    # Écrire le résultat
    cleaned_content = '\n'.join(final_lines)
    changelog_path.write_text(cleaned_content, encoding='utf-8')
    
    print(f"\n✅ Changelog nettoyé!")
    print(f"📊 {removed_count} lignes supprimées")
    print(f"📝 Fichier mis à jour: {changelog_path}")
    
    return True

def main():
    """Fonction principale"""
    print("🧹 Nettoyage du changelog...")
    print("Suppression des commits non pertinents pour les utilisateurs")
    print("-" * 60)
    
    if clean_changelog():
        print("\n🎉 Nettoyage terminé avec succès!")
    else:
        print("\n❌ Échec du nettoyage")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())