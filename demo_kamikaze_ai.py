#!/usr/bin/env python3
"""
Démonstration de l'IA avancée du Kamikaze (version refactorisée).
Simule différents scénarios de décision et montre comment l'unité Kamikaze réagit.
"""

from src.components.globals import mapComponent
from src.processeurs.KamikazeAiProcessor import KamikazeAiProcessor
from src.components.core.positionComponent import PositionComponent
import sys
import os
from pathlib import Path
import numpy as np
import joblib

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def demo_kamikaze_ai():
    print("🚀 DÉMONSTRATION DE L'IA AVANCÉE DU KAMIKAZE")
    print("=" * 60)

    # Préparer une carte de test réaliste
    grid = mapComponent.creer_grille()
    mapComponent.placer_elements(grid)

    ai_processor = KamikazeAiProcessor(grid=grid)
    model_path = "src/models/kamikaze_ai_rf_model.pkl"

    if os.path.exists(model_path):
        ai_processor.model = joblib.load(model_path)
        print("🤖 Modèle RandomForest chargé !")
    else:
        print("⚠️ Aucun modèle trouvé, les prédictions seront aléatoires.")

    scenarios = [
        {
            "name": "Trajectoire libre",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [],
            "threats": [],
            "expected": "Continuer ou booster"
        },
        {
            "name": "Obstacle devant",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [PositionComponent(x=400, y=750)],
            "threats": [],
            "expected": "Tourner pour éviter"
        },
        {
            "name": "Menace directe",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [],
            "threats": [PositionComponent(x=400, y=750)],
            "expected": "Évitement de projectile"
        },
        {
            "name": "Navigation complexe",
            "unit_pos": PositionComponent(x=200, y=750, direction=45),
            "obstacles": [PositionComponent(x=800, y=800), PositionComponent(x=1200, y=700)],
            "threats": [PositionComponent(x=500, y=780)],
            "expected": "Navigation stratégique"
        }
    ]

    success = 0

    for i, s in enumerate(scenarios, 1):
        print(f"\n📊 Scénario {i}: {s['name']}")

        target_pos = ai_processor.find_enemy_base_position(1)
        print(f"   - Position: ({s['unit_pos'].x:.0f}, {s['unit_pos'].y:.0f})")
        print(f"   - Cible: ({target_pos.x:.0f}, {target_pos.y:.0f})")
        print(
            f"   - Obstacles: {len(s['obstacles'])} | Menaces: {len(s['threats'])}")
        print(f"   - Attendu: {s['expected']}")

        start = (int(s['unit_pos'].x // 60), int(s['unit_pos'].y // 60))
        goal = (int(target_pos.x // 60), int(target_pos.y // 60))
        path = ai_processor.astar(ai_processor.grid, start, goal)

        if path:
            print(f"   => Chemin trouvé (A*): {len(path)} étapes")
        else:
            print("   => Aucun chemin trouvé (A*)")

        features = ai_processor._get_features_for_state(
            s['unit_pos'],
            target_pos,
            s['obstacles'],
            s['threats'],
            boost_cooldown=s.get('boost_cooldown', 0.0)
        )

        if ai_processor.model:
            q_values = [ai_processor.model.predict(
                [features + [a]])[0] for a in range(4)]
            actions = ["Continuer", "Tourner gauche",
                       "Tourner droite", "Activer boost"]
            best_action = actions[int(np.argmax(q_values))]
        else:
            best_action = np.random.choice(
                ["Continuer", "Tourner gauche", "Tourner droite", "Activer boost"])

        print(f"   => Action prédite: {best_action}")

        if ("tourner" in best_action.lower() and "éviter" in s['expected'].lower()) or \
           ("booster" in best_action.lower() and "boost" in s['expected'].lower()) or \
           ("continuer" in best_action.lower() and "Continuer" in s['expected']):
            success += 1
            print("      ✅ Cohérent avec l'attendu")
        else:
            print("      ❌ Décision inattendue")

    print("\n=" * 30)
    print(f"🎯 Résultats: {success}/{len(scenarios)} scénarios corrects")
    print("🎮 Démonstration terminée — L'IA du Kamikaze est opérationnelle !")


if __name__ == "__main__":
    demo_kamikaze_ai()
