"""
Moteur principal du jeu Galad Islands - Architecture par composants.

Ce module implémente le cœur du moteur de jeu avec une architecture
modulaire permettant le développement parallèle par composants.

Responsable: Behani Julien
"""

import pygame
import sys
import time
from typing import Dict, Optional
from enum import Enum
from pathlib import Path

# Import des interfaces pour communication entre composants
sys.path.append(str(Path(__file__).parent.parent.parent))
from interfaces.event_bus import EventBus, TypeEvenement, publier_evenement
from interfaces.entity_interface import entity_interface
from interfaces.render_interface import render_interface


class EtatJeu(Enum):
    """États possibles du jeu."""
    INITIALISATION = "initialisation"
    MENU_PRINCIPAL = "menu_principal"
    EN_JEU = "en_jeu"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    ARRET = "arret"


class GaladEngine:
    """
    Moteur principal coordonnant tous les composants.
    
    Responsabilités:
    - Boucle de jeu principale
    - Coordination entre composants via interfaces
    - Gestion des états du jeu
    - Event bus central
    """
    
    def __init__(self, largeur: int = 1280, hauteur: int = 720, fps_cible: int = 60):
        """
        Initialise le moteur principal.
        
        Args:
            largeur: Largeur de la fenêtre
            hauteur: Hauteur de la fenêtre
            fps_cible: FPS visé
        """
        self.largeur = largeur
        self.hauteur = hauteur
        self.fps_cible = fps_cible
        
        # État du moteur
        self.etat_actuel = EtatJeu.INITIALISATION
        self.actif = False
        self.delta_time = 0.0
        self.temps_precedent = 0.0
        
        # Pygame
        pygame.init()
        self.ecran = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Galad Islands")
        self.horloge = pygame.time.Clock()
        
        # Bus d'événements
        self.bus_evenements = EventBus()
        
        # Composants (seront initialisés par les responsables)
        self.composants: Dict[str, object] = {}
        
        print(f"🎮 Moteur Galad Islands initialisé ({largeur}x{hauteur}, {fps_cible} FPS)")
    
    def enregistrer_composant(self, nom: str, composant: object) -> None:
        """
        Enregistre un composant dans le moteur.
        
        Args:
            nom: Nom unique du composant
            composant: Instance du composant
        """
        self.composants[nom] = composant
        print(f"🔧 Composant '{nom}' enregistré")
        
        # Notifier l'enregistrement via le bus
        publier_evenement(
            TypeEvenement.JEU_DEMARRE,  # Réutilisation d'un type existant
            {"composant": nom, "action": "enregistre"},
            "core-engine"
        )
    
    def initialiser_composants(self) -> bool:
        """
        Initialise tous les composants enregistrés.
        
        Returns:
            True si l'initialisation réussit, False sinon
        """
        print("🚀 Initialisation des composants...")
        
        # Ordre d'initialisation (les dépendances en premier)
        ordre_init = ["entities", "renderer", "physics", "ai", "world"]
        
        for nom_composant in ordre_init:
            composant = self.composants.get(nom_composant)
            if composant and hasattr(composant, 'initialiser'):
                try:
                    if not composant.initialiser():
                        print(f"❌ Échec initialisation composant '{nom_composant}'")
                        return False
                    print(f"✅ Composant '{nom_composant}' initialisé")
                except Exception as e:
                    print(f"❌ Erreur initialisation '{nom_composant}': {e}")
                    return False
        
        return True
    
    def changer_etat(self, nouvel_etat: EtatJeu) -> None:
        """
        Change l'état du jeu.
        
        Args:
            nouvel_etat: Nouvel état à appliquer
        """
        ancien_etat = self.etat_actuel
        self.etat_actuel = nouvel_etat
        
        print(f"🔄 Changement d'état: {ancien_etat.value} → {nouvel_etat.value}")
        
        # Publier l'événement de changement d'état
        publier_evenement(
            TypeEvenement.ETAT_CHANGE,
            {"ancien_etat": ancien_etat.value, "nouvel_etat": nouvel_etat.value},
            "core-engine"
        )
    
    def gerer_evenements_pygame(self) -> None:
        """Gère les événements Pygame (clavier, souris, fenêtre)."""
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                self.arreter()
            elif evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_ESCAPE:
                    if self.etat_actuel == EtatJeu.EN_JEU:
                        self.changer_etat(EtatJeu.PAUSE)
                    elif self.etat_actuel == EtatJeu.PAUSE:
                        self.changer_etat(EtatJeu.EN_JEU)
                    elif self.etat_actuel == EtatJeu.MENU_PRINCIPAL:
                        self.arreter()
                elif evenement.key == pygame.K_SPACE:
                    if self.etat_actuel == EtatJeu.MENU_PRINCIPAL:
                        self.changer_etat(EtatJeu.EN_JEU)
            
            # Transmettre les événements aux composants intéressés
            publier_evenement(
                TypeEvenement.BOUTON_CLIQUE,  # Générique pour input
                {"type_pygame": evenement.type, "evenement": evenement},
                "core-engine"
            )
    
    def mettre_a_jour(self) -> None:
        """Met à jour tous les composants selon l'état actuel."""
        # Mise à jour selon l'état
        if self.etat_actuel == EtatJeu.EN_JEU:
            self._mettre_a_jour_jeu()
        elif self.etat_actuel == EtatJeu.MENU_PRINCIPAL:
            self._mettre_a_jour_menu()
        # Pause et autres états n'ont pas de mise à jour spécifique
    
    def _mettre_a_jour_jeu(self) -> None:
        """Met à jour les composants pendant le jeu."""
        # Ordre de mise à jour optimisé
        ordre_maj = ["ai", "physics", "entities", "world"]
        
        for nom_composant in ordre_maj:
            composant = self.composants.get(nom_composant)
            if composant and hasattr(composant, 'mettre_a_jour'):
                try:
                    composant.mettre_a_jour(self.delta_time)
                except Exception as e:
                    print(f"❌ Erreur MAJ '{nom_composant}': {e}")
    
    def _mettre_a_jour_menu(self) -> None:
        """Met à jour les composants du menu."""
        # Seul le renderer est actif dans le menu
        composant_renderer = self.composants.get("renderer")
        if composant_renderer and hasattr(composant_renderer, 'mettre_a_jour_menu'):
            composant_renderer.mettre_a_jour_menu(self.delta_time)
    
    def rendre(self) -> None:
        """Effectue le rendu via le composant renderer."""
        # Effacer l'écran
        self.ecran.fill((0, 50, 100))  # Bleu ciel sombre
        
        # Déléguer le rendu au composant renderer
        composant_renderer = self.composants.get("renderer")
        if composant_renderer and hasattr(composant_renderer, 'rendre'):
            composant_renderer.rendre(self.ecran, self.etat_actuel)
        else:
            # Rendu de fallback si pas de renderer
            self._rendre_fallback()
        
        # Affichage des FPS en mode debug
        self._afficher_debug_info()
        
        pygame.display.flip()
    
    def _rendre_fallback(self) -> None:
        """Rendu de base si le composant renderer n'est pas disponible."""
        font = pygame.font.Font(None, 36)
        
        if self.etat_actuel == EtatJeu.MENU_PRINCIPAL:
            texte = font.render("GALAD ISLANDS - Appuyez sur ESPACE", True, (255, 255, 255))
            rect = texte.get_rect(center=(self.largeur // 2, self.hauteur // 2))
            self.ecran.blit(texte, rect)
        elif self.etat_actuel == EtatJeu.EN_JEU:
            texte = font.render("JEU EN COURS - ESC pour pause", True, (255, 255, 255))
            self.ecran.blit(texte, (10, 10))
        elif self.etat_actuel == EtatJeu.PAUSE:
            texte = font.render("PAUSE - ESC pour reprendre", True, (255, 255, 0))
            rect = texte.get_rect(center=(self.largeur // 2, self.hauteur // 2))
            self.ecran.blit(texte, rect)
    
    def _afficher_debug_info(self) -> None:
        """Affiche les informations de debug."""
        font = pygame.font.Font(None, 24)
        fps_actuel = self.horloge.get_fps()
        
        infos = [
            f"FPS: {fps_actuel:.1f}",
            f"État: {self.etat_actuel.value}",
            f"Composants: {len(self.composants)}"
        ]
        
        for i, info in enumerate(infos):
            texte = font.render(info, True, (255, 255, 255))
            self.ecran.blit(texte, (10, 10 + i * 25))
    
    def calculer_delta_time(self) -> None:
        """Calcule le delta time pour cette frame."""
        temps_actuel = time.time()
        self.delta_time = temps_actuel - self.temps_precedent
        self.temps_precedent = temps_actuel
        
        # Limiter le delta time pour éviter les gros sauts
        self.delta_time = min(self.delta_time, 1.0 / 30.0)  # Max 30 FPS
    
    def demarrer(self) -> None:
        """Démarre le moteur de jeu."""
        print("🚀 Démarrage du moteur Galad Islands...")
        
        # Initialiser les composants
        if not self.initialiser_composants():
            print("❌ Échec de l'initialisation, arrêt du moteur")
            return
        
        # Publier l'événement de démarrage
        publier_evenement(TypeEvenement.JEU_DEMARRE, {"moteur": "galad"}, "core-engine")
        
        # Changer vers le menu principal
        self.changer_etat(EtatJeu.MENU_PRINCIPAL)
        
        # Démarrer la boucle principale
        self.actif = True
        self.temps_precedent = time.time()
        self.boucle_principale()
    
    def boucle_principale(self) -> None:
        """Boucle principale du moteur."""
        print("🔄 Boucle principale démarrée")
        
        while self.actif and self.etat_actuel != EtatJeu.ARRET:
            # Calculer le delta time
            self.calculer_delta_time()
            
            # Gestion des événements
            self.gerer_evenements_pygame()
            
            # Mise à jour
            self.mettre_a_jour()
            
            # Rendu
            self.rendre()
            
            # Limitation du framerate
            self.horloge.tick(self.fps_cible)
        
        print("🔄 Boucle principale terminée")
    
    def arreter(self) -> None:
        """Arrête proprement le moteur."""
        print("🛑 Arrêt du moteur Galad Islands...")
        
        self.changer_etat(EtatJeu.ARRET)
        self.actif = False
        
        # Publier l'événement d'arrêt
        publier_evenement(TypeEvenement.JEU_ARRETE, {"moteur": "galad"}, "core-engine")
        
        # Nettoyer les composants
        for nom, composant in self.composants.items():
            if hasattr(composant, 'nettoyer'):
                try:
                    composant.nettoyer()
                    print(f"🧹 Composant '{nom}' nettoyé")
                except Exception as e:
                    print(f"❌ Erreur nettoyage '{nom}': {e}")
        
        # Arrêter le bus d'événements
        self.bus_evenements.arreter()
        
        # Fermer Pygame
        pygame.quit()
        sys.exit()
    
    def obtenir_statistiques(self) -> Dict[str, any]:
        """Obtient les statistiques du moteur."""
        return {
            "fps_actuel": self.horloge.get_fps(),
            "fps_cible": self.fps_cible,
            "etat": self.etat_actuel.value,
            "delta_time": self.delta_time,
            "composants_charges": len(self.composants),
            "composants": list(self.composants.keys())
        }


def main():
    """Point d'entrée principal - Version composants."""
    print("🎮 Galad Islands - Architecture par composants")
    print("=" * 50)
    
    # Créer le moteur
    moteur = GaladEngine(largeur=1280, hauteur=720, fps_cible=60)
    
    # TODO: Les composants seront enregistrés ici par leurs responsables
    # moteur.enregistrer_composant("entities", composant_entities)
    # moteur.enregistrer_composant("renderer", composant_renderer)
    # etc.
    
    try:
        moteur.demarrer()
    except KeyboardInterrupt:
        print("\n🔒 Interruption clavier détectée")
        moteur.arreter()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        moteur.arreter()


if __name__ == "__main__":
    main()