"""Processor gérant la connaissance des bases ennemies.

Ce processeur stocke, pour chaque équipe, si elle connaît la position de la base
adverse et fournit une API simple (declare_enemy_base/is_enemy_base_known/get_enemy_base_position)
consultable par les autres systèmes/IA. an instance singleton `enemy_base_registry`
est exposée au module pour accès direct.
"""
from typing import Optional, Tuple
import threading
import esper


class KnownBaseProcessor(esper.Processor):
    """Processor léger qui maintient un registre thread-safe des bases ennemies connues.

    Les clés du mapping sont des team_id (int) représentant l'équipe cliente qui connaît
    l'information. La valeur contient 'known', 'pos' et 'enemy_team'.
    """

    def __init__(self):
        super().__init__()
        self._data = {}
        self._lock = threading.Lock()
        # Flag debug pour afficher les découvertes quand activé
        self.debug = False

    def declare_enemy_base(self, discover_team_id: int, enemy_team_id: int, x: float, y: float):
        """Déclare que `discover_team_id` a découvert la base de `enemy_team_id` en (x,y)."""
        with self._lock:
            prev = self._data.get(discover_team_id)
            prev_pos = prev.get('pos') if prev else None
            new_pos = (x, y)
            changed = (prev_pos != new_pos)
            self._data[discover_team_id] = {'known': True, 'pos': new_pos, 'enemy_team': enemy_team_id}

        if self.debug:
            if prev is None:
                print(f"[KNOWN_BASE] team {discover_team_id} a DECOUVERT la base ennemie (team {enemy_team_id}) en {new_pos}")
            elif changed:
                print(f"[KNOWN_BASE] team {discover_team_id} a MIS A JOUR la position de la base ennemie -> {new_pos} (ancienne {prev_pos})")
            else:
                print(f"[KNOWN_BASE] team {discover_team_id} avait déjà la base ennemie à {new_pos}")

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
        """Active/désactive le debug pour ce processeur."""
        self.debug = bool(enabled)

    def process(self, *args, **kwargs):
        """Méthode process requise par esper.Processor.

        Ce processeur n'a pas de logique périodique; on expose une méthode no-op
        pour satisfaire l'API d'esper et avoid NotImplementedError lors de
        l'appel global `es.process(...)`.
        """
        # No periodic work required for the registry
        return


# Instance globale prête à être importée
enemy_base_registry = KnownBaseProcessor()
