"""Event bus bridging game signals to the AI modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Deque, Iterable, List, Optional, Protocol
from collections import deque


@dataclass
class IAEvent:
    type: str
    payload: dict


class IAEventListener(Protocol):
    def handle_event(self, event: IAEvent) -> None:
        ...


class IAEventBus:
    """Simple publish/subscribe system dedicated to IA specific events."""

    def __init__(self, history: int = 32) -> None:
        self._listeners: List[IAEventListener] = []
        self._history: Deque[IAEvent] = deque(maxlen=history)

    def subscribe(self, listener: IAEventListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: IAEventListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def publish(self, event_type: str, **payload) -> None:
        event = IAEvent(event_type, payload)
        self._history.append(event)
        for listener in list(self._listeners):
            listener.handle_event(event)

    def last_events(self) -> Iterable[IAEvent]:
        return list(self._history)
