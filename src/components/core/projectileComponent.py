from dataclasses import dataclass as component

@component
class ProjectileComponent:
    """
    Composant pour identifier les projectiles dans le système ECS.
    
    Utilisé pour appliquer des règles spécifiques aux projectiles
    comme la suppression automatique aux limites de la carte.
    """
    def __init__(self, projectile_type: str = "bullet"):
        """
        Args:
            projectile_type (str): Type de projectile ("bullet", "missile", "magic", etc.)
        """
        self.projectile_type: str = projectile_type
        self.hit_entities: set = set()  # Ensemble des IDs d'entités déjà touchées