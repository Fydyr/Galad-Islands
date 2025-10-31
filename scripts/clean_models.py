#!/usr/bin/env python3
"""
Automatic cleaning script for AI model files (.pkl)

This script allows you to:
- Delete all PKL files (complete reset)
- Keep only the N most recent files
- Delete files older than a certain number of days
- Clean up specifically Marauder models (--marauder)

Usage:
    python clean_models.py --all              # Delete all PKL files
    python clean_models.py --keep 10          # Keep the 10 most recent
    python clean_models.py --older-than 7     # Delete those > 7 days old
    python clean_models.py --marauder --all   # Delete all Marauder models
"""

import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta


def get_pkl_files(models_dir="models", pattern="*.pkl"):
    """Retrieves all .pkl files in the models folder according to the pattern"""
    models_path = Path(models_dir)
    if not models_path.exists():
        print(f"❌ The folder '{models_dir}' does not exist.")
        return []
    
    pkl_files = list(models_path.glob(pattern))
    return pkl_files


def delete_all_pkl(models_dir="models", pattern="*.pkl"):
    """Deletes all PKL files according to the pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ No PKL files to delete.")
        return
    
    print(f"🗑️  Deleting {len(pkl_files)} PKL files...")
    for pkl_file in pkl_files:
        try:
            pkl_file.unlink()
            print(f"   ✓ Deleted: {pkl_file.name}")
        except Exception as e:
            print(f"   ✗ Error deleting {pkl_file.name}: {e}")

    print(f"\n✅ {len(pkl_files)} PKL files successfully deleted!")


def keep_recent_pkl(n_keep, models_dir="models", pattern="*.pkl"):
    """Keeps only the N most recent files according to the pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ No PKL files found.")
        return
    
    # Sort by modification date (most recent first)
    pkl_files_sorted = sorted(pkl_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    files_to_keep = pkl_files_sorted[:n_keep]
    files_to_delete = pkl_files_sorted[n_keep:]
    
    if not files_to_delete:
        print(f"✅ All files ({len(pkl_files)}) are already within the limit of {n_keep}.")
        return
    
    print(f"📁 Files to keep ({len(files_to_keep)}):")
    for f in files_to_keep:
        mod_time = datetime.fromtimestamp(f.stat().st_mtime)
        print(f"   ✓ {f.name} (modified on {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")

    print(f"\n🗑️  Deleting {len(files_to_delete)} old files...")
    for pkl_file in files_to_delete:
        try:
            pkl_file.unlink()
            print(f"   ✓ Deleted: {pkl_file.name}")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    print(f"\n✅ Cleaning completed! {len(files_to_delete)} files deleted, {len(files_to_keep)} kept.")


def delete_older_than(days, models_dir="models", pattern="*.pkl"):
    """Deletes files older than N days according to the pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ No PKL files found.")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    files_to_delete = []
    
    for pkl_file in pkl_files:
        mod_time = datetime.fromtimestamp(pkl_file.stat().st_mtime)
        if mod_time < cutoff_date:
            files_to_delete.append(pkl_file)
    
    if not files_to_delete:
        print(f"✅ No files older than {days} days.")
        return
    
    print(f"🗑️  Deleting {len(files_to_delete)} files older than {days} days...")
    for pkl_file in files_to_delete:
        try:
            mod_time = datetime.fromtimestamp(pkl_file.stat().st_mtime)
            pkl_file.unlink()
            print(f"   ✓ Deleted: {pkl_file.name} (modified on {mod_time.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    remaining = len(pkl_files) - len(files_to_delete)
    print(f"\n✅ {len(files_to_delete)} files deleted, {remaining} kept.")


def list_pkl_files(models_dir="models", pattern="*.pkl"):
    """Lists all PKL files with their information according to the pattern"""
    pkl_files = get_pkl_files(models_dir, pattern)
    
    if not pkl_files:
        print("✅ No PKL files found.")
        return
    
    # Sort by modification date (most recent first)
    pkl_files_sorted = sorted(pkl_files, key=lambda f: f.stat().st_mtime, reverse=True)
    
    print(f"\n📊 {len(pkl_files)} PKL files found:\n")
    print(f"{'File name':<30} {'Size':<10} {'Last modification'}")
    print("-" * 70)
    
    total_size = 0
    for pkl_file in pkl_files_sorted:
        size = pkl_file.stat().st_size
        total_size += size
        mod_time = datetime.fromtimestamp(pkl_file.stat().st_mtime)
        
        # Format the size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        
        print(f"{pkl_file.name:<30} {size_str:<10} {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Total size
    if total_size < 1024:
        total_str = f"{total_size} B"
    elif total_size < 1024 * 1024:
        total_str = f"{total_size / 1024:.1f} KB"
    else:
        total_str = f"{total_size / (1024 * 1024):.1f} MB"
    
    print("-" * 70)
    print(f"Total size: {total_str}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Automatic cleaning of AI model files (.pkl)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Delete ALL PKL files (complete reset)"
    )
    
    parser.add_argument(
        "--keep",
        type=int,
        metavar="N",
        help="Keep only the N most recent files"
    )
    
    parser.add_argument(
        "--older-than",
        type=int,
        metavar="DAYS",
        help="Delete files older than N days"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all PKL files with their information"
    )
    
    parser.add_argument(
        "--marauder",
        action="store_true",
        help="Only clean Marauder models (barhamus_ai_*.pkl)"
    )
    
    parser.add_argument(
        "--models-dir",
        type=str,
        default="models",
        help="Folder containing PKL files (default: models)"
    )
    
    args = parser.parse_args()
    
    # Determine the pattern based on the --marauder option
    pattern = "barhamus_ai_*.pkl" if args.marauder else "*.pkl"
    
    # If no option, display the list by default
    if not any([args.all, args.keep, args.older_than, args.list]):
        target = "Marauder" if args.marauder else "all"
        print(f"🔍 No action specified. List of {target} PKL files:\n")
        list_pkl_files(args.models_dir, pattern)
        print("\nUse --help to see all available options.")
        return
    
    # List the files
    if args.list:
        list_pkl_files(args.models_dir, pattern)
        return
    
    # Delete all files
    if args.all:
        target = "MARAUDER models" if args.marauder else "all PKL files"
        confirm = input(f"⚠️  Delete {target}? (yes/no): ")
        if confirm.lower() in ['oui', 'o', 'yes', 'y']:
            delete_all_pkl(args.models_dir, pattern)
        else:
            print("❌ Cancelled.")
        return
    
    # Keep only N files
    if args.keep:
        keep_recent_pkl(args.keep, args.models_dir, pattern)
        return
    
    # Delete old files
    if args.older_than:
        delete_older_than(args.older_than, args.models_dir, pattern)
        return


if __name__ == "__main__":
    main()
