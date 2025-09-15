from dataclasses import dataclass as component
from typing import Dict, Optional, Callable
import numpy as np

@component
class TroopUnit:
    """
    Définit les caractéristiques d'un type d'unité militaire.
    
    Attributs:
        unit_type: Type d'unité 
        cost: Coût de production de l'unité
        speed: Vitesse de déplacement
        damage: Dégâts infligés par attaque
        armor: Points d'armure
        action_range: Rayon d'action pour les attaques/capacités
        reload_delay: Délai entre deux attaques (en secondes)
        special_ability: Nom de la capacité spéciale
        ability_cooldown: Délai de rechargement de la capacité (en secondes)
        ability_function: Fonction de la capacité spéciale
    """
    unit_type: str
    cost: int
    speed: float
    damage: int
    armor: int
    action_range: float
    reload_delay: float
    special_ability: str
    ability_cooldown: float
    ability_function: Optional[Callable] = None

@component
class Troops:
    """
    Composant représentant les troupes d'une entité avec système d'unités détaillé.
    
    Attributs:
        unit_counts: Dictionnaire {type_unité: nombre} des unités possédées
        max_troops: Nombre maximum total de troupes
        troop_production_rate: Taux de production par unité de temps
        available_unit_types: Types d'unités que l'entité peut produire
        unit_definitions: Définitions des caractéristiques par type d'unité
        ability_cooldowns: Temps restant avant réutilisation des capacités par unité
    """
    unit_counts: Dict[str, int]
    max_troops: int = 0
    troop_production_rate: float = 0.0
    available_unit_types: list = None
    unit_definitions: Dict[str, TroopUnit] = None
    ability_cooldowns: Dict[str, np.ndarray] = None
    
    def __post_init__(self):
        """Initialise les structures de données par défaut."""
        if self.unit_counts is None:
            self.unit_counts = {}
        if self.available_unit_types is None:
            self.available_unit_types = []
        if self.unit_definitions is None:
            self.unit_definitions = {}
        if self.ability_cooldowns is None:
            self.ability_cooldowns = {}
    
    @property
    def total_troops(self) -> int:
        """Calcule le nombre total de troupes."""
        return sum(self.unit_counts.values())
    
    def get_unit_stats(self, unit_type: str) -> Optional[TroopUnit]:
        """
        Récupère les statistiques d'un type d'unité.
        
        Args:
            unit_type: Type d'unité à consulter
            
        Returns:
            TroopUnit correspondant ou None si inexistant
        """
        return self.unit_definitions.get(unit_type)
    
    def calculate_total_cost(self) -> int:
        """
        Calcule le coût total de toutes les troupes possédées.
        
        Returns:
            Coût total en ressources
        """
        if not self.unit_definitions:
            return 0
            
        unit_types = np.array(list(self.unit_counts.keys()))
        unit_quantities = np.array(list(self.unit_counts.values()))
        unit_costs = np.array([self.unit_definitions[unit_type].cost 
                              for unit_type in unit_types])
        
        return int(np.sum(unit_quantities * unit_costs))
    
    def update_ability_cooldowns(self, delta_time: float) -> None:
        """
        Met à jour les délais de rechargement des capacités spéciales.
        
        Args:
            delta_time: Temps écoulé depuis la dernière mise à jour (en secondes)
        """
        for unit_type in self.ability_cooldowns:
            # Utilisation vectorisée pour optimiser les performances
            self.ability_cooldowns[unit_type] = np.maximum(
                0.0, 
                self.ability_cooldowns[unit_type] - delta_time
            )
    
    def can_use_ability(self, unit_type: str, unit_index: int) -> bool:
        """
        Vérifie si une unité peut utiliser sa capacité spéciale.
        
        Args:
            unit_type: Type d'unité
            unit_index: Index de l'unité spécifique
            
        Returns:
            True si la capacité est disponible
        """
        if unit_type not in self.ability_cooldowns:
            return False
        if unit_index >= len(self.ability_cooldowns[unit_type]):
            return False
        return self.ability_cooldowns[unit_type][unit_index] <= 0.0
    
    def trigger_ability(self, unit_type: str, unit_index: int) -> bool:
        """
        Déclenche la capacité spéciale d'une unité.
        
        Args:
            unit_type: Type d'unité
            unit_index: Index de l'unité spécifique
            
        Returns:
            True si la capacité a été déclenchée avec succès
        """
        if not self.can_use_ability(unit_type, unit_index):
            return False
            
        unit_def = self.get_unit_stats(unit_type)
        if not unit_def or not unit_def.ability_function:
            return False
        
        # Déclenche la capacité et démarre le cooldown
        unit_def.ability_function()
        self.ability_cooldowns[unit_type][unit_index] = unit_def.ability_cooldown
        return True