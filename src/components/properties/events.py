from dataclasses import dataclass as component

@component
class Events:
    tempete: bool = False
    vague_bandits: bool = False
    kraken: bool = False
    coffre_volant: bool = False