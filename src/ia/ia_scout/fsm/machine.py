"""Finite state machine orchestrating the rapid troop AI."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Sequence

from .state import State
from .transition import Transition


class StateMachine:
    """Minimal yet robust FSM implementation with priority based transitions."""

    def __init__(self, initial_state: State):
        self._current: State = initial_state
        self._transitions: Dict[str, List[Transition]] = defaultdict(list)
        self._global_transitions: List[Transition] = []
        self._entered: bool = False

    @property
    def current_state(self) -> State:
        return self._current

    def add_transition(self, source: State, transition: Transition) -> None:
        self._transitions[source.name].append(transition)
        self._sort_transitions(self._transitions[source.name])

    def add_global_transition(self, transition: Transition) -> None:
        self._global_transitions.append(transition)
        self._sort_transitions(self._global_transitions)

    def _sort_transitions(self, transitions: List[Transition]) -> None:
        transitions.sort(key=lambda t: t.priority, reverse=True)

    def _iter_transitions(self) -> Iterable[Transition]:
        yield from self._global_transitions
        yield from self._transitions.get(self._current.name, [])

    def force_state(self, state: State, context) -> None:
        if self._current is state:
            return
        self._current.exit(context)
        self._current = state
        self._current.enter(context)

    def update(self, dt: float, context) -> None:
        if not self._entered:
            self._entered = True
            self._current.enter(context)

        for transition in self._iter_transitions():
            if transition.should_trigger(dt, context):
                self.force_state(transition.target, context)
                # Transition already entered -> update new state once to avoid lag
                self._current.update(dt, context)
                return

        self._current.update(dt, context)
