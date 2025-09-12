"""
Module principal du moteur de jeu Galad Islands.

Ce module implémente le moteur de jeu principal responsable de coordonner
tous les systèmes du jeu (rendu, physique, IA, événements).
"""

import pygame
import sys
from typing import Dict, List, Optional
from enum import Enum
import numpy as np

class EtatJeu(Enum):
    """Énumération des différents états possibles du jeu."""
    MENU_PRINCIPAL = "menu_principal"
    EN_JEU = "en_jeu"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    VICTOIRE = "victoire"


class GaladEngine:
    """
    Moteur principal du jeu Galad Islands.
    
    Responsable de la coordination entre tous les systèmes du jeu,
    de la boucle de jeu principale et de la gestion des états.
    
    Attributes:
        fps_cible (int): Nombre d'images par seconde visé
        horloge (pygame.time.Clock): Gestionnaire de temps Pygame
        etat_actuel (EtatJeu): État actuel du jeu
        systemes (Dict): Dictionnaire des systèmes enregistrés
        actif (bool): Indique si le moteur est en fonctionnement
    """
    
    def __init__(self, largeur: int = 1280, hauteur: int = 720, fps_cible: int = 60):
        """
        Initialise le moteur de jeu.
        
        Args:
            largeur: Largeur de la fenêtre en pixels
            hauteur: Hauteur de la fenêtre en pixels
            fps_cible: Nombre d'images par seconde visé
        """
        self.largeur = largeur
        self.hauteur = hauteur
        self.fps_cible = fps_cible
        
        # Initialisation Pygame
        pygame.init()
        self.ecran = pygame.display.set_mode((largeur, hauteur))
        pygame.display.set_caption("Galad Islands")
        self.horloge = pygame.time.Clock()
        
        # État du moteur
        self.etat_actuel = EtatJeu.MENU_PRINCIPAL
        self.actif = False
        self.delta_time = 0.0
        
        # Systèmes du jeu
        self.systemes: Dict[str, object] = {}
        
        # Métriques de performance
        self.fps_reel = 0.0
        self.temps_frame_precedente = 0.0
    
    def enregistrer_systeme(self, nom: str, systeme: object) -> None:
        """
        Enregistre un système dans le moteur.
        
        Args:
            nom: Nom unique du système
            systeme: Instance du système à enregistrer
        """
        self.systemes[nom] = systeme
        print(f"Système '{nom}' enregistré avec succès")
    
    def obtenir_systeme(self, nom: str) -> Optional[object]:
        """
        Récupère un système enregistré.
        
        Args:
            nom: Nom du système à récupérer
            
        Returns:
            L'instance du système ou None si non trouvé
        """
        return self.systemes.get(nom)
    
    def changer_etat(self, nouvel_etat: EtatJeu) -> None:
        """
        Change l'état actuel du jeu.
        
        Args:
            nouvel_etat: Nouvel état à appliquer
        """
        ancien_etat = self.etat_actuel
        self.etat_actuel = nouvel_etat
        print(f"Changement d'état: {ancien_etat.value} -> {nouvel_etat.value}")
        
        # Notifier les systèmes du changement d'état
        for systeme in self.systemes.values():
            if hasattr(systeme, 'sur_changement_etat'):
                systeme.sur_changement_etat(ancien_etat, nouvel_etat)
    
    def initialiser(self) -> bool:
        """
        Initialise tous les systèmes du jeu.
        
        Returns:
            True si l'initialisation s'est bien déroulée, False sinon
        """
        try:
            # Initialisation des systèmes dans l'ordre de dépendance
            systemes_a_initialiser = [
                'gestion_evenements',
                'rendu',
                'physique',
                'ia',
                'audio',
                'interface'
            ]
            
            for nom_systeme in systemes_a_initialiser:
                systeme = self.obtenir_systeme(nom_systeme)
                if systeme and hasattr(systeme, 'initialiser'):
                    if not systeme.initialiser():
                        print(f"Erreur lors de l'initialisation du système '{nom_systeme}'")
                        return False
            
            print("Tous les systèmes ont été initialisés avec succès")
            return True
            
        except Exception as e:
            print(f"Erreur critique lors de l'initialisation: {e}")
            return False
    
    def mettre_a_jour(self, delta_time: float) -> None:
        """
        Met à jour tous les systèmes du jeu.
        
        Args:
            delta_time: Temps écoulé depuis la dernière frame en secondes
        """
        # Mise à jour des systèmes selon l'état actuel
        if self.etat_actuel == EtatJeu.EN_JEU:
            self._mettre_a_jour_jeu(delta_time)
        elif self.etat_actuel == EtatJeu.MENU_PRINCIPAL:
            self._mettre_a_jour_menu(delta_time)
        elif self.etat_actuel == EtatJeu.PAUSE:
            self._mettre_a_jour_pause(delta_time)
    
    def _mettre_a_jour_jeu(self, delta_time: float) -> None:
        """Met à jour les systèmes pendant le jeu."""
        # Ordre de mise à jour optimisé pour les performances
        systemes_ordre = [
            'gestion_evenements',
            'ia',
            'physique',
            'collision',
            'audio',
            'interface'
        ]
        
        for nom_systeme in systemes_ordre:
            systeme = self.obtenir_systeme(nom_systeme)
            if systeme and hasattr(systeme, 'mettre_a_jour'):
                systeme.mettre_a_jour(delta_time)
    
    def _mettre_a_jour_menu(self, delta_time: float) -> None:
        """Met à jour les systèmes du menu principal."""
        systeme_interface = self.obtenir_systeme('interface')
        if systeme_interface and hasattr(systeme_interface, 'mettre_a_jour_menu'):
            systeme_interface.mettre_a_jour_menu(delta_time)
    
    def _mettre_a_jour_pause(self, delta_time: float) -> None:
        """Met à jour les systèmes en pause."""
        # En pause, seule l'interface est mise à jour
        systeme_interface = self.obtenir_systeme('interface')
        if systeme_interface and hasattr(systeme_interface, 'mettre_a_jour_pause'):
            systeme_interface.mettre_a_jour_pause(delta_time)
    
    def rendre(self) -> None:
        """Effectue le rendu de tous les éléments visuels."""
        # Effacer l'écran
        self.ecran.fill((0, 50, 100))  # Couleur de fond (bleu ciel sombre)
        
        # Rendu selon l'état actuel
        systeme_rendu = self.obtenir_systeme('rendu')
        if systeme_rendu and hasattr(systeme_rendu, 'rendre'):
            systeme_rendu.rendre(self.ecran, self.etat_actuel)
        
        # Rendu de l'interface utilisateur (toujours au-dessus)
        systeme_interface = self.obtenir_systeme('interface')
        if systeme_interface and hasattr(systeme_interface, 'rendre'):
            systeme_interface.rendre(self.ecran, self.etat_actuel)
        
        # Affichage des métriques de debug en mode développement
        if hasattr(self, 'mode_debug') and self.mode_debug:
            self._afficher_metriques_debug()
        
        # Mise à jour de l'affichage
        pygame.display.flip()
    
    def _afficher_metriques_debug(self) -> None:
        """Affiche les métriques de performance en mode debug."""
        # Informations à afficher
        infos_debug = [
            f"FPS: {self.fps_reel:.1f}",
            f"Delta: {self.delta_time*1000:.1f}ms",
            f"État: {self.etat_actuel.value}",
            f"Systèmes: {len(self.systemes)}"
        ]
        
        # Affichage simple des métriques (à améliorer avec une police)
        y_offset = 10
        for info in infos_debug:
            # Ici on pourrait utiliser pygame.font pour un meilleur rendu
            print(info)  # Temporaire : affichage console
            y_offset += 20
    
    def gerer_evenements(self) -> None:
        """Gère les événements système (fermeture, etc.)."""
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                self.arreter()
            elif evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_ESCAPE:
                    if self.etat_actuel == EtatJeu.EN_JEU:
                        self.changer_etat(EtatJeu.PAUSE)
                    elif self.etat_actuel == EtatJeu.PAUSE:
                        self.changer_etat(EtatJeu.EN_JEU)
            
            # Transmettre les événements aux systèmes concernés
            systeme_evenements = self.obtenir_systeme('gestion_evenements')
            if systeme_evenements and hasattr(systeme_evenements, 'traiter_evenement'):
                systeme_evenements.traiter_evenement(evenement)
    
    def demarrer(self) -> None:
        """Démarre la boucle principale du jeu."""
        if not self.initialiser():
            print("Impossible de démarrer le jeu : échec de l'initialisation")
            return
        
        self.actif = True
        print("Démarrage du moteur Galad Islands...")
        
        self.boucle_principale()
    
    def boucle_principale(self) -> None:
        """
        Boucle principale du jeu.
        
        Gère le timing, les mises à jour et le rendu à chaque frame.
        """
        while self.actif:
            # Calcul du delta time
            temps_actuel = pygame.time.get_ticks()
            self.delta_time = (temps_actuel - self.temps_frame_precedente) / 1000.0
            self.temps_frame_precedente = temps_actuel
            
            # Limitation du delta time pour éviter les gros sauts
            self.delta_time = min(self.delta_time, 1.0 / 30.0)  # Max 30 FPS minimum
            
            # Gestion des événements
            self.gerer_evenements()
            
            # Mise à jour des systèmes
            self.mettre_a_jour(self.delta_time)
            
            # Rendu
            self.rendre()
            
            # Limitation du framerate
            self.horloge.tick(self.fps_cible)
            self.fps_reel = self.horloge.get_fps()
    
    def arreter(self) -> None:
        """Arrête proprement le moteur de jeu."""
        print("Arrêt du moteur Galad Islands...")
        self.actif = False
        
        # Nettoyage des systèmes
        for nom, systeme in self.systemes.items():
            if hasattr(systeme, 'nettoyer'):
                try:
                    systeme.nettoyer()
                    print(f"Système '{nom}' nettoyé")
                except Exception as e:
                    print(f"Erreur lors du nettoyage du système '{nom}': {e}")
        
        # Fermeture de Pygame
        pygame.quit()
        sys.exit()


def main():
    """Point d'entrée principal du jeu."""
    # Création et démarrage du moteur
    moteur = GaladEngine(largeur=1280, hauteur=720, fps_cible=60)
    
    # Ici, on enregistrerait normalement tous les systèmes
    # moteur.enregistrer_systeme('rendu', SystemeRendu())
    # moteur.enregistrer_systeme('physique', SystemePhysique())
    # etc.
    
    try:
        moteur.demarrer()
    except KeyboardInterrupt:
        print("\nInterruption clavier détectée")
        moteur.arreter()
    except Exception as e:
        print(f"Erreur critique: {e}")
        moteur.arreter()


if __name__ == "__main__":
    main()