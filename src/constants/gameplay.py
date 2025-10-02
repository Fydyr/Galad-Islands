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

# Vie des unités (par type)
UNIT_HEALTH_SCOUT = 60
UNIT_HEALTH_MARAUDEUR = 80
UNIT_HEALTH_LEVIATHAN = 120
UNIT_HEALTH_DRUID = 70
UNIT_HEALTH_ARCHITECT = 75

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