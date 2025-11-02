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
from src.components.core.attackComponent import AttackComponent # Import manquant
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.events.flyChestComponent import FlyingChestComponent
from src.components.special.speDruidComponent import SpeDruid
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE
from src.functions.resource_path import get_resource_path
from src.settings.settings import config_manager
from src.ia.ia_barhamus.log import get_logger

def get_app_data_path() -> str:
    """
    Retourne un chemin sûr pour stocker les données de l'application (modèles, sauvegardes).
    Ex: C:/Users/Username/AppData/Roaming/GaladIslands sur Windows.
    """
    app_name = "GaladIslands"
    # Si exécuté en version compilée (PyInstaller)
    if getattr(sys, 'frozen', False):
        if os.name == 'nt':  # Windows
            path = os.path.join(os.environ['APPDATA'], app_name)
        else:  # Linux, macOS
            path = os.path.join(os.path.expanduser('~'), '.local', 'share', app_name)
        os.makedirs(path, exist_ok=True)
        return path
    else:
        # Version non compilée : stocker in src/models du projet
        path = os.path.join(os.path.dirname(__file__), '..', 'models')
        path = os.path.abspath(path)
        os.makedirs(path, exist_ok=True)
        return path

class BarhamusAI:
    """IA pour la troupe Barhamus (Maraudeur Zeppelin) utilisant scikit-learn"""

    def __init__(self, entity):
        self.entity = entity
        self.logger = get_logger()
        self.cooldown = 0.0
        self.shield_active = False
        self.grid = None
        self.debug_mode = False # NOUVEAU: Flag pour contrôler les logs

        # Chemin pour les modèles dynamiques
        self.models_dir = get_app_data_path()
        
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
        # Death penalty tracking (forte pénalité pour encourager la survie)
        self.death_penalty = 100.0  # montant soustrait si l'unit meurt
        self.death_penalized = False
        
        # Performance tracking
        self.survival_time = 0.0
        # Timer for periodic survival reward (grant at most once every N seconds)
        self.last_survival_reward_time = -9999.0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.successful_attacks = 0
        self.failed_attacks = 0
        
        # Comportement adaptatif
        self.current_strategy = "balanced"  # balanced, aggressive, defensive, tactical
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
        self.nav_grid = None # NOUVEAU: Grille de navigation avec obstacles gonflés
        self.path = [] # NOUVEAU: Chemin pour le pathfinding
        self.path_recalc_timer = 0.0
        
        # Initialize avec des données de base
        self._initialize_base_knowledge()
        
        # Charger modèle pré-entrainé si disponible
        self._load_pretrained_model()
        # Charger modèle sauvegardé spécifique à l'entity si disponible (priorité joueur)
        self._load_model()

    def _load_pretrained_model(self):
        """Charge le modèle/scaler pré-entrainé si disponible (pour démarrer avec une IA compétente)"""
        try:
            pretrained_path = os.path.join(self.models_dir, "barhamus_pretrained.pkl")
            if os.path.exists(pretrained_path):
                with open(pretrained_path, 'rb') as f:
                    model_data = pickle.load(f)
                self.decision_tree = model_data.get('decision_tree', self.decision_tree)
                self.scaler = model_data.get('scaler', self.scaler)
                self.is_trained = model_data.get('is_trained', False)
                self.logger.debug(f"Barhamus {self.entity}: Modèle pré-entrainé chargé")
        except (pickle.UnpicklingError, EOFError, KeyError) as e:
            # Erreurs courantes de déserialisation, non critiques
            self.logger.debug(f"Erreur chargement modèle pré-entrainé: {e}")

    def update(self, world, dt):
        """Mise à jour principale de l'IA avec apprentissage"""
        # Désactiver l'IA si l'unit est sélectionnée par le joueur
        if world.has_component(self.entity, PlayerSelectedComponent):
            # Optionnel : log pour debug
            if self.debug_mode:
                self.logger.debug(f"Barhamus {self.entity}: IA désactivée car unit sélectionnée.")
            return
        try:
            # Définir la variable ici pour qu'elle soit toujours disponible
            is_learning_disabled = config_manager.get("disable_ai_learning", False)

            # Récupérer les components
            pos = world.component_for_entity(self.entity, PositionComponent)
            vel = world.component_for_entity(self.entity, VelocityComponent) # Correction: pas de AttackComponent ici
            radius = world.component_for_entity(self.entity, RadiusComponent) # Correction: pas de AttackComponent ici
            health = world.component_for_entity(self.entity, HealthComponent) # Correction: pas de AttackComponent ici
            team = world.component_for_entity(self.entity, TeamComponent) # Correction: pas de AttackComponent ici
            spe = world.component_for_entity(self.entity, SpeMaraudeur) # Correction: pas de AttackComponent ici
            
        except Exception as e:
            self.logger.warning(f"Erreur composants Barhamus {self.entity}: {e}")
            return

        # Mettre à jour les statistiques de survie
        self.survival_time += dt
        
        # Create la grille de navigation si elle n'existe pas
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

            # NOUVEAU: Logique prioritaire pour chasser les coffres volants
            # Condition : pas en danger (santé > 60% et pas d'ennemis proches)
            enemies = self._find_nearby_enemies(world, pos, team)
            is_safe = health.currentHealth / health.maxHealth > 0.6 and not enemies

            if is_safe:
                closest_chest = self._find_nearby_chest(world, pos)
                if closest_chest:
                    # Chasser le coffre et ignorer les autres décisions pour ce tick
                    chest_pos = world.component_for_entity(closest_chest, PositionComponent)
                    angle = self._angle_to(pos.x - chest_pos.x, pos.y - chest_pos.y)
                    pos.direction = angle
                    vel.currentSpeed = 4.0 # Vitesse de chasse
                    return # Fin du traitement pour ce tick
            
            # Prédire la meilleure action en utilisant le modèle ou la logique By default
            action = self._predict_best_action(current_state)
            
            # Calculer la récompense de l'action précédente
            # Enregistrer l'expérience uniquement si l'apprentissage est activé
            if not is_learning_disabled and self.last_state is not None and self.last_action is not None:
                reward = self._calculate_reward(current_state, health)
                self._record_experience(self.last_state, self.last_action, reward, current_state)
            
            action_names = {0: "Approche", 1: "Attaque", 2: "Patrouille", 3: "Évitement", 4: "Bouclier", 5: "Défensif", 6: "Retraite", 7: "Embuscade"}
            if self.debug_mode:
                action_name = action_names.get(action, 'Inconnue')
                print(f"Barhamus {self.entity}: Exécute action {action} ({action_name})")
            
            # Exécuter l'action avec tir en salve si nécessaire
            self._execute_action_with_combat(action, world, pos, vel, health, team, spe)
            
        except Exception as e:
            self.logger.warning(f"Erreur IA Barhamus {self.entity}: {e}")
            # Action By default in case of error majeure
            self._action_patrol(pos, vel)
        
        # Sauvegarder l'état pour le prochain cycle
        self.last_state = current_state.copy()
        self.last_action = action
        
        # Ré-entraîner le modèle périodiquement si l'apprentissage est activé
        if not is_learning_disabled:
            if len(self.experiences) >= 10 and len(self.experiences) % 5 == 0:
                self._retrain_model()
        
            # Adapter la stratégie basée sur les performances
            self._adapt_strategy()
        
            # Sauvegarder le modèle périodiquement
            if self.survival_time > 0 and int(self.survival_time) % 30 == 0:
                self._save_model()

    def _analyze_situation(self, world, pos, health, team):
        """Analyse la situation actuelle et retourne un vecteur d'état"""
        state = np.zeros(15)  # Vecteur d'état de 15 dimensions
        
        # 0-2: Position normalisée
        if self.grid:
            state[0] = pos.x / (len(self.grid[0]) * TILE_SIZE)
            state[1] = pos.y / (len(self.grid) * TILE_SIZE)
        
        # 3: Santé normalisée
        state[2] = health.currentHealth / health.maxHealth
        
        # 4-6: Informations sur les ennemis proches
        enemies = self._find_nearby_enemies(world, pos, team)
        state[3] = min(len(enemies), 5) / 5.0  # Nombre d'ennemis (max 5)
        
        if enemies:
            closest_enemy = min(enemies, key=lambda e: e[1])
            state[4] = min(closest_enemy[1] / (10 * TILE_SIZE), 1.0)  # Distance normalisée
            # Force de l'ennemi le plus proche
            if world.has_component(closest_enemy[0], HealthComponent):
                enemy_health = world.component_for_entity(closest_enemy[0], HealthComponent)
                state[5] = enemy_health.currentHealth / enemy_health.maxHealth
        
        # 7-9: Obstacles et dangers
        obstacles = self._analyze_nearby_obstacles(pos)
        state[6] = obstacles['islands'] / 10.0
        state[7] = obstacles['mines'] / 5.0
        state[8] = obstacles['walls'] / 4.0
        
        # 10-11: Position tactique
        state[9] = self._calculate_tactical_advantage(pos, enemies)
        state[10] = self._is_in_safe_zone(pos)
        
        # 12-14: État interne
        state[11] = 1.0 if self.shield_active else 0.0
        state[12] = max(0, self.cooldown) / 5.0  # Cooldown normalisé (sur une base de 5s max)
        state[13] = self.survival_time / 300.0  # Temps de survie normalisé (5 min max)
        state[14] = {"balanced": 0, "aggressive": 0.33, "defensive": 0.66, "tactical": 1.0}[self.current_strategy]
        
        return state
    
    def _predict_best_action(self, state):
        """Prédit la meilleure action à partir de l'état actuel"""
        # Utiliser le modèle seulement s'il a été entraîné.
        # Ne pas dépendre de `training_data` qui n'est pas utilisé directement
        if not self.is_trained:
            if self.debug_mode:
                print(f"Barhamus {self.entity}: Modèle non entraîné -> action par défaut")
            return self._get_default_action(state)
        
        try:
            # Normaliser l'état
            state_scaled = self.scaler.transform([state])
            
            # Prédire l'action avec l'arbre de décision.
            # Utiliser predict_proba pour avoir une confiance et ajouter de l'aléatoire si l'IA est incertaine.
            predicted_action = self.decision_tree.predict(state_scaled)[0]
            
            # Add de l'exploration (30% de chance d'action aléatoire pour apprendre plus vite)
            if not config_manager.get("disable_ai_learning", False) and random.random() < 0.3:
                return random.randint(0, 7)  # 8 actions possibles
            
            print(f"Barhamus {self.entity}: Action PRÉDITE par modèle = {predicted_action}")
            # S'assurer que le type est bien un entier Python natif
            return int(predicted_action) 
            
        except Exception as e:
            print(f"Erreur prédiction IA: {e}")
            return self._get_default_action(state)
    
    def _get_default_action(self, state):
        """Action By default basée sur des règles simples"""
        health_ratio = state[2]
        enemy_count = state[3] * 5
        closest_enemy_dist = state[4]

        if health_ratio < 0.3:
            return 6  # Retraite
        elif enemy_count > 0 and closest_enemy_dist < 0.4: # Si ennemi proche
            return 1  # Attaque
        elif enemy_count > 2 and closest_enemy_dist < 0.8: # Si plusieurs ennemis à distance moyenne
            return 5  # Positionnement défensif
        else:
            return 0  # Approche
    
    def _execute_action_with_combat(self, action, world, pos, vel, health, team, spe):
        """Exécute l'action avec gestion du combat tactique"""
        # Exécuter l'action de mouvement
        self._execute_movement_action(action, world, pos, vel, team, spe)
        
        # Gestion spéciale du bouclier
        if action == 4:
            self._action_shield_management(spe, health)
        
        # Gestion du combat en parallèle
        self._handle_tactical_combat(action, world, pos, team)

        # NOUVEAU: Appliquer l'évitement d'obstacles after all décisions
        final_direction = self._apply_obstacle_avoidance(world, pos, vel)
        if final_direction is not None:
            # Limiter la vitesse de rotation pour éviter l'effet "toupie"
            pos.direction = self._smooth_turn(pos.direction, final_direction, max_delta=15.0)
    
    def _execute_movement_action(self, action, world, pos, vel, team, spe):
        """Execute only la partie mouvement de l'action"""
        if action == 0:
            self._action_aggressive_approach(world, pos, vel, team)
        elif action == 1:
            self._action_attack_movement(world, pos, vel, team)  # Mouvement d'attaque
        elif action == 2:
            self._action_patrol(pos, vel)
        elif action == 3:
            self._action_tactical_avoidance(world, pos, vel, team)
        elif action == 4:
            # Bouclier - pas de mouvement particulier
            pass
        elif action == 5:
            self._action_defensive_position(world, pos, vel, team)
        elif action == 6:
            self._action_retreat(world, pos, vel, team)
        elif action == 7:
            self._action_ambush(world, pos, vel, team)
    
    def _handle_tactical_combat(self, action, world, pos, team):
        """Gestion tactique du combat avec tir en salve"""
        if self.cooldown > 0:
            return  # En cooldown
            
        enemies = self._find_nearby_enemies(world, pos, team)
        if not enemies:
            return  # Pas d'ennemi
        
        # Trouver les ennemis à portée
        enemies_in_range = []
        try:
            for enemy_ent, distance, priority in enemies:
                if distance <= 8 * TILE_SIZE:  # Portée de tir
                    # NOUVEAU: Check la ligne de vue
                    if self._has_line_of_sight(world, pos, enemy_ent):
                        enemies_in_range.append((enemy_ent, distance, priority))
        except Exception as e:
            print(f"Erreur lors de la vérification de la ligne de vue: {e}")
        if not enemies_in_range:
            return
        
        # TIR EN SALVE - Attaquer jusqu'à 3 ennemis simultanément
        targets_to_attack = min(3, len(enemies_in_range))
        
        for i in range(targets_to_attack):
            enemy_ent = enemies_in_range[i][0]
            try:
                # Calcul de l'angle to la cible
                enemy_pos = world.component_for_entity(enemy_ent, PositionComponent)
                angle_to_target = self._angle_to(enemy_pos.x - pos.x, enemy_pos.y - pos.y)
                
                # Tir avec dispersion pour couvrir les flancs
                if i == 0:  # Tir principal
                    self._fire_at_angle(world, pos, angle_to_target)
                elif i == 1:  # Tir côté droit
                    self._fire_at_angle(world, pos, angle_to_target + 25)
                elif i == 2:  # Tir côté gauche  
                    self._fire_at_angle(world, pos, angle_to_target - 25)                    
            except Exception as e:
                print(f"Barhamus {self.entity}: Tir en salve #{i+1} to angle {angle_to_target:.0f}°")
                
            except Exception as e:
                print(f"Erreur tir salve: {e}")
        
        # Déclencher le cooldown after la salve
        if targets_to_attack > 0:
            self.cooldown = 3.0  # 3 secondes de cooldown
            self.successful_attacks += targets_to_attack

    def _has_line_of_sight(self, world, start_pos, target_entity):
        """Check sila ligne de vue entre deux points est dégagée."""
        if not self.grid:
            return True # Pas de grille, on suppose que c'est dégagé

        try:
            target_pos = world.component_for_entity(target_entity, PositionComponent)
        except KeyError:
            return False # La cible n'existe plus

        # Échantillonner des points le long de la ligne de vue
        num_steps = 10
        for i in range(1, num_steps + 1):
            t = i / num_steps
            check_x = start_pos.x + t * (target_pos.x - start_pos.x)
            check_y = start_pos.y + t * (target_pos.y - start_pos.y)

            grid_x = int(check_x // TILE_SIZE)
            grid_y = int(check_y // TILE_SIZE)

            if not (0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid)):
                continue # Hors de la carte, on ignore

            tile_type = self.grid[grid_y][grid_x]
            if tile_type == TileType.GENERIC_ISLAND:
                return False # Obstacle trouvé
        
        return True # Ligne de vue dégagée

    def _apply_obstacle_avoidance(self, world, pos, vel) -> Optional[float]:
        """Ajuste la direction pour éviter les obstacles proches."""
        if vel.currentSpeed == 0 or not self.grid:
            return None

        # Marche arrière temporaire si on vient de se débloquer
        if not hasattr(self, '_reverse_timer'):
            self._reverse_timer = 0.0
        if self._reverse_timer > 0.0:
            self._reverse_timer = max(0.0, self._reverse_timer - 0.016)
            # Reculer doucement
            vel.currentSpeed = max(vel.maxUpSpeed * 0.6, 2.5)
            return (pos.direction + 180) % 360

        # Distance de sécurité autour de la base ennemie (éviter de s'approcher trop)
        try:
            if world and hasattr(self, 'entity') and world.has_component(self.entity, TeamComponent):
                team = world.component_for_entity(self.entity, TeamComponent)
                enemy_base = self._find_enemy_base(world, team)
                if enemy_base:
                    dx = pos.x - enemy_base[0]
                    dy = pos.y - enemy_base[1]
                    base_dist = math.hypot(dx, dy)
                    min_radius = 7 * TILE_SIZE  # ne pas entrer à l'intérieur
                    if base_dist < min_radius:
                        # Forcer un éloignement immédiat de la base (prévenir les dégâts)
                        # IMPORTANT: le MovementProcessor soustrait le vecteur, donc pour reculer on prend (base - pos)
                        away = self._angle_to(enemy_base[0] - pos.x, enemy_base[1] - pos.y)
                        vel.currentSpeed = max(vel.maxUpSpeed * 0.6, 3.0)
                        return away
        except Exception:
            pass

        # --- 1. Détection de blocage (Stuck Detection) - AMÉLIORÉ ---
        if not hasattr(self, '_stuck_check_timer'):
            self._stuck_check_timer = 0.0
            self._last_stuck_check_pos = (pos.x, pos.y)
            self._stuck_counter = 0  # Compteur de blocages consécutifs
            self._preferred_avoidance_direction = None  # Mémoriser la direction de contournement

        self._stuck_check_timer += 0.016  # dt approximatif
        if self._stuck_check_timer > 3.0:  # Check toutes les 3 secondes (augmenté)
            dist_moved = math.hypot(pos.x - self._last_stuck_check_pos[0], pos.y - self._last_stuck_check_pos[1])
            if vel.currentSpeed > 1.0 and dist_moved < TILE_SIZE * 0.5:  # Vraiment coincé
                self._stuck_counter += 1
                if self._stuck_counter >= 2:  # Coincé 2 fois de suite (6 secondes)
                    # Nouvelle stratégie: MARCHE ARRIÈRE courte pour se désengorger
                    self._reverse_timer = 0.8
                    vel.currentSpeed = max(vel.maxUpSpeed * 0.6, 2.5)
                    return (pos.direction + 180) % 360
            else:
                self._stuck_counter = 0  # Réinitialiser si on bouge
                self._preferred_avoidance_direction = None  # Réinitialiser la direction préférée
            
            self._last_stuck_check_pos = (pos.x, pos.y)
            self._stuck_check_timer = 0.0

        # --- 2. Évitement d'obstacles par capteurs - AMÉLIORÉ ---
        probe_length = 5.0 * TILE_SIZE  # Plus long pour anticiper les obstacles (unités lourdes)
        # Angles des capteurs avec meilleure couverture (plus large)
        angles = [-60, -30, -10, 0, 10, 30, 60]
        direction_rad = math.radians(pos.direction)

        steering_force = 0.0
        obstacle_detected = False

        for i, angle_offset in enumerate(angles):
            probe_angle_rad = direction_rad - math.radians(angle_offset)
            
            # Échantillonner le long du capteur
            for step in range(1, 4):
                dist = probe_length * (step / 3.0)
                probe_x = pos.x - dist * math.cos(probe_angle_rad)
                probe_y = pos.y - dist * math.sin(probe_angle_rad)

                grid_x = int(probe_x // TILE_SIZE)
                grid_y = int(probe_y // TILE_SIZE)

                if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
                    if self.grid[grid_y][grid_x] == TileType.GENERIC_ISLAND:
                        obstacle_detected = True
                        # Force de répulsion progressive et limitée
                        distance_factor = (1.0 - (dist / probe_length))
                        repulsion_strength = distance_factor * 60.0  # Réduit de 120 à 60 pour moins d'oscillations

                        if angle_offset == 0:  # Capteur central
                            vel.currentSpeed *= 0.8  # Ralentir progressivement
                            # Utiliser la direction préférée si définie, sinon choisir
                            if self._preferred_avoidance_direction is None:
                                self._preferred_avoidance_direction = self._choose_best_avoidance_direction(pos)
                            steering_force += self._preferred_avoidance_direction
                        else:  # Capteurs latéraux
                            # Force opposée à l'angle du capteur
                            steering_force += -math.copysign(repulsion_strength, angle_offset)
                        
                        break  # Obstacle trouvé sur ce capteur

        # Si obstacle détecté, réinitialiser le compteur de stuck (car on évite activement)
        if obstacle_detected and hasattr(self, '_stuck_counter'):
            self._stuck_counter = max(0, self._stuck_counter - 1)

        if abs(steering_force) > 0.1:
            # Limiter l'amplitude du virage pour éviter les oscillations
            steering_force = max(-90, min(90, steering_force))  # Limiter à ±90°
            new_direction = (pos.direction + steering_force) % 360
            return new_direction
        else:
            # Pas d'obstacle : réinitialiser la direction préférée
            if hasattr(self, '_preferred_avoidance_direction'):
                self._preferred_avoidance_direction = None
        
        return None  # Pas d'obstacle, pas de changement

    def _choose_best_avoidance_direction(self, pos):
        """Choisit la meilleure direction pour contourner (gauche ou droite)."""
        if not self.grid:
            return 60  # Par défaut : droite
        
        # Échantillonner les deux côtés pour trouver le plus dégagé
        left_clear = 0
        right_clear = 0
        check_angles = [30, 60, 90]
        
        for angle in check_angles:
            # Côté gauche
            left_rad = math.radians(pos.direction + angle)
            left_x = pos.x - 3 * TILE_SIZE * math.cos(left_rad)
            left_y = pos.y - 3 * TILE_SIZE * math.sin(left_rad)
            if self._is_position_clear(left_x, left_y):
                left_clear += 1
            
            # Côté droit
            right_rad = math.radians(pos.direction - angle)
            right_x = pos.x - 3 * TILE_SIZE * math.cos(right_rad)
            right_y = pos.y - 3 * TILE_SIZE * math.sin(right_rad)
            if self._is_position_clear(right_x, right_y):
                right_clear += 1
        
        # Retourner la direction avec le plus d'espace
        return 60 if left_clear > right_clear else -60

    def _is_position_clear(self, x, y):
        """Vérifie si une position est dégagée (pas d'île)."""
        if not self.grid:
            return True
        
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        if 0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid):
            return self.grid[grid_y][grid_x] != TileType.GENERIC_ISLAND
        return False  # Hors limites = pas clair

    
    def _action_retreat(self, world, pos, vel, team):
        """Action: Retraite tactique. Cherche un Druide allié ou fuit l'ennemi."""
        # 1. Chercher un Druide allié à proximité
        for ent, (druid_spec, ally_team, ally_pos) in world.get_components(SpeDruid, TeamComponent, PositionComponent):
            if ally_team.team_id == team.team_id:
                # Druide trouvé, se diriger vers lui en évitant les îles
                # Si la ligne de vue est claire (nav-grid), on y va direct, sinon on suit un chemin
                self._create_navigation_grid()
                if self._grid_line_clear((pos.x, pos.y), (ally_pos.x, ally_pos.y)):
                    angle = self._angle_to(pos.x - ally_pos.x, pos.y - ally_pos.y)
                    pos.direction = self._smooth_turn(pos.direction, angle, max_delta=15.0)
                    vel.currentSpeed = 4.0
                else:
                    if not self.path or self.path_recalc_timer <= 0:
                        self.path = self._find_path(pos, ally_pos)
                        self.path_recalc_timer = 2.0
                    if self.path:
                        waypoint = self.path[0]
                        if math.hypot(pos.x - waypoint[0], pos.y - waypoint[1]) < TILE_SIZE * 1.5:
                            self.path.pop(0)
                            if self.path:
                                waypoint = self.path[0]
                        angle = self._angle_to(pos.x - waypoint[0], pos.y - waypoint[1])
                        pos.direction = self._smooth_turn(pos.direction, angle, max_delta=15.0)
                        vel.currentSpeed = 3.2
                    else:
                        angle = self._angle_to(pos.x - ally_pos.x, pos.y - ally_pos.y)
                        pos.direction = self._smooth_turn(pos.direction, angle, max_delta=15.0)
                        vel.currentSpeed = 3.5
                print(f"Barhamus {self.entity}: Retraite vers Druide allié {ent}")
                return

        # 2. Si pas de Druide, fuir l'ennemi le plus proche (comportement original)
        self._flee_from_closest_enemy(world, pos, vel, team)

    def _fire_at_angle(self, world, pos, angle):
        """Tire un projectile in la direction spécifiée"""
        try:
            # Utiliser le système d'événements of the game to tirer
            world.dispatch_event("attack_event", self.entity)
        except Exception as e:
            print(f"Erreur tir: {e}")
    
    def _action_attack_movement(self, world, pos, vel, team):
        """Mouvement d'attaque - se positionner pour tirer"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            
            # Garder une distance optimale pour le tir (6-8 tiles)
            distance = enemies[0][1]
            if distance < 6 * TILE_SIZE:  # Trop proche, reculer
                # IMPORTANT : inverser direction car movementProcessor soustrait
                angle = self._angle_to(target_pos.x - pos.x, target_pos.y - pos.y)
                vel.currentSpeed = 2.0
                print(f"Barhamus {self.entity}: Recul (trop proche: {distance/TILE_SIZE:.1f} tiles)")
            elif distance > 8 * TILE_SIZE:  # Trop loin, s'approcher
                # Si la ligne de vue est bloquée, suivre un chemin plutôt que de foncer dans une île
                if not self._has_line_of_sight(world, pos, enemies[0][0]):
                    if not self.path or self.path_recalc_timer <= 0:
                        self.path = self._find_path(pos, target_pos)
                        self.path_recalc_timer = 2.0
                    if self.path:
                        waypoint = self.path[0]
                        if math.hypot(pos.x - waypoint[0], pos.y - waypoint[1]) < TILE_SIZE * 1.5:
                            self.path.pop(0)
                            if self.path:
                                waypoint = self.path[0]
                        angle = self._angle_to(pos.x - waypoint[0], pos.y - waypoint[1])
                        vel.currentSpeed = 3.2
                        print(f"Barhamus {self.entity}: Approche via chemin (reste {len(self.path)} waypoints)")
                    else:
                        # Pas de chemin: fallback direct (l'évitement gérera)
                        angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                        vel.currentSpeed = 3.5
                        print(f"Barhamus {self.entity}: Approche directe (pas de chemin)")
                else:
                    # IMPORTANT : inverser direction
                    angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                    vel.currentSpeed = 3.5
                    print(f"Barhamus {self.entity}: Approche (trop loin: {distance/TILE_SIZE:.1f} tiles)")
            else:  # Distance parfaite, maintenir position stable
                # FIX TOUPIE: Ne pas ajouter constamment +90°, juste maintenir orientation vers cible
                angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                # Mouvement latéral léger pour éviter les tirs ennemis
                if not hasattr(self, '_strafe_direction'):
                    self._strafe_direction = random.choice([-1, 1])  # -1 = gauche, 1 = droite
                    self._strafe_timer = 0.0
                
                self._strafe_timer += 0.016  # dt approximatif
                if self._strafe_timer > 3.0:  # Changer direction toutes les 3 secondes
                    self._strafe_direction *= -1
                    self._strafe_timer = 0.0
                
                # Légère déviation pour esquiver (±15° au lieu de ±90°)
                angle = (angle + self._strafe_direction * 15) % 360
                vel.currentSpeed = 2.0  # Vitesse réduite pour position stable
                
            # Lisser la rotation pour éviter les oscillations
            pos.direction = self._smooth_turn(pos.direction, angle, max_delta=12.0)
            print(f"Barhamus {self.entity}: Position d'attaque - distance {distance/TILE_SIZE:.1f} tiles")
    
    def _default_defense_behavior(self, world, pos, vel, team):
        """Comportement de défense By default in case of error"""
        try:
            base_pos = self._find_team_base(world, team)
            if base_pos:
                # Return to la base - IMPORTANT : inverser direction
                angle = self._angle_to(pos.x - base_pos[0], pos.y - base_pos[1])
                pos.direction = angle
                vel.currentSpeed = 3.0
                print(f"Barhamus {self.entity}: Retour défensif vers la base")
        except:
            # En dernier recours, patrouiller
            vel.currentSpeed = 2.0
            pos.direction = (pos.direction + 45) % 360
    
    def _find_team_base(self, world, team):
        """Trouve la position de la base de l'équipe"""
        try:
            # Chercher les bâtiments de l'équipe (bases, tours)
            for ent, (t_team, t_pos) in world.get_components(TeamComponent, PositionComponent):
                if t_team.team_id == team.team_id:
                    # Check sic'est un bâtiment (a un BuildingComponent ou similaire)
                    if (world.has_component(ent, AttackComponent) and 
                        world.has_component(ent, HealthComponent)):
                        attack_comp = world.component_for_entity(ent, AttackComponent)
                        health_comp = world.component_for_entity(ent, HealthComponent)
                        # Base/Tour = beaucoup de vie et immobile
                        if health_comp.maxHealth > 200:  # Seuil pour identifier une base
                            return (t_pos.x, t_pos.y)
            
            # Si pas de base trouvée, utiliser le centre de la carte
            if self.grid:
                center_x = len(self.grid[0]) * TILE_SIZE // 2
                center_y = len(self.grid) * TILE_SIZE // 2
                return (center_x, center_y)
        except Exception:
            pass
        
        return (500, 500)  # Position By default
    
    def _check_enemies_near_base(self, world, team, base_pos):
        """Check s'il y a des ennemis près de la base"""
        if not base_pos:
            return False
            
        threat_radius = 12 * TILE_SIZE  # 12 tiles de la base = zone de menace
        
        try:
            for ent, (t_team, t_pos) in world.get_components(TeamComponent, PositionComponent):
                if t_team.team_id != team.team_id:  # Ennemi
                    distance = math.sqrt((t_pos.x - base_pos[0])**2 + (t_pos.y - base_pos[1])**2)
                    if distance <= threat_radius:
                        print(f"Barhamus {self.entity}: Ennemi {ent} détecté à {distance/TILE_SIZE:.1f} tiles de la base!")
                        return True
        except Exception as e:
            print(f"Erreur détection ennemis base: {e}")
        
        return False
    
    def _decide_defensive_action(self, world, pos, team, base_pos):
        """Décide de l'action défensive à prendre"""
        if not base_pos:
            return 2  # Patrouille By default
            
        # Distance à la base
        base_distance = math.sqrt((pos.x - base_pos[0])**2 + (pos.y - base_pos[1])**2)
        
        # Si loin de la base, y Return
        if base_distance > 8 * TILE_SIZE:
            return 0  # Approche (to la base)
        else:
            # Près de la base, défendre activement
            enemies = self._find_nearby_enemies(world, pos, team)
            if enemies and enemies[0][1] <= 8 * TILE_SIZE:  # Ennemi à portée
                return 1  # Attaque
            else:
                return 0  # Approche pour se rapprocher de l'ennemi
    
    def _decide_offensive_action(self, world, pos, team):
        """Décide de l'action offensive à prendre"""
        enemies = self._find_nearby_enemies(world, pos, team)
        
        # Si pas d'ennemis proches, aller attaquer la base ennemie
        if not enemies:
            enemy_base = self._find_enemy_base(world, team)
            if enemy_base:
                base_distance = math.sqrt((pos.x - enemy_base[0])**2 + (pos.y - enemy_base[1])**2)
                if base_distance > 6 * TILE_SIZE:  # Loin de la base ennemie
                    print(f"Barhamus {self.entity}: Attaque de la base ennemie à {base_distance/TILE_SIZE:.1f} tiles")
                    return 0  # Approche to la base ennemie
                else:
                    return 1  # Attaque la base ennemie
            else:
                return 2  # Patrouille pour chercher des ennemis
        
        closest_enemy = enemies[0]
        distance = closest_enemy[1]
        
        # Logique offensive basée sur la distance
        if distance <= 4 * TILE_SIZE:  # Très proche
            return 1  # Attaque directe
        elif distance <= 8 * TILE_SIZE:  # Portée moyenne
            return 0  # Approche agressive
        else:
            return 7  # Embuscade pour se rapprocher
    
    def _find_enemy_base(self, world, team):
        """Trouve la position de la base ennemie"""
        try:
            enemy_team_id = 2 if team.team_id == 1 else 1
            
            # Chercher les bâtiments ennemis (bases, tours)
            for ent, (t_team, t_pos) in world.get_components(TeamComponent, PositionComponent):
                if t_team.team_id == enemy_team_id:
                    # Check sic'est un bâtiment (a beaucoup de vie)
                    if (world.has_component(ent, AttackComponent) and 
                        world.has_component(ent, HealthComponent)):
                        health_comp = world.component_for_entity(ent, HealthComponent)
                        # Base/Tour = beaucoup de vie et immobile
                        if health_comp.maxHealth > 200:  # Seuil pour identifier une base
                            return (t_pos.x, t_pos.y)
            
            # Si pas de base trouvée, utiliser les positions By default
            if enemy_team_id == 1:  # Base alliée
                return (200, 200)  # Coin haut-gauche
            else:  # Base ennemie
                if self.grid:
                    return (len(self.grid[0]) * TILE_SIZE - 200, len(self.grid) * TILE_SIZE - 200)  # Coin bas-droite
                else:
                    return (1800, 1800)  # Position By default
        except Exception as e:
            print(f"Erreur recherche base ennemie: {e}")
        
        return None
    
    def _find_nearby_enemies(self, world, pos, team):
        """Trouve all ennemis in un rayon donné"""
        enemies = []
        
        # Si world est None (test), Return des données simulées
        if world is None:
            return []
            
        search_radius = 15 * TILE_SIZE  # 15 tiles de rayon
        
        try:
            from src.components.core.projectileComponent import ProjectileComponent
            from src.components.events.flyChestComponent import FlyingChestComponent

            for ent, t_team in world.get_component(TeamComponent):
                # Ignorer les projectiles et les coffres volants
                if world.has_component(ent, ProjectileComponent) or world.has_component(ent, FlyingChestComponent):
                    continue

                if t_team.team_id != team.team_id and t_team.team_id != 0 and world.has_component(ent, PositionComponent):
                    t_pos = world.component_for_entity(ent, PositionComponent)
                    dist = ((pos.x - t_pos.x)**2 + (pos.y - t_pos.y)**2)**0.5
                    if dist <= search_radius:
                        priority = self._calculate_target_priority(world, ent)
                        enemies.append((ent, dist, priority))
        except Exception as e:
            print(f"Erreur recherche ennemis: {e}")
            return []
        
        # Trier par priorité puis par distance
        enemies.sort(key=lambda x: (x[2], x[1]), reverse=True)
        return enemies

    def _calculate_reward(self, current_state, health):
        """Calcule la récompense pour l'action précédente"""
        reward = 0
        
        # Récompense de survie — limitée à une fois every 2 seconds
        try:
            if (self.survival_time - getattr(self, 'last_survival_reward_time', -9999.0)) >= 15.0:
                reward += 1
                self.last_survival_reward_time = self.survival_time
        except Exception:
            # En cas de problème, donner quand même la récompense (sécurité)
            reward += 1
        
        # Pénalité pour dégâts subis
        if hasattr(self, 'last_health'):
            damage = self.last_health - health.currentHealth
            if damage > 0:
                reward -= damage * 2
                self.damage_taken += damage
        
        # Récompense pour la santé
        health_ratio = health.currentHealth / health.maxHealth
        if health_ratio > 0.8:
            reward += 5
        elif health_ratio < 0.3:
            reward -= 10
        
        # Récompense pour position tactique
        tactical_advantage = current_state[9]
        reward += tactical_advantage * 3
        
        # GRANDE récompense pour attaquer (encourager le combat)
        enemy_count = current_state[3] * 5  # Nombre d'ennemis
        if enemy_count > 0:
            reward += 3  # Bonus pour être près d'ennemis
        
        # Récompense pour évitement d'obstacles
        if current_state[6] < 0.3:  # Peu d'îles autour
            reward += 2
        if current_state[7] < 0.2:  # Peu de mines autour
            reward += 3
        
        # NOUVELLE: Pénalité pour position près des bords (encourage à rester au centre)
        border_penalty = self._calculate_border_penalty(current_state)
        if border_penalty > 0:
            reward -= border_penalty
            # Retiré le log pour réduire le spam
        
        # NOUVELLE: Récompense pour attaquer la base ennemie
        enemy_base_bonus = self._calculate_enemy_base_bonus(current_state)
        if enemy_base_bonus > 0:
            reward += enemy_base_bonus
        
        # PÉNALITÉ DE MORT : appliquer une forte pénalité unique si l'unit meurt
        try:
            if health.currentHealth <= 0 and not getattr(self, 'death_penalized', False):
                reward -= self.death_penalty
                self.death_penalized = True
                print(f"Barhamus {self.entity}: MORT - Pénalité appliquée: -{self.death_penalty}")
        except Exception:
            pass
        
        self.last_health = health.currentHealth
        return reward
    
    def _calculate_border_penalty(self, current_state):
        """Calcule la pénalité pour être près des bords de la carte"""
        if not self.grid or len(current_state) < 2:
            return 0
        
        # Position normalisée (0-1)
        norm_x = current_state[0]  # Position X normalisée
        norm_y = current_state[1]  # Position Y normalisée
        
        # Distance aux bords (0 = sur le bord, 0.5 = au centre)
        dist_to_edge_x = min(norm_x, 1.0 - norm_x)
        dist_to_edge_y = min(norm_y, 1.0 - norm_y)

        # Pénalité si trop près des bords (moins de 5% de la carte)
        edge_threshold = 0.5
        penalty = 0
        
        if dist_to_edge_x < edge_threshold:
            penalty += (edge_threshold - dist_to_edge_x) * 10  # Pénalité max = 5.0
        
        if dist_to_edge_y < edge_threshold:
            penalty += (edge_threshold - dist_to_edge_y) * 10  # Pénalité max = 5.0

        return penalty
    
    def _calculate_enemy_base_bonus(self, current_state):
        """Calcule le bonus pour s'approcher de la base ennemie"""
        # Ce bonus est déjà intégré in l'avantage tactique
        # On peut Add un bonus supplémentaire si nécessaire
        if len(current_state) >= 10:
            tactical_advantage = current_state[9]  # Avantage tactique
            if tactical_advantage > 0.7:  # Bonne position tactique
                return 1.0  # Bonus pour bonne position offensive
        return 0
    
    def _record_experience(self, state, action, reward, next_state):
        """Enregistre une expérience pour l'apprentissage"""
        experience = {
            'state': state.copy(),
            'action': action,
            'reward': reward,
            'next_state': next_state.copy()
        }
        self.experiences.append(experience)
        # Log d'appoint pour Check queles expériences s'accumulent
        if self.debug_mode:
            if len(self.experiences) % 10 == 0 or len(self.experiences) < 20:
                print(f"Barhamus {self.entity}: Expérience enregistrée (total={len(self.experiences)})")
        
        # Garder seulement les 1000 dernières expériences
        if len(self.experiences) > 1000:
            self.experiences = self.experiences[-1000:]
    
    def _retrain_model(self):
        """Réentraîne le modèle avec les nouvelles expériences"""
        if len(self.experiences) < 10:
            if self.debug_mode:
                print(f"Barhamus {self.entity}: Pas assez d'expériences pour réentraîner ({len(self.experiences)})")
            return
        
        try:
            if self.debug_mode:
                print(f"Barhamus {self.entity}: Démarrage réentraînement avec {len(self.experiences)} expériences")
            # Préparer les données d'entraînement
            X = []
            y = []
            
            for exp in self.experiences[-100:]:  # Utiliser les 100 dernières expériences
                X.append(exp['state'])
                # Ajuster l'action basée sur la récompense
                adjusted_action = exp['action']
                if exp['reward'] < -5:  # Mauvaise action
                    adjusted_action = random.randint(0, 7)  # Action aléatoire
                y.append(adjusted_action)
            
            X = np.array(X)
            y = np.array(y)
            
            # Normaliser les données
            self.scaler.fit(X)
            X_scaled = self.scaler.transform(X)
            
            # Entraîner l'arbre de décision
            self.decision_tree.fit(X_scaled, y)
            self.is_trained = True
            # Pour compatibilité/diagnostic, exposer aussi training_data/labels
            self.training_data = X.tolist() if isinstance(X, np.ndarray) else list(X)
            self.training_labels = y.tolist() if isinstance(y, np.ndarray) else list(y)

            if self.debug_mode:
                print(f"Modèle IA réentraîné avec {len(X)} expériences (Barhamus {self.entity})")
            
        except Exception as e:
            print(f"Erreur lors du réentraînement: {e}")
    
    def _adapt_strategy(self):
        """Adapte la stratégie basée sur les performances"""
        if self.survival_time < 30:  # Pas assez de données
            return
        
        # Calculer le score de performance actuel
        current_score = self._calculate_performance_score()
        
        # Mettre à jour les statistiques de stratégie
        if current_score > 0:
            self.strategy_performance[self.current_strategy]["success"] += 1
        else:
            self.strategy_performance[self.current_strategy]["failure"] += 1
        
        # Changer de stratégie si les performances sont mauvaises
        success_rate = self._get_strategy_success_rate(self.current_strategy)
        if success_rate < 0.3 and random.random() < 0.2:  # 20% chance de changer
            self._switch_strategy()
    
    def _calculate_performance_score(self):
        """Calcule un score de performance global"""
        score = 0
        score += self.survival_time / 10  # Points pour survie
        score += self.successful_attacks * 5  # Points pour attaques réussies
        score -= self.damage_taken / 20  # Pénalité pour dégâts subis
        score -= self.failed_attacks * 2  # Pénalité pour attaques ratées
        return score
    
    def _get_strategy_success_rate(self, strategy):
        """Calcule le taux de succès d'une stratégie"""
        stats = self.strategy_performance[strategy]
        total = stats["success"] + stats["failure"]
        if total == 0:
            return 0.5  # Neutre si pas de données
        return stats["success"] / total
    
    def _switch_strategy(self):
        """Change to la stratégie la plus performante"""
        best_strategy = max(self.strategy_performance.keys(), 
                           key=lambda s: self._get_strategy_success_rate(s))
        if best_strategy != self.current_strategy:
            if self.debug_mode:
                print(f"IA Barhamus change de stratégie: {self.current_strategy} -> {best_strategy}")
            self.current_strategy = best_strategy
    
    # Actions spécifiques
    def _action_aggressive_approach(self, world, pos, vel, team):
        """Action: Approche agressive vers l'ennemi ou base ennemie (si force suffisante)"""
        enemies = self._find_nearby_enemies(world, pos, team)

        if enemies:
            # Attaquer l'ennemi le plus proche
            target_entity = enemies[0][0]
            target_pos = world.component_for_entity(target_entity, PositionComponent)

            # Check si la ligne de vue est dégagée
            if self._has_line_of_sight(world, pos, target_entity):
                # Ligne de vue dégagée : foncer
                angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                pos.direction = angle
                vel.currentSpeed = 4.0 # Vitesse légèrement réduite pour plus de contrôle
                if self.debug_mode:
                    print(f"Barhamus {self.entity}: Approche agressive vers ennemi {target_entity} (directe)")
            else:
                # Ligne de vue bloquée : utiliser le pathfinding pour contourner
                vel.currentSpeed = 3.5  # Vitesse de contournement
                
                # AMÉLIORATION: Pathfinding avec recalcul intelligent
                if not self.path or self.path_recalc_timer <= 0:
                    self.path = self._find_path(pos, target_pos)
                    self.path_recalc_timer = 2.5  # Recalculer toutes les 2.5s (augmenté pour stabilité)

                if self.path and len(self.path) > 0:
                    # Suivre le chemin - prendre le premier waypoint non atteint
                    next_waypoint = self.path[0]
                    waypoint_dist = math.hypot(pos.x - next_waypoint[0], pos.y - next_waypoint[1])
                    
                    # Avancer au waypoint suivant si assez proche
                    if waypoint_dist < TILE_SIZE * 2.0:  # Augmenté de 1.5 à 2.0 pour éviter oscillations
                        self.path.pop(0)
                        if self.path:  # S'il reste des waypoints
                            next_waypoint = self.path[0]
                    
                    # Se diriger vers le waypoint (l'évitement d'obstacles ajustera si nécessaire)
                    if self.path:
                        angle = self._angle_to(pos.x - next_waypoint[0], pos.y - next_waypoint[1])
                        pos.direction = angle
                        if self.debug_mode:
                            print(f"Barhamus {self.entity}: Suit chemin vers waypoint (angle={angle:.1f}°, reste {len(self.path)} waypoints)")
                    else:
                        # Chemin terminé mais pas encore à la cible : aller direct
                        angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                        pos.direction = angle
                else:
                    # Pas de chemin trouvé : essayer d'aller direct (l'évitement gérera)                    
                    angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                    pos.direction = angle
                    print(f"Barhamus {self.entity}: Pas de chemin, tentative directe")
        else:
            # Pas d'ennemi visible : comportement tactique selon la force disponible
            allies_nearby = self._count_nearby_allies(world, pos, team)
            
            # Assault coordonné seulement si force suffisante (3+ alliés Maraudeurs)
            if allies_nearby >= 3:
                # Assez d'unités pour un assault : attaquer la base de façon prudente (distance de sécurité)
                enemy_base_pos = self._find_enemy_base(world, team)
                if enemy_base_pos:
                    safe_radius = 9 * TILE_SIZE  # distance de sécurité minimale autour de la base
                    min_radius = 7 * TILE_SIZE  # ne jamais entrer dans ce rayon

                    # Si trop près de la base: reculer d'abord
                    base_dist = math.hypot(pos.x - enemy_base_pos[0], pos.y - enemy_base_pos[1])
                    if base_dist < min_radius:
                        # S'éloigner de la base
                        # IMPORTANT: le MovementProcessor soustrait, donc pour reculer => (base - pos)
                        away_angle = self._angle_to(enemy_base_pos[0] - pos.x, enemy_base_pos[1] - pos.y)
                        pos.direction = self._smooth_turn(pos.direction, away_angle, max_delta=18.0)
                        vel.currentSpeed = 3.5 # Augmenté pour un recul plus rapide
                        if self.debug_mode:
                            print(f"Barhamus {self.entity}: Trop proche de la base ({base_dist/TILE_SIZE:.1f}t) — recul de sécurité")
                        return

                    # Si on est à portée "safe" de la base et avec une ligne de vue claire, s'arrêter totalement
                    try:
                        self._create_navigation_grid()
                        if min_radius <= base_dist <= safe_radius and self._grid_line_clear((pos.x, pos.y), enemy_base_pos):
                            hold_angle = self._angle_to(pos.x - enemy_base_pos[0], pos.y - enemy_base_pos[1])
                            pos.direction = self._smooth_turn(pos.direction, hold_angle, max_delta=15.0)
                            vel.currentSpeed = 0.5 # Mouvement très lent pour ajustements fins
                            if self.debug_mode:
                                print(f"Barhamus {self.entity}: À portée de la base — maintien de position")
                            return
                    except Exception:
                        pass

                    # Choisir un point de positionnement autour de la base avec LoS
                    standoff = self._compute_standoff_point(enemy_base_pos, (pos.x, pos.y), safe_radius)
                    # Option coffre seulement s'il est sur la route vers le standoff
                    closest_chest = self._find_nearby_chest(world, pos)
                    if closest_chest:
                        chest_pos = world.component_for_entity(closest_chest, PositionComponent)
                        angle_to_standoff = self._angle_to(pos.x - standoff[0], pos.y - standoff[1])
                        angle_to_chest = self._angle_to(pos.x - chest_pos.x, pos.y - chest_pos.y)
                        angle_diff = abs(angle_to_standoff - angle_to_chest)
                        if angle_diff > 180:
                            angle_diff = 360 - angle_diff
                        chest_distance = math.hypot(pos.x - chest_pos.x, pos.y - chest_pos.y)
                        if chest_distance < 8 * TILE_SIZE and angle_diff < 30:
                            angle = self._angle_to(pos.x - chest_pos.x, pos.y - chest_pos.y)
                            pos.direction = self._smooth_turn(pos.direction, angle, max_delta=18.0)
                            vel.currentSpeed = 3.8 # Vitesse augmentée pour la collecte
                            if self.debug_mode:
                                print(f"Barhamus {self.entity}: Détour coffre sur la route du standoff")
                            return

                    # Aller vers le standoff en A* si LoS bloquée
                    self._create_navigation_grid()
                    if not self._grid_line_clear((pos.x, pos.y), standoff):
                        if not self.path or self.path_recalc_timer <= 0:
                            # Calculer un chemin jusqu'au standoff
                            dummy = type('obj', (), {'x': standoff[0], 'y': standoff[1]})
                            self.path = self._find_path(pos, dummy)
                            self.path_recalc_timer = 2.0
                        if self.path:
                            waypoint = self.path[0]
                            if math.hypot(pos.x - waypoint[0], pos.y - waypoint[1]) < TILE_SIZE * 1.5:
                                self.path.pop(0)
                                if self.path:
                                    waypoint = self.path[0]
                            move_angle = self._angle_to(pos.x - waypoint[0], pos.y - waypoint[1])
                            pos.direction = self._smooth_turn(pos.direction, move_angle, max_delta=18.0)
                            vel.currentSpeed = 3.6 # Vitesse de navigation standard
                            if self.debug_mode:
                                print(f"Barhamus {self.entity}: Vers standoff via chemin (reste {len(self.path)} wp)")
                        else:
                            # Fallback: avancer direct (évitement fera le reste)
                            move_angle = self._angle_to(pos.x - standoff[0], pos.y - standoff[1])
                            pos.direction = self._smooth_turn(pos.direction, move_angle, max_delta=18.0)
                            vel.currentSpeed = 3.8
                            if self.debug_mode:
                                print(f"Barhamus {self.entity}: Vers standoff (fallback direct)")
                    else:
                        # Ligne directe vers le standoff
                        # Si on atteint le standoff (proche) et qu'on a LoS vers la base, arrêter le mouvement
                        if math.hypot(pos.x - standoff[0], pos.y - standoff[1]) < TILE_SIZE * 1.5 and self._grid_line_clear((standoff[0], standoff[1]), enemy_base_pos):
                            hold_angle = self._angle_to(pos.x - enemy_base_pos[0], pos.y - enemy_base_pos[1])
                            pos.direction = self._smooth_turn(pos.direction, hold_angle, max_delta=15.0)
                            vel.currentSpeed = 0.0
                            if self.debug_mode:
                                print(f"Barhamus {self.entity}: Arrivé au standoff — maintien de position")
                            return
                        else:
                            move_angle = self._angle_to(pos.x - standoff[0], pos.y - standoff[1])
                            pos.direction = self._smooth_turn(pos.direction, move_angle, max_delta=18.0)
                            vel.currentSpeed = 3.8
                            if self.debug_mode:
                                print(f"Barhamus {self.entity}: Vers standoff (LoS OK)")
                else:
                    # Pas de base trouvée : patrouiller
                    self._action_patrol(pos, vel)
            else:
                # Pas assez d'alliés : chercher des coffres ou patrouiller (priorité coffres)
                closest_chest = self._find_nearby_chest(world, pos)
                if closest_chest:
                    chest_pos = world.component_for_entity(closest_chest, PositionComponent)
                    angle = self._angle_to(pos.x - chest_pos.x, pos.y - chest_pos.y)
                    pos.direction = angle
                    vel.currentSpeed = 3.8
                    if self.debug_mode:
                        print(f"Barhamus {self.entity}: Collecte de coffre (solo/petit groupe)")
                else:
                    # Pas de coffre : patrouiller en attendant des renforts
                    self._action_patrol(pos, vel)
                    if self.debug_mode:
                        print(f"Barhamus {self.entity}: Patrouille ({allies_nearby} alliés, attente renforts)")
            enemy_base = self._find_enemy_base(world, team)
            if enemy_base:
                # IMPORTANT : inverser la direction pour le movementProcessor
                angle = self._angle_to(pos.x - enemy_base[0], pos.y - enemy_base[1])
                pos.direction = angle
                vel.currentSpeed = 4.0
                if self.debug_mode:
                    print(f"Barhamus {self.entity}: Approche vers base ennemie - angle={angle:.1f}°")
            else:
                # Patrouiller
                vel.currentSpeed = 2.5
                pos.direction = (pos.direction + 30) % 360
                if self.debug_mode:
                    print(f"Barhamus {self.entity}: Patrouille défensive")
    
    def _action_attack(self, world, pos, vel, team):
        """Action: Attaque si ennemi à portée"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies and self.cooldown <= 0:
            closest = enemies[0]
            if closest[1] <= 8 * TILE_SIZE:  # À portée
                target_pos = world.component_for_entity(closest[0], PositionComponent)
                # IMPORTANT : inverser direction pour movementProcessor
                angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                pos.direction = angle
                vel.currentSpeed = 1.0  # Ralentir pour viser
                
                try:
                    world.dispatch_event("attack_event", self.entity)
                    self.cooldown = 1.5
                    self.successful_attacks += 1
                    if self.debug_mode:
                        print(f"Barhamus {self.entity} attaque (IA intelligente)!")
                except Exception:
                    self.failed_attacks += 1
    
    def _action_patrol(self, pos, vel):
        """Action: Patrouille aléatoire"""
        if not hasattr(self, 'patrol_direction') or random.random() < 0.1:
            self.patrol_direction = random.uniform(0, 360)
        pos.direction = self.patrol_direction
        vel.currentSpeed = 2.5
        if self.debug_mode:
            print(f"Barhamus {self.entity}: Patrouille - direction={pos.direction:.1f}°, vitesse={vel.currentSpeed}")
    
    def _action_tactical_avoidance(self, world, pos, vel, team):
        """Action: Évitement tactique intelligent"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            # Calculer direction d'évitement
            avoid_x, avoid_y = 0, 0
            for enemy, dist, _ in enemies:
                enemy_pos = world.component_for_entity(enemy, PositionComponent)
                weight = max(0, 5 * TILE_SIZE - dist) / (5 * TILE_SIZE)
                avoid_x += (pos.x - enemy_pos.x) * weight
                avoid_y += (pos.y - enemy_pos.y) * weight
            
            if avoid_x != 0 or avoid_y != 0:
                # IMPORTANT : inverser pour movementProcessor (déjà in la bonne direction ici)
                angle = self._angle_to(-avoid_x, -avoid_y)
                pos.direction = angle
                vel.currentSpeed = 3.5
    
    def _action_shield_management(self, spe, health):
        """Action: Gestion intelligente du bouclier"""
        health_ratio = health.currentHealth / health.maxHealth
        
        if health_ratio < 0.5 and not self.shield_active:
            self._activate_shield(spe)
        elif health_ratio > 0.8 and self.shield_active:
            self._deactivate_shield(spe)
    
    def _action_defensive_position(self, world, pos, vel, team):
        """Action: Position défensive"""
        # Chercher une position sûre
        safe_pos = self._find_safe_position(pos)
        if safe_pos:
            # IMPORTANT : inverser direction pour movementProcessor
            angle = self._angle_to(pos.x - safe_pos[0], pos.y - safe_pos[1])
            pos.direction = angle
            vel.currentSpeed = 2.0
    
    def _action_ambush(self, world, pos, vel, team):
        """Action: Embuscade - attendre in une position avantageuse"""
        vel.currentSpeed = 0.5  # Mouvement minimal
        # Rester orienté to la zone de danger
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            # IMPORTANT : inverser pour movementProcessor
            angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
            pos.direction = angle

    def _find_nearby_chest(self, world, pos):
        """Trouve le coffre volant le plus proche."""
        closest_chest = None
        min_dist = float('inf')
        
        try:
            for ent, (chest, chest_pos) in world.get_components(FlyingChestComponent, PositionComponent):
                # Ignorer les coffres déjà collectés ou en train de couler
                if chest.is_collected or chest.is_sinking:
                    continue
                
                dist = math.hypot(pos.x - chest_pos.x, pos.y - chest_pos.y)
                if dist < min_dist:
                    min_dist = dist
                    closest_chest = ent
        except Exception as e:
            print(f"Erreur recherche coffres: {e}")
        
        return closest_chest

    def _count_nearby_allies(self, world, pos, team):
        """Compte le nombre d'alliés Maraudeurs à proximité."""
        ally_count = 0
        search_radius = 15 * TILE_SIZE  # 15 tiles de rayon
        
        try:
            for ent, (ally_spe, ally_team, ally_pos) in world.get_components(SpeMaraudeur, TeamComponent, PositionComponent):
                # Ignorer soi-même
                if ent == self.entity:
                    continue
                
                # Vérifier que c'est un allié
                if ally_team.team_id != team.team_id:
                    continue
                
                # Vérifier la distance
                dist = math.hypot(pos.x - ally_pos.x, pos.y - ally_pos.y)
                if dist <= search_radius:
                    ally_count += 1
        except Exception as e:
            print(f"Erreur comptage alliés: {e}")
        
        return ally_count

    def _flee_from_closest_enemy(self, world, pos, vel, team):
        """Logique de fuite de base : s'éloigner de l'ennemi le plus proche."""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            closest = enemies[0]
            enemy_pos = world.component_for_entity(closest[0], PositionComponent)
            # IMPORTANT : inverser la direction pour le movementProcessor qui soustrait
            retreat_angle = self._angle_to(enemy_pos.x - pos.x, enemy_pos.y - pos.y)
            pos.direction = retreat_angle
            vel.currentSpeed = 4.5  # Vitesse de fuite augmentée
            if self.debug_mode:
                print(f"Barhamus {self.entity}: Fuite de l'ennemi {closest[0]}")

    def _calculate_border_penalty(self, current_state):
        """Calcule la pénalité pour être près des bords de la carte"""
        if not self.grid or len(current_state) < 2:
            return 0
        
        # Position normalisée (0-1)
        norm_x = current_state[0]  # Position X normalisée
        norm_y = current_state[1]  # Position Y normalisée
        
        # Distance aux bords (0 = sur le bord, 0.5 = au centre)
        dist_to_edge_x = min(norm_x, 1.0 - norm_x)
        dist_to_edge_y = min(norm_y, 1.0 - norm_y)
        
        # Pénalité si trop près des bords (moins de 15% de la carte)
        edge_threshold = 0.15
        penalty = 0
        
        if dist_to_edge_x < edge_threshold:
            penalty += (edge_threshold - dist_to_edge_x) * 10  # Pénalité max = 1.5
        
        if dist_to_edge_y < edge_threshold:
            penalty += (edge_threshold - dist_to_edge_y) * 10  # Pénalité max = 1.5
        
        return penalty
    
    def _calculate_enemy_base_bonus(self, current_state):
        """Calcule le bonus pour s'approcher de la base ennemie"""
        # Ce bonus est déjà intégré in l'avantage tactique
        # On peut Add un bonus supplémentaire si nécessaire
        if len(current_state) >= 10:
            tactical_advantage = current_state[9]  # Avantage tactique
            if tactical_advantage > 0.7:  # Bonne position tactique
                return 1.0  # Bonus pour bonne position offensive
        return 0
    
    def _create_navigation_grid(self):
        """creates une grille de navigation où les îles sont 'gonflées' pour l'évitement."""
        if not self.grid:
            return

        grid_h, grid_w = len(self.grid), len(self.grid[0])
        self.nav_grid = [row[:] for row in self.grid] # Copie de la grille
        
        # Le rayon de 'gonflement' en tuiles. 1 signifie qu'on bloque les 8 tuiles autour d'une île.
        # Pour une unit large comme le Maraudeur, 1 est un bon début.
        # Augmenté encore pour les Maraudeurs (grands et lourds) afin d'éviter les couloirs trop étroits
        inflation_radius = 3

        for r in range(grid_h):
            for c in range(grid_w):
                if self.grid[r][c] == TileType.GENERIC_ISLAND:
                    # Marquer les tuiles adjacentes comme des obstacles de navigation
                    for dr in range(-inflation_radius, inflation_radius + 1):
                        for dc in range(-inflation_radius, inflation_radius + 1):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < grid_h and 0 <= nc < grid_w:
                                # On ne modifie que les tuiles de mer pour ne pas bloquer d'autres îles
                                if self.nav_grid[nr][nc] == TileType.SEA:
                                    self.nav_grid[nr][nc] = TileType.GENERIC_ISLAND

    def _find_path(self, start_pos, end_pos):
        """Implémentation A* adaptée (clearance + anti-corner-cut + lissage)."""
        # Toujours (re)générer la grille de navigation gonflée pour garantir la clearance
        self._create_navigation_grid()
        # Utiliser la grille de navigation gonflée si elle existe, sinon la grille normale
        grid_to_use = self.nav_grid if hasattr(self, 'nav_grid') and self.nav_grid else self.grid
        if not grid_to_use:
            return []

        start_node = (int(start_pos.x // TILE_SIZE), int(start_pos.y // TILE_SIZE))
        end_node = (int(end_pos.x // TILE_SIZE), int(end_pos.y // TILE_SIZE))
        
        grid_w, grid_h = len(grid_to_use[0]), len(grid_to_use)

        def is_valid(n):
            return 0 <= n[0] < grid_w and 0 <= n[1] < grid_h and grid_to_use[n[1]][n[0]] != TileType.GENERIC_ISLAND

        if not is_valid(end_node): # Si la cible est in un mur, ne pas calculer
            return []

        frontier = [(0, start_node)]
        came_from = {start_node: None}
        cost_so_far = {start_node: 0}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == end_node:
                break

            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if is_valid(neighbor):
                    # Éviter le "corner cutting": en diagonale, vérifier que les adjacents sont libres
                    if dx != 0 and dy != 0:
                        if not (is_valid((current[0] + dx, current[1])) and is_valid((current[0], current[1] + dy))):
                            continue
                    new_cost = cost_so_far[current] + (1.414 if dx != 0 and dy != 0 else 1)
                    if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                        cost_so_far[neighbor] = new_cost
                        priority = new_cost + math.hypot(end_node[0] - neighbor[0], end_node[1] - neighbor[1])
                        heapq.heappush(frontier, (priority, neighbor))
                        came_from[neighbor] = current
        
        path = []
        node = end_node
        while node != start_node and node in came_from:
            path.append(((node[0] + 0.5) * TILE_SIZE, (node[1] + 0.5) * TILE_SIZE))
            node = came_from[node]
        path.reverse()
        # Lisser le chemin pour réduire les zigzags et mieux négocier les passages larges
        if path:
            path = self._smooth_path(path)
        return path

    def _smooth_path(self, path_points):
        """Lisse la liste de waypoints en supprimant les points inutiles (line-of-sight sur nav_grid)."""
        if not path_points or len(path_points) <= 2 or not hasattr(self, 'nav_grid'):
            return path_points

        smoothed = [path_points[0]]
        last_kept = path_points[0]
        for i in range(2, len(path_points)):
            candidate = path_points[i]
            # Si la ligne est claire entre last_kept et candidate, on peut sauter le point i-1
            if self._grid_line_clear(last_kept, candidate):
                continue
            else:
                # Garder le point précédent car on ne peut pas aller directement
                smoothed.append(path_points[i-1])
                last_kept = path_points[i-1]
        # Ajouter le dernier point
        smoothed.append(path_points[-1])
        return smoothed

    def _grid_line_clear(self, p1, p2):
        """Vérifie si le segment p1->p2 traverse une île dans nav_grid."""
        try:
            if not hasattr(self, 'nav_grid') or not self.nav_grid:
                return False
            x1, y1 = p1
            x2, y2 = p2
            dx = x2 - x1
            dy = y2 - y1
            dist = max(1.0, math.hypot(dx, dy))
            steps = int(dist // (TILE_SIZE * 0.5))  # échantillonnage tous les 0.5 tuile
            for s in range(1, steps + 1):
                t = s / float(steps)
                sx = x1 + dx * t
                sy = y1 + dy * t
                gx = int(sx // TILE_SIZE)
                gy = int(sy // TILE_SIZE)
                if 0 <= gy < len(self.nav_grid) and 0 <= gx < len(self.nav_grid[0]):
                    if self.nav_grid[gy][gx] == TileType.GENERIC_ISLAND:
                        return False
                else:
                    return False
            return True
        except Exception:
            return False

    def _compute_standoff_point(self, base_pos, current_xy, radius):
        """Choisit un point sur un cercle autour de la base avec ligne de vue depuis ce point vers la base.
        Préférence pour la direction approximative du Barhamus actuel.
        """
        bx, by = base_pos
        cx, cy = current_xy
        # Direction de base -> unité
        vx, vy = cx - bx, cy - by
        base_angle = math.degrees(math.atan2(vy, vx)) % 360
        # Liste d'angles candidats autour de la base (priorité proche base_angle)
        candidates_deg = [0, 20, -20, 40, -40, 60, -60, 90, -90, 120, -120, 150, -150, 180]
        candidates_deg = [((base_angle + d) % 360) for d in candidates_deg]

        best = None
        best_score = float('inf')
        self._create_navigation_grid()
        grid_to_use = self.nav_grid if hasattr(self, 'nav_grid') and self.nav_grid else self.grid

        for ang in candidates_deg:
            rad = math.radians(ang)
            tx = bx + math.cos(rad) * radius
            ty = by + math.sin(rad) * radius
            # 1) Le point doit être dans la carte et praticable
            gx = int(tx // TILE_SIZE)
            gy = int(ty // TILE_SIZE)
            if not grid_to_use:
                # Pas de grille: accepter le point
                return (tx, ty)
            if not (0 <= gy < len(grid_to_use) and 0 <= gx < len(grid_to_use[0])):
                continue
            if grid_to_use[gy][gx] == TileType.GENERIC_ISLAND:
                continue
            # 2) Doit avoir LoS du point vers la base
            if not self._grid_line_clear((tx, ty), (bx, by)):
                continue
            # 3) Si possible, ligne claire depuis la position courante jusqu'au point
            los_from_current = self._grid_line_clear((cx, cy), (tx, ty))
            dist = math.hypot(cx - tx, cy - ty)
            score = dist - (200 if los_from_current else 0)  # Favoriser les points accessibles direct
            if score < best_score:
                best_score = score
                best = (tx, ty)

        # Fallback : point le plus proche sur l'angle actuel même sans LoS
        if best is None:
            rad = math.radians(base_angle)
            best = (bx + math.cos(rad) * radius, by + math.sin(rad) * radius)
        return best
    
    # Méthodes utilitaires et d'analyse
    def _analyze_nearby_obstacles(self, pos):
        """Analyse les obstacles autour de la position"""
        obstacles = {'islands': 0, 'mines': 0, 'walls': 0}
        
        if not self.grid:
            return obstacles
        
        # Check in un rayon de 3 tiles
        check_radius = 3
        grid_x = int(pos.x // TILE_SIZE)
        grid_y = int(pos.y // TILE_SIZE)
        
        for dy in range(-check_radius, check_radius + 1):
            for dx in range(-check_radius, check_radius + 1):
                x, y = grid_x + dx, grid_y + dy
                if 0 <= x < len(self.grid[0]) and 0 <= y < len(self.grid):
                    tile_type = self.grid[y][x]
                    if tile_type == TileType.GENERIC_ISLAND:
                        obstacles['islands'] += 1
                    elif tile_type == TileType.MINE:
                        obstacles['mines'] += 1
                else:
                    obstacles['walls'] += 1
        
        return obstacles
    
    def _calculate_tactical_advantage(self, pos, enemies):
        """Calcule l'avantage tactique de la position actuelle"""
        if not enemies:
            return 0.5
        
        # Facteurs: distance aux ennemis, couverture, mobilité
        advantage = 0
        
        # Distance optimale (ni trop près ni trop loin)
        closest_dist = enemies[0][1] if enemies else float('inf')
        optimal_dist = 6 * TILE_SIZE
        dist_factor = 1.0 - abs(closest_dist - optimal_dist) / optimal_dist
        advantage += dist_factor * 0.4
        
        # Nombre d'ennemis (moins il y en a, mieux c'est)
        enemy_factor = max(0, 1.0 - len(enemies) / 5.0)
        advantage += enemy_factor * 0.3
        
        # Position par rapport aux obstacles
        obstacles = self._analyze_nearby_obstacles(pos)
        cover_factor = min(obstacles['islands'] / 3.0, 1.0)  # Un peu de couverture est bien
        advantage += cover_factor * 0.3
        
        return min(1.0, max(0.0, advantage))
    
    def _is_in_safe_zone(self, pos):
        """Check sila position est in une zone sûre"""
        if not self.grid:
            return 0.5
        
        # Check la distance aux bords
        margin = 2 * TILE_SIZE
        world_width = len(self.grid[0]) * TILE_SIZE
        world_height = len(self.grid) * TILE_SIZE
        
        if (pos.x < margin or pos.x > world_width - margin or
            pos.y < margin or pos.y > world_height - margin):
            return 0.0  # Près des bords = dangereux
        
        return 1.0
    
    def _calculate_target_priority(self, world, entity):
        """Calcule la priorité d'une cible"""
        priority = 0
        
        # Priorité basée sur la santé (cibles faibles = priorité haute)
        if world.has_component(entity, HealthComponent):
            health_comp = world.component_for_entity(entity, HealthComponent)
            if health_comp.maxHealth > 0:
                health_ratio = health_comp.currentHealth / health_comp.maxHealth
                priority += (1.0 - health_ratio) * 3
        
        # Priorité basée sur l'attaque (cibles dangereuses = priorité haute)
        if world.has_component(entity, AttackComponent):
            attack = world.component_for_entity(entity, AttackComponent)
            if attack.hitPoints >= 45:  # Léviathan
                priority += 5
            else:
                priority += attack.hitPoints / 20.0
        
        return priority
    
    def _find_safe_position(self, current_pos):
        """Trouve une position sûre proche"""
        if not self.grid:
            return None
        
        # Chercher in un rayon de 5 tiles
        for radius in range(1, 6):
            for angle in range(0, 360, 45):
                x = current_pos.x + radius * TILE_SIZE * math.cos(math.radians(angle))
                y = current_pos.y + radius * TILE_SIZE * math.sin(math.radians(angle))
                
                if self._is_position_safe(x, y):
                    return (x, y)
        
        return None
    
    def _is_position_safe(self, x, y):
        """Check siune position est sûre"""
        if not self.grid:
            return True
        
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        if (grid_x < 0 or grid_x >= len(self.grid[0]) or 
            grid_y < 0 or grid_y >= len(self.grid)):
            return False
        
        tile_type = self.grid[grid_y][grid_x]
        return tile_type in {TileType.SEA, TileType.CLOUD}
    
    def _initialize_base_knowledge(self):
        """Initialise la base de connaissances avec des données de base"""
        # Create quelques expériences de base pour démarrer l'apprentissage
        base_experiences = [
            # État, Action, Récompense attendue
            ([0.5, 0.5, 0.8, 0.2, 0.3, 0.8, 0.1, 0.0, 0.0, 0.7, 1.0, 0.0, 0.0, 0.1, 0.0], 1, 5),  # Attaque quand santé haute
            ([0.5, 0.5, 0.2, 0.4, 0.2, 0.6, 0.3, 0.1, 0.0, 0.3, 0.5, 0.0, 0.0, 0.2, 0.66], 6, 3),  # Retraite quand santé basse
            ([0.5, 0.5, 0.6, 0.0, 0.0, 0.0, 0.2, 0.3, 0.0, 0.5, 1.0, 0.0, 0.0, 0.3, 0.0], 2, 2),  # Patrouille quand pas d'ennemi
        ]
        
        for state, action, reward in base_experiences:
            self.experiences.append({
                'state': np.array(state),
                'action': action,
                'reward': reward,
                'next_state': np.array(state)  # Simplification pour l'initialisation
            })
    
    def _save_model(self):
        """Sauvegarde le modèle entraîné"""
        try:
            if not os.path.exists(self.models_dir):
                os.makedirs(self.models_dir)
            
            model_data = {
                'decision_tree': self.decision_tree,
                'scaler': self.scaler,
                'experiences': self.experiences[-100:],  # Garder les 100 dernières
                'strategy_performance': self.strategy_performance,
                'is_trained': self.is_trained
            }
            
            with open(os.path.join(self.models_dir, f"barhamus_ai_{self.entity}.pkl"), 'wb') as f:
                pickle.dump(model_data, f)
        except Exception as e:
            print(f"Erreur sauvegarde modèle: {e}")
    
    def _load_model(self):
        """Charge un modèle sauvegardé"""
        try:
            model_path = os.path.join(self.models_dir, f"barhamus_ai_{self.entity}.pkl")
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.decision_tree = model_data.get('decision_tree', self.decision_tree)
                self.scaler = model_data.get('scaler', self.scaler)
                self.experiences = model_data.get('experiences', [])
                self.strategy_performance = model_data.get('strategy_performance', self.strategy_performance)
                self.is_trained = model_data.get('is_trained', False)
                
                if self.debug_mode:
                    print(f"Modèle IA chargé pour Barhamus {self.entity}")
        except Exception as e:
            print(f"Erreur chargement modèle: {e}")
    
    # Méthodes legacy maintenues pour compatibilité
    def _fire_salvo(self, world, pos, radius):
        """Tir en salve : before + côtés"""
        try:
            world.dispatch_event("attack_event", self.entity)
            self.successful_attacks += 1
            if self.debug_mode:
                print(f"Barhamus {self.entity} tire (IA scikit-learn)!")
        except Exception as e:
            self.failed_attacks += 1
            print(f"Erreur lors du tir Barhamus: {e}")

    def _activate_shield(self, spe):
        spe.mana_shield_active = True
        spe.damage_reduction = random.randint(20, 45) / 100.0
        self.shield_active = True

    def _deactivate_shield(self, spe):
        spe.mana_shield_active = False
        spe.damage_reduction = 0.0
        self.shield_active = False

    def _is_leviathan(self, world, ent):
        if world.has_component(ent, AttackComponent):
            atk = world.component_for_entity(ent, AttackComponent)
            return atk.hitPoints >= 45
        return False

    def _angle_to(self, dx, dy):
        return math.degrees(math.atan2(dy, dx)) % 360

    def _smooth_turn(self, current_dir: float, target_dir: float, max_delta: float = 15.0) -> float:
        """Tourne progressivement vers la direction cible (limite de rotation par frame).
        - current_dir, target_dir en degrés [0..360)
        - max_delta: variation angulaire max autorisée
        """
        # Calcul du plus petit écart angulaire signé (-180..180]
        diff = (target_dir - current_dir + 540.0) % 360.0 - 180.0
        if diff > max_delta:
            diff = max_delta
        elif diff < -max_delta:
            diff = -max_delta
        return (current_dir + diff) % 360.0