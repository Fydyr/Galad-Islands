from dataclasses import dataclass as component


@component
class ClasseComponent:
    """Métadonnées simples associées à une unit contrôlable."""

    def __init__(self, unit_type: str, shop_id: str, display_name: str, is_enemy: bool = False):
        self.unit_type: str = unit_type
        self.shop_id: str = shop_id
        self.display_name: str = display_name
        self.is_enemy: bool = is_enemy
