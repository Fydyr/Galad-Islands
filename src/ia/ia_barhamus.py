import esper
import random
import math
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
    """IA pour la troupe Barhamus (Maraudeur Zeppelin)"""

    def __init__(self, entity):
        self.entity = entity
        self.cooldown = 0.0
        self.shield_active = False
        self.combat_stance = "aggressive"  # "aggressive", "defensive", "retreat"
        self.last_health = None
        self.grid = None  # Référence à la grille du jeu pour évitement d'obstacles
        self.stuck_timer = 0.0  # Timer pour détecter si l'unité est bloquée
        self.last_position = None  # Dernière position pour détecter si bloqué
        
        # Stabilité directionnelle pour éviter le spinning
        self.current_target_direction = None
        self.direction_change_cooldown = 0.0
        self.path_recalc_timer = 0.0
        self.stable_direction = None
        self.movement_mode = "direct"  # "direct", "avoiding", "patrolling"

    def update(self, world, dt):
        # Récupérer les composants
        pos = world.component_for_entity(self.entity, PositionComponent)
        vel = world.component_for_entity(self.entity, VelocityComponent)
        radius = world.component_for_entity(self.entity, RadiusComponent)
        attack = world.component_for_entity(self.entity, AttackComponent)
        health = world.component_for_entity(self.entity, HealthComponent)
        team = world.component_for_entity(self.entity, TeamComponent)
        spe = world.component_for_entity(self.entity, SpeMaraudeur)

        # Gestion des timers
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.direction_change_cooldown > 0:
            self.direction_change_cooldown -= dt
        self.path_recalc_timer += dt

        # Analyser la situation de combat
        self._analyze_combat_situation(health)

        # Recherche des cibles à portée
        targets = []
        for ent, t_team in world.get_component(TeamComponent):
            if t_team.team_id != team.team_id and world.has_component(ent, PositionComponent):
                t_pos = world.component_for_entity(ent, PositionComponent)
                dist = ((pos.x - t_pos.x)**2 + (pos.y - t_pos.y)**2)**0.5
                if dist <= 12 * 32:  # Détection élargie à 12 cases pour plus d'agressivité
                    targets.append((ent, dist))

        # Priorité Léviathan
        leviathans = [ent for ent, _ in targets if self._is_leviathan(world, ent)]
        if leviathans:
            target = leviathans[0]
        elif targets:
            # Cible la troupe la plus faible (en vérifiant qu'elle a bien un HealthComponent)
            valid_targets = [(ent, dist) for ent, dist in targets if world.has_component(ent, HealthComponent)]
            if valid_targets:
                target = min(valid_targets, key=lambda t: world.component_for_entity(t[0], HealthComponent).currentHealth)[0]
            else:
                target = targets[0][0] if targets else None  # Prendre la première cible si aucune n'a de health
        else:
            target = None

        # Déplacement vers la cible avec évitement d'obstacles stable
        if target:
            t_pos = world.component_for_entity(target, PositionComponent)
            dx, dy = t_pos.x - pos.x, t_pos.y - pos.y
            distance = ((dx)**2 + (dy)**2)**0.5
            
            # Calculer direction vers la cible
            target_angle = self._angle_to(dx, dy)
            
            # Ne recalculer le chemin que si nécessaire (tous les 0.5s ou si bloqué)
            should_recalculate = (
                self.path_recalc_timer > 0.5 or 
                self.stable_direction is None or
                self._is_significantly_different_target(target_angle)
            )
            
            if should_recalculate:
                self.stable_direction = self._find_safe_path(pos, t_pos, target_angle)
                self.path_recalc_timer = 0.0
                self.movement_mode = "direct" if self.stable_direction == target_angle else "avoiding"
            
            # Détecter si l'unité est bloquée
            self._detect_stuck_state(pos, dt)
            
            # Appliquer la direction stable
            movement_direction = self.stable_direction
            
            # Comportement selon la stance de combat
            if self.combat_stance == "retreat":
                # Retraite : s'éloigner tout en tirant
                if distance < 8 * 32:
                    retreat_angle = self._angle_to(-dx, -dy)
                    if should_recalculate:
                        movement_direction = self._find_safe_path(pos, None, retreat_angle, retreating=True)
                    pos.direction = movement_direction
                    vel.currentSpeed = 4.0  # Vitesse de retraite
                else:
                    self.combat_stance = "aggressive"
                    
            elif self.combat_stance == "defensive":
                # Défensif : maintenir distance optimale
                optimal_distance = 6 * 32
                if distance > optimal_distance + 64:  # Augmenter la tolérance
                    pos.direction = movement_direction
                    vel.currentSpeed = 2.0
                elif distance < optimal_distance - 64:
                    retreat_angle = self._angle_to(-dx, -dy)
                    if should_recalculate:
                        movement_direction = self._find_safe_path(pos, None, retreat_angle, retreating=True)
                    pos.direction = movement_direction
                    vel.currentSpeed = 2.0
                else:
                    # Distance parfaite, se stabiliser
                    vel.currentSpeed = 0.5  # Mouvement minimal pour rester agile
                    pos.direction = target_angle  # Viser directement la cible
                    
            else:  # aggressive (par défaut)
                # Agressif : se rapprocher pour attaquer
                if distance > 6 * 32:
                    pos.direction = movement_direction
                    vel.currentSpeed = 4.0  # Vitesse aggressive
                else:
                    # À bonne portée : mouvement stable
                    pos.direction = movement_direction
                    vel.currentSpeed = 1.5  # Mouvement léger pour éviter les tirs

            # Tir si cooldown terminé et à portée
            if self.cooldown <= 0 and distance <= 8 * 32:
                self._fire_salvo(world, pos, radius)
                self.cooldown = 1.5

        else:
            # Pas de cible : patrouille stable
            if self.path_recalc_timer > 1.0:  # Moins fréquent pour la patrouille
                patrol_angle = self._get_safe_patrol_direction(pos)
                self.stable_direction = patrol_angle
                self.path_recalc_timer = 0.0
                self.movement_mode = "patrolling"
            
            if self.stable_direction is not None:
                pos.direction = self.stable_direction
            vel.currentSpeed = 2.0

        # Bouclier de mana : gestion intelligente selon la situation
        if health.currentHealth < health.maxHealth * 0.3 and not self.shield_active:
            # Santé critique : activer bouclier et passer en mode retraite
            self._activate_shield(spe)
            self.combat_stance = "retreat"
        elif health.currentHealth < health.maxHealth * 0.6 and not self.shield_active:
            # Santé moyenne : activer bouclier et mode défensif
            self._activate_shield(spe)
            self.combat_stance = "defensive"
        elif health.currentHealth >= health.maxHealth * 0.8 and self.shield_active:
            # Santé haute : désactiver bouclier et reprendre l'attaque
            self._deactivate_shield(spe)
            self.combat_stance = "aggressive"

    def _analyze_combat_situation(self, health):
        """Analyse la situation de combat pour adapter la stratégie"""
        if self.last_health is None:
            self.last_health = health.currentHealth
            return
            
        # Détection de dégâts subis
        if health.currentHealth < self.last_health:
            damage_taken = self.last_health - health.currentHealth
            # Si on prend beaucoup de dégâts, devenir plus prudent
            if damage_taken > health.maxHealth * 0.2:
                if self.combat_stance == "aggressive":
                    self.combat_stance = "defensive"
                elif self.combat_stance == "defensive":
                    self.combat_stance = "retreat"
        
        self.last_health = health.currentHealth

    def _fire_salvo(self, world, pos, radius):
        """Tir en salve : avant + côtés"""
        # Utiliser le système d'événements du jeu pour tirer
        try:
            world.dispatch_event("attack_event", self.entity)
            print(f"Barhamus {self.entity} tire en mode {self.combat_stance}!")
        except Exception as e:
            print(f"Erreur lors du tir Barhamus: {e}")
            pass

    def _activate_shield(self, spe):
        spe.mana_shield_active = True
        spe.damage_reduction = random.randint(20, 45) / 100.0
        self.shield_active = True

    def _deactivate_shield(self, spe):
        spe.mana_shield_active = False
        spe.damage_reduction = 0.0
        self.shield_active = False

    def _is_leviathan(self, world, ent):
        # Vérifie si l'entité est un Léviathan
        if world.has_component(ent, AttackComponent):
            atk = world.component_for_entity(ent, AttackComponent)
            return atk.hitPoints >= 45  # Seuil typique Léviathan
        return False

    def _angle_to(self, dx, dy):
        return math.degrees(math.atan2(dy, dx)) % 360

    def _is_significantly_different_target(self, new_angle):
        """Vérifie si le nouvel angle de cible est significativement différent"""
        if self.current_target_direction is None:
            self.current_target_direction = new_angle
            return True
        
        # Calculer la différence d'angle (en tenant compte du wrap-around)
        diff = abs(new_angle - self.current_target_direction)
        if diff > 180:
            diff = 360 - diff
        
        # Ne recalculer que si la différence est importante (> 45°)
        if diff > 45:
            self.current_target_direction = new_angle
            return True
        
        return False

    def _find_safe_path(self, current_pos, target_pos, preferred_angle, retreating=False):
        """Trouve un chemin sûr vers la cible en évitant les obstacles dangereux"""
        if not self.grid:
            return preferred_angle
        
        # Vérifier si la direction préférée est sûre
        if self._is_direction_safe(current_pos, preferred_angle):
            return preferred_angle
        
        # Sinon, chercher une direction alternative
        return self._find_alternative_direction(current_pos, target_pos, preferred_angle, retreating)
    
    def _is_direction_safe(self, pos, angle, distance=3.0):
        """Vérifie si une direction est sûre sur une certaine distance"""
        if not self.grid:
            return True
            
        # Réduire la sensibilité - vérifier seulement 2 points au lieu de nombreux
        angle_rad = math.radians(angle)
        check_distance = distance * TILE_SIZE
        
        # Vérifier seulement 2 points : milieu et fin du trajet
        for i in [0.5, 1.0]:
            check_x = pos.x + (check_distance * i) * math.cos(angle_rad)
            check_y = pos.y + (check_distance * i) * math.sin(angle_rad)
            
            if self._is_dangerous_position(check_x, check_y):
                return False
                
        return True
    
    def _is_dangerous_position(self, x, y):
        """Vérifie si une position est dangereuse (île, mine, base ennemie)"""
        if not self.grid:
            return False
            
        # Convertir en coordonnées de grille
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        # Vérifier les limites
        if (grid_x < 0 or grid_x >= len(self.grid[0]) or 
            grid_y < 0 or grid_y >= len(self.grid)):
            return True  # Hors limites = dangereux
        
        tile_type = self.grid[grid_y][grid_x]
        
        # Types de terrain dangereux à éviter (réduit pour moins de sensibilité)
        dangerous_tiles = {
            TileType.GENERIC_ISLAND,  # Îles bloquent le passage
            TileType.MINE,            # Mines causent des dégâts (40 HP)
            # Retirer les bases pour permettre plus de liberté de mouvement
        }
        
        # Seulement vérifier les obstacles vraiment bloquants
        if tile_type in dangerous_tiles:
            return True
            
        # Ne vérifier les mines entités que si on est très proche
        return self._check_for_mine_entities_close(x, y)
    
    def _check_for_mine_entities_close(self, x, y):
        """Vérifie s'il y a des entités mines très proches (rayon réduit)"""
        try:
            import esper
            # Rayon de sécurité réduit pour moins de sensibilité
            search_radius = TILE_SIZE * 0.8  # 0.8 tiles au lieu de 1.5
            
            for entity, (pos, health, attack) in esper.get_components(
                PositionComponent, HealthComponent, AttackComponent
            ):
                # Vérifier si c'est une mine (health max = 1, dégâts = 40)
                if health.maxHealth == 1 and attack.hitPoints == 40:
                    distance = math.sqrt((x - pos.x)**2 + (y - pos.y)**2)
                    if distance < search_radius:
                        return True  # Mine dangereuse détectée
                        
        except Exception:
            pass
            
        return False
    
    def _check_for_mine_entities(self, x, y):
        """Vérifie s'il y a des entités mines dangereuses à proximité"""
        try:
            import esper
            # Chercher les entités mines dans un rayon proche
            search_radius = TILE_SIZE * 1.5  # 1.5 tiles de rayon de sécurité
            
            for entity, (pos, health, attack) in esper.get_components(
                PositionComponent, HealthComponent, AttackComponent
            ):
                # Vérifier si c'est une mine (health max = 1, dégâts = 40)
                if health.maxHealth == 1 and attack.hitPoints == 40:
                    distance = math.sqrt((x - pos.x)**2 + (y - pos.y)**2)
                    if distance < search_radius:
                        return True  # Mine dangereuse détectée
                        
            # Vérifier aussi les tempêtes et autres obstacles dynamiques
            return self._check_for_dynamic_obstacles(x, y)
            
        except Exception:
            # En cas d'erreur, être prudent
            pass
            
        return False
    
    def _check_for_dynamic_obstacles(self, x, y):
        """Vérifie les obstacles dynamiques comme les tempêtes, navires pirates, etc."""
        try:
            import esper
            from src.components.events.stormComponent import StormComponent
            from src.components.events.banditsComponent import Bandits
            
            danger_radius = TILE_SIZE * 3.0  # 3 tiles de sécurité
            
            # Éviter les tempêtes
            if hasattr(esper, 'get_component'):
                for entity, storm in esper.get_component(StormComponent):
                    if esper.has_component(entity, PositionComponent):
                        storm_pos = esper.component_for_entity(entity, PositionComponent)
                        distance = math.sqrt((x - storm_pos.x)**2 + (y - storm_pos.y)**2)
                        if distance < danger_radius:
                            return True
            
                # Éviter les navires pirates
                for entity, bandit in esper.get_component(Bandits):
                    if esper.has_component(entity, PositionComponent):
                        bandit_pos = esper.component_for_entity(entity, PositionComponent)
                        distance = math.sqrt((x - bandit_pos.x)**2 + (y - bandit_pos.y)**2)
                        if distance < danger_radius:
                            return True
                            
        except Exception:
            # Si les composants n'existent pas, ignorer
            pass
            
        return False
    
    def _find_alternative_direction(self, current_pos, target_pos, preferred_angle, retreating=False):
        """Trouve une direction alternative sûre (moins d'options pour plus de stabilité)"""
        # Angles à tester réduits pour éviter trop de changements
        angle_offsets = [30, -30, 60, -60, 90, -90]
        
        for offset in angle_offsets:
            test_angle = (preferred_angle + offset) % 360
            if self._is_direction_safe(current_pos, test_angle, 2.0):
                return test_angle
        
        # Si aucune direction sûre trouvée, garder l'angle préféré
        # (mieux que de changer constamment)
        return preferred_angle
    
    def _get_safe_patrol_direction(self, pos):
        """Obtient une direction de patrouille sûre quand aucune cible n'est présente"""
        # Si on a déjà une direction stable, la garder plus longtemps
        if self.stable_direction is not None and self._is_direction_safe(pos, self.stable_direction, 2.0):
            return self.stable_direction
            
        # Sinon, essayer quelques directions aléatoirement (moins que avant)
        for _ in range(4):  # Réduit de 8 à 4
            random_angle = random.uniform(0, 360)
            if self._is_direction_safe(pos, random_angle, 2.0):
                return random_angle
        
        # Si aucune direction sûre, garder direction actuelle ou aller vers le centre
        return pos.direction if pos.direction else 0
    
    def _detect_stuck_state(self, pos, dt):
        """Détecte si l'unité est bloquée et réagit en conséquence"""
        if self.last_position is None:
            self.last_position = (pos.x, pos.y)
            return
        
        # Calculer la distance parcourue
        distance_moved = math.sqrt(
            (pos.x - self.last_position[0])**2 + 
            (pos.y - self.last_position[1])**2
        )
        
        # Si l'unité bouge très peu, elle pourrait être bloquée
        if distance_moved < TILE_SIZE * 0.05:  # Seuil réduit pour moins de sensibilité
            self.stuck_timer += dt
            if self.stuck_timer > 3.0:  # Attendre plus longtemps (3s au lieu de 2s)
                # Forcer un changement de direction
                self._handle_stuck_situation(pos)
                self.stuck_timer = 0.0
        else:
            self.stuck_timer = 0.0
        
        self.last_position = (pos.x, pos.y)
    
    def _handle_stuck_situation(self, pos):
        """Gère la situation quand l'unité est bloquée"""
        # Essayer seulement quelques directions principales
        for angle in [45, 135, 225, 315]:  # Diagonales d'abord
            if self._is_direction_safe(pos, angle, 1.5):
                self.stable_direction = angle
                self.path_recalc_timer = 0.0  # Forcer recalcul
                print(f"Barhamus {self.entity} was stuck, trying diagonal direction {angle}°")
                return
        
        # Si les diagonales ne marchent pas, essayer les directions cardinales
        for angle in [0, 90, 180, 270]:
            if self._is_direction_safe(pos, angle, 1.5):
                self.stable_direction = angle
                self.path_recalc_timer = 0.0
                print(f"Barhamus {self.entity} was stuck, trying cardinal direction {angle}°")
                return
        
        # En dernier recours, forcer une direction opposée
        self.stable_direction = (pos.direction + 180) % 360
        self.path_recalc_timer = 0.0
        print(f"Barhamus {self.entity} is stuck, retreating")