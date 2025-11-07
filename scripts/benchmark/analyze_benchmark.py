#!/usr/bin/env python3
"""
Analyse des résultats de benchmark Galad Islands
Lit le CSV et affiche une analyse détaillée
"""

import csv
import sys
import os
from datetime import datetime

def analyze_csv(filename):
    """Analyse un fichier CSV de benchmark."""
    
    if not os.path.exists(filename):
        print(f"❌ Fichier non trouvé: {filename}")
        return
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)[0]
    
    print('📊 ANALYSE DU BENCHMARK GALAD ISLANDS')
    print('='*70)
    
    # Informations système
    print('\n💻 SYSTÈME:')
    print(f'  OS: {data["os"]} {data["os_version"]}')
    print(f'  Python: {data["python_version"]}')
    print(f'  CPU: {data["cpu_count"]} cores physiques / {data["cpu_count_logical"]} logiques')
    print(f'  Fréquence CPU: {float(data["cpu_freq_current"]):.0f} MHz (max: {float(data["cpu_freq_max"]):.0f} MHz)')
    print(f'  RAM: {data["memory_total_gb"]} GB total / {data["memory_available_gb"]} GB disponible')
    print(f'  Usage CPU: {data["cpu_usage_percent"]}%')
    print(f'  Usage RAM: {data["memory_usage_percent"]}%')
    
    # Performances globales
    print('\n⚡ PERFORMANCES GLOBALES:')
    duration = float(data["duration_s"])
    fps = float(data["fps_average"])
    frames = int(data["total_frames"])
    print(f'  Durée test: {duration:.1f}s')
    print(f'  FPS moyen: {fps:.1f} FPS')
    print(f'  Total frames: {frames} frames')
    print(f'  Type: {data["benchmark_name"]}')
    
    # Budget temps
    budget_60fps = 16.67
    budget_current = 1000 / fps if fps > 0 else 0
    print(f'\n⏱️  BUDGET TEMPS:')
    print(f'  Budget @60 FPS: {budget_60fps:.2f} ms/frame')
    print(f'  Budget actuel @{fps:.1f} FPS: {budget_current:.2f} ms/frame')
    if fps < 60:
        overhead = budget_current - budget_60fps
        print(f'  ⚠️  Dépassement: +{overhead:.2f} ms/frame ({overhead/budget_60fps*100:.1f}%)')
    
    # Analyse profiling
    print('\n🔥 TOP CONSOMMATEURS CPU (% du temps total):')
    profile_data = []
    for key, value in data.items():
        if key.startswith('profile_') and key.endswith('_percent'):
            try:
                percent = float(value)
                if percent > 0:
                    name = key.replace('profile_', '').replace('_percent', '')
                    profile_data.append((name, percent))
            except:
                pass
    
    profile_data.sort(key=lambda x: x[1], reverse=True)
    total_profiled = sum(p[1] for p in profile_data)
    
    for i, (name, percent) in enumerate(profile_data[:10], 1):
        bar = '█' * int(percent / 2)
        ms_per_frame = (duration * 1000 * percent / 100) / frames if frames > 0 else 0
        print(f'  {i:2}. {name:20} {percent:6.2f}% {bar:20} ({ms_per_frame:5.2f} ms/frame)')
    
    if total_profiled < 100:
        other = 100 - total_profiled
        print(f'  {"Autres/Non profilé":>24} {other:6.2f}%')
    
    # Analyse temps moyens
    print('\n⏱️  TEMPS MOYENS PAR APPEL:')
    avg_data = []
    for key, value in data.items():
        if key.startswith('profile_') and key.endswith('_avg_ms'):
            try:
                avg_ms = float(value)
                if avg_ms > 0:
                    name = key.replace('profile_', '').replace('_avg_ms', '')
                    calls_key = f'profile_{name}_calls'
                    total_key = f'profile_{name}_total_s'
                    if calls_key in data and total_key in data:
                        calls = int(data[calls_key])
                        total_s = float(data[total_key])
                        avg_data.append((name, avg_ms, calls, total_s))
            except:
                pass
    
    avg_data.sort(key=lambda x: x[1], reverse=True)
    for i, (name, avg_ms, calls, total_s) in enumerate(avg_data[:10], 1):
        calls_per_frame = calls / frames if frames > 0 else 0
        print(f'  {i:2}. {name:20} {avg_ms:7.3f} ms/call | {calls:5} appels ({calls_per_frame:.1f}/frame) | {total_s:6.2f}s total')
    
    # Analyse IA - vérifier si des colonnes AI existent
    print('\n🤖 ACTIVITÉ IA:')
    has_ai_data = any(key.startswith('ai_') and key.endswith('_calls') for key in data.keys())
    
    if has_ai_data:
        ai_data = []
        for key, value in data.items():
            if key.startswith('ai_') and key.endswith('_calls'):
                try:
                    calls = int(value)
                    if calls > 0:
                        name = key.replace('ai_', '').replace('_calls', '')
                        total_key = f'ai_{name}_total_s'
                        avg_key = f'ai_{name}_avg_ms'
                        if total_key in data and avg_key in data:
                            total_s = float(data[total_key])
                            avg_ms = float(data[avg_key])
                            ai_data.append((name, total_s, calls, avg_ms))
                except:
                    pass
        
        if ai_data:
            ai_data.sort(key=lambda x: x[1], reverse=True)
            for name, total_s, calls, avg_ms in ai_data:
                calls_per_frame = calls / frames if frames > 0 else 0
                print(f'  • {name:18} {total_s:7.3f}s total | {avg_ms:7.3f} ms/call | {calls:5} appels ({calls_per_frame:.1f}/frame)')
        else:
            print(f'  ✅ Aucune IA active (mode {data["benchmark_name"]})')
    else:
        print(f'  ℹ️  Pas de données IA dans ce benchmark')
    
    # Recommandations
    print('\n💡 RECOMMANDATIONS:')
    
    # Check rendering
    rendering_percent = 0
    for key, value in data.items():
        if key == 'profile_rendering_percent':
            rendering_percent = float(value)
    
    if rendering_percent > 40:
        print(f'  ⚠️  Rendering très coûteux ({rendering_percent:.1f}%) - optimiser l\'affichage')
    elif rendering_percent > 25:
        print(f'  📊 Rendering normal ({rendering_percent:.1f}%)')
    
    # Check game update
    game_update_percent = 0
    for key, value in data.items():
        if key == 'profile_game_update_percent':
            game_update_percent = float(value)
    
    if game_update_percent > 10:
        print(f'  ⚠️  Game update coûteux ({game_update_percent:.1f}%) - optimiser la logique')
    
    # Check AI
    if has_ai_data and ai_data:
        total_ai_time = sum(t for _, t, _, _ in ai_data)
        ai_percent = (total_ai_time / duration) * 100 if duration > 0 else 0
        if ai_percent > 5:
            print(f'  ⚠️  IA consomme {ai_percent:.1f}% du temps - vérifier les algorithmes')
    
    # Check FPS
    if fps < 30:
        print(f'  🚨 FPS très bas ({fps:.1f}) - jeu non jouable')
    elif fps < 60:
        print(f'  ⚠️  FPS sous la cible ({fps:.1f}/60) - optimisation nécessaire')
    else:
        print(f'  ✅ FPS excellent ({fps:.1f})')
    
    print('\n' + '='*70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Trouver le fichier CSV le plus récent
        csv_files = [f for f in os.listdir('.') if f.startswith('benchmark_') and f.endswith('.csv')]
        if csv_files:
            csv_files.sort(reverse=True)
            filename = csv_files[0]
            print(f"📁 Fichier auto-détecté: {filename}\n")
        else:
            print("❌ Aucun fichier CSV trouvé")
            print("Usage: python3 analyze_benchmark.py [fichier.csv]")
            sys.exit(1)
    
    analyze_csv(filename)
