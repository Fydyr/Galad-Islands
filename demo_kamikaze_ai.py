#!/usr/bin/env python3
"""
Démonstration animée de l'IA avancée du Kamikaze avec pygame.
Montre comment l'unité Kamikaze prend des décisions stratégiques de navigation.
"""

from src.components.globals import mapComponent
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN
from src.components.core.KamikazeAiComponent import KamikazeAiComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.velocityComponent import VelocityComponent
from src.processeurs.KamikazeAiProcessor import KamikazeAiProcessor
from src.components.core.positionComponent import PositionComponent
import sys
import os
from pathlib import Path
import time
import math

import pygame
import numpy as np
import esper

sys.path.insert(0, str(Path(__file__).parent / "src"))


# Paramètres graphiques
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 800
TILE_SIZE = 60
FPS = 60
CAMIKAZE_RADIUS = 15
OBSTACLE_RADIUS = 20
THREAT_RADIUS = 12
BASE_RADIUS = 25
BOOST_DURATION = 1.0  # secondes


def draw_grid(screen):
    """Affiche la grille simplifiée en bleu océan avec lignes claires."""
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (50, 150, 200), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (50, 150, 200), (0, y), (SCREEN_WIDTH, y))


def draw_scenario(screen, kamikaze_pos, kamikaze_angle, obstacles, threats, base_pos, action=None, boost=False):
    """Dessine tous les éléments du scénario."""
    screen.fill((100, 180, 255))  # bleu océan clair
    draw_grid(screen)

    # Obstacles
    for obs in obstacles:
        pygame.draw.circle(screen, (100, 100, 100),
                           (int(obs.x), int(obs.y)), OBSTACLE_RADIUS)

    # Menaces
    for threat in threats:
        pygame.draw.circle(screen, (220, 50, 50), (int(
            threat.x), int(threat.y)), THREAT_RADIUS)

    # Base ennemie
    pygame.draw.circle(screen, (200, 30, 30), (int(
        base_pos.x), int(base_pos.y)), BASE_RADIUS)

    # Kamikaze
    color = (0, 255, 255) if boost else (255, 255, 0)
    pygame.draw.circle(screen, color, (int(kamikaze_pos.x),
                       int(kamikaze_pos.y)), CAMIKAZE_RADIUS)
    # Flèche directionnelle
    tip_x = kamikaze_pos.x + CAMIKAZE_RADIUS * \
        math.cos(math.radians(kamikaze_angle))
    tip_y = kamikaze_pos.y + CAMIKAZE_RADIUS * \
        math.sin(math.radians(kamikaze_angle))
    pygame.draw.line(screen, (0, 0, 0), (kamikaze_pos.x,
                     kamikaze_pos.y), (tip_x, tip_y), 2)


def demo_kamikaze_ai():
    """Démontre les décisions de l'IA du Kamikaze avec animation pygame."""
    print("🚀 DÉMONSTRATION DE L'IA AVANCÉE DU KAMIKAZE (pygame)")

    # Initialiser pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Démo Kamikaze AI")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    # Créer une vraie grille de jeu simplifiée
    dummy_grid = mapComponent.creer_grille()
    mapComponent.placer_elements(dummy_grid)

    # Initialiser l'IA
    ai_processor = KamikazeAiProcessor(world_map=dummy_grid)
    import joblib
    rf_path = "src/models/kamikaze_ai_rf_model.pkl"
    if os.path.exists(rf_path):
        ai_processor.model = joblib.load(rf_path)
        print("🤖 Modèle RandomForest chargé pour la démo Kamikaze !")
    else:
        print("❌ Aucun modèle RandomForest Kamikaze trouvé !")

    # Scénarios
    scenarios = [
        {
            "name": "Boost indisponible - doit avancer sans boost",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [PositionComponent(x=400, y=750), PositionComponent(x=600, y=750)],
            "threats": [],
            "expected": "Continuer (boost impossible)",
            "boost_cooldown": 5.0
        },
        {
            "name": "Trajectoire directe - Aucun obstacle",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [],
            "threats": [],
            "expected": "Continuer tout droit"
        },
        {
            "name": "Évitement d'obstacle - Île sur le chemin",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [PositionComponent(x=400, y=750), PositionComponent(x=550, y=750)],
            "threats": [],
            "expected": "Tourner pour éviter"
        },
        {
            "name": "Évitement de projectiles - Menaces en approche",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [],
            "threats": [PositionComponent(x=350, y=750), PositionComponent(x=500, y=750)],
            "expected": "Tourner pour éviter"
        },
        {
            "name": "Boost stratégique - Distance importante",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            # un obstacle tardif pour forcer boost
            "obstacles": [PositionComponent(x=600, y=750)],
            "threats": [],
            "expected": "Continuer (boost possible)"
        },
        {
            "name": "Navigation complexe - Obstacles et menaces",
            "unit_pos": PositionComponent(x=200, y=750, direction=0),
            "obstacles": [PositionComponent(x=400, y=700), PositionComponent(x=600, y=750), PositionComponent(x=800, y=800)],
            "threats": [PositionComponent(x=350, y=720), PositionComponent(x=500, y=780)],
            "expected": "Navigation stratégique"
        }
    ]


    success_count = 0

    for scenario in scenarios:
        kamikaze_pos = PositionComponent(
            scenario['unit_pos'].x, scenario['unit_pos'].y, scenario['unit_pos'].direction)
        boost_cooldown = scenario.get('boost_cooldown', 0.0)
        my_team_id = 1
        base_pos = ai_processor.find_enemy_base_position(my_team_id)

        # Features et prédiction
        features = ai_processor._get_features_for_state(
            kamikaze_pos, base_pos, scenario['obstacles'], scenario['threats'], boost_cooldown)
        if ai_processor.model:
            q_values = []
            action_names = ["Continuer", "Tourner gauche",
                            "Tourner droite", "Activer boost"]
            for act in range(len(action_names)):
                state_action = features + [act]
                q_value = ai_processor.model.predict([state_action])[0]
                q_values.append(q_value)
            best_action_index = np.argmax(q_values)
            predicted_action = action_names[best_action_index]
        else:
            predicted_action = "Aucune IA"

        # Vérification réussite
        name_lower = scenario["name"].lower()
        if "boost indisponible" in name_lower:
            success = predicted_action == "Continuer"
        elif "trajectoire directe" in name_lower or "boost stratégique" in name_lower:
            success = predicted_action in ["Continuer", "Activer boost"]
        elif "évitement" in name_lower or "navigation complexe" in name_lower:
            success = predicted_action in [
                "Tourner gauche", "Tourner droite", "Activer boost"]
        else:
            success = predicted_action in ["Continuer", "Activer boost"]
        if success:
            success_count += 1
        success_str = "✅" if success else "❌"

        # Animation
        start_time = time.time()
        boost_flag = predicted_action == "Activer boost"
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Déplacement simplifié vers base
            dx = base_pos.x - kamikaze_pos.x
            dy = base_pos.y - kamikaze_pos.y
            distance = math.hypot(dx, dy)
            if distance > 1:
                angle = math.degrees(math.atan2(dy, dx))
                kamikaze_pos.x += math.cos(math.radians(angle)) * 2
                kamikaze_pos.y += math.sin(math.radians(angle)) * 2
                kamikaze_pos.direction = angle
            else:
                running = False

            # Affichage
            draw_scenario(screen, kamikaze_pos, kamikaze_pos.direction,
                          scenario['obstacles'], scenario['threats'], base_pos, predicted_action, boost_flag and time.time() - start_time < BOOST_DURATION)

            # Infos
            info_lines = [
                f"Scénario: {scenario['name']}",
                f"Action IA: {predicted_action}",
                f"Attendu: {scenario['expected']}",
                f"Évaluation: {success_str}"
            ]
            for i, line in enumerate(info_lines):
                txt_surface = font.render(line, True, (0, 0, 0))
                screen.blit(txt_surface, (10, 10 + i * 22))

            pygame.display.flip()
            clock.tick(FPS)

        print(
            f"{scenario['name']} -> Action IA: {predicted_action} ({success_str})")
        print("Appuyez sur Entrée pour passer au scénario suivant...")
        input()

    print(
        f"\n🎯 RÉSULTATS DE LA DÉMONSTRATION: {success_count}/{len(scenarios)} scénarios réussis")
    pygame.quit()


if __name__ == "__main__":
    demo_kamikaze_ai()
