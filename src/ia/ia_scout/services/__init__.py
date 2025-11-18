"""Shared service layer used by the rapid troop AI."""

from .context import AIContextManager, UnitContext
from .danger_map import DangerMapService
from .pathfinding import PathfindingService
from .goals import GoalEvaluator, Objective, TargetInfo
from .event_bus import IAEventBus
from .coordination import CoordinationService
from .exploration import ExplorationPlanner, exploration_planner, exploration_observer

__all__ = [
    "AIContextManager",
    "UnitContext",
    "DangerMapService",
    "PathfindingService",
    "GoalEvaluator",
    "Objective",
    "TargetInfo",
    "IAEventBus",
    "CoordinationService",
    "ExplorationPlanner",
    "exploration_planner",
    "exploration_observer",
]
