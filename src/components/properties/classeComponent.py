from dataclasses import dataclass as component

@component
class ClasseComponent:
    
    def __init__(self, class_id=0):
        self.class_id: int = class_id  # ID de la classe (0: Zasper, 1: Barhamus...)
