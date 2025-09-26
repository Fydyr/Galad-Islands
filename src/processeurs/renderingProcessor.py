import esper
import pygame
from src.components.properties.positionComponent import PositionComponent
from src.components.properties.spriteComponent import SpriteComponent
from src.components.properties.healthComponent import HealthComponent

class RenderProcessor(esper.Processor):
    def __init__(self, screen, camera=None):
        super().__init__()
        self.screen = screen
        self.camera = camera

    def process(self):
        for ent, (pos, sprite) in esper.get_components(PositionComponent, SpriteComponent):
            # Load the sprite
            image = pygame.image.load(sprite.image_path).convert_alpha()
            
            # Calculate sprite size based on camera zoom
            if self.camera:
                # Scale sprite size according to camera zoom to maintain consistent screen size
                display_width = int(sprite.width * self.camera.zoom)
                display_height = int(sprite.height * self.camera.zoom)
                screen_x, screen_y = self.camera.world_to_screen(pos.x, pos.y)
            else:
                # Fallback if no camera is provided
                display_width = sprite.width
                display_height = sprite.height
                screen_x, screen_y = pos.x, pos.y
            
            # Rotate the scaled image from the sprite
            sprite.scale_sprite(display_width, display_height)
            rotated_image = pygame.transform.rotate(sprite.surface, -pos.direction)
            
            # Get the rect and set its center to the screen position
            rect = rotated_image.get_rect(center=(screen_x, screen_y))
            # pygame.draw.rect(self.screen, 5, rect, 2)
            # Blit using the rect's topleft to keep the rotation centered
            self.screen.blit(rotated_image, rect.topleft)
            
            # Afficher la barre de vie si l'entité a un HealthComponent
            if esper.has_component(ent, HealthComponent):
                health = esper.component_for_entity(ent, HealthComponent)
                if health.currentHealth < health.maxHealth :
                    self._draw_health_bar(screen_x, screen_y, health, display_width, display_height)
    
    def _draw_health_bar(self, x, y, health, sprite_width, sprite_height):
    # Configuration de la barre de vie
        bar_width = sprite_width
        bar_height = 6
        bar_offset_y = sprite_height // 2 + 10  # Position au-dessus du sprite
        
        # Position de la barre (centrée au-dessus de l'entité)
        bar_x = x - bar_width // 2
        bar_y = y - bar_offset_y
        
        # Vérifier que maxHealth n'est pas zéro pour éviter la division par zéro
        if health.maxHealth <= 0:
            # Si maxHealth est 0 ou négatif, on ne dessine pas la barre de vie
            return
        
        # Calculer le pourcentage de vie
        health_ratio = max(0, min(1, health.currentHealth / health.maxHealth))
        
        # Dessiner le fond de la barre (rouge foncé)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (100, 0, 0), background_rect)
        
        # Dessiner la barre de vie (couleur selon le pourcentage)
        if health_ratio > 0:
            health_bar_width = int(bar_width * health_ratio)
            health_rect = pygame.Rect(bar_x, bar_y, health_bar_width, bar_height)
            
            # Couleur qui change selon la vie restante
            if health_ratio > 0.6:
                color = (0, 200, 0)  # Vert
            elif health_ratio > 0.3:
                color = (255, 165, 0)  # Orange
            else:
                color = (255, 0, 0)  # Rouge
            
            pygame.draw.rect(self.screen, color, health_rect)
        
        # Bordure noire autour de la barre
        pygame.draw.rect(self.screen, (0, 0, 0), background_rect, 1)