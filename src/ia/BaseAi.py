"""
IA de la base utilisant un modèle de Machine Learning pré-entraîné.
Ce processeur charge un modèle et l'utilise pour prendre des décisions stratégiques,
comme la production d'unités.
"""

import esper
import random
import numpy as np
import joblib
import os
import time

from src.components.core.baseComponent import BaseComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.constants.gameplay import UNIT_COSTS
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType
from src.components.core.positionComponent import PositionComponent
from src.constants.team import Team
from src.settings.settings import config_manager
from src.processeurs.KnownBaseProcessor import enemy_base_registry


class BaseAi(esper.Processor):
    """
    IA de la base utilisant un arbre de décision.

    Cette classe est un processeur ECS qui agit comme le cerveau stratégique pour une équipe.
    Elle charge un modèle `scikit-learn` pré-entraîné pour décider quelle unité produire.

    Features: [gold, base_health_ratio, allied_units, enemy_units, enemy_base_known, towers_needed, enemy_base_health_ratio, action] 
    Actions: 0: rien, 1: éclaireur, 2: architecte, 3: maraudeur, 4: léviathan, 5: druide, 6: kamikaze
    """

    UNIT_TYPE_MAPPING = {
        "scout": UnitType.SCOUT,
        "maraudeur": UnitType.MARAUDEUR,
        "leviathan": UnitType.LEVIATHAN,
        "druid": UnitType.DRUID,
        "architect": UnitType.ARCHITECT,
        "kamikaze": UnitType.KAMIKAZE,
        "warrior": UnitType.MARAUDEUR,
    }

    ACTION_MAPPING = {
        0: {"name": "Rien", "unit_type": None, "cost": 0, "reserve": 0},
        1: {"name": "Éclaireur", "unit_type": UnitType.SCOUT, "cost": UNIT_COSTS.get("scout", 30), "reserve": 0},
        2: {"name": "Architecte", "unit_type": UnitType.ARCHITECT, "cost": UNIT_COSTS.get("architect", 50), "reserve": 50},
        3: {"name": "Maraudeur", "unit_type": UnitType.MARAUDEUR, "cost": UNIT_COSTS.get("maraudeur", 40), "reserve": 50},
        4: {"name": "Léviathan", "unit_type": UnitType.LEVIATHAN, "cost": UNIT_COSTS.get("leviathan", 120), "reserve": 50},
        5: {"name": "Druide", "unit_type": UnitType.DRUID, "cost": UNIT_COSTS.get("druid", 80), "reserve": 50},
        6: {"name": "Kamikaze", "unit_type": UnitType.KAMIKAZE, "cost": UNIT_COSTS.get("kamikaze", 60), "reserve": 50},
    }

    def __init__(self, team_id=2):
        self.default_team_id = team_id
        self.gold_reserve = 50
        self.action_cooldown = 8.0
        self.last_action_time = 0
        self.last_decision_time = time.time()
        self.enabled = True
        self.model = None
        self.load_model()
        
        # Activer les logs de l'IA si le mode développeur est activé
        self.debug_mode = config_manager.get('dev_mode', False)

    def load_model(self):
        """Charge le modèle de décision pré-entraîné."""
        unified_model_path = "src/models/base_ai_unified_final.pkl"

        if os.path.exists(unified_model_path):
            try:
                self.model = joblib.load(unified_model_path)
                print(f"🤖 Modèle IA chargé pour l'équipe {self.default_team_id}: {type(self.model).__name__}")
            except Exception as e:
                print(f"❌ Erreur lors du chargement du modèle IA: {e}")
                self.model = None
        else:
            print("❌ Modèle IA non trouvé. L'IA de la base sera inactive.")
            self.model = None

    def process(self, dt: float = 0.016, active_player_team_id: int = 1):
        """Exécute la logique de l'IA de la base à chaque frame."""
        if not getattr(self, 'enabled', True):
            return

        if self.default_team_id == active_player_team_id:
            return

        ai_team_id = Team.ENEMY if active_player_team_id == Team.ALLY else Team.ALLY

        self.last_action_time += dt
        if self.last_action_time < self.action_cooldown:
            return

        time_since_last_decision = time.time() - self.last_decision_time
        game_state = self._get_current_game_state(ai_team_id)
        if game_state is None:
            return

        game_state['time_since_last_decision'] = time_since_last_decision

        action = self._decide_action(game_state)
        self.last_decision_time = time.time()

        if self.debug_mode:
            action_name = self.ACTION_MAPPING.get(action, {}).get("name", "Inconnue")
            gold = game_state['gold']
            base_hp = game_state['base_health_ratio']
            ally_u, enemy_u = game_state['allied_units'], game_state['enemy_units']            
            print(f"🤖 IA Base (team {self.default_team_id}): {action_name} | Or={gold} HP={base_hp:.0%} Alliés={ally_u} Ennemis={enemy_u} | Base ennemie connue: {game_state['enemy_base_known']}")

        if self._execute_action(action, self.default_team_id):
            self.last_action_time = 0

    def _get_current_game_state(self, ai_team_id: int):
        """Récupère l'état actuel du jeu pour la prise de décision."""
        try:
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return None

            base_health_comp = esper.component_for_entity(
                base_entity, HealthComponent)
            base_health_ratio = base_health_comp.currentHealth / base_health_comp.maxHealth

            enemy_base_health_ratio = 1.0
            enemy_team_id = 1 if ai_team_id == 2 else 2
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == enemy_team_id:
                    enemy_base_health_comp = esper.component_for_entity(
                        ent, HealthComponent)
                    enemy_base_health_ratio = enemy_base_health_comp.currentHealth / \
                        enemy_base_health_comp.maxHealth
                    break

            allied_units = 0
            enemy_units = 0
            allied_health_total = 0.0
            allied_health_count = 0

            for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
                if esper.has_component(ent, BaseComponent) or esper.has_component(ent, TowerComponent):
                    continue
                if esper.has_component(ent, ProjectileComponent):
                    continue

                if team_comp.team_id == ai_team_id:
                    allied_units += 1
                    # collecter santé moyenne des unités alliées (exclure la base/tours)
                    try:
                        if hasattr(health_comp, 'currentHealth') and hasattr(health_comp, 'maxHealth') and health_comp.maxHealth > 0:
                            allied_health_total += (health_comp.currentHealth / health_comp.maxHealth)
                            allied_health_count += 1
                    except Exception:
                        pass
                elif team_comp.team_id != 0:
                    enemy_units += 1

            # Déterminer si la base ennemie est connue via le registry central
            try:
                enemy_base_known = 1 if enemy_base_registry.is_enemy_base_known(ai_team_id) else 0
            except Exception:
                # fallback: considérer connue (ancienne logique) pour compatibilité
                enemy_base_known = 1
            towers_needed = 1 if base_health_ratio < 0.6 else 0

            gold = 0
            for ent, (player_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    gold = player_comp.get_gold()
                    break

            return {
                'gold': gold,
                'base_health_ratio': base_health_ratio,
                'allied_units': allied_units,
                'enemy_units': enemy_units,
                'enemy_base_known': enemy_base_known,
                'towers_needed': towers_needed,
                'enemy_base_health_ratio': enemy_base_health_ratio,
                # santé moyenne (0.0 - 1.0) des unités alliées; 1.0 si aucune unité
                'allied_units_health': (allied_health_total / allied_health_count) if allied_health_count > 0 else 1.0
            }

        except Exception as e:
            print(f"Erreur dans _get_current_game_state: {e}")
            return None

    def _decide_action(self, game_state):
        """Décide de l'action à prendre basée sur l'état du jeu."""
        if self.model is None:
            return 0 # Ne rien faire si aucun modèle n'est chargé

        features = [
            game_state['gold'],
            game_state['base_health_ratio'],
            game_state['allied_units'],
            game_state['enemy_units'],
            game_state['enemy_base_known'],
            game_state['towers_needed'],
            game_state['enemy_base_health_ratio']
        ]

        try:
            # Calculer Q pour chaque action
            q_values = []
            for action in range(7):
                # include allied_units_health feature (model trained with 9 features before action)
                allied_health = game_state.get('allied_units_health', 1.0)
                state_action = features + [allied_health, action]
                q_value = self.model.predict([state_action])[0]
                q_values.append(q_value)

            # Filtrer les actions possibles en fonction de l'or disponible
            affordable_actions = [
                action for action, details in self.ACTION_MAPPING.items()
                if game_state['gold'] >= details['cost'] + details['reserve']
            ]
            
            if not affordable_actions:
                return 0

            # Choisir la meilleure action parmi celles qui sont abordables
            best_action = max(affordable_actions, key=lambda a: q_values[a])
            return int(best_action)

        except Exception as e:
            print(f"Erreur dans _decide_action: {e}")
            return 0

    def _execute_action(self, action, ai_team_id: int):
        """Exécute l'action décidée."""
        try:
            base_entity = None
            for ent, (base_comp, team_comp) in esper.get_components(BaseComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    base_entity = ent
                    break

            if base_entity is None:
                return False

            gold = 0
            player_entity = None
            player_comp = None
            for ent, (p_comp, team_comp) in esper.get_components(PlayerComponent, TeamComponent):
                if team_comp.team_id == ai_team_id:
                    gold = p_comp.get_gold()
                    player_entity = ent
                    player_comp = p_comp
                    break

            if player_comp is None:
                return False

            # Action 0: Ne rien faire
            if action == 0:
                return True

            action_details = self.ACTION_MAPPING.get(action)
            if not action_details or not action_details["unit_type"]:
                return False

            unit_to_spawn = action_details["unit_type"]
            cost = action_details["cost"]
            
            if player_comp.can_afford(cost):
                if player_comp.spend_gold(cost):
                    try:
                        self._spawn_unit(unit_to_spawn, ai_team_id)
                    except Exception as e:
                        print(f"Erreur lors du spawn unit: {e}")
                    self.action_cooldown = 8.0
                    return True
                else:
                    return False

            return True

        except Exception as e:
            print(f"Erreur dans _execute_action: {e}")
            return False

    def _spawn_unit(self, unit_type: UnitType, ai_team_id: int):
        """Fait apparaître une unité depuis la base."""
        try:
            is_enemy = (ai_team_id == Team.ENEMY)
            spawn_x, spawn_y = BaseComponent.get_spawn_position(
                is_enemy=is_enemy)
            pos = PositionComponent(spawn_x, spawn_y, 0)
            new_entity = UnitFactory(unit_type, is_enemy, pos)

            if new_entity is not None:
                BaseComponent.add_unit_to_base(new_entity, is_enemy=is_enemy)

        except Exception as e:
            print(f"Erreur dans _spawn_unit: {e}")
