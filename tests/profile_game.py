import cProfile
import pstats
import io
import os
import sys
import pygame

# --- Configuration du chemin d'accès ---
# Add the directory parent (racine du projet) au path pour que les imports fonctionnent
# comme si on lançait from la racine du projet.
# Ceci est crucial pour que `from src.game import game` fonctionne.
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

import main

def run_profiler():
    """
    Lance le jeu avec le profiler cProfile et affiche les résultats.
    Le profilage se fait sur toute la durée de la partie.
    """
    # Create an instance du profiler
    profiler = cProfile.Profile()

    # Lancer le jeu sous le contrôle du profiler
    print("="*70)
    print("🚀 PROFILAGE DU JEU GALAD ISLANDS - SESSION COMPLÈTE")
    print("="*70)
    print("🎮 PROFILAGE ACTIF - C'est une vraie partie !")
    print("   • Le profilage enregistre TOUTES les performances du jeu")
    print("   • Jouez normalement : construisez, combattez, explorez...")
    print("   • Plus vous jouez longtemps, plus les données sont précises")
    print("   • Fermez le jeu (Échap ou X) pour obtenir le rapport détaillé")
    print("="*70)
    print("💡 Conseil: Jouez pendant 2-5 minutes pour des résultats optimaux")
    print("   Le rapport montrera les fonctions les plus lentes de votre partie.")
    print("="*70)

    profiler.enable()

    try:
        # Appeler la Main function du jeu
        main.main_menu()
    except (SystemExit, pygame.error):
        # Pygame.quit() peut lever SystemExit, on l'intercepte pour continuer.
        print("\n✅ Partie terminée. Analyse du profilage en cours...")
    finally:
        profiler.disable()    # Create un flux en mémoire pour capturer la sortie de pstats
    s = io.StringIO()

    # Trier les statistiques par temps cumulé ('cumulative')
    # 'tottime' : TOTAL TIME passé in la fonction (sans les sous-fonctions)
    # 'cumulative' : TOTAL TIME passé in la fonction ET ses sous-fonctions
    sortby = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)

    # Afficher les statistiques des 30 fonctions les plus gourmandes
    print("\n" + "="*70)
    print("📊 RAPPORT DE PERFORMANCE - TOP 30 FONCTIONS LES PLUS LENTES")
    print("="*70)
    print("🔍 Analyse basée sur votre vraie partie de jeu")
    print("   • 'cumulative': Temps total passé dans la fonction + sous-fonctions")
    print("   • 'percall': Temps moyen par appel")
    print("   • Identifiez les goulots d'étranglement pour optimiser !")
    print("="*70)

    ps.print_stats(30)

    print(s.getvalue())

    # Sauvegarder les résultats complets pour une analyse plus poussée
    output_file = "profile_results.prof"
    profiler.dump_stats(output_file)
    print(f"\n💾 Résultats complets sauvegardés dans '{output_file}'")
    print(f"   Pour analyse interactive: python -m pstats {output_file}")
    print("\n🎯 Prochaines étapes d'optimisation:")
    print("   1. Concentrez-vous sur les fonctions avec le plus de 'cumulative'")
    print("   2. Vérifiez les appels fréquents (haut 'ncalls')")
    print("   3. Optimisez les boucles et les calculs mathématiques")

if __name__ == "__main__":
    run_profiler()