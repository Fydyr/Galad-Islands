"""Processor managing knowledge of enemy bases.

This processor stores, for each team, whether it knows the position of the opposing
base and provides a simple API (declare_enemy_base/is_enemy_base_known/get_enemy_base_position)
accessible by other systems/AI. A singleton instance `enemy_base_registry`
is exposed to the module for direct access.
"""
from typing import Optional, Tuple
import threading
import esper


class KnownBaseProcessor(esper.Processor):
    """Lightweight processor that maintains a thread-safe registry of known enemy bases.

    The mapping keys are team_ids (int) representing the client team that knows
    the information. The value contains 'known', 'pos' and 'enemy_team'.
    """

    def __init__(self):
        super().__init__()
        self._data = {}
        self._lock = threading.Lock()
        # Debug flag to display discoveries when enabled
        self.debug = False

    def declare_enemy_base(self, discover_team_id: int, enemy_team_id: int, x: float, y: float):
        """Declares that `discover_team_id` has discovered the base of `enemy_team_id` at (x,y)."""
        with self._lock:
            prev = self._data.get(discover_team_id)
            prev_pos = prev.get('pos') if prev else None
            new_pos = (x, y)
            changed = (prev_pos != new_pos)
            self._data[discover_team_id] = {'known': True, 'pos': new_pos, 'enemy_team': enemy_team_id}

        if self.debug:
            if prev is None:
                print(f"[KNOWN_BASE] team {discover_team_id} DISCOVERED the enemy base (team {enemy_team_id}) at {new_pos}")
            elif changed:
                print(f"[KNOWN_BASE] team {discover_team_id} UPDATED the enemy base position -> {new_pos} (previous {prev_pos})")
            else:
                print(f"[KNOWN_BASE] team {discover_team_id} already had the enemy base at {new_pos}")

    def is_enemy_base_known(self, team_id: int) -> bool:
        with self._lock:
            v = self._data.get(team_id)
            return bool(v and v.get('known', False))

    def get_enemy_base_position(self, team_id: int) -> Optional[Tuple[float, float]]:
        with self._lock:
            v = self._data.get(team_id)
            if v and v.get('known', False):
                return v.get('pos')
            return None

    def set_debug(self, enabled: bool):
        """Enables/disables debug for this processor."""
        self.debug = bool(enabled)

    def process(self, *args, **kwargs):
        """Process method required by esper.Processor.

        This processor has no periodic logic; we expose a no-op method
        to satisfy the esper API and avoid NotImplementedError during
        the global `es.process(...)` call.
        """
        # No periodic work required for the registry
        return


# Global instance ready to be imported
enemy_base_registry = KnownBaseProcessor()
