# src/components/core/steeringComponent.py
from dataclasses import dataclass, field
import numpy as np

@dataclass
class SteeringComponent:
    """Stocke les informations de pilotage pour un mouvement lissé."""
    # Stocke le vecteur de vélocité de la frame précédente pour le lissage.
    last_velocity_vector: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0]))
