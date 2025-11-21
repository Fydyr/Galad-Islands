import esper
import random
import math
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import pickle
import os
import sys
import heapq
from typing import Optional
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.special.speDruidComponent import SpeDruid
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE, config_manager

class MaraudeurAI:
    """IA améliorée pour la troupe Maraudeur (Maraudeur Zeppelin) utilisant scikit-learn"""

    def __init__(self, entity):
        self.entity = entity
        self.cooldown = 0.0
        self.shield_active = False
        self.grid = None
        self.debug_mode = False  # Flag pour contrôler les logs
        
        # Système d'apprentissage avec scikit-learn
        self.decision_tree = DecisionTreeClassifier(random_state=42, max_depth=8)
        self.scaler = StandardScaler()
        self.pathfinding_nn = NearestNeighbors(n_neighbors=5, algorithm='ball_tree')
        
        # Base de données d'expérience
        self.experiences = []
        self.training_data = []
        self.training_labels = []
        self.is_trained = False
        
        # État actuel pour apprentissage
        self.last_state = None
        self.last_action = None
        self.last_reward = 0
        self.death_penalty = 100.0
        self.death_penalized = False
        
        # Performance tracking
        self.survival_time = 0.0
        self.last_survival_reward_time = -9999.0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.successful_attacks = 0
        self.failed_attacks = 0
        
        # Comportement adaptatif
        self.current_strategy = "balanced"
        self.strategy_performance = {
            "balanced": {"success": 0, "failure": 0},
            "aggressive": {"success": 0, "failure": 0},
            "defensive": {"success": 0, "failure": 0},
            "tactical": {"success": 0, "failure": 0}
        }
        
        # Pathfinding intelligent
        self.safe_positions = []
        self.dangerous_positions = []
        self.optimal_distances = {}
        self.nav_grid = None
        self.path = []
        self.path_recalc_timer = 0.0
        
        # Initialiser avec des données de base
        self._initialize_base_knowledge()
        
        # Charger modèle sauvegardé si disponible
        self._load_model()

    def update(self, world, dt):
        """Mise à jour principale de l'IA avec apprentissage"""
        # Désactiver l'IA si l'unité est sélectionnée par le joueur
        if world.has_component(self.entity, PlayerSelectedComponent):
            return
            
        try:
            # Récupérer les composants
            pos = world.component_for_entity(self.entity, PositionComponent)
            vel = world.component_for_entity(self.entity, VelocityComponent)
            radius = world.component_for_entity(self.entity, RadiusComponent)
            health = world.component_for_entity(self.entity, HealthComponent)
            team = world.component_for_entity(self.entity, TeamComponent)
            spe = world.component_for_entity(self.entity, SpeMaraudeur)
            
        except Exception as e:
            if self.debug_mode:
                print(f"Erreur composants Maraudeur {self.entity}: {e}")
            return

        # Mettre à jour les statistiques de survie
        self.survival_time += dt
        
        # Momentum pour éviter changements brusques de vitesse
        if not hasattr(self, '_last_speed'):
            self._last_speed = 0.0
        
        # Créer la grille de navigation si elle n'existe pas
        if self.grid and self.nav_grid is None:
            self._create_navigation_grid()

        # Mettre à jour le timer de recalcul de chemin
        if self.path_recalc_timer > 0:
            self.path_recalc_timer -= dt

        # Gestion du cooldown
        if self.cooldown > 0:
            self.cooldown -= dt

        # Analyser la situation tactique
        try:
            current_state = self._analyze_situation(world, pos, health, team)
            
            # Prédire la meilleure action
            action = self._predict_best_action(current_state)
            
            # Calculer la récompense de l'action précédente
            is_learning_disabled = config_manager.get("disable_ai_learning", False)
            if not is_learning_disabled and self.last_state is not None and self.last_action is not None:
                reward = self._calculate_reward(current_state, health)
                self._record_experience(self.last_state, self.last_action, reward, current_state)
            
            # Exécuter l'action avec tir en salve si nécessaire
            self._execute_action_with_combat(action, world, pos, vel, health, team, spe)
            
            # Appliquer l'évitement d'obstacles après toutes décisions
            final_direction = self._apply_obstacle_avoidance(world, pos, vel)
            if final_direction is not None:
                # Limiter la vitesse de rotation pour éviter l'effet "toupie"
                pos.direction = self._smooth_turn(pos.direction, final_direction, max_delta=12.0)
            
            # Lisser les transitions de vitesse
            if abs(vel.currentSpeed - self._last_speed) > 1.5:
                vel.currentSpeed = self._last_speed + math.copysign(1.5, vel.currentSpeed - self._last_speed)
            self._last_speed = vel.currentSpeed
            
        except Exception as e:
            if self.debug_mode:
                print(f"Erreur IA Maraudeur {self.entity}: {e}")
            self._action_patrol(pos, vel)
        
        # Sauvegarder l'état pour le prochain cycle
        self.last_state = current_state.copy()
        self.last_action = action
        
        # Réentraîner le modèle périodiquement si l'apprentissage est activé
        if not is_learning_disabled:
            if len(self.experiences) >= 10 and len(self.experiences) % 5 == 0:
                self._retrain_model()
        
            # Adapter la stratégie basée sur les performances
            self._adapt_strategy()
        
            # Sauvegarder le modèle périodiquement
            if self.survival_time > 0 and int(self.survival_time) % 30 == 0:
                self._save_model()

    def _smooth_turn(self, current_dir: float, target_dir: float, max_delta: float = 12.0) -> float:
        """Tourne progressivement vers la direction cible pour éviter les rotations brusques"""
        current_dir = current_dir % 360.0
        target_dir = target_dir % 360.0
        
        # Calcul du plus petit écart angulaire signé (-180..180]
        diff = (target_dir - current_dir + 540.0) % 360.0 - 180.0
        
        # Limiter le changement à max_delta
        if diff > max_delta:
            diff = max_delta
        elif diff < -max_delta:
            diff = -max_delta
        
        new_dir = (current_dir + diff) % 360.0
        return new_dir

    def _apply_obstacle_avoidance(self, world, pos, vel) -> Optional[float]:
        """Ajuste la direction pour éviter les obstacles proches"""
        if vel.currentSpeed == 0 or not self.grid:
            return None

        # Marche arrière temporaire si coincé
        if not hasattr(self, '_reverse_timer'):
            self._reverse_timer = 0.0
            self._new_direction_after_reverse = None
            
        if self._reverse_timer > 0.0:
            self._reverse_timer = max(0.0, self._reverse_timer - 0.016)
            
            if self._reverse_timer <= 0.0 and self._new_direction_after_reverse is not None:
                pos.direction = self._new_direction_after_reverse
                self._new_direction_after_reverse = None
                vel.currentSpeed = max(vel.maxUpSpeed * 0.8, 3.5)
                return pos.direction
            
            vel.currentSpeed = max(vel.maxUpSpeed * 0.7, 3.0)
            return (pos.direction + 180) % 360

        # Détection de blocage
        if not hasattr(self, '_stuck_check_timer'):
            self._stuck_check_timer = 0.0
            self._last_stuck_check_pos = (pos.x, pos.y)
            self._stuck_counter = 0
            self._preferred_avoidance_direction = None

        self._stuck_check_timer += 0.016
        if self._stuck_check_timer > 2.0:
            dist_moved = math.hypot(pos.x - self._last_stuck_check_pos[0], pos.y - self._last_stuck_check_pos[1])
            if vel.currentSpeed > 1.0 and dist_moved < TILE_SIZE * 0.8:
                self._stuck_counter += 1
                if self._stuck_counter >= 1:
                    self._reverse_timer = 1.8
                    best_angle = self._choose_best_avoidance_direction(pos)
                    angle_change = best_angle + random.randint(-20, 20)
                    self._new_direction_after_reverse = (pos.direction + angle_change) % 360
                    vel.currentSpeed = max(vel.maxUpSpeed * 0.7, 3.0)
                    return (pos.direction + 180) % 360
            else:
                self._stuck_counter = 0
                self._preferred_avoidance_direction = None
            
            self._last_stuck_check_pos = (pos.x, pos.y)
            self._stuck_check_timer = 0.0

        # Évitement d'obstacles par capteurs
        probe_length = 5.0 * TILE_SIZE
        angles = [-60, -30, -10, 0, 10, 30, 60]
        direction_rad = math.radians(pos.direction)

        steering_force = 0.0
        obstacle_detected = False

        for i, angle_offset in enumerate(angles):
            probe_angle_rad = direction_rad + math.radians(angle_offset)
            
            for step in range(1, 4):
                dist = probe_length * (step / 3.0)
                probe_x = pos.x + dist * math.cos(probe_angle_rad)
                probe_y = pos.y + dist * math.sin(probe_angle_rad)

                grid_x = int(probe_x // TILE_SIZE)
                grid_y = int(probe_y // TILE_SIZE)

                if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
                    if self.grid[grid_y][grid_x] == TileType.GENERIC_ISLAND:
                        obstacle_detected = True
                        distance_factor = (1.0 - (dist / probe_length))
                        repulsion_strength = distance_factor * 50.0  # Réduit pour moins d'oscillations

                        if angle_offset == 0:
                            vel.currentSpeed *= 0.8
                            if self._preferred_avoidance_direction is None:
                                self._preferred_avoidance_direction = self._choose_best_avoidance_direction(pos)
                            steering_force += self._preferred_avoidance_direction
                        else:
                            steering_force += -math.copysign(repulsion_strength, angle_offset)
                        
                        break

        if obstacle_detected and hasattr(self, '_stuck_counter'):
            self._stuck_counter = max(0, self._stuck_counter - 1)

        if abs(steering_force) > 0.1:
            steering_force = max(-90, min(90, steering_force))
            new_direction = (pos.direction + steering_force) % 360
            return new_direction
        else:
            if hasattr(self, '_preferred_avoidance_direction'):
                self._preferred_avoidance_direction = None
        
        return None

    def _choose_best_avoidance_direction(self, pos):
        """Choisit la meilleure direction pour contourner (gauche ou droite)"""
        if not self.grid:
            return 60
        
        left_clear = 0
        right_clear = 0
        check_angles = [30, 60, 90]
        
        for angle in check_angles:
            left_rad = math.radians(pos.direction + angle)
            left_x = pos.x + 3 * TILE_SIZE * math.cos(left_rad)
            left_y = pos.y + 3 * TILE_SIZE * math.sin(left_rad)
            if self._is_position_clear(left_x, left_y):
                left_clear += 1
            
            right_rad = math.radians(pos.direction - angle)
            right_x = pos.x + 3 * TILE_SIZE * math.cos(right_rad)
            right_y = pos.y + 3 * TILE_SIZE * math.sin(right_rad)
            if self._is_position_clear(right_x, right_y):
                right_clear += 1
        
        return 60 if left_clear > right_clear else -60

    def _is_position_clear(self, x, y):
        """Vérifie si une position est dégagée (pas d'île)"""
        if not self.grid:
            return True
        
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
            return self.grid[grid_y][grid_x] != TileType.GENERIC_ISLAND
        return False

    def _create_navigation_grid(self):
        """Crée une grille de navigation où les îles sont 'gonflées' pour l'évitement"""
        if not self.grid:
            return

        grid_h, grid_w = len(self.grid), len(self.grid[0])
        self.nav_grid = [row[:] for row in self.grid]
        
        inflation_radius = 2

        for r in range(grid_h):
            for c in range(grid_w):
                if self.grid[r][c] == TileType.GENERIC_ISLAND:
                    for dr in range(-inflation_radius, inflation_radius + 1):
                        for dc in range(-inflation_radius, inflation_radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < grid_h and 0 <= nc < grid_w:
                                if self.nav_grid[nr][nc] != TileType.GENERIC_ISLAND:
                                    self.nav_grid[nr][nc] = TileType.GENERIC_ISLAND

    # ... (continuer avec toutes les autres méthodes du fichier original)
    # Pour l'instant, je copie les méthodes essentielles manquantes
    
    def _analyze_situation(self, world, pos, health, team):
        """Analyse la situation actuelle et retourne un vecteur d'état"""
        state = np.zeros(15)
        
        if self.grid:
            state[0] = pos.x / (len(self.grid[0]) * TILE_SIZE)
            state[1] = pos.y / (len(self.grid) * TILE_SIZE)
        
        state[2] = health.currentHealth / health.maxHealth
        
        enemies = self._find_nearby_enemies(world, pos, team)
        state[3] = min(len(enemies), 5) / 5.0
        
        if enemies:
            closest_enemy = min(enemies, key=lambda e: e[1])
            state[4] = min(closest_enemy[1] / (10 * TILE_SIZE), 1.0)
            if world.has_component(closest_enemy[0], HealthComponent):
                enemy_health = world.component_for_entity(closest_enemy[0], HealthComponent)
                state[5] = enemy_health.currentHealth / enemy_health.maxHealth
        
        obstacles = self._analyze_nearby_obstacles(pos)
        state[6] = obstacles['islands'] / 10.0
        state[7] = obstacles['mines'] / 5.0
        state[8] = obstacles['walls'] / 4.0
        
        state[9] = self._calculate_tactical_advantage(pos, enemies)
        state[10] = self._is_in_safe_zone(pos)
        
        state[11] = 1.0 if self.shield_active else 0.0
        state[12] = max(0, self.cooldown) / 5.0
        state[13] = self.survival_time / 300.0
        state[14] = {"balanced": 0, "aggressive": 0.33, "defensive": 0.66, "tactical": 1.0}[self.current_strategy]
        
        return state
    
    def _predict_best_action(self, state):
        """Prédit la meilleure action à partir de l'état actuel"""
        if not self.is_trained:
            return self._get_default_action(state)
        
        try:
            state_scaled = self.scaler.transform([state])
            predicted_action = self.decision_tree.predict(state_scaled)[0]
            
            # Exploration réduite à 15% pour mouvements plus stables
            if not config_manager.get("disable_ai_learning", False) and random.random() < 0.15:
                return random.randint(0, 7)
            
            return int(predicted_action)
            
        except Exception as e:
            return self._get_default_action(state)
    
    def _get_default_action(self, state):
        """Action par défaut basée sur des règles simples"""
        health_ratio = state[2]
        enemy_count = state[3] * 5
        closest_enemy_dist = state[4]
        
        if health_ratio < 0.3:
            return 6  # Retraite
        elif enemy_count > 0 and closest_enemy_dist < 0.4:
            return 1  # Attaque
        elif enemy_count > 2 and closest_enemy_dist < 0.8:
            return 5  # Défensif
        else:
            return 0  # Approche
    
    # Copie des autres méthodes depuis le fichier original...
    # (toutes les méthodes _find_nearby_enemies, _calculate_reward, etc.)
