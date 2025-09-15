from dataclasses import dataclass as component

@component
class VineComponent:
    time: int = 0
    block: bool = False