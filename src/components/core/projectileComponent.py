from dataclasses import dataclass as component
from typing import Optional

@component
class ProjectileComponent:
    """
    Composant pour identifier les projectiles dans le système ECS.
    
    Utilisé pour appliquer des règles spécifiques aux projectiles
    comme la suppression automatique aux limites de la carte.
    """
    def __init__(self, projectile_type: str = "bullet", owner_entity: Optional[int] = None):
        """
        Args:
            projectile_type (str): Type de projectile ("bullet", "missile", "magic", etc.)
            owner_entity (int): ID de l'entité qui a tiré le projectile
        """
        self.projectile_type: str = projectile_type
        self.owner_entity: Optional[int] = owner_entity
        self.hit_entities: set = set()  # Ensemble des IDs d'entités déjà touchées