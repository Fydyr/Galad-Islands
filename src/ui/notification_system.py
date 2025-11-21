"""
Système de notification générique pour afficher des messages à l'utilisateur.
"""
import pygame
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum


class NotificationType(Enum):
    """Types de notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Notification:
    """Représente une notification à afficher."""
    message: str
    notification_type: NotificationType
    duration: float  # Durée d'affichage en secondes
    elapsed_time: float = 0.0
    alpha: int = 255  # Transparence pour le fade out


class NotificationSystem:
    """Système de gestion et affichage des notifications."""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.max_notifications = 5
        # Make notifications slightly larger and wider for readability
        self.notification_height = 56
        self.notification_width = 520
        self.padding = 12
        self.fade_duration = 0.5  # Durée du fade out en secondes
        
        # Couleurs par type
        self.colors = {
            NotificationType.INFO: (70, 130, 180),      # Bleu
            NotificationType.SUCCESS: (60, 179, 113),   # Vert
            NotificationType.WARNING: (255, 165, 0),    # Orange
            NotificationType.ERROR: (220, 53, 69),      # Rouge
        }
        
        # Police
        try:
            # Slightly larger font for better readability
            self.font = pygame.font.Font(None, 28)
        except:
            self.font = pygame.font.SysFont("Arial", 28)
    
    def add_notification(self, message: str, notification_type: NotificationType = NotificationType.INFO, duration: float = 3.0):
        """
        adds une nouvelle notification.
        
        Args:
            message: Le message à afficher
            notification_type: Le type de notification
            duration: Durée d'affichage en secondes
        """
        # Limiter le nombre de notifications
        if len(self.notifications) >= self.max_notifications:
            self.notifications.pop(0)
        
        notification = Notification(
            message=message,
            notification_type=notification_type,
            duration=duration
        )
        self.notifications.append(notification)
    
    def update(self, dt: float):
        """Met à jour les notifications (fade out, suppression)."""
        notifications_to_remove = []
        
        for notification in self.notifications:
            notification.elapsed_time += dt
            
            # Calculer l'alpha pour le fade out
            remaining_time = notification.duration - notification.elapsed_time
            if remaining_time < self.fade_duration:
                notification.alpha = int(255 * (remaining_time / self.fade_duration))
            
            # Marquer pour suppression si expirée
            if notification.elapsed_time >= notification.duration:
                notifications_to_remove.append(notification)
        
        # Supprimer les notifications expirées
        for notification in notifications_to_remove:
            self.notifications.remove(notification)
    
    def render(self, screen: pygame.Surface):
        """Affiche all notifications actives."""
        if not self.notifications:
            return
        
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Position de départ (en haut à droite, en dessous de l'ActionBar)
        start_x = screen_width - self.notification_width - self.padding
        start_y = 140  # En dessous de la barre d'action
        
        for i, notification in enumerate(self.notifications):
            y_pos = start_y + i * (self.notification_height + self.padding)
            
            # Create une surface pour la notification avec alpha
            notif_surface = pygame.Surface((self.notification_width, self.notification_height), pygame.SRCALPHA)
            
            # Couleur de fond avec transparence
            bg_color = self.colors[notification.notification_type]
            bg_with_alpha = (*bg_color, min(200, notification.alpha))
            
            # Dessiner le fond
            pygame.draw.rect(
                notif_surface,
                bg_with_alpha,
                (0, 0, self.notification_width, self.notification_height),
                border_radius=5
            )
            
            # Bordure
            border_color = (*bg_color, notification.alpha)
            pygame.draw.rect(
                notif_surface,
                border_color,
                (0, 0, self.notification_width, self.notification_height),
                width=2,
                border_radius=5
            )
            
            # Texte
            text_color = (255, 255, 255, notification.alpha)
            text_surface = self.font.render(notification.message, True, (255, 255, 255))
            
            # Appliquer l'alpha au texte
            text_with_alpha = text_surface.copy()
            text_with_alpha.set_alpha(notification.alpha)
            
            # Centrer le texte verticalement
            text_rect = text_with_alpha.get_rect(
                center=(self.notification_width // 2, self.notification_height // 2)
            )
            notif_surface.blit(text_with_alpha, text_rect)
            
            # Afficher la notification sur l'écran
            screen.blit(notif_surface, (start_x, y_pos))
    
    def clear(self):
        """Efface all notifications."""
        self.notifications.clear()


# Instance globale pour faciliter l'accès
_notification_system = None


def get_notification_system() -> NotificationSystem:
    """Retourne l'instance globale du système de notification."""
    global _notification_system
    if _notification_system is None:
        _notification_system = NotificationSystem()
    return _notification_system
