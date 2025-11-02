#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour la notification de mise à jour.
Force l'affichage d'une notification même si aucune mise à jour n'est disponible.
"""
import pygame
import sys
import os
from src.managers.display import get_display_manager
from src.ui.update_notification import UpdateNotification
from src.settings.localization import t
from src.functions.resource_path import get_resource_path

def main():
    """Lance un menu de test avec une notification de mise à jour forcée."""
    pygame.init()
    
    # Initialisation de l'affichage
    display_manager = get_display_manager()
    surface = display_manager.initialize()
    pygame.display.set_caption("Test - Notification de mise à jour")
    
    # Chargement du fond
    bg_path = get_resource_path(os.path.join("assets", "image", "galad_islands_bg2.png"))
    bg_original = pygame.image.load(bg_path)
    width, height = display_manager.get_size()
    bg_scaled = pygame.transform.scale(bg_original, (width, height))
    
    # Création d'une notification de test (simule v0.11.0 disponible)
    notification = UpdateNotification(
        new_version="0.11.0",
        current_version="0.10.0",
        release_url="https://github.com/Fydyr/Galad-Islands/releases/tag/v0.11.0"
    )
    notification.set_position(width, height)
    
    # Texte d'instruction
    font = pygame.font.Font(None, 36)
    instruction_text = "Test de la notification de mise à jour"
    instruction_text2 = "Cliquez sur 'Télécharger' ou 'Plus tard'"
    
    # Boucle principale
    clock = pygame.time.Clock()
    running = True
    
    print("🎮 Menu de test lancé - Notification affichée")
    print(f"   Nouvelle version: 0.11.0")
    print(f"   Version actuelle: 0.10.0")
    print(f"   URL: {notification.release_url}")
    
    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            
            # Laisse la notification gérer ses événements
            if notification.handle_event(event):
                if notification.dismissed:
                    print("✅ Notification fermée par l'utilisateur")
                    running = False
        
        # Rendu
        surface.blit(bg_scaled, (0, 0))
        
        # Instructions
        text_surf = font.render(instruction_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(width // 2, height // 2 - 50))
        surface.blit(text_surf, text_rect)
        
        text_surf2 = font.render(instruction_text2, True, (200, 200, 200))
        text_rect2 = text_surf2.get_rect(center=(width // 2, height // 2))
        surface.blit(text_surf2, text_rect2)
        
        # Affichage de la notification
        notification.draw(surface)
        
        pygame.display.update()
        clock.tick(60)
    
    pygame.quit()
    print("👋 Test terminé")

if __name__ == "__main__":
    main()
