import esper
import random
import math
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import pickle
import os
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.attackComponent import AttackComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE

class BarhamusAI:
    """IA pour la troupe Barhamus (Maraudeur Zeppelin) utilisant scikit-learn"""

    def __init__(self, entity):
        self.entity = entity
        self.cooldown = 0.0
        self.shield_active = False
        self.grid = None
        
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
        
        # Performance tracking
        self.survival_time = 0.0
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
        
        # Initialiser avec des données de base
        self._initialize_base_knowledge()
        
        # Charger modèle sauvegardé si disponible
        self._load_model()

    def update(self, world, dt):
        """Mise à jour principale de l'IA avec apprentissage"""
        # Récupérer les composants
        pos = world.component_for_entity(self.entity, PositionComponent)
        vel = world.component_for_entity(self.entity, VelocityComponent)
        radius = world.component_for_entity(self.entity, RadiusComponent)
        attack = world.component_for_entity(self.entity, AttackComponent)
        health = world.component_for_entity(self.entity, HealthComponent)
        team = world.component_for_entity(self.entity, TeamComponent)
        spe = world.component_for_entity(self.entity, SpeMaraudeur)

        # Mettre à jour les statistiques de survie
        self.survival_time += dt
        
        # Gestion du cooldown
        if self.cooldown > 0:
            self.cooldown -= dt

        # Analyser la situation actuelle
        current_state = self._analyze_situation(world, pos, health, team)
        
        # Calculer la récompense de l'action précédente
        if self.last_state is not None and self.last_action is not None:
            reward = self._calculate_reward(current_state, health)
            self._record_experience(self.last_state, self.last_action, reward, current_state)
        
        # Prédire la meilleure action avec l'IA
        action = self._predict_best_action(current_state)
        
        # Exécuter l'action
        self._execute_action(action, world, pos, vel, health, team, spe)
        
        # Sauvegarder l'état pour le prochain cycle
        self.last_state = current_state.copy()
        self.last_action = action
        
        # Entraîner le modèle périodiquement
        if len(self.experiences) > 50 and len(self.experiences) % 25 == 0:
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
        state[12] = max(0, self.cooldown) / 2.0  # Cooldown normalisé
        state[13] = self.survival_time / 300.0  # Temps de survie normalisé (5 min max)
        state[14] = {"balanced": 0, "aggressive": 0.33, "defensive": 0.66, "tactical": 1.0}[self.current_strategy]
        
        return state
    
    def _predict_best_action(self, state):
        """Prédit la meilleure action à partir de l'état actuel"""
        if not self.is_trained or len(self.training_data) < 10:
            return self._get_default_action(state)
        
        try:
            # Normaliser l'état
            state_scaled = self.scaler.transform([state])
            
            # Prédire l'action avec l'arbre de décision
            predicted_action = self.decision_tree.predict(state_scaled)[0]
            
            # Ajouter un peu d'exploration (10% de chance d'action aléatoire)
            if random.random() < 0.1:
                return random.randint(0, 7)  # 8 actions possibles
            
            return int(predicted_action)
            
        except Exception as e:
            print(f"Erreur prédiction IA: {e}")
            return self._get_default_action(state)
    
    def _get_default_action(self, state):
        """Action par défaut basée sur des règles simples"""
        health_ratio = state[2]
        enemy_count = state[3] * 5
        closest_enemy_dist = state[4]
        
        if health_ratio < 0.3:
            return 6  # Retraite
        elif enemy_count > 2:
            return 5  # Défensif
        elif closest_enemy_dist < 0.3:
            return 1  # Attaque
        else:
            return 0  # Approche
    
    def _execute_action(self, action, world, pos, vel, health, team, spe):
        """Exécute l'action décidée par l'IA"""
        # Actions possibles:
        # 0: Approche agressive
        # 1: Attaque
        # 2: Patrouille
        # 3: Évitement tactique
        # 4: Activation bouclier
        # 5: Position défensive
        # 6: Retraite
        # 7: Embuscade
        
        if action == 0:
            self._action_aggressive_approach(world, pos, vel, team)
        elif action == 1:
            self._action_attack(world, pos, vel, team)
        elif action == 2:
            self._action_patrol(pos, vel)
        elif action == 3:
            self._action_tactical_avoidance(world, pos, vel, team)
        elif action == 4:
            self._action_shield_management(spe, health)
        elif action == 5:
            self._action_defensive_position(world, pos, vel, team)
        elif action == 6:
            self._action_retreat(world, pos, vel, team)
        elif action == 7:
            self._action_ambush(world, pos, vel, team)
    
    def _find_nearby_enemies(self, world, pos, team):
        """Trouve tous les ennemis dans un rayon donné"""
        enemies = []
        
        # Si world est None (test), retourner des données simulées
        if world is None:
            return []
            
        search_radius = 15 * TILE_SIZE  # 15 tiles de rayon
        
        try:
            for ent, t_team in world.get_component(TeamComponent):
                if t_team.team_id != team.team_id and world.has_component(ent, PositionComponent):
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
        
        # Récompense de survie
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
        
        # Récompense pour évitement d'obstacles
        if current_state[6] < 0.3:  # Peu d'îles autour
            reward += 2
        if current_state[7] < 0.2:  # Peu de mines autour
            reward += 3
        
        self.last_health = health.currentHealth
        return reward
    
    def _record_experience(self, state, action, reward, next_state):
        """Enregistre une expérience pour l'apprentissage"""
        experience = {
            'state': state.copy(),
            'action': action,
            'reward': reward,
            'next_state': next_state.copy()
        }
        self.experiences.append(experience)
        
        # Garder seulement les 1000 dernières expériences
        if len(self.experiences) > 1000:
            self.experiences = self.experiences[-1000:]
    
    def _retrain_model(self):
        """Réentraîne le modèle avec les nouvelles expériences"""
        if len(self.experiences) < 20:
            return
        
        try:
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
            
            print(f"Modèle IA réentraîné avec {len(X)} expériences")
            
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
        """Change vers la stratégie la plus performante"""
        best_strategy = max(self.strategy_performance.keys(), 
                           key=lambda s: self._get_strategy_success_rate(s))
        if best_strategy != self.current_strategy:
            print(f"IA Barhamus change de stratégie: {self.current_strategy} -> {best_strategy}")
            self.current_strategy = best_strategy
    
    # Actions spécifiques
    def _action_aggressive_approach(self, world, pos, vel, team):
        """Action: Approche agressive vers l'ennemi"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            angle = self._angle_to(target_pos.x - pos.x, target_pos.y - pos.y)
            pos.direction = angle
            vel.currentSpeed = 4.5  # Vitesse élevée
    
    def _action_attack(self, world, pos, vel, team):
        """Action: Attaque si ennemi à portée"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies and self.cooldown <= 0:
            closest = enemies[0]
            if closest[1] <= 8 * TILE_SIZE:  # À portée
                target_pos = world.component_for_entity(closest[0], PositionComponent)
                angle = self._angle_to(target_pos.x - pos.x, target_pos.y - pos.y)
                pos.direction = angle
                vel.currentSpeed = 1.0  # Ralentir pour viser
                
                try:
                    world.dispatch_event("attack_event", self.entity)
                    self.cooldown = 1.5
                    self.successful_attacks += 1
                    print(f"Barhamus {self.entity} attaque (IA intelligente)!")
                except Exception:
                    self.failed_attacks += 1
    
    def _action_patrol(self, pos, vel):
        """Action: Patrouille aléatoire"""
        if not hasattr(self, 'patrol_direction') or random.random() < 0.1:
            self.patrol_direction = random.uniform(0, 360)
        pos.direction = self.patrol_direction
        vel.currentSpeed = 2.5
    
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
                angle = self._angle_to(avoid_x, avoid_y)
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
            angle = self._angle_to(safe_pos[0] - pos.x, safe_pos[1] - pos.y)
            pos.direction = angle
            vel.currentSpeed = 2.0
    
    def _action_retreat(self, world, pos, vel, team):
        """Action: Retraite tactique"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            # Fuir dans la direction opposée à l'ennemi le plus proche
            closest = enemies[0]
            enemy_pos = world.component_for_entity(closest[0], PositionComponent)
            retreat_angle = self._angle_to(pos.x - enemy_pos.x, pos.y - enemy_pos.y)
            pos.direction = retreat_angle
            vel.currentSpeed = 4.0  # Vitesse de fuite
    
    def _action_ambush(self, world, pos, vel, team):
        """Action: Embuscade - attendre dans une position avantageuse"""
        vel.currentSpeed = 0.5  # Mouvement minimal
        # Rester orienté vers la zone de danger
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            angle = self._angle_to(target_pos.x - pos.x, target_pos.y - pos.y)
            pos.direction = angle

    # Méthodes utilitaires et d'analyse
    def _analyze_nearby_obstacles(self, pos):
        """Analyse les obstacles autour de la position"""
        obstacles = {'islands': 0, 'mines': 0, 'walls': 0}
        
        if not self.grid:
            return obstacles
        
        # Vérifier dans un rayon de 3 tiles
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
        """Vérifie si la position est dans une zone sûre"""
        if not self.grid:
            return 0.5
        
        # Vérifier la distance aux bords
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
            health = world.component_for_entity(entity, HealthComponent)
            health_ratio = health.currentHealth / health.maxHealth
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
        
        # Chercher dans un rayon de 5 tiles
        for radius in range(1, 6):
            for angle in range(0, 360, 45):
                x = current_pos.x + radius * TILE_SIZE * math.cos(math.radians(angle))
                y = current_pos.y + radius * TILE_SIZE * math.sin(math.radians(angle))
                
                if self._is_position_safe(x, y):
                    return (x, y)
        
        return None
    
    def _is_position_safe(self, x, y):
        """Vérifie si une position est sûre"""
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
        # Créer quelques expériences de base pour démarrer l'apprentissage
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
            model_dir = "models"
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            
            model_data = {
                'decision_tree': self.decision_tree,
                'scaler': self.scaler,
                'experiences': self.experiences[-100:],  # Garder les 100 dernières
                'strategy_performance': self.strategy_performance,
                'is_trained': self.is_trained
            }
            
            with open(f"{model_dir}/barhamus_ai_{self.entity}.pkl", 'wb') as f:
                pickle.dump(model_data, f)
        except Exception as e:
            print(f"Erreur sauvegarde modèle: {e}")
    
    def _load_model(self):
        """Charge un modèle sauvegardé"""
        try:
            model_path = f"models/barhamus_ai_{self.entity}.pkl"
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.decision_tree = model_data.get('decision_tree', self.decision_tree)
                self.scaler = model_data.get('scaler', self.scaler)
                self.experiences = model_data.get('experiences', [])
                self.strategy_performance = model_data.get('strategy_performance', self.strategy_performance)
                self.is_trained = model_data.get('is_trained', False)
                
                print(f"Modèle IA chargé pour Barhamus {self.entity}")
        except Exception as e:
            print(f"Erreur chargement modèle: {e}")
    
    # Méthodes legacy maintenues pour compatibilité
    def _fire_salvo(self, world, pos, radius):
        """Tir en salve : avant + côtés"""
        try:
            world.dispatch_event("attack_event", self.entity)
            self.successful_attacks += 1
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