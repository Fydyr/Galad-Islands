#!/usr/bin/env python3
"""
Démonstration animée du pathfinding A* et de l'évitement d'obstacles du Kamikaze.
"""

from src.processeurs.CapacitiesSpecialesProcessor import CapacitiesSpecialesProcessor
from src.factory.unitType import UnitType
from src.components.globals import mapComponent
from src.constants.gameplay import SPECIAL_ABILITY_COOLDOWN
from src.components.core.KamikazeAiComponent import KamikazeAiComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.processeurs.KamikazeAiProcessor import KamikazeAiProcessor
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.settings.settings import MAP_WIDTH, MAP_HEIGHT
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
TARGET_RADIUS = 25
BOOST_DURATION = 1.0  # secondes


def draw_grid(screen):
    """Affiche la grille simplifiée en bleu océan avec lignes claires."""
    # Fond bleu
    screen.fill((100, 180, 255))
    for x in range(0, SCREEN_WIDTH, TILE_SIZE):
        pygame.draw.line(screen, (50, 150, 200), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
        pygame.draw.line(screen, (50, 150, 200), (0, y), (SCREEN_WIDTH, y))


def draw_scenario(screen, kamikaze_pos, kamikaze_angle, obstacles, threats, base_pos, action=None, boost=False):
    """Obsolète, conservée pour compatibilité si nécessaire."""
    draw_grid(screen)
    # ... (le reste de la fonction est maintenant dans draw_simulation_state)


def draw_path(screen, path):
    """Dessine le chemin A* en jaune."""
    if len(path) > 1:
        pygame.draw.lines(screen, (255, 255, 0), False, path, 2)


def draw_target(screen, target_pos):
    """Dessine la cible finale (croix rouge)."""
    pygame.draw.line(screen, (255, 0, 0), (target_pos.x - 15, target_pos.y - 15), (target_pos.x + 15, target_pos.y + 15), 3)
    pygame.draw.line(screen, (255, 0, 0), (target_pos.x - 15, target_pos.y + 15), (target_pos.x + 15, target_pos.y - 15), 3)


def draw_waypoint(screen, waypoint_pos):
    """Dessine le waypoint actuel (cercle vert)."""
    pygame.draw.circle(screen, (0, 255, 0), (int(waypoint_pos[0]), int(waypoint_pos[1])), 8, 2)


def draw_threats_and_trajectories(screen, threats, initial_threats):
    """Dessine les menaces (cercles rouges) et leur trajectoire (ligne pointillée)."""
    for i, threat in enumerate(threats):
        # Dessiner la trajectoire depuis le point de départ
        start_pos = initial_threats[i]['pos']
        current_pos = threat['pos']
        pygame.draw.line(screen, (255, 100, 100), start_pos, current_pos, 1) # Ligne simple pour la trajectoire

        # Dessiner la menace
        pygame.draw.circle(screen, (255, 0, 0), (int(current_pos[0]), int(current_pos[1])), THREAT_RADIUS)

def draw_simulation_state(screen, kamikaze_pos, kamikaze_angle, obstacles, heavy_units, threats, initial_threats, target_pos, path, current_waypoint_index, ally_base_pos, enemy_base_pos, boost=False, recalculating=False):
    """Dessine tous les éléments du scénario."""
    # Obstacles
    for obs in obstacles:
        pygame.draw.circle(screen, (100, 100, 100),
                           (int(obs.x), int(obs.y)), OBSTACLE_RADIUS)

    # Menaces
    if threats:
        draw_threats_and_trajectories(screen, threats, initial_threats)

    # Bases
    if ally_base_pos:
        pygame.draw.rect(screen, (0, 0, 200), (ally_base_pos.x - 20, ally_base_pos.y - 20, 40, 40))
    if enemy_base_pos:
        pygame.draw.rect(screen, (139, 0, 0), (enemy_base_pos.x - 20, enemy_base_pos.y - 20, 40, 40))

    # Unités lourdes ennemies
    for unit in heavy_units:
        pygame.draw.rect(screen, (180, 0, 0), (unit.x - 15, unit.y - 15, 30, 30))

    # Cible finale
    draw_target(screen, target_pos)

    # Chemin A*
    draw_path(screen, path)
    if current_waypoint_index < len(path):
        draw_waypoint(screen, path[current_waypoint_index])

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
    
    if recalculating:
        font = pygame.font.SysFont("Arial", 18)
        txt_surface = font.render("Recalcul du chemin...", True, (255, 100, 0))
        screen.blit(txt_surface, (kamikaze_pos.x + 20, kamikaze_pos.y - 20))


def demo_kamikaze_ai():
    """Démontre le pathfinding A* de l'IA du Kamikaze avec animation pygame."""
    print("🚀 DÉMONSTRATION DU PATHFINDING A* DU KAMIKAZE (pygame)")

    # Initialiser pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Démo Pathfinding A* - Kamikaze AI")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    # Créer une vraie grille de jeu simplifiée
    dummy_grid = mapComponent.creer_grille()
    mapComponent.placer_elements(dummy_grid)

    # Initialiser l'IA
    ai_processor = KamikazeAiProcessor(world_map=dummy_grid, auto_train_model=False)
    capacities_processor = CapacitiesSpecialesProcessor()

    # Scénarios
    scenarios = [
        {
            "name": "Trajectoire directe - Aucun obstacle",
            "unit_pos": PositionComponent(x=100, y=400, direction=0),
            "obstacles": [],
            "heavy_units": [],
            "threats": [],
        },
        {
            "name": "Évitement d'obstacle - Île sur le chemin",
            "unit_pos": PositionComponent(x=100, y=400, direction=0),
            "obstacles": [PositionComponent(x=400, y=400), PositionComponent(x=550, y=400)],
            "heavy_units": [],
            "threats": [],
        },
        {
            "name": "Ciblage d'unité lourde",
            "unit_pos": PositionComponent(x=100, y=400, direction=0),
            "obstacles": [PositionComponent(x=400, y=350), PositionComponent(x=400, y=450)],
            "heavy_units": [PositionComponent(x=800, y=400)],
            "threats": [],
        },
        {
            "name": "Évitement de menaces mobiles",
            "unit_pos": PositionComponent(x=100, y=400, direction=0),
            "obstacles": [],
            "heavy_units": [],
            "threats": [
                {'pos': np.array([800.0, 350.0]), 'vel': np.array([-1.0, 0.05])},
                {'pos': np.array([800.0, 450.0]), 'vel': np.array([-1.0, -0.05])},
                {'pos': np.array([400.0, 200.0]), 'vel': np.array([1.0, 0.5])},
                {'pos': np.array([400.0, 600.0]), 'vel': np.array([1.0, -0.5])},
            ],
        },
        {
            "name": "Navigation complexe",
            "unit_pos": PositionComponent(x=100, y=400, direction=0),
            "obstacles": [
                PositionComponent(x=400, y=300),
                PositionComponent(x=600, y=500),
                PositionComponent(x=800, y=200),
            ],
            "heavy_units": [],
            "threats": [],
        }
    ]

    for scenario in scenarios:
        # --- Initialisation du scénario ---
        kamikaze_pos = PositionComponent(
            scenario['unit_pos'].x, scenario['unit_pos'].y, scenario['unit_pos'].direction)
        my_team_id = 1

        # Copie profonde pour garder l'état initial des menaces
        threats = [t.copy() for t in scenario.get("threats", [])]
        initial_threats = [t.copy() for t in scenario.get("threats", [])]
        threat_speed = 150.0 # pixels par seconde

        # Nettoyer la base de données esper AVANT de créer les entités du scénario
        esper.clear_database()

        ally_base_pos = ai_processor.find_enemy_base_position(2) # Base de l'équipe 1

        # Créer l'entité kamikaze pour la simulation
        kamikaze_ent = esper.create_entity(
            kamikaze_pos,
            VelocityComponent(maxUpSpeed=3.0 * 60), # Vitesse en pixels/seconde
            TeamComponent(my_team_id),
            KamikazeAiComponent(unit_type=UnitType.KAMIKAZE),
            SpeKamikazeComponent()
        )
        # Créer des entités factices pour le ciblage et les menaces
        enemy_base_pos = ai_processor.find_enemy_base_position(my_team_id)
        esper.create_entity(TeamComponent(2), HealthComponent(1000, 1000), enemy_base_pos)
        for unit_pos in scenario.get("heavy_units", []):
            esper.create_entity(TeamComponent(2), HealthComponent(500, 500), unit_pos)
        # Créer des entités pour les menaces afin que l'IA puisse les détecter
        threat_entities = []
        for i, threat in enumerate(threats):
            threat_ent = esper.create_entity(
                PositionComponent(threat['pos'][0], threat['pos'][1]),
                TeamComponent(2) # Menace ennemie
            )
            threat_entities.append(threat_ent)

        # --- Boucle d'animation ---
        start_time = time.time()
        recalculating_indicator_timer = 0.0
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    running = False
            
            dt = clock.get_time() / 1000.0 # Delta time en secondes
            if recalculating_indicator_timer > 0:
                recalculating_indicator_timer -= dt


            # Mettre à jour la position des menaces
            for i, threat in enumerate(threats):
                vel = threat['vel'] / np.linalg.norm(threat['vel']) if np.linalg.norm(threat['vel']) > 0 else np.array([0,0])
                threat['pos'] += vel * threat_speed * dt
                # Mettre à jour la position du composant esper
                if i < len(threat_entities):
                    threat_pos_comp = esper.component_for_entity(threat_entities[i], PositionComponent)
                    threat_pos_comp.x = threat['pos'][0]
                    threat_pos_comp.y = threat['pos'][1]
            
            # Mettre à jour les timers des capacités (boost, etc.)
            capacities_processor.process(dt)

            # --- Logique de l'IA ---
            # Sauvegarder l'état du chemin avant l'appel à l'IA
            path_before = ai_processor._kamikaze_paths.get(kamikaze_ent, {}).get('path', [])
            
            # Laisser l'IA décider et agir
            ai_processor.kamikaze_logic(kamikaze_ent, kamikaze_pos, esper.component_for_entity(kamikaze_ent, VelocityComponent), esper.component_for_entity(kamikaze_ent, TeamComponent))
            
            # Mettre à jour la position du kamikaze en fonction de sa vélocité
            kamikaze_vel = esper.component_for_entity(kamikaze_ent, VelocityComponent)
            kamikaze_spe = esper.component_for_entity(kamikaze_ent, SpeKamikazeComponent)
            speed_multiplier = kamikaze_spe.speed_multiplier if kamikaze_spe.is_active else 1.0
            kamikaze_pos.x += kamikaze_vel.currentSpeed * speed_multiplier * dt * math.cos(math.radians(kamikaze_pos.direction))
            kamikaze_pos.y += kamikaze_vel.currentSpeed * speed_multiplier * dt * math.sin(math.radians(kamikaze_pos.direction))
            effective_speed = kamikaze_vel.currentSpeed * (kamikaze_spe.speed_multiplier if kamikaze_spe.is_active else 1.0)
            kamikaze_pos.x += effective_speed * dt * math.cos(math.radians(kamikaze_pos.direction))
            kamikaze_pos.y += effective_speed * dt * math.sin(math.radians(kamikaze_pos.direction))

            # Vérifier si un recalcul a eu lieu
            path_after = ai_processor._kamikaze_paths.get(kamikaze_ent, {}).get('path', [])
            if path_before != path_after:
                recalculating_indicator_timer = 1.0 # Afficher pendant 1 seconde

            # Extraire les infos pour l'affichage
            path_info = ai_processor._kamikaze_paths.get(kamikaze_ent, {})
            path_world = path_info.get('path', [])
            waypoint_index = path_info.get('waypoint_index', 0)
            target_pos = ai_processor.find_best_kamikaze_target(kamikaze_pos, my_team_id)

            # Affichage
            draw_grid(screen)
            is_boosting = esper.component_for_entity(kamikaze_ent, SpeKamikazeComponent).is_active if esper.entity_exists(kamikaze_ent) else False
            draw_simulation_state(screen, kamikaze_pos, kamikaze_pos.direction, scenario['obstacles'], scenario.get("heavy_units", []),
                                  threats, initial_threats, target_pos, path_world, waypoint_index, ally_base_pos, enemy_base_pos, boost=is_boosting, recalculating=(recalculating_indicator_timer > 0))

            # Infos
            info_lines = [
                f"Scénario: {scenario['name']}",
                f"Cible: {'Unité lourde' if scenario.get('heavy_units') and target_pos != enemy_base_pos else 'Base Ennemie'}",
                f"Waypoints: {len(path_world)}",
                "Appuyez sur Entrée pour le scénario suivant..."
            ]
            for i, line in enumerate(info_lines):
                txt_surface = font.render(line, True, (0, 0, 0))
                screen.blit(txt_surface, (10, 10 + i * 22))

            pygame.display.flip()
            clock.tick(FPS)

    print(
        f"\n🎯 DÉMONSTRATION TERMINÉE")
    pygame.quit()


if __name__ == "__main__":
    demo_kamikaze_ai()
