"""
Interface de communication pour le système d'entités.

Définit les contrats de communication entre le composant entités
et les autres composants du moteur.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import numpy as np
from dataclasses import dataclass


class TypeUnite(Enum):
    """Types d'unités disponibles."""
    ZASPER = "zasper"
    BARHAMUS = "barhamus"
    DRAUPNIR = "draupnir"
    DRUID = "druid"
    ARCHITECT = "architect"


class Faction(Enum):
    """Factions disponibles."""
    AUBE = "aube"
    ABYSSES = "abysses"
    NEUTRE = "neutre"


@dataclass
class DonneesUnite:
    """Données d'une unité pour communication entre composants."""
    id: str
    type_unite: TypeUnite
    faction: Faction
    position: np.ndarray
    vie_actuelle: int
    vie_max: int
    vitesse_max: float
    radius_action: int
    en_vie: bool
    controlable: bool = True


@dataclass
class CommandeUnite:
    """Commande à exécuter par une unité."""
    id_unite: str
    type_commande: str  # "deplacer", "attaquer", "capacite_speciale"
    cible_position: Optional[np.ndarray] = None
    cible_unite_id: Optional[str] = None
    parametres: Optional[Dict[str, Any]] = None


class IEntityInterface(ABC):
    """
    Interface abstraite pour la communication avec le système d'entités.
    
    Cette interface définit tous les contrats que le composant entités
    doit respecter pour communiquer avec les autres composants.
    """
    
    @abstractmethod
    def creer_unite(self, type_unite: TypeUnite, position: np.ndarray, faction: Faction) -> str:
        """
        Crée une nouvelle unité.
        
        Args:
            type_unite: Type d'unité à créer
            position: Position initiale [x, y]
            faction: Faction propriétaire
            
        Returns:
            ID unique de l'unité créée
        """
        pass
    
    @abstractmethod
    def detruire_unite(self, id_unite: str) -> bool:
        """
        Détruit une unité.
        
        Args:
            id_unite: ID de l'unité à détruire
            
        Returns:
            True si l'unité a été détruite, False sinon
        """
        pass
    
    @abstractmethod
    def obtenir_unite(self, id_unite: str) -> Optional[DonneesUnite]:
        """
        Obtient les données d'une unité.
        
        Args:
            id_unite: ID de l'unité
            
        Returns:
            Données de l'unité ou None si non trouvée
        """
        pass
    
    @abstractmethod
    def obtenir_toutes_unites(self, faction: Optional[Faction] = None) -> List[DonneesUnite]:
        """
        Obtient toutes les unités.
        
        Args:
            faction: Faction à filtrer (None pour toutes)
            
        Returns:
            Liste des unités
        """
        pass
    
    @abstractmethod
    def obtenir_unites_dans_zone(self, position: np.ndarray, rayon: float, 
                                faction: Optional[Faction] = None) -> List[DonneesUnite]:
        """
        Obtient les unités dans une zone donnée.
        
        Args:
            position: Centre de la zone [x, y]
            rayon: Rayon de recherche
            faction: Faction à filtrer (None pour toutes)
            
        Returns:
            Liste des unités dans la zone
        """
        pass
    
    @abstractmethod
    def donner_commande(self, commande: CommandeUnite) -> bool:
        """
        Donne une commande à une unité.
        
        Args:
            commande: Commande à exécuter
            
        Returns:
            True si la commande a été acceptée, False sinon
        """
        pass
    
    @abstractmethod
    def infliger_degats(self, id_unite: str, degats: int, source: str = "inconnu") -> bool:
        """
        Inflige des dégâts à une unité.
        
        Args:
            id_unite: ID de l'unité cible
            degats: Quantité de dégâts
            source: Source des dégâts
            
        Returns:
            True si les dégâts ont été infligés, False sinon
        """
        pass
    
    @abstractmethod
    def soigner_unite(self, id_unite: str, soins: int) -> bool:
        """
        Soigne une unité.
        
        Args:
            id_unite: ID de l'unité à soigner
            soins: Quantité de soins
            
        Returns:
            True si l'unité a été soignée, False sinon
        """
        pass
    
    @abstractmethod
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """
        Obtient les statistiques du système d'entités.
        
        Returns:
            Dictionnaire contenant les statistiques
        """
        pass


class EntityInterfaceProxy:
    """
    Proxy pour l'interface entités permettant la communication découplée.
    
    Cette classe agit comme un proxy vers l'implémentation réelle de l'interface entités,
    permettant de changer d'implémentation facilement et de mocker pour les tests.
    """
    
    def __init__(self):
        """Initialise le proxy sans implémentation."""
        self._implementation: Optional[IEntityInterface] = None
    
    def definir_implementation(self, implementation: IEntityInterface) -> None:
        """
        Définit l'implémentation à utiliser.
        
        Args:
            implementation: Implémentation de l'interface entités
        """
        self._implementation = implementation
    
    def _verifier_implementation(self) -> None:
        """Vérifie qu'une implémentation est définie."""
        if self._implementation is None:
            raise RuntimeError("Aucune implémentation définie pour EntityInterface")
    
    def creer_unite(self, type_unite: TypeUnite, position: np.ndarray, faction: Faction) -> str:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.creer_unite(type_unite, position, faction)
    
    def detruire_unite(self, id_unite: str) -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.detruire_unite(id_unite)
    
    def obtenir_unite(self, id_unite: str) -> Optional[DonneesUnite]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_unite(id_unite)
    
    def obtenir_toutes_unites(self, faction: Optional[Faction] = None) -> List[DonneesUnite]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_toutes_unites(faction)
    
    def obtenir_unites_dans_zone(self, position: np.ndarray, rayon: float, 
                                faction: Optional[Faction] = None) -> List[DonneesUnite]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_unites_dans_zone(position, rayon, faction)
    
    def donner_commande(self, commande: CommandeUnite) -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.donner_commande(commande)
    
    def infliger_degats(self, id_unite: str, degats: int, source: str = "inconnu") -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.infliger_degats(id_unite, degats, source)
    
    def soigner_unite(self, id_unite: str, soins: int) -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.soigner_unite(id_unite, soins)
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_statistiques()


# Instance globale du proxy
entity_interface = EntityInterfaceProxy()


# Fonctions utilitaires pour simplifier l'utilisation
def creer_unite(type_unite: TypeUnite, position: Tuple[float, float], faction: Faction) -> str:
    """
    Fonction utilitaire pour créer une unité.
    
    Args:
        type_unite: Type d'unité à créer
        position: Position initiale (x, y)
        faction: Faction propriétaire
        
    Returns:
        ID de l'unité créée
    """
    pos_array = np.array(position, dtype=np.float32)
    return entity_interface.creer_unite(type_unite, pos_array, faction)


def obtenir_unites_ennemies(position: Tuple[float, float], rayon: float, faction_joueur: Faction) -> List[DonneesUnite]:
    """
    Obtient les unités ennemies dans une zone.
    
    Args:
        position: Position centrale (x, y)
        rayon: Rayon de recherche
        faction_joueur: Faction du joueur (pour déterminer les ennemis)
        
    Returns:
        Liste des unités ennemies
    """
    pos_array = np.array(position, dtype=np.float32)
    toutes_unites = entity_interface.obtenir_unites_dans_zone(pos_array, rayon)
    return [unite for unite in toutes_unites if unite.faction != faction_joueur]


def obtenir_unites_alliees(position: Tuple[float, float], rayon: float, faction_joueur: Faction) -> List[DonneesUnite]:
    """
    Obtient les unités alliées dans une zone.
    
    Args:
        position: Position centrale (x, y)
        rayon: Rayon de recherche
        faction_joueur: Faction du joueur
        
    Returns:
        Liste des unités alliées
    """
    pos_array = np.array(position, dtype=np.float32)
    toutes_unites = entity_interface.obtenir_unites_dans_zone(pos_array, rayon)
    return [unite for unite in toutes_unites if unite.faction == faction_joueur]