"""
AI Processor Manager - Active/désactive les processeurs IA dynamiquement
Économise du CPU en n'appelant que les processeurs nécessaires
"""

import esper
from typing import Dict, Set, Type, Any


class AIProcessorManager:
    """
    Gère l'activation/désactivation dynamique des processeurs IA.
    Les processeurs ne sont ajoutés que quand les entités correspondantes existent.
    """
    
    def __init__(self, world):
        self.world = world
        
        # Mapping: component_type -> (processor_instance, priority, is_active)
        self.registered_processors: Dict[Type, tuple[Any, int, bool]] = {}
        
        # Compteur d'entités par type de composant
        self.entity_counts: Dict[Type, int] = {}
        
        # Cache pour éviter les checks répétitifs
        self._check_interval = 1.0  # Vérifier toutes les secondes
        self._time_since_check = 0.0
    
    def register_ai_processor(self, component_type: Type, processor: Any, priority: int):
        """
        Enregistre un processeur IA à activer/désactiver dynamiquement.
        
        Args:
            component_type: Type de composant qui déclenche l'activation (ex: DruidAiComponent)
            processor: Instance du processeur
            priority: Priorité esper
        """
        self.registered_processors[component_type] = (processor, priority, False)
        self.entity_counts[component_type] = 0
        
    def update(self, dt: float):
        """
        Met à jour l'état des processeurs (appelé chaque frame).
        Vérifie périodiquement si des processeurs doivent être activés/désactivés.
        """
        self._time_since_check += dt
        
        if self._time_since_check >= self._check_interval:
            self._time_since_check = 0.0
            self._update_processor_states()
    
    def _update_processor_states(self):
        """Vérifie et met à jour l'état de tous les processeurs enregistrés."""
        for component_type, (processor, priority, is_active) in list(self.registered_processors.items()):
            # Compter les entités avec ce composant
            count = sum(1 for _ in esper.get_component(component_type))
            self.entity_counts[component_type] = count
            
            # Activer si entités > 0 et pas déjà actif
            if count > 0 and not is_active:
                self._activate_processor(component_type, processor, priority)
            
            # Désactiver si entités == 0 et actif
            elif count == 0 and is_active:
                self._deactivate_processor(component_type, processor)
    
    def _activate_processor(self, component_type: Type, processor: Any, priority: int):
        """Active un processeur."""
        try:
            esper.add_processor(processor, priority=priority)
            self.registered_processors[component_type] = (processor, priority, True)
            # print(f"✅ AI Processor activé: {processor.__class__.__name__} (priority {priority})")
        except ValueError:
            # Le processeur est déjà ajouté, mettre à jour l'état quand même
            self.registered_processors[component_type] = (processor, priority, True)
    
    def _deactivate_processor(self, component_type: Type, processor: Any):
        """Désactive un processeur."""
        try:
            # esper.remove_processor() ne fonctionne qu'avec les types, pas les instances
            # On manipule directement la liste des processeurs
            if processor in esper._processors:
                esper._processors.remove(processor)
            
            priority = self.registered_processors[component_type][1]
            self.registered_processors[component_type] = (processor, priority, False)
            # print(f"⏸️  AI Processor désactivé: {processor.__class__.__name__}")
        except (ValueError, AttributeError) as e:
            # Le processeur n'est pas dans la liste, mettre à jour l'état quand même
            priority = self.registered_processors[component_type][1]
            self.registered_processors[component_type] = (processor, priority, False)
    
    def force_check(self):
        """Force une vérification immédiate (utile après spawn/delete d'entités)."""
        self._update_processor_states()
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut actuel (debug)."""
        status = {}
        for component_type, (processor, priority, is_active) in self.registered_processors.items():
            status[processor.__class__.__name__] = {
                'active': is_active,
                'entity_count': self.entity_counts.get(component_type, 0),
                'priority': priority
            }
        return status
