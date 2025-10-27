"""Transition primitives used by the AI FSM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Protocol, TYPE_CHECKING

from .state import State

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.ia.ia_scout.services.context import UnitContext


class TransitionCondition(Protocol):
    """Callback returning True when a transition should happen."""

    def __call__(self, dt: float, context: "UnitContext") -> bool:
        ...


@dataclass
class Transition:
    """Association between a condition and a target state."""

    condition: TransitionCondition
    target: State
    priority: int = 0
    name: Optional[str] = None

    def should_trigger(self, dt: float, context: "UnitContext") -> bool:
        try:
            return self.condition(dt, context)
        except Exception:
            return False


def make_condition(predicate: Callable[["UnitContext"], bool]) -> TransitionCondition:
    """Wrap a predicate without dt into a TransitionCondition."""

    def _condition(_: float, context: "UnitContext") -> bool:
        return predicate(context)

    return _condition
