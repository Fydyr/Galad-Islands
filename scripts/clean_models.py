#!/usr/bin/env python3
"""
Script de nettoyage automatique des fichiers de modèles d'IA (.pkl)

Ce script permet de :
- Supprimer tous les fichiers PKL (réinitialisation complète)
- Garder seulement les N fichiers les plus récents
- Supprimer les fichiers plus anciens qu'un certain nombre de jours
- Nettoyer spécifiquement les modèles des Maraudeurs (--marauder)

Usage:
    python clean_models.py --all              # Supprimer tous les fichiers PKL
    python clean_models.py --keep 10          # Garder les 10 plus récents
    python clean_models.py --older-than 7     # Supprimer ceux > 7 jours
    python clean_models.py --marauder --all   # Supprimer tous les modèles Maraudeur
"""

import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta


def get_pkl_files(models_dir="models", pattern="*.pkl"):
    """Récupère tous les fichiers .pkl dans le dossier models selon le pattern"""
    models_path = Path(models_dir)
    if not models_path.exists():
        print(f"❌ Le dossier '{models_dir}' n'existe pas.")
        return []
    
    pkl_files = list(models_path.glob(pattern))
    return pkl_files


def delete_all_pkl(models_dir="models", pattern="*.pkl"):
    """Supprime tous les fichiers PKL selon le pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ Aucun fichier PKL à supprimer.")
        return
    
    print(f"🗑️  Suppression de {len(pkl_files)} fichiers PKL...")
    for pkl_file in pkl_files:
        try:
            pkl_file.unlink()
            print(f"   ✓ Supprimé: {pkl_file.name}")
        except Exception as e:
            print(f"   ✗ Erreur lors de la suppression de {pkl_file.name}: {e}")
    
    print(f"\n✅ {len(pkl_files)} fichiers PKL supprimés avec succès !")


def keep_recent_pkl(n_keep, models_dir="models", pattern="*.pkl"):
    """Garde seulement les N fichiers les plus récents selon le pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ Aucun fichier PKL trouvé.")
        return
    
    # Trier par date de modification (plus récent en premier)
    pkl_files_sorted = sorted(pkl_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    files_to_keep = pkl_files_sorted[:n_keep]
    files_to_delete = pkl_files_sorted[n_keep:]
    
    if not files_to_delete:
        print(f"✅ Tous les fichiers ({len(pkl_files)}) sont déjà dans la limite de {n_keep}.")
        return
    
    print(f"📁 Fichiers à garder ({len(files_to_keep)}):")
    for f in files_to_keep:
        mod_time = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"   ✓ {f.name} (modifié le {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    print(f"\n🗑️  Suppression de {len(files_to_delete)} anciens fichiers...")
    for pkl_file in files_to_delete:
        try:
            pkl_file.unlink()
            print(f"   ✓ Supprimé: {pkl_file.name}")
        except Exception as e:
            print(f"   ✗ Erreur: {e}")
    
    print(f"\n✅ Nettoyage terminé ! {len(files_to_delete)} fichiers supprimés, {len(files_to_keep)} conservés.")


def delete_older_than(days, models_dir="models", pattern="*.pkl"):
    """Supprime les fichiers plus anciens que N jours selon le pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ Aucun fichier PKL trouvé.")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    files_to_delete = []
    
    for pkl_file in pkl_files:
        mod_time = datetime.fromtimestamp(pkl_file.stat().st_mtime)
        if mod_time < cutoff_date:
            files_to_delete.append(pkl_file)
    
    if not files_to_delete:
        print(f"✅ Aucun fichier plus ancien que {days} jours.")
        return
    
    print(f"🗑️  Suppression de {len(files_to_delete)} fichiers plus anciens que {days} jours...")
    for pkl_file in files_to_delete:
        try:
            mod_time = datetime.fromtimestamp(pkl_file.stat().st_mtime)
            pkl_file.unlink()
            print(f"   ✓ Supprimé: {pkl_file.name} (modifié le {mod_time.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"   ✗ Erreur: {e}")
    
    remaining = len(pkl_files) - len(files_to_delete)
    print(f"\n✅ {len(files_to_delete)} fichiers supprimés, {remaining} conservés.")


def list_pkl_files(models_dir="models", pattern="*.pkl"):
    """Liste tous les fichiers PKL avec leurs informations selon le pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ Aucun fichier PKL trouvé.")
        return
    
    # Trier par date de modification (plus récent en premier)
    pkl_files_sorted = sorted(pkl_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    print(f"\n📊 {len(pkl_files)} fichiers PKL trouvés:\n")
    print(f"{'Nom du fichier':<30} {'Taille':<10} {'Dernière modification'}")
    print("-" * 70)
    
    total_size = 0
    for pkl_file in pkl_files_sorted:
        size = pkl_file.stat().st_size
        total_size += size
        mod_time = datetime.fromtimestamp(pkl_file.stat().st_mtime)
        
        # Formater la taille
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        
        print(f"{pkl_file.name:<30} {size_str:<10} {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Taille totale
    if total_size < 1024:
        total_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        total_str = f"{total_size / 1024:.1f} KB"
    else:
        total_str = f"{total_size / (1024 * 1024):.1f} MB"
    
    print("-" * 70)
    print(f"Taille totale: {total_str}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Nettoyage automatique des fichiers de modèles d'IA (.pkl)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Supprimer TOUS les fichiers PKL (réinitialisation complète)"
    )
    
    parser.add_argument(
        "--keep",
        type=int,
        metavar="N",
        help="Garder seulement les N fichiers les plus récents"
    )
    
    parser.add_argument(
        "--older-than",
        type=int,
        metavar="DAYS",
        help="Supprimer les fichiers plus anciens que N jours"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lister tous les fichiers PKL avec leurs informations"
    )
    
    parser.add_argument(
        "--marauder",
        action="store_true",
        help="Ne nettoyer que les modèles des Maraudeurs (barhamus_ai_*.pkl)"
    )
    
    parser.add_argument(
        "--models-dir",
        type=str,
        default="models",
        help="Dossier contenant les fichiers PKL (défaut: models)"
    )
    
    args = parser.parse_args()
    
    # Déterminer le pattern selon l'option --marauder
    pattern = "barhamus_ai_*.pkl" if args.marauder else "*.pkl"
    
    # Si aucune option, afficher la liste par défaut
    if not any([args.all, args.keep, args.older_than, args.list]):
        target = "Maraudeur" if args.marauder else "tous les"
        print(f"🔍 Aucune action spécifiée. Liste des fichiers PKL {target}:\n")
        list_pkl_files(args.models_dir, pattern)
        print("\nUtilise --help pour voir toutes les options disponibles.")
        return
    
    # Lister les fichiers
    if args.list:
        list_pkl_files(args.models_dir, pattern)
        return
    
    # Supprimer tous les fichiers
    if args.all:
        target = "MARAUDEUR" if args.marauder else "tous les fichiers PKL"
        confirm = input(f"⚠️  Supprimer {target} ? (oui/non): ")
        if confirm.lower() in ['oui', 'o', 'yes', 'y']:
            delete_all_pkl(args.models_dir, pattern)
        else:
            print("❌ Annulé.")
        return
    
    # Garder seulement N fichiers
    if args.keep:
        keep_recent_pkl(args.keep, args.models_dir, pattern)
        return
    
    # Supprimer les fichiers anciens
    if args.older_than:
        delete_older_than(args.older_than, args.models_dir, pattern)
        return


if __name__ == "__main__":
    main()
