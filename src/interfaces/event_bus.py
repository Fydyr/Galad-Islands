"""
Bus d'événements central pour la communication entre composants.

Ce module implémente un système d'événements découplé permettant
aux différents composants du moteur de communiquer sans dépendances directes.
"""

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from enum import Enum
import threading
import time
from collections import defaultdict


class TypeEvenement(Enum):
    """Types d'événements supportés par le bus."""
    
    # Événements entités
    UNITE_CREEE = "unite_creee"
    UNITE_DETRUITE = "unite_detruite"
    UNITE_DEPLACEE = "unite_deplacee"
    UNITE_ATTAQUE = "unite_attaque"
    
    # Événements combat
    PROJECTILE_TIRE = "projectile_tire"
    DEGATS_INFLIGES = "degats_infliges"
    COLLISION_DETECTEE = "collision_detectee"
    
    # Événements monde
    RESSOURCE_EXTRAITE = "ressource_extraite"
    EVENEMENT_ALEATOIRE = "evenement_aleatoire"
    CARTE_GENEREE = "carte_generee"
    
    # Événements interface
    BOUTON_CLIQUE = "bouton_clique"
    UNITE_SELECTIONNEE = "unite_selectionnee"
    COMMANDE_DONNEE = "commande_donnee"
    
    # Événements système
    JEU_DEMARRE = "jeu_demarre"
    JEU_ARRETE = "jeu_arrete"
    ETAT_CHANGE = "etat_change"


@dataclass
class Evenement:
    """
    Représente un événement dans le système.
    
    Attributes:
        type: Type de l'événement
        donnees: Données associées à l'événement
        timestamp: Moment de création de l'événement
        source: Composant source de l'événement
    """
    type: TypeEvenement
    donnees: Dict[str, Any]
    timestamp: float
    source: str = "inconnu"


class EventBus:
    """
    Bus d'événements central pour la communication entre composants.
    
    Implémente le pattern Publisher/Subscriber pour découpler les composants.
    Thread-safe pour permettre l'utilisation dans un environnement multi-thread.
    """
    
    def __init__(self):
        """Initialise le bus d'événements."""
        self._abonnes: Dict[TypeEvenement, List[Callable]] = defaultdict(list)
        self._historique: List[Evenement] = []
        self._verrou = threading.Lock()
        self._actif = True
        self._max_historique = 1000  # Limite de l'historique
    
    def s_abonner(self, type_evenement: TypeEvenement, callback: Callable[[Evenement], None]) -> None:
        """
        Abonne un callback à un type d'événement.
        
        Args:
            type_evenement: Type d'événement à écouter
            callback: Fonction appelée lors de la réception de l'événement
        """
        with self._verrou:
            self._abonnes[type_evenement].append(callback)
    
    def se_desabonner(self, type_evenement: TypeEvenement, callback: Callable[[Evenement], None]) -> None:
        """
        Désabonne un callback d'un type d'événement.
        
        Args:
            type_evenement: Type d'événement
            callback: Fonction à désabonner
        """
        with self._verrou:
            if callback in self._abonnes[type_evenement]:
                self._abonnes[type_evenement].remove(callback)
    
    def publier(self, type_evenement: TypeEvenement, donnees: Dict[str, Any] = None, source: str = "inconnu") -> None:
        """
        Publie un événement sur le bus.
        
        Args:
            type_evenement: Type de l'événement
            donnees: Données associées à l'événement
            source: Composant source de l'événement
        """
        if not self._actif:
            return
        
        # Créer l'événement
        evenement = Evenement(
            type=type_evenement,
            donnees=donnees or {},
            timestamp=time.time(),
            source=source
        )
        
        # Ajouter à l'historique
        with self._verrou:
            self._historique.append(evenement)
            
            # Limiter la taille de l'historique
            if len(self._historique) > self._max_historique:
                self._historique.pop(0)
            
            # Notifier les abonnés
            abonnes = self._abonnes[type_evenement].copy()
        
        # Appeler les callbacks (en dehors du verrou pour éviter les deadlocks)
        for callback in abonnes:
            try:
                callback(evenement)
            except Exception as e:
                print(f"Erreur dans callback pour {type_evenement}: {e}")
    
    def obtenir_historique(self, type_evenement: TypeEvenement = None, limite: int = 100) -> List[Evenement]:
        """
        Obtient l'historique des événements.
        
        Args:
            type_evenement: Type d'événement à filtrer (None pour tous)
            limite: Nombre maximum d'événements à retourner
            
        Returns:
            Liste des événements correspondants
        """
        with self._verrou:
            evenements = self._historique.copy()
        
        if type_evenement:
            evenements = [e for e in evenements if e.type == type_evenement]
        
        return evenements[-limite:] if limite else evenements
    
    def vider_historique(self) -> None:
        """Vide l'historique des événements."""
        with self._verrou:
            self._historique.clear()
    
    def arreter(self) -> None:
        """Arrête le bus d'événements."""
        self._actif = False
        with self._verrou:
            self._abonnes.clear()
            self._historique.clear()
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """
        Obtient des statistiques sur l'utilisation du bus.
        
        Returns:
            Dictionnaire contenant les statistiques
        """
        with self._verrou:
            stats = {
                'nombre_abonnes': sum(len(callbacks) for callbacks in self._abonnes.values()),
                'taille_historique': len(self._historique),
                'types_evenements_actifs': len(self._abonnes),
                'dernier_evenement': self._historique[-1].timestamp if self._historique else None,
                'actif': self._actif
            }
        
        return stats


# Instance globale du bus d'événements
bus_evenements = EventBus()


# Fonctions utilitaires pour simplifier l'utilisation
def publier_evenement(type_evenement: TypeEvenement, donnees: Dict[str, Any] = None, source: str = "inconnu") -> None:
    """Fonction utilitaire pour publier un événement."""
    bus_evenements.publier(type_evenement, donnees, source)


def s_abonner_evenement(type_evenement: TypeEvenement, callback: Callable[[Evenement], None]) -> None:
    """Fonction utilitaire pour s'abonner à un événement."""
    bus_evenements.s_abonner(type_evenement, callback)


def se_desabonner_evenement(type_evenement: TypeEvenement, callback: Callable[[Evenement], None]) -> None:
    """Fonction utilitaire pour se désabonner d'un événement."""
    bus_evenements.se_desabonner(type_evenement, callback)


# Décorateurs pour simplifier l'abonnement
def ecouter_evenement(type_evenement: TypeEvenement):
    """
    Décorateur pour marquer une méthode comme écouteur d'événement.
    
    Args:
        type_evenement: Type d'événement à écouter
    """
    def decorator(func):
        func._type_evenement = type_evenement
        return func
    return decorator


class ComposantAvecEvenements:
    """
    Classe de base pour les composants qui utilisent le bus d'événements.
    
    Fournit des méthodes utilitaires et un système d'abonnement automatique.
    """
    
    def __init__(self, nom_composant: str):
        """
        Initialise le composant.
        
        Args:
            nom_composant: Nom unique du composant
        """
        self.nom_composant = nom_composant
        self._callbacks_enregistres = []
        self._auto_abonner()
    
    def _auto_abonner(self) -> None:
        """Abonne automatiquement les méthodes marquées avec @ecouter_evenement."""
        for nom_attribut in dir(self):
            attribut = getattr(self, nom_attribut)
            if hasattr(attribut, '_type_evenement'):
                type_evenement = attribut._type_evenement
                s_abonner_evenement(type_evenement, attribut)
                self._callbacks_enregistres.append((type_evenement, attribut))
    
    def publier(self, type_evenement: TypeEvenement, donnees: Dict[str, Any] = None) -> None:
        """
        Publie un événement avec le nom du composant comme source.
        
        Args:
            type_evenement: Type de l'événement
            donnees: Données associées
        """
        publier_evenement(type_evenement, donnees, self.nom_composant)
    
    def nettoyer(self) -> None:
        """Nettoie les abonnements du composant."""
        for type_evenement, callback in self._callbacks_enregistres:
            se_desabonner_evenement(type_evenement, callback)
        self._callbacks_enregistres.clear()


# Exemple d'utilisation dans un composant
class ExempleComposant(ComposantAvecEvenements):
    """Exemple d'utilisation du système d'événements."""
    
    def __init__(self):
        super().__init__("exemple_composant")
    
    @ecouter_evenement(TypeEvenement.UNITE_CREEE)
    def sur_unite_creee(self, evenement: Evenement) -> None:
        """Réagit à la création d'une unité."""
        print(f"Unité créée: {evenement.donnees}")
    
    def creer_unite(self, type_unite: str, position: tuple) -> None:
        """Crée une unité et publie l'événement."""
        # Logique de création...
        
        # Publier l'événement
        self.publier(TypeEvenement.UNITE_CREEE, {
            'type': type_unite,
            'position': position,
            'id': 'unite_123'
        })