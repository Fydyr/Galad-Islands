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

class MaraudeurAI:
    """IA pour la troupe Barhamus (Maraudeur Zeppelin) utilisant scikit-learn"""

    def __init__(self, entity):
        self.entity = entity
        self.cooldown = 0.0
        self.shield_active = False
        self.grid = None
        
        # Stratégie déterministe : choix aléatoire au début seulement
        self.mode = random.choice(["offensive", "defensive"])
        print(f"Maraudeur {self.entity}: Mode choisi = {self.mode}")
        
        # Statistiques simples
        self.survival_time = 0.0
        self.last_obstacle_check = 0.0
        self.stuck_counter = 0
        self.last_position = None

    def update(self, world, dt):
        """Mise à jour principale de l'IA avec apprentissage"""
        try:
            # Récupérer les composants
            pos = world.component_for_entity(self.entity, PositionComponent)
            vel = world.component_for_entity(self.entity, VelocityComponent)
            radius = world.component_for_entity(self.entity, RadiusComponent)
            attack = world.component_for_entity(self.entity, AttackComponent)
            health = world.component_for_entity(self.entity, HealthComponent)
            team = world.component_for_entity(self.entity, TeamComponent)
            spe = world.component_for_entity(self.entity, SpeMaraudeur)
            
            print(f"Barhamus {self.entity}: Composants OK - pos={pos.x:.1f},{pos.y:.1f} vel={vel.currentSpeed}")
        except Exception as e:
            print(f"Erreur composants Barhamus {self.entity}: {e}")
            return

        # Mettre à jour les statistiques de survie
        self.survival_time += dt
        self.last_obstacle_check += dt
        
        # Gestion du cooldown
        if self.cooldown > 0:
            self.cooldown -= dt

        # Détecter si bloqué
        if self.last_position:
            dist_moved = math.sqrt((pos.x - self.last_position[0])**2 + (pos.y - self.last_position[1])**2)
            if dist_moved < 5 and vel.currentSpeed > 1.0:  # Bloqué !
                self.stuck_counter += 1
            else:
                self.stuck_counter = 0
        self.last_position = (pos.x, pos.y)

        # Logique simple et déterministe
        try:
            if self.mode == "defensive":
                self._defensive_behavior(world, pos, vel, team, health)
            else:  # offensive
                self._offensive_behavior(world, pos, vel, team, health)
            
            # Tirer si ennemi à portée
            self._auto_fire(world, pos, team)
            
        except Exception as e:
            print(f"Erreur IA Maraudeur {self.entity}: {e}")
            vel.currentSpeed = 2.0
            pos.direction = (pos.direction + 45) % 360

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
        # Utiliser le modèle seulement s'il a été entraîné.
        # Ne pas dépendre de `training_data` qui n'est pas utilisé directement
        if not self.is_trained:
            # Log utile pour debug apprentissage
            print(f"Barhamus {self.entity}: Modèle non entraîné -> action par défaut")
            return self._get_default_action(state)
        
        try:
            # Normaliser l'état
            state_scaled = self.scaler.transform([state])
            
            # Prédire l'action avec l'arbre de décision
            predicted_action = self.decision_tree.predict(state_scaled)[0]
            
            # Ajouter de l'exploration (15% de chance d'action aléatoire pour apprendre)
            if random.random() < 0.15:
                return random.randint(0, 7)  # 8 actions possibles
            
            print(f"Barhamus {self.entity}: Action PRÉDITE par modèle = {predicted_action}")
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
    
    def _defensive_behavior(self, world, pos, vel, team, health):
        """Comportement défensif : protéger la base"""
        base_pos = self._find_team_base(world, team)
        if not base_pos:
            base_pos = (500, 500)
        
        # Distance à la base
        base_dist = math.sqrt((pos.x - base_pos[0])**2 + (pos.y - base_pos[1])**2)
        
        # Chercher ennemis proches
        enemies = self._find_nearby_enemies(world, pos, team)
        
        if enemies and enemies[0][1] < 10 * TILE_SIZE:
            # Ennemi proche : l'attaquer
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            target_angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
            
            # Éviter obstacles
            if self._check_obstacle_ahead(pos, target_angle):
                target_angle = self._find_clear_direction(pos, target_angle)
            
            pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=15.0)
            vel.currentSpeed = 3.5
            print(f"Maraudeur {self.entity} (DEF): Attaque ennemi proche")
        
        elif base_dist > 8 * TILE_SIZE:
            # Trop loin de la base : y retourner
            target_angle = self._angle_to(pos.x - base_pos[0], pos.y - base_pos[1])
            
            # Éviter obstacles
            if self._check_obstacle_ahead(pos, target_angle):
                target_angle = self._find_clear_direction(pos, target_angle)
            
            pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=15.0)
            vel.currentSpeed = 3.0
            print(f"Maraudeur {self.entity} (DEF): Retour à la base")
        
        else:
            # Patrouiller autour de la base
            patrol_angle = self._angle_to(pos.x - base_pos[0], pos.y - base_pos[1]) + 90
            pos.direction = self._smooth_turn(pos.direction, patrol_angle, max_delta=10.0)
            vel.currentSpeed = 2.0
            print(f"Maraudeur {self.entity} (DEF): Patrouille base")
    
    def _offensive_behavior(self, world, pos, vel, team, health):
        """Comportement offensif : attaquer la base ennemie"""
        # Chercher ennemis proches d'abord
        enemies = self._find_nearby_enemies(world, pos, team)
        
        # Si santé basse, reculer
        health_ratio = health.currentHealth / health.maxHealth
        if health_ratio < 0.3 and enemies:
            # Fuir
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            retreat_angle = self._angle_to(target_pos.x - pos.x, target_pos.y - pos.y)
            
            if self._check_obstacle_ahead(pos, retreat_angle):
                retreat_angle = self._find_clear_direction(pos, retreat_angle)
            
            pos.direction = self._smooth_turn(pos.direction, retreat_angle, max_delta=20.0)
            vel.currentSpeed = 4.0
            print(f"Maraudeur {self.entity} (OFF): Retraite (santé basse)")
            return
        
        # Attaquer ennemi proche
        if enemies and enemies[0][1] < 8 * TILE_SIZE:
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            target_angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
            
            if self._check_obstacle_ahead(pos, target_angle):
                target_angle = self._find_clear_direction(pos, target_angle)
            
            pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=15.0)
            vel.currentSpeed = 3.5
            print(f"Maraudeur {self.entity} (OFF): Attaque ennemi proche")
        
        else:
            # Aller vers la base ennemie
            enemy_base = self._find_enemy_base(world, team)
            if enemy_base:
                target_angle = self._angle_to(pos.x - enemy_base[0], pos.y - enemy_base[1])
                
                # Éviter obstacles
                if self._check_obstacle_ahead(pos, target_angle):
                    target_angle = self._find_clear_direction(pos, target_angle)
                
                pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=15.0)
                vel.currentSpeed = 4.0
                print(f"Maraudeur {self.entity} (OFF): Fonce vers base ennemie")
            else:
                # Chercher la base ennemie
                pos.direction = (pos.direction + 20) % 360
                vel.currentSpeed = 3.0
                print(f"Maraudeur {self.entity} (OFF): Recherche base ennemie")
    
    def _auto_fire(self, world, pos, team):
        """Tir automatique sur les ennemis à portée"""
        if self.cooldown > 0:
            return
        
        enemies = self._find_nearby_enemies(world, pos, team)
        if not enemies:
            return
        
        # Tirer sur les ennemis à portée
        for enemy_ent, distance, _ in enemies[:3]:  # Max 3 cibles
            if distance <= 8 * TILE_SIZE:
                try:
                    world.dispatch_event("attack_event", self.entity)
                    self.cooldown = 1.5
                    print(f"Maraudeur {self.entity}: TIR !")
                    break
                except Exception as e:
                    print(f"Erreur tir: {e}")
    
    def _execute_movement_action(self, action, world, pos, vel, team, spe):
        """Exécute seulement la partie mouvement de l'action"""
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
        for enemy_ent, distance, priority in enemies:
            if distance <= 8 * TILE_SIZE:  # Portée de tir
                enemies_in_range.append((enemy_ent, distance, priority))
        
        if not enemies_in_range:
            return
        
        # TIR EN SALVE - Attaquer jusqu'à 3 ennemis simultanément
        targets_to_attack = min(3, len(enemies_in_range))
        
        for i in range(targets_to_attack):
            enemy_ent = enemies_in_range[i][0]
            try:
                # Calcul de l'angle vers la cible
                enemy_pos = world.component_for_entity(enemy_ent, PositionComponent)
                angle_to_target = self._angle_to(enemy_pos.x - pos.x, enemy_pos.y - pos.y)
                
                # Tir avec dispersion pour couvrir les flancs
                if i == 0:  # Tir principal
                    self._fire_at_angle(world, pos, angle_to_target)
                elif i == 1:  # Tir côté droit
                    self._fire_at_angle(world, pos, angle_to_target + 25)
                elif i == 2:  # Tir côté gauche  
                    self._fire_at_angle(world, pos, angle_to_target - 25)
                    
                print(f"Barhamus {self.entity}: Tir en salve #{i+1} vers angle {angle_to_target:.0f}°")
                
            except Exception as e:
                print(f"Erreur tir salve: {e}")
        
        # Déclencher le cooldown après la salve
        if targets_to_attack > 0:
            self.cooldown = 2.0  # 2 secondes de cooldown
            self.successful_attacks += targets_to_attack
    
    def _fire_at_angle(self, world, pos, angle):
        """Tire un projectile dans la direction spécifiée"""
        try:
            # Utiliser le système d'événements du jeu pour tirer
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
            target_angle = None
            
            if distance < 6 * TILE_SIZE:  # Trop proche, reculer
                # IMPORTANT : inverser direction car movementProcessor soustrait
                target_angle = self._angle_to(target_pos.x - pos.x, target_pos.y - pos.y)
                vel.currentSpeed = 2.0
            elif distance > 8 * TILE_SIZE:  # Trop loin, s'approcher
                # IMPORTANT : inverser direction
                target_angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                vel.currentSpeed = 3.5
            else:  # Distance parfaite, cercler doucement
                base_angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
                target_angle = (base_angle + 90) % 360
                vel.currentSpeed = 2.5
            
            # Appliquer rotation progressive pour éviter les toupies
            if target_angle is not None:
                pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=12.0)
            
            print(f"Barhamus {self.entity}: Position d'attaque - distance {distance/TILE_SIZE:.1f} tiles")
    
    def _default_defense_behavior(self, world, pos, vel, team):
        """Comportement de défense par défaut en cas d'erreur"""
        try:
            base_pos = self._find_team_base(world, team)
            if base_pos:
                # Retourner vers la base - IMPORTANT : inverser direction
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
                    # Vérifier si c'est un bâtiment (a un BuildingComponent ou similaire)
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
        
        return (500, 500)  # Position par défaut
    
    def _check_enemies_near_base(self, world, team, base_pos):
        """Vérifie s'il y a des ennemis près de la base"""
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
            return 2  # Patrouille par défaut
            
        # Distance à la base
        base_distance = math.sqrt((pos.x - base_pos[0])**2 + (pos.y - base_pos[1])**2)
        
        # Si loin de la base, y retourner
        if base_distance > 8 * TILE_SIZE:
            return 0  # Approche (vers la base)
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
                    return 0  # Approche vers la base ennemie
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
                    # Vérifier si c'est un bâtiment (a beaucoup de vie)
                    if (world.has_component(ent, AttackComponent) and 
                        world.has_component(ent, HealthComponent)):
                        health_comp = world.component_for_entity(ent, HealthComponent)
                        # Base/Tour = beaucoup de vie et immobile
                        if health_comp.maxHealth > 200:  # Seuil pour identifier une base
                            return (t_pos.x, t_pos.y)
            
            # Si pas de base trouvée, utiliser les positions par défaut
            if enemy_team_id == 1:  # Base alliée
                return (200, 200)  # Coin haut-gauche
            else:  # Base ennemie
                if self.grid:
                    return (len(self.grid[0]) * TILE_SIZE - 200, len(self.grid) * TILE_SIZE - 200)  # Coin bas-droite
                else:
                    return (1800, 1800)  # Position par défaut
        except Exception as e:
            print(f"Erreur recherche base ennemie: {e}")
        
        return None
    
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
        
        # Récompense de survie — limitée à une fois toutes les 15 secondes
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
        
        # PÉNALITÉ DE MORT : appliquer une forte pénalité unique si l'unité meurt
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
        # Ce bonus est déjà intégré dans l'avantage tactique
        # On peut ajouter un bonus supplémentaire si nécessaire
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
        # Log d'appoint pour vérifier que les expériences s'accumulent
        if len(self.experiences) % 10 == 0 or len(self.experiences) < 20:
            print(f"Barhamus {self.entity}: Expérience enregistrée (total={len(self.experiences)})")
        
        # Garder seulement les 1000 dernières expériences
        if len(self.experiences) > 1000:
            self.experiences = self.experiences[-1000:]
    
    def _retrain_model(self):
        """Réentraîne le modèle avec les nouvelles expériences"""
        if len(self.experiences) < 10:
            print(f"Barhamus {self.entity}: Pas assez d'expériences pour réentraîner ({len(self.experiences)})")
            return
        
        try:
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
        """Change vers la stratégie la plus performante"""
        best_strategy = max(self.strategy_performance.keys(), 
                           key=lambda s: self._get_strategy_success_rate(s))
        if best_strategy != self.current_strategy:
            print(f"IA Barhamus change de stratégie: {self.current_strategy} -> {best_strategy}")
            self.current_strategy = best_strategy
    
    # Actions spécifiques
    def _action_aggressive_approach(self, world, pos, vel, team):
        """Action: Approche agressive vers l'ennemi ou base ennemie"""
        enemies = self._find_nearby_enemies(world, pos, team)
        
        if enemies:
            # Attaquer l'ennemi le plus proche
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            # IMPORTANT : movementProcessor SOUSTRAIT cos/sin, donc inverser la direction
            target_angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
            pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=12.0)
            vel.currentSpeed = 4.5  # Vitesse élevée
            print(f"Barhamus {self.entity}: Approche agressive vers ennemi - angle={pos.direction:.1f}°")
        else:
            # Pas d'ennemi, aller vers la base ennemie
            enemy_base = self._find_enemy_base(world, team)
            if enemy_base:
                # IMPORTANT : inverser la direction pour le movementProcessor
                target_angle = self._angle_to(pos.x - enemy_base[0], pos.y - enemy_base[1])
                pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=12.0)
                vel.currentSpeed = 4.0
                print(f"Barhamus {self.entity}: Approche vers base ennemie - angle={pos.direction:.1f}°")
            else:
                # Patrouiller
                vel.currentSpeed = 2.5
                pos.direction = (pos.direction + 30) % 360
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
                    print(f"Barhamus {self.entity} attaque (IA intelligente)!")
                except Exception:
                    self.failed_attacks += 1
    
    def _action_patrol(self, pos, vel):
        """Action: Patrouille aléatoire"""
        if not hasattr(self, 'patrol_direction') or random.random() < 0.1:
            self.patrol_direction = random.uniform(0, 360)
        pos.direction = self.patrol_direction
        vel.currentSpeed = 2.5
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
                # IMPORTANT : inverser pour movementProcessor (déjà dans la bonne direction ici)
                target_angle = self._angle_to(-avoid_x, -avoid_y)
                pos.direction = self._smooth_turn(pos.direction, target_angle, max_delta=12.0)
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
    
    def _action_retreat(self, world, pos, vel, team):
        """Action: Retraite tactique"""
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            # Fuir dans la direction opposée à l'ennemi le plus proche
            closest = enemies[0]
            enemy_pos = world.component_for_entity(closest[0], PositionComponent)
            # IMPORTANT : déjà inversé (pos - enemy) donc garder tel quel
            retreat_angle = self._angle_to(pos.x - enemy_pos.x, pos.y - enemy_pos.y)
            # Mais pour movementProcessor qui soustrait, ré-inverser !
            retreat_angle = self._angle_to(enemy_pos.x - pos.x, enemy_pos.y - pos.y)
            pos.direction = retreat_angle
            vel.currentSpeed = 4.0  # Vitesse de fuite
    
    def _action_ambush(self, world, pos, vel, team):
        """Action: Embuscade - attendre dans une position avantageuse"""
        vel.currentSpeed = 0.5  # Mouvement minimal
        # Rester orienté vers la zone de danger
        enemies = self._find_nearby_enemies(world, pos, team)
        if enemies:
            target_pos = world.component_for_entity(enemies[0][0], PositionComponent)
            # IMPORTANT : inverser pour movementProcessor
            angle = self._angle_to(pos.x - target_pos.x, pos.y - target_pos.y)
            pos.direction = angle

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
        # Ce bonus est déjà intégré dans l'avantage tactique
        # On peut ajouter un bonus supplémentaire si nécessaire
        if len(current_state) >= 10:
            tactical_advantage = current_state[9]  # Avantage tactique
            if tactical_advantage > 0.7:  # Bonne position tactique
                return 1.0  # Bonus pour bonne position offensive
        return 0
    
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
    
    def _smooth_turn(self, current_dir, target_dir, max_delta=12.0):
        """Limite la vitesse de rotation pour éviter les mouvements brusques"""
        current_dir = current_dir % 360.0
        target_dir = target_dir % 360.0
        
        diff = target_dir - current_dir
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        
        if abs(diff) <= max_delta:
            return target_dir
        else:
            return (current_dir + math.copysign(max_delta, diff)) % 360.0
    
    def _check_obstacle_ahead(self, pos, direction, check_distance=4):
        """Vérifie s'il y a un obstacle devant dans la direction donnée"""
        if not self.grid:
            return False
        
        # Vérifier plusieurs points devant
        for dist in range(1, check_distance + 1):
            angle_rad = math.radians(direction)
            # IMPORTANT: MovementProcessor soustrait cos/sin, donc on inverse
            check_x = pos.x - dist * TILE_SIZE * math.cos(angle_rad)
            check_y = pos.y - dist * TILE_SIZE * math.sin(angle_rad)
            
            grid_x = int(check_x // TILE_SIZE)
            grid_y = int(check_y // TILE_SIZE)
            
            if 0 <= grid_y < len(self.grid) and 0 <= grid_x < len(self.grid[0]):
                tile = self.grid[grid_y][grid_x]
                if tile in [TileType.ISLAND, TileType.MINE, TileType.WALL]:
                    return True
        
        return False
    
    def _find_clear_direction(self, pos, preferred_direction):
        """Trouve une direction libre d'obstacles proche de la direction préférée"""
        # Si bloqué, essayer des angles autour de la direction préférée
        angles_to_try = [0, 30, -30, 60, -60, 90, -90, 120, -120, 180]
        
        for angle_offset in angles_to_try:
            test_direction = (preferred_direction + angle_offset) % 360
            if not self._check_obstacle_ahead(pos, test_direction, check_distance=3):
                if angle_offset != 0:
                    print(f"Maraudeur {self.entity}: Évitement obstacle, déviation de {angle_offset}°")
                return test_direction
        
        # Aucune direction libre trouvée, faire demi-tour
        print(f"Maraudeur {self.entity}: Bloqué ! Demi-tour")
        return (preferred_direction + 180) % 360