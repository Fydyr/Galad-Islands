"""
Configuration globale du jeu Galad Islands.

Ce module centralise tous les paramètres configurables du jeu
pour faciliter l'équilibrage et la maintenance.
"""

import pygame
from enum import Enum
from typing import Dict, Tuple, Any

# =============================================================================
# CONFIGURATION GÉNÉRALE
# =============================================================================

class ConfigJeu:
    """Configuration générale du jeu."""
    
    # Informations du jeu
    NOM_JEU = "Galad Islands"
    VERSION = "0.1.0-alpha"
    DEVELOPPEURS = ["Behani Julien", "Fournier Enzo", "Alluin Edouard", "Cailliau Ethann", "Lambert Romain", "Damman Alexandre"]
    
    # Fenêtre et affichage
    LARGEUR_ECRAN = 1280
    HAUTEUR_ECRAN = 720
    FPS_CIBLE = 60
    VSYNC = True
    MODE_PLEIN_ECRAN = False
    
    # Performances
    NOMBRE_MAX_UNITES = 50
    NOMBRE_MAX_PROJECTILES = 100
    DISTANCE_CULLING = 1500  # Distance au-delà de laquelle les objets ne sont pas rendus
    
    # Debug
    MODE_DEBUG = True
    AFFICHER_FPS = True
    AFFICHER_COLLISIONS = False
    AFFICHER_PATHFINDING = False


# =============================================================================
# CONFIGURATION DES UNITÉS
# =============================================================================

class TypeUnite(Enum):
    """Types d'unités disponibles dans le jeu."""
    ZASPER = "zasper"           # Scout léger
    BARHAMUS = "barhamus"       # Maraudeur moyen
    DRAUPNIR = "draupnir"       # Léviathan lourd
    DRUID = "druid"             # Support soigneur
    ARCHITECT = "architect"     # Support constructeur


class ConfigUnites:
    """Configuration des caractéristiques de toutes les unités."""
    
    # Zasper (Scout léger)
    ZASPER = {
        'cout_gold': 10,
        'vitesse_max': 5.0,  # cases par seconde
        'degats_min': 10,
        'degats_max': 15,
        'radius_action': 5,  # cases
        'delai_rechargement': 1.0,  # secondes
        'armure_max': 60,
        'capacite_cooldown': 10.0,  # secondes
        'capacite_duree': 3.0,  # durée invincibilité
        'taille_sprite': (32, 32),
        'type_tir': 'canon_simple',
        'vitesse_rotation': 180.0,  # degrés par seconde
    }
    
    # Barhamus (Maraudeur moyen)
    BARHAMUS = {
        'cout_gold': 20,
        'vitesse_max': 3.5,
        'degats_min_salve': 20,
        'degats_max_salve': 30,
        'degats_min_boulet': 10,
        'degats_max_boulet': 15,
        'radius_action': 7,
        'delai_rechargement': 2.0,
        'armure_max': 130,
        'capacite_reduction_degats_min': 0.20,  # 20%
        'capacite_reduction_degats_max': 0.45,  # 45%
        'capacite_cooldown': 15.0,
        'capacite_duree': 5.0,
        'taille_sprite': (40, 40),
        'type_tir': 'canon_lateral',
        'vitesse_rotation': 120.0,
    }
    
    # Draupnir (Léviathan lourd)
    DRAUPNIR = {
        'cout_gold': 40,
        'vitesse_max': 2.0,
        'degats_min_salve': 40,
        'degats_max_salve': 60,
        'degats_min_boulet': 15,
        'degats_max_boulet': 20,
        'radius_action': 10,
        'delai_rechargement': 4.5,
        'armure_max': 300,
        'capacite_cooldown': 20.0,
        'taille_sprite': (56, 56),
        'type_tir': 'canon_multiple',
        'vitesse_rotation': 60.0,
        'nombre_canons': 6,  # 3 de chaque côté
    }
    
    # Druid (Support soigneur)
    DRUID = {
        'cout_gold': 30,
        'vitesse_max': 4.0,
        'degats': 0,  # Pas d'attaque
        'soin': 20,
        'radius_action': 7,
        'delai_rechargement': 4.0,
        'armure_max': 100,
        'capacite_duree_lierre': 5.0,
        'capacite_cooldown': 12.0,
        'taille_sprite': (36, 36),
        'type_tir': 'soin',
        'vitesse_rotation': 150.0,
    }
    
    # Architect (Support constructeur)
    ARCHITECT = {
        'cout_gold': 30,
        'vitesse_max': 4.0,
        'degats': 0,  # Pas d'attaque
        'radius_action': 0,  # Doit être sur une île
        'delai_rechargement': 0.0,
        'armure_max': 100,
        'bonus_rechargement': 0.5,  # Divise délai par 2
        'radius_bonus': 8,
        'taille_sprite': (36, 36),
        'type_tir': 'construction',
        'vitesse_rotation': 150.0,
    }


# =============================================================================
# CONFIGURATION DES BÂTIMENTS
# =============================================================================

class ConfigBatiments:
    """Configuration des bâtiments constructibles."""
    
    TOUR_DEFENSE = {
        'cout_gold': 25,
        'degats': 25,
        'delai_rechargement': 10.0,
        'radius_action': 8,
        'armure_max': 70,
        'taille_sprite': (24, 32),
        'type_tir': 'canon_automatique',
    }
    
    TOUR_SOIN = {
        'cout_gold': 20,
        'soin': 15,
        'delai_rechargement': 10.0,
        'radius_action': 5,
        'armure_max': 70,
        'taille_sprite': (24, 32),
        'type_effet': 'regeneration',
    }


# =============================================================================
# CONFIGURATION DES ÉVÉNEMENTS
# =============================================================================

class ConfigEvenements:
    """Configuration des événements aléatoires."""
    
    # Tempêtes
    TEMPETES = {
        'chance_apparition': 0.15,  # 15%
        'degats': 30,
        'duree_apparition': 20.0,  # secondes
        'cooldown_unite': 3.0,  # secondes entre chaque dégât
        'radius': 4,  # cases
        'vitesse_deplacement': 1.0,  # cases par seconde
    }
    
    # Vagues de bandits
    VAGUE_BANDITS = {
        'chance_apparition': 0.25,  # 25%
        'degats': 20,
        'radius_detection': 5,
        'nombre_min': 1,
        'nombre_max': 6,
        'vitesse_deplacement': 3.0,
        'armure': 40,
    }
    
    # Kraken
    KRAKEN = {
        'chance_apparition': 0.10,  # 10%
        'degats': 70,
        'nombre_tentacules_min': 2,
        'nombre_tentacules_max': 6,
        'duree_attaque': 15.0,  # secondes
        'radius_tentacule': 2,
    }
    
    # Coffres volants
    COFFRES_VOLANTS = {
        'chance_apparition': 0.20,  # 20%
        'gold_min': 10,
        'gold_max': 20,
        'duree_apparition': 20.0,
        'nombre_min': 2,
        'nombre_max': 5,
        'vitesse_chute': 2.0,  # cases par seconde
    }
    
    # Mines volantes
    MINES_VOLANTES = {
        'degats': 40,
        'nombre_initial_min': 5,
        'nombre_initial_max': 15,
        'radius_explosion': 1.5,
    }


# =============================================================================
# CONFIGURATION DU MONDE
# =============================================================================

class ConfigMonde:
    """Configuration de la génération et des propriétés du monde."""
    
    # Taille de la carte
    LARGEUR_CARTE = 100  # cases
    HAUTEUR_CARTE = 60   # cases
    TAILLE_CASE = 16     # pixels par case
    
    # Génération procédurale
    SEED_DEFAUT = 42
    DENSITE_ILOTS = 0.15  # 15% de la carte
    DISTANCE_MIN_ILOTS = 3  # cases minimum entre îlots
    TAILLE_MIN_ILOT = 2     # cases
    TAILLE_MAX_ILOT = 8     # cases
    
    # Ressources
    GOLD_INITIAL_JOUEUR = 100
    GOLD_INITIAL_IA = 100
    GOLD_PAR_ILOT_MIN = 50
    GOLD_PAR_ILOT_MAX = 150
    VITESSE_EXTRACTION = 5  # gold par seconde sur un îlot
    
    # Bases
    DISTANCE_ENTRE_BASES = 80  # cases minimum
    ARMURE_BASE = 1000
    TAILLE_BASE = (5, 3)  # cases


# =============================================================================
# CONFIGURATION DE L'IA
# =============================================================================

class ConfigIA:
    """Configuration de l'intelligence artificielle."""
    
    # Comportement général
    FREQUENCE_DECISION_STRATEGIQUE = 5.0  # secondes
    FREQUENCE_MISE_A_JOUR_PATHFINDING = 0.5  # secondes
    DISTANCE_DETECTION_ENNEMI = 15  # cases
    
    # Stratégies
    PROBABILITE_STRATEGIE_AGGRESSIVE = 0.4  # 40%
    PROBABILITE_STRATEGIE_DEFENSIVE = 0.3   # 30%
    PROBABILITE_STRATEGIE_ECONOMIQUE = 0.3  # 30%
    
    # Difficultés
    DIFFICULTES = {
        'facile': {
            'multiplicateur_ressources': 0.8,
            'delai_reaction': 2.0,
            'precision_tir': 0.7,
        },
        'normal': {
            'multiplicateur_ressources': 1.0,
            'delai_reaction': 1.0,
            'precision_tir': 0.85,
        },
        'difficile': {
            'multiplicateur_ressources': 1.2,
            'delai_reaction': 0.5,
            'precision_tir': 0.95,
        }
    }


# =============================================================================
# CONFIGURATION DES CONTRÔLES
# =============================================================================

class ConfigControles:
    """Configuration des contrôles et des touches."""
    
    # Déplacement (contrôle direct)
    TOUCHE_AVANT = pygame.K_z
    TOUCHE_ARRIERE = pygame.K_s
    TOUCHE_GAUCHE = pygame.K_q
    TOUCHE_DROITE = pygame.K_d
    
    # Déplacement alternatif (flèches)
    TOUCHE_FLECHE_HAUT = pygame.K_UP
    TOUCHE_FLECHE_BAS = pygame.K_DOWN
    TOUCHE_FLECHE_GAUCHE = pygame.K_LEFT
    TOUCHE_FLECHE_DROITE = pygame.K_RIGHT
    
    # Actions
    BOUTON_SELECTION = 1  # Clic gauche
    BOUTON_ACTION = 3     # Clic droit
    BOUTON_CAMERA = 2     # Clic molette
    
    # Interface
    TOUCHE_PAUSE = pygame.K_ESCAPE
    TOUCHE_DEBUG = pygame.K_F3
    TOUCHE_HELP = pygame.K_F1
    TOUCHE_PLEIN_ECRAN = pygame.K_F11
    
    # Caméra
    VITESSE_DEPLACEMENT_CAMERA = 300.0  # pixels par seconde
    VITESSE_ZOOM = 0.1
    ZOOM_MIN = 0.5
    ZOOM_MAX = 2.0


# =============================================================================
# CONFIGURATION AUDIO
# =============================================================================

class ConfigAudio:
    """Configuration audio du jeu."""
    
    # Volumes (0.0 à 1.0)
    VOLUME_MAITRE = 0.8
    VOLUME_MUSIQUE = 0.6
    VOLUME_EFFETS = 0.7
    VOLUME_INTERFACE = 0.5
    
    # Canaux audio
    CANAUX_AUDIO = 16
    FREQUENCE_AUDIO = 44100
    TAILLE_BUFFER = 512
    
    # Distance pour l'audio 3D
    DISTANCE_MAX_AUDIO = 1000  # pixels


# =============================================================================
# CONFIGURATION GRAPHIQUE
# =============================================================================

class ConfigGraphique:
    """Configuration du rendu graphique."""
    
    # Couleurs principales (R, G, B)
    COULEUR_NUAGE = (0, 50, 100)        # Bleu ciel sombre
    COULEUR_EAU = (0, 80, 150)         # Bleu océan
    COULEUR_ILOT = (101, 67, 33)       # Brun terre
    COULEUR_OR = (255, 215, 0)         # Jaune or
    
    # Interface
    COULEUR_UI_FOND = (40, 40, 40)     # Gris foncé
    COULEUR_UI_BORDURE = (100, 100, 100)  # Gris moyen
    COULEUR_UI_TEXTE = (255, 255, 255)    # Blanc
    COULEUR_UI_SELECTION = (255, 255, 0)  # Jaune
    
    # Factions
    COULEUR_AUBE = (255, 200, 50)      # Doré
    COULEUR_ABYSSES = (150, 0, 150)    # Violet sombre
    
    # Effets
    DUREE_EXPLOSION = 1.0  # secondes
    DUREE_DEGATS_TEXTE = 2.0  # secondes
    TRANSPARENCE_SELECTION = 128  # 0-255


# =============================================================================
# UTILITAIRES DE CONFIGURATION
# =============================================================================

def obtenir_config_unite(type_unite: TypeUnite) -> Dict[str, Any]:
    """
    Obtient la configuration d'un type d'unité.
    
    Args:
        type_unite: Type d'unité demandé
        
    Returns:
        Dictionnaire de configuration de l'unité
    """
    configs = {
        TypeUnite.ZASPER: ConfigUnites.ZASPER,
        TypeUnite.BARHAMUS: ConfigUnites.BARHAMUS,
        TypeUnite.DRAUPNIR: ConfigUnites.DRAUPNIR,
        TypeUnite.DRUID: ConfigUnites.DRUID,
        TypeUnite.ARCHITECT: ConfigUnites.ARCHITECT,
    }
    
    return configs.get(type_unite, {})


def obtenir_couleur_faction(faction: str) -> Tuple[int, int, int]:
    """
    Obtient la couleur associée à une faction.
    
    Args:
        faction: Nom de la faction ("aube" ou "abysses")
        
    Returns:
        Tuple RGB de la couleur
    """
    couleurs = {
        'aube': ConfigGraphique.COULEUR_AUBE,
        'abysses': ConfigGraphique.COULEUR_ABYSSES,
    }
    
    return couleurs.get(faction, (255, 255, 255))  # Blanc par défaut


def sauvegarder_config(chemin_fichier: str) -> None:
    """
    Sauvegarde la configuration actuelle dans un fichier.
    
    Args:
        chemin_fichier: Chemin du fichier de sauvegarde
    """
    # TODO: Implémenter la sauvegarde en JSON/YAML
    pass


def charger_config(chemin_fichier: str) -> None:
    """
    Charge une configuration depuis un fichier.
    
    Args:
        chemin_fichier: Chemin du fichier à charger
    """
    # TODO: Implémenter le chargement depuis JSON/YAML
    pass