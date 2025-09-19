from dataclasses import dataclass as component

@component
class ClasseComponent:
    
    def __init__(self, class_id=0, sprite_path=""):
        self.class_id: int = 0  # ID de la classe (0: Zasper, 1: Barhamus...)
        self.sprite_path: str = ""  # Chemin du sprite associé à la classe

    def assign_sprite(self, class_id: int, sprite_dict: dict):
        """
        Attribue le sprite à la classe selon l'ID
        sprite_dict: dictionnaire {id: chemin_sprite}
        """
        self.class_id = class_id
        self.sprite_path = sprite_dict.get(class_id, "")