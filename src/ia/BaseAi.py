"""
IA de la base utilisant un modèle de Machine Learning pré-entraîné.
Ce processeur charge un modèle et l'utilise pour prendre des décisions stratégiques,
comme la production d'units.

Note sur l'économie: un revenu passif minimal peut être accordé par
`PassiveIncomeProcessor` lorsque l'équipe n'a plus d'unités. Ce mécanisme
ne sert qu'à débloquer le jeu. L'IA en tient compte en priorisant la
création d'un Éclaireur dès que possible et en raccourcissant son délai
de décision lorsqu'elle attend ce revenu passif.
"""

import esper
import random
import numpy as np
import joblib
import os
import time
import sys

from src.components.core.baseComponent import BaseComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.classeComponent import ClasseComponent
from src.components.core.towerComponent import TowerComponent
from src.components.core.projectileComponent import ProjectileComponent
from src.components.core.aiEnabledComponent import AIEnabledComponent
from src.constants.gameplay import UNIT_COSTS
from src.factory.unitFactory import UnitFactory
from src.factory.unitType import UnitType, UnitKey
from src.components.core.positionComponent import PositionComponent
from src.constants.team import Team
from src.settings.settings import config_manager
from src.processeurs.KnownBaseProcessor import enemy_base_registry
from src.functions.resource_path import get_resource_path


def _get_app_data_path() -> str:
    """Chemin de données utilisateur pour la version compilée.

    Windows: %APPDATA%/GaladIslands
    Linux/macOS: ~/.local/share/GaladIslands
    Dev: retourne le dossier src/models du repo
    """
    app_name = "GaladIslands"
    if getattr(sys, 'frozen', False):
        if os.name == 'nt':
            path = os.path.join(os.environ.get('APPDATA', ''), app_name)
        else:
            path = os.path.join(os.path.expanduser('~'), '.local', 'share', app_name)
        os.makedirs(path, exist_ok=True)
        return path
    # En dev, utiliser le dossier du projet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))


class BaseAi(esper.Processor):
    """
    IA de la base utilisant un arbre de décision.

    Cette classe est un processeur ECS qui agit comme le cerveau stratégique pour une équipe.
    Elle charge un modèle `scikit-learn` pré-entraîné pour décider quelle unit produire.

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

    # Limites d'unités de support pour éviter le spam
    MAX_ARCHITECTS = 5  # Maximum 5 Architects simultanés
    # MAX_DRUIDS est calculé dynamiquement : 1 Druide par 5 unités (minimum 1, maximum 4)

    def __init__(self, team_id=2):
        self.default_team_id = team_id
        self.gold_reserve = 50
        self.action_cooldown = 8.0
        self.last_action_time = 0
        self.last_decision_time = time.time()
        self.enabled = True
        self.model = None
        self.active_player_team_id = 1  # By default allié
        self.self_play_mode = False
        self.load_model()
        # Activer les logs de l'IA si le mode développeur est activé
        self.debug_mode = config_manager.get('dev_mode', False)

    def load_model(self):
        """Charge le modèle de décision pré-entraîné (robuste dev/compilé)."""
        candidates = []
        # 1) Dossier données utilisateur (priorité pour permettre override par l'utilisateur)
        user_dir = _get_app_data_path()
        candidates.append(os.path.join(user_dir, 'base_ai_unified_final.pkl'))
        # 2) Ressource packagée avec PyInstaller (ou à côté de l'exécutable)
        # Packagé par PyInstaller via --add-data "src/models:models"
        candidates.append(get_resource_path(os.path.join('models', 'base_ai_unified_final.pkl')))
        candidates.append(get_resource_path(os.path.join('src', 'models', 'base_ai_unified_final.pkl')))
        # 3) Chemin dev relatif (repo)
        candidates.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'base_ai_unified_final.pkl')))

        for path in candidates:
            try:
                if os.path.exists(path):
                    self.model = joblib.load(path)
                    print(f"🤖 Modèle IA chargé pour l'équipe {self.default_team_id} depuis: {path}")
                    return
            except Exception as e:
                print(f"❌ Erreur lors du chargement du modèle IA ({path}): {e}")
                self.model = None
                return

        print("❌ Modèle IA non trouvé. L'IA de la base sera inactive.")
        self.model = None

    def process(self, dt: float = 0.016, active_player_team_id=None):
        """Exécute la logique de l'IA de la base à chaque frame."""
        if not getattr(self, 'enabled', True):
            return

        # Vérifier si l'entité de la base a AIEnabledComponent et si l'IA est activée
        base_entity = None
        if self.default_team_id == 1:  # Team.ALLY
            base_entity = BaseComponent._ally_base_entity
        elif self.default_team_id == 2:  # Team.ENEMY
            base_entity = BaseComponent._enemy_base_entity
        
        if base_entity is not None and esper.has_component(base_entity, AIEnabledComponent):
            ai_component = esper.component_for_entity(base_entity, AIEnabledComponent)
            if not ai_component.enabled:
                return

        # Utiliser l'attribut si le paramètre n'est pas passé
        if active_player_team_id is None:
            active_player_team_id = getattr(self, 'active_player_team_id', 1)

        # En mode IA vs IA, toujours autoriser l'IA
        # En mode Joueur vs IA, l'IA est contrôlée par AIEnabledComponent uniquement
        # (le joueur peut activer/désactiver l'IA de sa propre base avec le bouton Auto)
        # La vérification de AIEnabledComponent.enabled a déjà été faite ci-dessus

        self.last_action_time += dt
        if self.last_action_time < self.action_cooldown:
            return

        game_state = self._get_current_game_state(self.default_team_id)
        if game_state is None:
            return

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
        """Récupère l'état actuel of the game to la prise de décision."""
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
            allied_architects = 0
            allied_druids = 0

            for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
                if esper.has_component(ent, BaseComponent) or esper.has_component(ent, TowerComponent):
                    continue
                if esper.has_component(ent, ProjectileComponent):
                    continue

                if team_comp.team_id == ai_team_id:
                    allied_units += 1
                    # Compter les architectes et druides alliés
                    try:
                        if esper.has_component(ent, ClasseComponent):
                            classe = esper.component_for_entity(ent, ClasseComponent)
                            unit_type = getattr(classe, 'unit_type', None)
                            if unit_type == UnitType.ARCHITECT:
                                allied_architects += 1
                            elif unit_type == UnitType.DRUID:
                                allied_druids += 1
                    except Exception:
                        pass
                    # collecter santé moyenne des units alliées (exclure la base/tours)
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
                # santé moyenne (0.0 - 1.0) des units alliées; 1.0 si aucune unit
                'allied_units_health': (allied_health_total / allied_health_count) if allied_health_count > 0 else 1.0,
                # nombre d'architectes et druides alliés actifs
                'ally_architects': allied_architects,
                'ally_druids': allied_druids,
            }

        except Exception as e:
            print(f"Erreur dans _get_current_game_state: {e}")
            return None

    def _decide_action(self, game_state):
        """Décide de l'action à prendre basée sur l'état du jeu."""
        if self.model is None:
            return 0 # Ne rien faire si aucun modèle n'est chargé

        # Le modèle est entraîné avec 9 caractéristiques (état + action)
        features = [
            game_state['gold'],
            game_state['base_health_ratio'],
            game_state['allied_units'],
            game_state['enemy_units'],
            game_state['enemy_base_known'],
            game_state['towers_needed'],
            game_state['enemy_base_health_ratio'],
            game_state.get('allied_units_health', 1.0) # add de la santé moyenne des alliés
        ]

        try:
            # Compter le nombre de Scouts alliés
            scout_count = 0
            ai_team_id = self.default_team_id
            for ent, (team_comp, health_comp) in esper.get_components(TeamComponent, HealthComponent):
                if team_comp.team_id == ai_team_id:
                    try:
                        if esper.has_component(ent, ClasseComponent):
                            classe = esper.component_for_entity(ent, ClasseComponent)
                            unit_type = getattr(classe, 'unit_type', None)
                            if unit_type == UnitType.SCOUT:
                                scout_count += 1
                    except Exception:
                        pass

            # Calculer Q pour chaque action
            q_values = []
            for action in range(7):
                state_action = features + [action]
                q_value = self.model.predict([state_action])[0]
                # Bonus pour le Scout si la base ennemie n'est pas connue
                if action == 1 and game_state['enemy_base_known'] == 0:
                    q_value += 10.0
                q_values.append(q_value)

            # Heuristiques légères pour corriger des cas stratégiques fréquents
            base_hp = game_state.get('base_health_ratio', 1.0)
            towers_needed = game_state.get('towers_needed', 0)
            ally_architects = game_state.get('ally_architects', 0)
            ally_druids = game_state.get('ally_druids', 0)
            allies = game_state.get('allied_units', 0)
            enemies = game_state.get('enemy_units', 0)
            avg_ally_hp = game_state.get('allied_units_health', 1.0)
            gold = game_state.get('gold', 0)
            enemy_base_hp = game_state.get('enemy_base_health_ratio', 1.0)

            # Bootstrapping: si aucune unité et assez d'or pour un Scout, prioriser l'exploration
            scout_total_cost = self.ACTION_MAPPING[1]['cost'] + self.ACTION_MAPPING[1]['reserve']
            if allies == 0:
                if gold >= scout_total_cost:
                    return 1
                else:
                    # Attendre le revenu passif pour débloquer la partie (ne rien faire, mais décider plus souvent)
                    # Ce comportement s'appuie sur PassiveIncomeProcessor
                    # pour remonter graduellement l'or jusqu'au coût d'un scout.
                    self.action_cooldown = 2.5  # accélérer la cadence des décisions pendant l'attente
                    if self.debug_mode:
                        print(f"[BaseAI] Team {self.default_team_id}: en attente du revenu passif (or={gold}/{scout_total_cost}) pour produire un Éclaireur.")
                    return 0

            # CALCUL DYNAMIQUE : Limite de Druides proportionnelle au nombre d'unités
            # Formule : 1 Druide par 5 unités de combat (minimum 1, maximum 4)
            # Exemples : 0-4 unités = 1 Druide max, 5-9 unités = 2 Druides max, 10-14 = 3, 15-19 = 4, 20+ = 4
            max_druids_allowed = max(1, min(4, (allies // 5) + 1))

            # LIMITES D'UNITÉS DE SUPPORT : Pénaliser fortement si limite atteinte
            if ally_architects >= self.MAX_ARCHITECTS:
                q_values[2] -= 1000.0  # Bloquer complètement les Architects si limite atteinte
            if ally_druids >= max_druids_allowed:
                q_values[5] -= 1000.0  # Bloquer complètement les Druides si limite atteinte

            # Si des tours sont nécessaires et peu d'architectes présents, encourager Architecte
            # MAIS uniquement si la limite n'est pas atteinte
            if towers_needed == 1 and ally_architects < self.MAX_ARCHITECTS:
                if ally_architects == 0:
                    q_values[2] += 50.0  # Bonus massif pour le premier Architecte
                else:
                    q_values[2] += 20.0  # Bonus modéré pour un second Architecte
                q_values[6] -= 15.0  # Kamikaze moins pertinent en défense
                q_values[3] += 2.0   # Maraudeur légèrement utile mais pas prioritaire

            # Si les unités alliées sont très blessées, prioriser Druide (si limite non atteinte)
            if avg_ally_hp < 0.5 and allies > 3 and ally_druids < max_druids_allowed:
                q_values[5] += 15.0  # Druide (augmenté de 12 à 15)

            # Défense prioritaire: base très endommagée ET forte infériorité numérique
            # -> Préférer Maraudeur (défensif) plutôt que Kamikaze (offensif)
            if base_hp < 0.4 and enemies > allies + 2:
                q_values[3] += 40.0  # Maraudeur pour défense robuste (augmenté de 25 à 40)
                q_values[6] -= 20.0  # Kamikaze fortement pénalisé en défense pure (augmenté de 5 à 20)

            # Coup de grâce ou pression rapide avec base ennemie affaiblie
            if enemy_base_hp < 0.3:
                q_values[6] += 15.0  # Kamikaze pour finir rapidement
                
            # Pression rapide à faible/moyen or quand on est en infériorité légère: favoriser Kamikaze
            # MAIS uniquement si notre base n'est PAS critique
            if towers_needed == 0 and base_hp > 0.5 and enemies > allies and gold >= self.ACTION_MAPPING[6]['cost'] + self.ACTION_MAPPING[6]['reserve']:
                q_values[6] += 12.0  # Kamikaze (augmenté de 8 à 12)
                q_values[1] -= 5.0   # Réduire Scout dans ce contexte

            # Filtrer les actions possibles en fonction de l'or disponible
            affordable_actions = [
                action
                for action, details in self.ACTION_MAPPING.items()
                if game_state['gold'] >= details['cost'] + details['reserve']
            ]

            # Limite de Scouts IA base : 4 au début, 6 si la base ennemie est découverte
            scout_limit = 6 if game_state['enemy_base_known'] else 4
            if scout_count >= scout_limit:
                # Si la limite est atteinte, on ne propose pas l'action Scout
                affordable_actions = [a for a in affordable_actions if a != 1]
            # Exclure certaines actions si la base ennemie n'est pas connue
            if game_state['enemy_base_known'] == 0:
                # Bloquer Kamikaze (6) et Léviathan (4) si la base ennemie n'est pas découverte
                # Si Léviathan était abordable mais bloqué, favoriser un fallback Maraudeur
                if 4 in affordable_actions and (game_state['gold'] >= self.ACTION_MAPPING[3]['cost'] + self.ACTION_MAPPING[3]['reserve']):
                    # Petit coup de pouce au Maraudeur comme alternative raisonnable
                    q_values[3] += 8.0
                affordable_actions = [a for a in affordable_actions if a not in (4, 6)]

            if not affordable_actions:
                return 0

            # Si l'action la plus haute est Scout mais la limite est atteinte, faire rien
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

    def _spawn_unit(self, unit_type: UnitKey, ai_team_id: int):
        """Fait apparaître une unit from la base."""
        try:
            base_pos_comp = None
            for ent, (base_comp, team_comp, pos_comp) in esper.get_components(BaseComponent, TeamComponent, PositionComponent):
                if team_comp.team_id == ai_team_id:
                    base_pos_comp = pos_comp
                    break
            
            if base_pos_comp is None: return

            is_enemy = (ai_team_id == Team.ENEMY)
            spawn_x, spawn_y = BaseComponent.get_spawn_position(base_pos_comp.x, base_pos_comp.y, is_enemy=is_enemy)
            pos = PositionComponent(spawn_x, spawn_y, 0)
            new_entity = UnitFactory(unit_type, is_enemy, pos, enable_ai=True, self_play_mode=self.self_play_mode, active_team_id=self.active_player_team_id)

            if new_entity is not None:
                BaseComponent.add_unit_to_base(new_entity, is_enemy=is_enemy)

        except Exception as e:
            print(f"Erreur dans _spawn_unit: {e}")
