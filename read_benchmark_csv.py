#!/usr/bin/env python3
"""
Utilitaire pour lire et afficher les résultats de benchmark CSV de Galad Islands.

Usage:
    python read_benchmark_csv.py [fichier.csv]
    python read_benchmark_csv.py --latest  # pour le fichier le plus récent
    python read_benchmark_csv.py --all     # pour tous les fichiers
"""

import csv
import sys
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional


def format_timestamp(timestamp_str: str) -> str:
    """Formate un timestamp ISO en format lisible."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%d/%m/%Y à %H:%M:%S")
    except:
        return timestamp_str


def read_benchmark_csv(filename: str) -> Optional[Dict]:
    """Lit un fichier CSV de benchmark et retourne les données."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return next(reader)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {filename}")
        return None
    except Exception as e:
        print(f"❌ Erreur lecture fichier {filename}: {e}")
        return None


def display_benchmark_results(data: Dict, filename: str = ""):
    """Affiche les résultats de benchmark de manière formatée."""
    
    print("=" * 60)
    if filename:
        print(f"📄 Fichier: {os.path.basename(filename)}")
    
    print("🖥️  INFORMATIONS SYSTÈME:")
    print(f"📅 Date: {format_timestamp(data.get('timestamp', 'N/A'))}")
    print(f"💻 OS: {data.get('os', 'N/A')} {data.get('os_version', 'N/A')}")
    print(f"🐍 Python: {data.get('python_version', 'N/A')}")
    print(f"⚙️  CPU: {data.get('cpu_count', 'N/A')} cœurs ({data.get('cpu_count_logical', 'N/A')} logiques)")
    
    # Fréquences CPU
    cpu_freq_current = float(data.get('cpu_freq_current', 0))
    cpu_freq_max = float(data.get('cpu_freq_max', 0))
    if cpu_freq_current > 0 and cpu_freq_max > 0:
        print(f"🔥 Fréq CPU: {cpu_freq_current:.0f} MHz (max: {cpu_freq_max:.0f} MHz)")
    
    # Mémoire
    memory_total = float(data.get('memory_total_gb', 0))
    memory_available = float(data.get('memory_available_gb', 0))
    if memory_total > 0:
        print(f"🧠 Mémoire: {memory_total:.1f} GB total, {memory_available:.1f} GB disponible")
    
    # Usage système
    cpu_usage = float(data.get('cpu_usage_percent', 0))
    memory_usage = float(data.get('memory_usage_percent', 0))
    print(f"📊 Usage: CPU {cpu_usage:.1f}%, Mémoire {memory_usage:.1f}%")
    
    print()
    print("🎮 PERFORMANCES JEU:")
    print(f"🎯 Benchmark: {data.get('benchmark_name', 'N/A')}")
    print(f"⏱️  Durée: {float(data.get('duration_s', 0)):.1f}s")
    print(f"🖼️  FPS: {float(data.get('fps_average', 0)):.1f}")
    print(f"📊 Frames: {data.get('total_frames', 'N/A')}")
    print(f"💾 Mémoire jeu: {float(data.get('memory_mb', 0)):.1f} MB")
    
    # Analyser les performances des systèmes
    print()
    print("⚡ TOP SYSTÈMES LES PLUS COÛTEUX:")
    system_perfs = []
    for key, value in data.items():
        if key.startswith('profile_') and key.endswith('_percent'):
            system_name = key.replace('profile_', '').replace('_percent', '')
            percent = float(value)
            if percent > 0:
                system_perfs.append((system_name, percent))
    
    system_perfs.sort(key=lambda x: x[1], reverse=True)
    for system_name, percent in system_perfs[:5]:
        print(f"• {system_name}: {percent:.1f}%")
    
    # Analyser les performances IA
    print()
    print("🤖 PERFORMANCES IA:")
    ai_perfs = []
    for key, value in data.items():
        if key.startswith('ai_') and key.endswith('_avg_ms'):
            # Gérer le format ai_xxxx_ai_avg_ms
            ai_name = key.replace('ai_', '').replace('_avg_ms', '')
            if ai_name.endswith('_ai'):
                ai_name = ai_name[:-3]  # Retirer le "_ai" final
            
            avg_ms = float(value)
            if avg_ms > 0:
                # Récupérer le nombre d'appels avec le bon format
                calls_key = f'ai_{ai_name}_ai_calls' if not key.startswith('ai_base_') else f'ai_{ai_name}_calls'
                calls = int(data.get(calls_key, 0))
                ai_perfs.append((ai_name, avg_ms, calls))
    
    ai_perfs.sort(key=lambda x: x[1], reverse=True)
    for ai_name, avg_ms, calls in ai_perfs:
        if calls > 0:
            print(f"• {ai_name}: {avg_ms:.2f}ms/appel ({calls} appels)")


def find_latest_csv() -> Optional[str]:
    """Trouve le fichier CSV le plus récent."""
    csv_files = glob.glob("benchmark_results_*.csv")
    if not csv_files:
        print("❌ Aucun fichier benchmark_results_*.csv trouvé")
        return None
    
    # Trier par date de modification
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files[0]


def find_all_csvs() -> List[str]:
    """Trouve tous les fichiers CSV de benchmark."""
    csv_files = glob.glob("benchmark_results_*.csv")
    csv_files.sort(key=os.path.getmtime, reverse=True)
    return csv_files


def main():
    """Fonction principale."""
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python read_benchmark_csv.py fichier.csv")
        print("  python read_benchmark_csv.py --latest")
        print("  python read_benchmark_csv.py --all")
        return
    
    arg = sys.argv[1]
    
    if arg == "--latest":
        filename = find_latest_csv()
        if not filename:
            return
        
        print(f"📄 Lecture du fichier le plus récent: {filename}")
        data = read_benchmark_csv(filename)
        if data:
            display_benchmark_results(data, filename)
    
    elif arg == "--all":
        csv_files = find_all_csvs()
        if not csv_files:
            print("❌ Aucun fichier benchmark_results_*.csv trouvé")
            return
        
        print(f"📄 Trouvé {len(csv_files)} fichier(s) CSV:")
        for i, filename in enumerate(csv_files):
            data = read_benchmark_csv(filename)
            if data:
                display_benchmark_results(data, filename)
                if i < len(csv_files) - 1:  # Pas de séparateur après le dernier
                    print("\n" + "─" * 60 + "\n")
    
    else:
        # Fichier spécifique
        filename = arg
        data = read_benchmark_csv(filename)
        if data:
            display_benchmark_results(data, filename)


if __name__ == "__main__":
    main()