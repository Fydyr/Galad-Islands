"""FSM state primitives used by the rapid troop AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from src.ia.ia_scout.services.context import UnitContext


class State(Protocol):
    """Interface every AI state must comply with."""

    name: str

    def enter(self, context: "UnitContext") -> None:
        """Called once when the state is entered."""

    def update(self, dt: float, context: "UnitContext") -> None:
        """Main update loop executed each frame."""

    def exit(self, context: "UnitContext") -> None:
        """Called when the state is about to be left."""


@dataclass
class BaseState:
    """Convenience base class implementing the boilerplate logic."""

    name: str

    def enter(self, context: "UnitContext") -> None:  # pragma: no cover - default no-op
        context.debug_last_state = self.name

    def update(self, dt: float, context: "UnitContext") -> None:  # pragma: no cover - to override
        raise NotImplementedError("States must override update()")

    def exit(self, context: "UnitContext") -> None:  # pragma: no cover - default no-op
        context.debug_previous_state = self.name


class NullState(BaseState):
    """Sentinel state used when the FSM is not initialised yet."""

    def __init__(self) -> None:
        super().__init__(name="Null")

    def update(self, dt: float, context: "UnitContext") -> None:
        """Remain idle."""
        return None
