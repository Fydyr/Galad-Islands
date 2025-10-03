"""
Constants de gameplay - Valeurs numériques du jeu Galad Islands.
Centralise toutes les constantes magiques pour faciliter la maintenance et l'équilibrage.
"""

# =============================================================================
# CONSTANTES DE PERFORMANCE ET RENDU
# =============================================================================

# Framerate
TARGET_FPS = 60
FRAME_TIME_MS = 1000.0  # pour les calculs de deltatime

# Interface utilisateur
HEALTH_BAR_HEIGHT = 6
HEALTH_BAR_OFFSET = 10  # pixels au-dessus du sprite
DEBUG_FONT_SIZE = 36

# Constantes pour les modales
MODAL_MARGIN = 20
MODAL_PADDING = 15
MODAL_SCROLL_SPEED = 30
MODAL_HEADER_HEIGHT = 50
MODAL_FOOTER_HEIGHT = 70
MODAL_BUTTON_WIDTH = 120
MODAL_BUTTON_HEIGHT = 40
MODAL_SCROLLBAR_WIDTH = 15
MODAL_ERROR_SURFACE_WIDTH = 200
MODAL_ERROR_SURFACE_HEIGHT = 100
MODAL_DEFAULT_MAX_WIDTH = 620
MODAL_DEFAULT_GIF_DURATION = 100  # millisecondes

# Tailles de police pour les modales
MODAL_FONT_SIZE_SMALL = 20
MODAL_FONT_SIZE_NORMAL = 22
MODAL_FONT_SIZE_MEDIUM = 26
MODAL_FONT_SIZE_LARGE = 30
MODAL_FONT_SIZE_XLARGE = 36
MODAL_TEXT_LINE_SPACING = 8
MODAL_MEDIA_SPACING = 10

# Constantes de la boutique - Dimensions
SHOP_WIDTH = 900
SHOP_HEIGHT = 650

# Constantes de la boutique - Onglets
SHOP_TAB_WIDTH = 160
SHOP_TAB_HEIGHT = 40
SHOP_TAB_SPACING = 10

# Constantes du joueur
PLAYER_DEFAULT_GOLD = 100

# Constantes de la boutique - Items
SHOP_ITEM_WIDTH = 200
SHOP_ITEM_HEIGHT = 100
SHOP_ITEMS_PER_ROW = 4
SHOP_ITEM_SPACING_X = 15
SHOP_ITEM_SPACING_Y = 15

# Constantes de la boutique - Icônes
SHOP_ICON_SIZE_LARGE = 64  # Icônes principales
SHOP_ICON_SIZE_MEDIUM = 56  # Icônes d'items
SHOP_ICON_SIZE_SMALL = 24  # Icônes d'onglets
SHOP_ICON_SIZE_TINY = 16   # Petites icônes

# Constantes de la boutique - Marges et espacements
SHOP_MARGIN = 20
SHOP_PADDING = 30
SHOP_TAB_Y_OFFSET = 80
SHOP_ITEMS_START_Y = 140

# Constantes de la boutique - Interface
SHOP_CLOSE_BUTTON_SIZE = 35
SHOP_CLOSE_BUTTON_MARGIN = 15
SHOP_CLOSE_X_SIZE = 8
SHOP_CLOSE_X_THICKNESS = 3
SHOP_SHADOW_OFFSET = 5
SHOP_SHADOW_LAYERS = 10

# Constantes de la boutique - Animations et feedback
SHOP_FEEDBACK_DURATION = 3.0  # secondes
SHOP_TEXT_X_OFFSET = 30

# Constantes de la boutique - Or du joueur par défaut
SHOP_DEFAULT_PLAYER_GOLD = 100

# Constantes de la boutique - Polices
SHOP_FONT_SIZE_TITLE = 32
SHOP_FONT_SIZE_SUBTITLE = 26
SHOP_FONT_SIZE_NORMAL = 20
SHOP_FONT_SIZE_SMALL = 16
SHOP_FONT_SIZE_TINY = 14

# Seuils de couleur pour les barres de vie
HEALTH_HIGH_THRESHOLD = 0.6  # Vert si > 60%
HEALTH_MEDIUM_THRESHOLD = 0.3   # Orange si > 30%, Rouge si < 30%
HEALTH_LOW_THRESHOLD = 0.3   # Rouge si < 30%, Orange entre les deux

# =============================================================================
# COULEURS (RGB)
# =============================================================================

# Couleurs de l'interface
COLOR_OCEAN_BLUE = (0, 50, 100)
COLOR_HEALTH_BACKGROUND = (100, 0, 0)
COLOR_HEALTH_HIGH = (0, 200, 0)      # Vert
COLOR_HEALTH_MEDIUM = (255, 165, 0)  # Orange
COLOR_HEALTH_LOW = (200, 0, 0)       # Rouge

# Couleurs pour les modales et interfaces
COLOR_WHITE = (255, 255, 255)
COLOR_GOLD = (255, 215, 0)
COLOR_GRAY = (128, 128, 128)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_LIGHT_GRAY = (192, 192, 192)
COLOR_ERROR_GRAY = (100, 100, 100)

# Couleurs communes pour les boutiques
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN_SUCCESS = (80, 200, 80)
COLOR_RED_ERROR = (200, 80, 80)

# Couleurs de placeholder pour icônes
COLOR_PLACEHOLDER_UNIT = (100, 150, 200)
COLOR_PLACEHOLDER_BUILDING = (150, 120, 80)
COLOR_PLACEHOLDER_UPGRADE = (200, 150, 100)

# =============================================================================
# CONSTANTES DE MOUVEMENT ET PHYSICS
# =============================================================================

# Vitesses par défaut
DEFAULT_UNIT_SPEED = 3.5
DEFAULT_REVERSE_SPEED = -0.6
SPEED_ACCELERATION = 0.2
SPEED_DECELERATION = 0.1
BOUNDARY_MARGIN = 32  # pixels pour les bordures de collision

# =============================================================================
# CONSTANTES DE COMBAT
# =============================================================================

# Projectiles
PROJECTILE_SPEED = 10.0
PROJECTILE_DAMAGE = 10
PROJECTILE_HEALTH = 1
PROJECTILE_WIDTH = 20
PROJECTILE_HEIGHT = 10
EXPLOSION_SIZE_WIDTH = 20
EXPLOSION_SIZE_HEIGHT = 10

# Vie des unités (par type) - Valeurs mises à jour depuis unitFactory.py
UNIT_HEALTH_SCOUT = 60
UNIT_HEALTH_MARAUDEUR = 130  # Était 80, mise à jour depuis factory
UNIT_HEALTH_LEVIATHAN = 300  # Était 120, mise à jour depuis factory
UNIT_HEALTH_DRUID = 130      # Était 70, mise à jour depuis factory
UNIT_HEALTH_ARCHITECT = 130  # Était 75, mise à jour depuis factory

# Vitesses des unités (par type)
UNIT_SPEED_SCOUT = 5.0
UNIT_SPEED_MARAUDEUR = 3.5
UNIT_SPEED_LEVIATHAN = 2.0
UNIT_SPEED_DRUID = 3.5
UNIT_SPEED_ARCHITECT = 3.5

# Vitesses de recul des unités (par type)
UNIT_REVERSE_SPEED_SCOUT = -1.0
UNIT_REVERSE_SPEED_MARAUDEUR = -0.6
UNIT_REVERSE_SPEED_LEVIATHAN = -0.2
UNIT_REVERSE_SPEED_DRUID = -0.6
UNIT_REVERSE_SPEED_ARCHITECT = -0.6

# Attaques des unités (par type)
UNIT_ATTACK_SCOUT = 10
UNIT_ATTACK_MARAUDEUR = 20
UNIT_ATTACK_LEVIATHAN = 30
UNIT_ATTACK_DRUID = 20
UNIT_ATTACK_ARCHITECT = 20

# Cooldowns d'attaque des unités (en secondes)
UNIT_COOLDOWN_SCOUT = 2
UNIT_COOLDOWN_MARAUDEUR = 4
UNIT_COOLDOWN_LEVIATHAN = 8
UNIT_COOLDOWN_DRUID = 4
UNIT_COOLDOWN_ARCHITECT = 4

# Capacités spéciales

SPECIAL_ABILITY_COOLDOWN = 15.0 # Cooldown générique pour les capacités spéciales

# Barhamus : Bouclier de mana
BARHAMUS_SHIELD_REDUCTION_MIN = 0.20  # 20%
BARHAMUS_SHIELD_REDUCTION_MAX = 0.45  # 45%
BARHAMUS_SHIELD_DURATION = 5.0        # Durée d'effet du bouclier (secondes)

# NOTE: historical name "Barhamus" was used for these shield constants.
# The Maraudeur unit uses the same values. To support a clean rename
# without breaking existing imports, we provide MARAUDEUR_* aliases.
# Prefer MARAUDEUR_* in new code.
MARAUDEUR_SHIELD_REDUCTION_MIN = BARHAMUS_SHIELD_REDUCTION_MIN
MARAUDEUR_SHIELD_REDUCTION_MAX = BARHAMUS_SHIELD_REDUCTION_MAX
MARAUDEUR_SHIELD_DURATION = BARHAMUS_SHIELD_DURATION

# Druid : Lierre volant
DRUID_IMMOBILIZATION_DURATION = 5.0 # Durée d'immobilisation
DRUID_PROJECTILE_SPEED = 15.0     # Vitesse du projectile druide

# Architecte : Rayon d'effet
ARCHITECT_RADIUS = 400.0           # Rayon d'effet de l'architecte
ARCHITECT_RELOAD_FACTOR = 1.0      # Facteur de rechargement
ARCHITECT_DURATION = 10.0          # Durée de l'effet architecte

# Zasper : Invincibilité
ZASPER_INVINCIBILITY_DURATION = 3.0 # Durée d'invincibilité de Zasper

# Vie des bases
BASE_HEALTH = 1000
BASE_MAX_HEALTH = 1000

# =============================================================================
# CONSTANTES DE POSITIONNEMENT
# =============================================================================

# Directions par défaut (degrés)
ALLY_DEFAULT_DIRECTION = 180  # Alliés regardent vers la droite
ENEMY_DEFAULT_DIRECTION = 0   # Ennemis regardent vers la gauche

# Offsets pour le placement initial des unités ennemies de test
ENEMY_SPAWN_OFFSET_X = 150
ENEMY_SPAWN_OFFSETS_Y = {
    'scout': -150,
    'maraudeur': 0,
    'leviathan': 200,
    'druid': 400,
    'architect': 500
}

# =============================================================================
# CONSTANTES DE TERRAIN ET EFFETS
# =============================================================================

# Modificateurs de vitesse
TERRAIN_NORMAL_MODIFIER = 1.0
TERRAIN_SLOW_MODIFIER = 0.5  # Dans les nuages par exemple
TERRAIN_STOP_MODIFIER = 0.0  # Arrêt complet

# Effets de pourcentage
CLOUD_SPEED_REDUCTION = 100  # 100% pour debug print