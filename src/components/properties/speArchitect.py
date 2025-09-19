from dataclasses import dataclass as component
from typing import List, Dict, Optional, Tuple

@component
class SpeArchitect:
    """
    Composant représentant les capacités spéciales de l'Architect.
    
    Selon GameDesign.md:
    - Rechargement automatique: radius 8 cases
    - Construction de tours de défense/régénération
    - Rechargement: 0 (instantané)
    - Type: Support
    - Doit être sur île pour agir
    """
    # Capacité Rechargement automatique
    auto_reload_available: bool = True
    auto_reload_is_active: bool = False
    auto_reload_radius: float = 8.0  # 8 cases selon GameDesign.md
    auto_reload_boost_factor: float = 2.0  # 2x plus rapide
    auto_reload_mana_cost_per_second: int = 5
    auto_reload_affected_units: List[int] = None
    auto_reload_efficiency: float = 1.0
    
    # Capacité Construction
    construction_available: bool = True
    construction_range: float = 3.0  # Rayon de construction
    max_towers: int = 4  # Maximum 4 tours
    constructed_towers: Dict[Tuple[float, float], str] = None
    construction_queue: List[Dict] = None
    construction_time_remaining: float = 0.0
    
    # Coûts de construction
    defense_tower_cost: int = 40
    healing_tower_cost: int = 35
    defense_tower_construction_time: float = 5.0
    healing_tower_construction_time: float = 4.0
    
    # État de l'Architect
    is_on_island: bool = False
    current_island_id: Optional[int] = None
    mana_points: int = 120
    max_mana: int = 120
    mana_regeneration: float = 8.0  # Mana par seconde
    
    def __post_init__(self):
        """Initialise les structures de données par défaut."""
        if self.auto_reload_affected_units is None:
            self.auto_reload_affected_units = []
        if self.constructed_towers is None:
            self.constructed_towers = {}
        if self.construction_queue is None:
            self.construction_queue = []
    
    def can_activate_auto_reload(self) -> bool:
        """
        Vérifie si le rechargement automatique peut être activé.
        
        Returns:
            True si la capacité peut être activée
        """
        return (self.auto_reload_available and 
                not self.auto_reload_is_active and
                self.is_on_island and
                self.mana_points >= self.auto_reload_mana_cost_per_second)
    
    def can_construct_tower(self, tower_type: str, position: Tuple[float, float]) -> bool:
        """
        Vérifie si une tour peut être construite.
        
        Args:
            tower_type: Type de tour ("defense" ou "healing")
            position: Position de construction
            
        Returns:
            True si la construction est possible
        """
        if not self.is_on_island or not self.construction_available:
            return False
        
        if len(self.constructed_towers) >= self.max_towers:
            return False
        
        if position in self.constructed_towers:
            return False
        
        # Vérification du coût
        tower_cost = (self.defense_tower_cost if tower_type == "defense" 
                     else self.healing_tower_cost)
        return self.mana_points >= tower_cost
    
    def activate_auto_reload(self) -> bool:
        """
        Active la capacité de rechargement automatique.
        
        Returns:
            True si la capacité a été activée
        """
        if not self.can_activate_auto_reload():
            return False
        
        self.auto_reload_is_active = True
        return True
    
    def deactivate_auto_reload(self) -> None:
        """Désactive la capacité de rechargement automatique."""
        self.auto_reload_is_active = False
        self.auto_reload_affected_units.clear()
    
    def start_tower_construction(self, tower_type: str, position: Tuple[float, float]) -> bool:
        """
        Démarre la construction d'une tour.
        
        Args:
            tower_type: Type de tour à construire ("defense" ou "healing")
            position: Position de construction
            
        Returns:
            True si la construction a commencé
        """
        if not self.can_construct_tower(tower_type, position):
            return False
        
        tower_cost = (self.defense_tower_cost if tower_type == "defense" 
                     else self.healing_tower_cost)
        construction_time = (self.defense_tower_construction_time if tower_type == "defense"
                           else self.healing_tower_construction_time)
        
        construction_order = {
            "type": tower_type,
            "position": position,
            "cost": tower_cost,
            "construction_time": construction_time
        }
        
        self.construction_queue.append(construction_order)
        
        # Si c'est la première construction, on la démarre
        if len(self.construction_queue) == 1:
            self.construction_time_remaining = construction_time
            self.mana_points -= tower_cost
        
        return True
    
    def update(self, dt):
        """
        Met à jour les capacités de l'Architect.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        # Régénération du mana
        if self.mana_points < self.max_mana:
            mana_gain = self.mana_regeneration * dt
            self.mana_points = min(self.max_mana, 
                                 self.mana_points + int(mana_gain))
        
        # Mise à jour du rechargement automatique
        if self.auto_reload_is_active:
            mana_cost = self.auto_reload_mana_cost_per_second * dt
            if self.mana_points < mana_cost:
                self.deactivate_auto_reload()
            else:
                self.mana_points -= int(mana_cost)
        
        # Mise à jour de la construction
        self._update_construction(dt)
    
    def _update_construction(self, dt):
        """
        Met à jour le processus de construction.
        
        Args:
            dt: Temps écoulé depuis la dernière frame
        """
        if not self.construction_queue or self.construction_time_remaining <= 0:
            return
        
        self.construction_time_remaining -= dt
        
        if self.construction_time_remaining <= 0:
            # Construction terminée
            completed_tower = self.construction_queue.pop(0)
            self.constructed_towers[completed_tower["position"]] = completed_tower["type"]
            
            # Démarrer la construction suivante si elle existe
            if self.construction_queue:
                next_construction = self.construction_queue[0]
                self.construction_time_remaining = next_construction["construction_time"]
                self.mana_points -= next_construction["cost"]
    
    def get_construction_progress(self) -> float:
        """
        Retourne le progrès de construction actuel.
        
        Returns:
            Pourcentage de completion (0.0 à 1.0)
        """
        if not self.construction_queue:
            return 0.0
        
        current_construction = self.construction_queue[0]
        total_time = current_construction["construction_time"]
        elapsed_time = total_time - self.construction_time_remaining
        
        return min(1.0, elapsed_time / total_time)
    
    def get_tower_count(self) -> Dict[str, int]:
        """
        Retourne le nombre de tours par type.
        
        Returns:
            Dictionnaire {type: count}
        """
        tower_counts = {"defense": 0, "healing": 0}
        for tower_type in self.constructed_towers.values():
            tower_counts[tower_type] += 1
        return tower_counts
    
    def set_island_position(self, island_id: int) -> None:
        """
        Place l'Architect sur une île.
        
        Args:
            island_id: ID de l'île
        """
        self.is_on_island = True
        self.current_island_id = island_id
        self.construction_available = True
    
    def leave_island(self) -> None:
        """Fait quitter l'Architect de l'île."""
        self.is_on_island = False
        self.current_island_id = None
        self.construction_available = False
        self.deactivate_auto_reload()
    
    def update_affected_units(self, nearby_units: List[int]) -> None:
        """
        Met à jour la liste des unités affectées par le rechargement automatique.
        
        Args:
            nearby_units: Liste des IDs des unités à portée
        """
        if self.auto_reload_is_active:
            self.auto_reload_affected_units = nearby_units.copy()
        else:
            self.auto_reload_affected_units.clear()