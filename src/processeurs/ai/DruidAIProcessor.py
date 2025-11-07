"""
Main processor for AI-controlled units.
This processor:
1.  Observes the world (via _build_game_state).
2.  Asks Minimax to make a decision (via minimax.run_minimax).
3.  Executes the decision (via _execute_action).
4.  Manages A* pathfinding (in process()).
"""

import esper
import math
from typing import Dict, Any, List, Optional, Tuple

# AI component
from src.components.ai.DruidAiComponent import DruidAiComponent

# Core components
from src.components.core.positionComponent import PositionComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.radiusComponent import RadiusComponent
from src.components.core.playerSelectedComponent import PlayerSelectedComponent

# Special components (Druid)
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.isVinedComponent import isVinedComponent

# Algorithms
# Make sure these import paths match your structure
from src.ia.ia_druid.astar.aStarPathfinding import a_star_pathfinding, Grid, PositionPixel
from src.ia.ia_druid.minimax.minimax import run_minimax, AI_DEPTH, GameState


# Type alias for grid (from mapComponent.py)
Grid = List[List[int]]
GameState = Dict[str, Any]  # Type alias for simplified game state

# Constants and Types
from src.constants.gameplay import UNIT_COOLDOWN_DRUID
from src.factory.unitType import UnitType
# Make sure you have a team.py file or a Team enum/class somewhere
# I'm using a numeric value based on unitFactory.py (1=ally, 2=enemy)
# If you have an enum, import it (e.g.: from src.constants.team import Team)
from src.settings.settings import TILE_SIZE

# Druid healing amount
from src.factory.unitType import get_unit_metadata
DRUID_HEAL_AMOUNT = get_unit_metadata(UnitType.DRUID).ally.stats.get("soin", 20)  #


class DruidAIProcessor(esper.Processor):

    def __init__(self, grid: Grid, world):
        self.grid = grid
        self.world = world
        self.pathfinding_service = a_star_pathfinding
        self.minimax_service = run_minimax
        self.debug_timer = 0.0
        self.last_dt = 0.0
        
    def process(self, dt: float, **kwargs):
        self.debug_timer -= dt
        debug_this_frame = False
        if self.debug_timer <= 0.0:
            self.debug_timer = 2.0
            debug_this_frame = True

        for ent, (ai, pos, team, vel, health) in self.world.get_components(
            DruidAiComponent,
            PositionComponent,
            TeamComponent,
            VelocityComponent,
            HealthComponent):
            # Disable AI if unit selected by player
            if self.world.has_component(ent, PlayerSelectedComponent):
                continue
            # Movement handling
            if ai.current_path:
                # code mouvement
                try:
                    next_pos_coords = ai.current_path[0]
                except IndexError:
                    vel.currentSpeed = 0
                    ai.current_path = []
                    ai.current_action = None
                    continue

                dx = next_pos_coords[0] - pos.x
                dy = next_pos_coords[1] - pos.y
                dist = math.hypot(dx, dy)

                if dist < (TILE_SIZE / 2):
                    ai.current_path.pop(0)
                    if not ai.current_path:
                        # print(f"[AI DEBUG 8b] entity {ent} a atteint la fin du chemin.") Moins de spam
                        vel.currentSpeed = 0
                        ai.current_action = None
                        continue
                    else:
                        next_pos_coords = ai.current_path[0]
                        dx = next_pos_coords[0] - pos.x
                        dy = next_pos_coords[1] - pos.y

                angle = math.degrees(math.atan2(pos.y - next_pos_coords[1], pos.x - next_pos_coords[0]))
                pos.direction = angle
                vel.currentSpeed = vel.maxUpSpeed

            ai.think_cooldown_current -= dt
            # --- 2. GESTION DE LA DÉCISION (PÉRIODIQUEMENT) ---
            # L'IA doit pouvoir réévaluer la situation même si une action est en cours (ex: un mouvement)
            # On retire la condition `and ai.current_action is None` mais on garde le cooldown.
            if ai.think_cooldown_current <= 0.0:
                if debug_this_frame:
                    print(f"[AI DEBUG 3] L'entité {ent} commence à RÉFLÉCHIR (action en cours: {ai.current_action}).")

                ai.think_cooldown_current = ai.think_cooldown_max

                game_state = self._build_game_state(ent, ai, pos, team, health)

                if not game_state:
                    # print(f"[AI DEBUG 4] ECHEC _build_game_state pour l'entity {ent}.") Moins de spam
                    continue

                if debug_this_frame: # Afficher l'état seulement all 2s
                    print(f"[AI DEBUG 4] Entité {ent} voit: {len(game_state['allies'])} alliés, {len(game_state['enemies'])} ennemis. Cooldown Special: {game_state['druid']['spec_cooldown']:.2f}")

                best_action, best_score = self.minimax_service(
                    game_state,
                    self.grid,
                    depth=AI_DEPTH,
                    alpha=-math.inf,
                    beta=math.inf,
                    is_maximizing_player=True
                )

                if debug_this_frame: # Afficher décision seulement all 2s
                    print(f"[AI DEBUG 5] Entité {ent} a pris une décision: {best_action} (Score: {best_score:.1f})")

                if best_action:
                    ai.current_action = best_action
                    self._execute_action(ent, ai, pos, best_action)

    def _build_game_state(self, druid_entity: int, ai: DruidAiComponent, druid_pos: PositionComponent, druid_team: TeamComponent, druid_health: HealthComponent) -> Optional[GameState]:
        """Construit un état de jeu simplifié pour Minimax."""
        try:
            spe_druid = esper.component_for_entity(druid_entity, SpeDruid)
            radius = esper.component_for_entity(druid_entity, RadiusComponent)
        except KeyError:
            # print(f"error IA: entity {druid_entity} n'est pas un Druide complet.") Moins de spam
            return None

        # --- DEBUG COOLDOWN ---
        # Lire la valeur actuelle du cooldown in le component SpeDruid
        current_spec_cooldown = getattr(spe_druid, 'cooldown', 999.0) # Lire la valeur réelle
        # --- FIN DEBUG ---

        game_state: GameState = {
            "druid": {
                "id": druid_entity,
                "pos": (druid_pos.x, druid_pos.y),
                "health": druid_health.currentHealth,
                "max_health": druid_health.maxHealth,
                "heal_cooldown": radius.cooldown,
                # Utiliser la valeur lue pour le debug
                "spec_cooldown": current_spec_cooldown
            },
            "allies": [],
            "enemies": []
        }

        
        for ent, (pos, health, team) in esper.get_components(PositionComponent, HealthComponent, TeamComponent):
            if ent == druid_entity:
                continue

            dist = math.hypot(pos.x - druid_pos.x, pos.y - druid_pos.y)

            if dist > ai.vision_range:
                continue

            entity_data = {
                "id": ent,
                "pos": (pos.x, pos.y),
                "health": health.currentHealth,
                "max_health": health.maxHealth
            }

            if team.team_id == druid_team.team_id:
                game_state["allies"].append(entity_data)

            elif team.team_id != 0:
                is_vined = esper.has_component(ent, isVinedComponent)
                entity_data["is_vined"] = is_vined
                vine_duration = 0.0
                if is_vined:
                    try:
                        vine_comp = esper.component_for_entity(ent, isVinedComponent)
                        vine_duration = vine_comp.remaining_time
                    except KeyError:
                        pass
                entity_data["vine_duration"] = vine_duration
                game_state["enemies"].append(entity_data)


        return game_state

    def _execute_action(self, druid_entity: int, ai: DruidAiComponent, druid_pos_comp: PositionComponent, action: Tuple[str, Any]):
        """Traduit une décision Minimax en commandes de jeu."""

        action_type, target_id = action
        # print(f"[AI DEBUG 6] L'entity {druid_entity} exécute l'action: {action}") Moins de spam

        try:
            if action_type == "HEAL":
                radius = esper.component_for_entity(druid_entity, RadiusComponent)
                target_health = esper.component_for_entity(target_id, HealthComponent)
                target_health.currentHealth = min(target_health.maxHealth, target_health.currentHealth + DRUID_HEAL_AMOUNT)
                radius.cooldown = UNIT_COOLDOWN_DRUID
                ai.current_action = None

            elif action_type == "CAST_IVY":
                target_pos = esper.component_for_entity(target_id, PositionComponent)
                spe_druid = esper.component_for_entity(druid_entity, SpeDruid)
                angle = math.degrees(math.atan2(druid_pos_comp.y - target_pos.y, druid_pos_comp.x - target_pos.x))
                druid_pos_comp.direction = angle
                # --- Check SUPPLÉMENTAIRE ---
                if spe_druid.can_cast_ivy(): # Check une dernière fois before de lancer
                    spe_druid.launch_projectile(druid_entity)
                    print(f"[AI ACTION] Druid {druid_entity} LANCE LIERRE sur {target_id}") # Confirmation
                else:
                    print(f"[AI WARNING] Druid {druid_entity} voulait lancer lierre mais cooldown pas prêt in extremis!")
                # --- FIN Check ---
                ai.current_action = None

            elif action_type in ["MOVE_TO_ALLY", "MOVE_TO_ENEMY", "FLEE"]:
                target_pos_comp = esper.component_for_entity(target_id, PositionComponent)
                start_pos: PositionPixel = (druid_pos_comp.x, druid_pos_comp.y)
                end_pos: PositionPixel = (target_pos_comp.x, target_pos_comp.y)

                if action_type == "FLEE":
                    dx = druid_pos_comp.x - target_pos_comp.x
                    dy = druid_pos_comp.y - target_pos_comp.y
                    dist = math.hypot(dx, dy)
                    if dist == 0: dist = 1.0
                    flee_dist = 10 * TILE_SIZE
                    end_pos = (druid_pos_comp.x + (dx / dist) * flee_dist,
                               druid_pos_comp.y + (dy / dist) * flee_dist)

                path = self.pathfinding_service(self.grid, start_pos, end_pos)

                # print(f"[AI DEBUG 7] Pathfinding demandé. Chemin trouvé de {len(path)} points.") Moins de spam

                if path and len(path) > 1:
                    ai.current_path = path[1:]
                else:
                    # print(f"[AI DEBUG 7b] Pathfinding ÉCHOUÉ ou chemin trop court.") Moins de spam
                    ai.current_action = None # Se remet en mode 'réflexion'

            elif action_type == "WAIT":
                vel = esper.component_for_entity(druid_entity, VelocityComponent)
                vel.currentSpeed = 0
                ai.current_path = []
                ai.current_action = None
        except KeyError:
            # print(f"[AI DEBUG 9] Action {action} ANNULÉE (cible morte ?)") Moins de spam
            ai.current_action = None
            ai.current_path = []