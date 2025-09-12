"""
Interface de communication pour le moteur de rendu.

Définit les contrats de communication entre le composant rendu
et les autres composants du moteur.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import numpy as np
from dataclasses import dataclass


class TypeRendu(Enum):
    """Types de rendu disponibles."""
    SPRITE = "sprite"
    EFFET = "effet"
    UI = "ui"
    PARTICULE = "particule"
    TEXTE = "texte"


class CoucheRendu(Enum):
    """Couches de rendu (ordre z)."""
    ARRIERE_PLAN = 0
    TERRAIN = 1
    OMBRES = 2
    ENTITES = 3
    PROJECTILES = 4
    EFFETS = 5
    UI_MONDE = 6
    UI_INTERFACE = 7
    DEBUG = 8


@dataclass
class ElementRendu:
    """Élément à rendre par le moteur de rendu."""
    id: str
    type_rendu: TypeRendu
    couche: CoucheRendu
    position: np.ndarray
    sprite_id: Optional[str] = None
    couleur: Optional[Tuple[int, int, int, int]] = None  # RGBA
    taille: Optional[Tuple[float, float]] = None
    rotation: float = 0.0
    visible: bool = True
    donnees_specifiques: Optional[Dict[str, Any]] = None


@dataclass
class ParametresCamera:
    """Paramètres de la caméra."""
    position: np.ndarray
    zoom: float = 1.0
    rotation: float = 0.0
    limites: Optional[Tuple[float, float, float, float]] = None  # x_min, y_min, x_max, y_max


@dataclass
class EffetVisuel:
    """Définition d'un effet visuel."""
    id: str
    type_effet: str  # "explosion", "degats", "soin", etc.
    position: np.ndarray
    duree: float
    parametres: Dict[str, Any]


class IRenderInterface(ABC):
    """
    Interface abstraite pour la communication avec le moteur de rendu.
    
    Cette interface définit tous les contrats que le composant rendu
    doit respecter pour communiquer avec les autres composants.
    """
    
    @abstractmethod
    def ajouter_element(self, element: ElementRendu) -> None:
        """
        Ajoute un élément à rendre.
        
        Args:
            element: Élément à ajouter au rendu
        """
        pass
    
    @abstractmethod
    def supprimer_element(self, id_element: str) -> bool:
        """
        Supprime un élément du rendu.
        
        Args:
            id_element: ID de l'élément à supprimer
            
        Returns:
            True si l'élément a été supprimé, False sinon
        """
        pass
    
    @abstractmethod
    def mettre_a_jour_element(self, id_element: str, **kwargs) -> bool:
        """
        Met à jour un élément existant.
        
        Args:
            id_element: ID de l'élément à mettre à jour
            **kwargs: Propriétés à modifier
            
        Returns:
            True si l'élément a été mis à jour, False sinon
        """
        pass
    
    @abstractmethod
    def definir_camera(self, parametres: ParametresCamera) -> None:
        """
        Définit les paramètres de la caméra.
        
        Args:
            parametres: Nouveaux paramètres de caméra
        """
        pass
    
    @abstractmethod
    def obtenir_camera(self) -> ParametresCamera:
        """
        Obtient les paramètres actuels de la caméra.
        
        Returns:
            Paramètres de la caméra
        """
        pass
    
    @abstractmethod
    def ajouter_effet(self, effet: EffetVisuel) -> None:
        """
        Ajoute un effet visuel.
        
        Args:
            effet: Effet à ajouter
        """
        pass
    
    @abstractmethod
    def charger_sprite(self, id_sprite: str, chemin_fichier: str) -> bool:
        """
        Charge un sprite.
        
        Args:
            id_sprite: ID unique du sprite
            chemin_fichier: Chemin vers le fichier image
            
        Returns:
            True si le chargement a réussi, False sinon
        """
        pass
    
    @abstractmethod
    def convertir_ecran_vers_monde(self, position_ecran: Tuple[int, int]) -> np.ndarray:
        """
        Convertit une position écran en position monde.
        
        Args:
            position_ecran: Position sur l'écran (pixels)
            
        Returns:
            Position dans le monde
        """
        pass
    
    @abstractmethod
    def convertir_monde_vers_ecran(self, position_monde: np.ndarray) -> Tuple[int, int]:
        """
        Convertit une position monde en position écran.
        
        Args:
            position_monde: Position dans le monde
            
        Returns:
            Position sur l'écran (pixels)
        """
        pass
    
    @abstractmethod
    def obtenir_elements_visibles(self) -> List[ElementRendu]:
        """
        Obtient tous les éléments actuellement visibles.
        
        Returns:
            Liste des éléments visibles
        """
        pass
    
    @abstractmethod
    def definir_couleur_fond(self, couleur: Tuple[int, int, int]) -> None:
        """
        Définit la couleur de fond.
        
        Args:
            couleur: Couleur RGB
        """
        pass
    
    @abstractmethod
    def obtenir_fps(self) -> float:
        """
        Obtient le FPS actuel.
        
        Returns:
            FPS actuel
        """
        pass
    
    @abstractmethod
    def obtenir_statistiques_rendu(self) -> Dict[str, Any]:
        """
        Obtient les statistiques de rendu.
        
        Returns:
            Dictionnaire contenant les statistiques
        """
        pass


class RenderInterfaceProxy:
    """
    Proxy pour l'interface de rendu permettant la communication découplée.
    
    Cette classe agit comme un proxy vers l'implémentation réelle de l'interface rendu,
    permettant de changer d'implémentation facilement et de mocker pour les tests.
    """
    
    def __init__(self):
        """Initialise le proxy sans implémentation."""
        self._implementation: Optional[IRenderInterface] = None
    
    def definir_implementation(self, implementation: IRenderInterface) -> None:
        """
        Définit l'implémentation à utiliser.
        
        Args:
            implementation: Implémentation de l'interface rendu
        """
        self._implementation = implementation
    
    def _verifier_implementation(self) -> None:
        """Vérifie qu'une implémentation est définie."""
        if self._implementation is None:
            raise RuntimeError("Aucune implémentation définie pour RenderInterface")
    
    def ajouter_element(self, element: ElementRendu) -> None:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        self._implementation.ajouter_element(element)
    
    def supprimer_element(self, id_element: str) -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.supprimer_element(id_element)
    
    def mettre_a_jour_element(self, id_element: str, **kwargs) -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.mettre_a_jour_element(id_element, **kwargs)
    
    def definir_camera(self, parametres: ParametresCamera) -> None:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        self._implementation.definir_camera(parametres)
    
    def obtenir_camera(self) -> ParametresCamera:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_camera()
    
    def ajouter_effet(self, effet: EffetVisuel) -> None:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        self._implementation.ajouter_effet(effet)
    
    def charger_sprite(self, id_sprite: str, chemin_fichier: str) -> bool:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.charger_sprite(id_sprite, chemin_fichier)
    
    def convertir_ecran_vers_monde(self, position_ecran: Tuple[int, int]) -> np.ndarray:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.convertir_ecran_vers_monde(position_ecran)
    
    def convertir_monde_vers_ecran(self, position_monde: np.ndarray) -> Tuple[int, int]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.convertir_monde_vers_ecran(position_monde)
    
    def obtenir_elements_visibles(self) -> List[ElementRendu]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_elements_visibles()
    
    def definir_couleur_fond(self, couleur: Tuple[int, int, int]) -> None:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        self._implementation.definir_couleur_fond(couleur)
    
    def obtenir_fps(self) -> float:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_fps()
    
    def obtenir_statistiques_rendu(self) -> Dict[str, Any]:
        """Délègue à l'implémentation."""
        self._verifier_implementation()
        return self._implementation.obtenir_statistiques_rendu()


# Instance globale du proxy
render_interface = RenderInterfaceProxy()


# Fonctions utilitaires pour simplifier l'utilisation
def afficher_sprite(id_element: str, sprite_id: str, position: Tuple[float, float], 
                   couche: CoucheRendu = CoucheRendu.ENTITES) -> None:
    """
    Fonction utilitaire pour afficher un sprite.
    
    Args:
        id_element: ID unique de l'élément
        sprite_id: ID du sprite à afficher
        position: Position (x, y)
        couche: Couche de rendu
    """
    element = ElementRendu(
        id=id_element,
        type_rendu=TypeRendu.SPRITE,
        couche=couche,
        position=np.array(position, dtype=np.float32),
        sprite_id=sprite_id
    )
    render_interface.ajouter_element(element)


def afficher_effet_explosion(position: Tuple[float, float], duree: float = 1.0) -> None:
    """
    Fonction utilitaire pour afficher une explosion.
    
    Args:
        position: Position de l'explosion (x, y)
        duree: Durée de l'effet en secondes
    """
    effet = EffetVisuel(
        id=f"explosion_{int(position[0])}_{int(position[1])}",
        type_effet="explosion",
        position=np.array(position, dtype=np.float32),
        duree=duree,
        parametres={"taille": 32, "couleur": (255, 128, 0)}
    )
    render_interface.ajouter_effet(effet)


def deplacer_camera(position: Tuple[float, float], zoom: float = None) -> None:
    """
    Fonction utilitaire pour déplacer la caméra.
    
    Args:
        position: Nouvelle position de la caméra (x, y)
        zoom: Nouveau zoom (optionnel)
    """
    parametres_actuels = render_interface.obtenir_camera()
    nouveaux_parametres = ParametresCamera(
        position=np.array(position, dtype=np.float32),
        zoom=zoom if zoom is not None else parametres_actuels.zoom,
        rotation=parametres_actuels.rotation,
        limites=parametres_actuels.limites
    )
    render_interface.definir_camera(nouveaux_parametres)