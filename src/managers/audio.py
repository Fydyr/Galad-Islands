"""
Centralized audio manager for music and sound effects.
"""

import pygame
import os
import json
from typing import Optional
from src.settings import settings
from src.settings.localization import t
from src.functions.resource_path import get_resource_path


class AudioManager:
    """Manages background music and sound effects."""

    def __init__(self):
        pygame.mixer.init()
        self.music_loaded = False
        self.select_sound: Optional[pygame.mixer.Sound] = None
        self._load_assets()

    def _load_assets(self):
        """Loads audio assets."""
        self._load_music()
        self._load_sound_effects()

    def _load_music(self):
        """Loads and starts ambient music."""
        music_path = get_resource_path(os.path.join("assets", "sounds", "xDeviruchi-TitleTheme.ogg"))
        try:
            pygame.mixer.music.load(music_path)
            self.update_music_volume()
            pygame.mixer.music.play(-1)  # Infinite loop
            self.music_loaded = True
            print(f"🎵 Music loaded")
        except Exception as e:
            print(t("system.music_load_error", error=e))
            self.music_loaded = False

    def _load_sound_effects(self):
        """Loads sound effects."""
        try:
            self.select_sound = pygame.mixer.Sound(
                get_resource_path(os.path.join("assets", "sounds", "select_sound_2.mp3"))
            )
            self.update_effects_volume()
            print("🔊 Sound effects loaded")
        except Exception as e:
            print(t("system.sound_load_error", error=e))
            self.select_sound = None

    def update_music_volume(self):
        """Updates music volume from configuration."""
        if not self.music_loaded:
            return

        music_volume = settings.config_manager.get("volume_music", 0.5)
        master_volume = settings.config_manager.get("volume_master", 0.8)
        final_volume = music_volume * master_volume

        pygame.mixer.music.set_volume(final_volume)

    def update_effects_volume(self):
        """Updates sound effects volume from configuration."""
        if not self.select_sound:
            return

        effects_volume = settings.config_manager.get("volume_effects", 0.7)
        master_volume = settings.config_manager.get("volume_master", 0.8)
        final_volume = effects_volume * master_volume

        self.select_sound.set_volume(final_volume)

    def update_all_volumes(self):
        """Updates all volumes from configuration."""
        self.update_music_volume()
        self.update_effects_volume()

    def play_select_sound(self):
        """Plays the selection sound."""
        if self.select_sound:
            self.select_sound.play()

    def stop_music(self):
        """Stops the music."""
        if self.music_loaded:
            pygame.mixer.music.stop()

    def get_select_sound(self) -> Optional[pygame.mixer.Sound]:
        """Returns the selection sound to inject into components."""
        return self.select_sound


class VolumeWatcher:
    """Monitors volume changes in the configuration."""

    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
        self.last_music_volume = settings.config_manager.get("volume_music", 0.5)
        self.last_effects_volume = settings.config_manager.get("volume_effects", 0.7)
        self.last_master_volume = settings.config_manager.get("volume_master", 0.8)
        
        # HACK: Read config directly at startup to force volume
        self._force_volume_from_config()

    def check_for_changes(self) -> bool:
        """
        Checks if volumes have changed in the configuration.
        Updates audio if necessary.

        Returns:
            True if changes were detected
        """
        new_music = settings.config_manager.get("volume_music", 0.5)
        new_effects = settings.config_manager.get("volume_effects", 0.7)
        new_master = settings.config_manager.get("volume_master", 0.8)

        changed = (
            new_music != self.last_music_volume or
            new_effects != self.last_effects_volume or
            new_master != self.last_master_volume
        )

        if changed:
            self.last_music_volume = new_music
            self.last_effects_volume = new_effects
            self.last_master_volume = new_master
            self.audio_manager.update_all_volumes()
            print(f"🎚️ Volumes updated")

        return changed
    
    def _force_volume_from_config(self):
        """HACK: Force le volume en lisant directement galad_config.json au démarrage."""
        try:
            with open("galad_config.json", "r") as f:
                config = json.load(f)

            # Récupérer les volumes
            volume_master = config.get("volume_master", 0.8)
            volume_music = config.get("volume_music", 0.5)
            volume_effects = config.get("volume_effects", 0.7)

            # Calculer et appliquer le volume final pour la musique
            final_music_volume = volume_music * volume_master
            pygame.mixer.music.set_volume(final_music_volume)

            # Appliquer le volume aux effets sonores si disponible
            if self.audio_manager.select_sound:
                final_effects_volume = volume_effects * volume_master
                self.audio_manager.select_sound.set_volume(
                    final_effects_volume)

            print(
                f"🎚️ Volume forcé au démarrage: musique={final_music_volume:.3f}, effets={final_effects_volume:.3f}")

        except Exception as e:
            print(f"⚠️ Erreur lors du chargement du volume: {e}")
            # Fallback: utiliser les valeurs par défaut
            pygame.mixer.music.set_volume(0.4)  # 0.5 * 0.8
