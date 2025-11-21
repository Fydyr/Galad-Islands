"""
Centralized audio manager for music and sound effects.
"""

import pygame
import os
import json
import sys
import random
from typing import Optional, List
from src.settings import settings
from src.settings.localization import t
from src.constants.assets import MUSIC_MAIN_THEME
from src.functions.resource_path import get_resource_path

# Force UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class AudioManager:
    """Manages background music and sound effects."""

    def __init__(self):
        pygame.mixer.init()
        self.music_loaded = False
        self.current_music_path: Optional[str] = None
        self.select_sound: Optional[pygame.mixer.Sound] = None

        # Explosion sounds management
        self.explosion_sounds: List[pygame.mixer.Sound] = []
        self.explosion_channel = None
        self._explosion_initialized = False

        self._load_assets()

    def _load_assets(self):
        """Loads audio assets."""
        self.play_music(MUSIC_MAIN_THEME)
        self._load_sound_effects()

    def play_music(self, music_path: str, loops: int = -1):
        """Loads and plays a music file."""
        full_path = get_resource_path(music_path)
        if self.current_music_path == full_path:
            return  # Avoid reloading the same music
        try:
            pygame.mixer.music.load(full_path)
            self.update_music_volume()
            pygame.mixer.music.play(loops)
            self.music_loaded = True
            self.current_music_path = full_path
            print("🎵 Music loaded")
        except Exception as e:
            print(t("system.music_load_error", error=e))
            self.music_loaded = False

    def _load_sound_effects(self):
        """Loads sound effects."""
        try:
            self.select_sound = pygame.mixer.Sound(
                get_resource_path(os.path.join("assets", "sounds", "select_sound.ogg"))
            )
            self.update_effects_volume()
            print("🔊 Sound effects loaded")
        except Exception as e:
            print(t("system.sound_load_error", error=e))
            self.select_sound = None

    def _ensure_explosion_initialized(self):
        """Initializes the dedicated explosion channel if not already done."""
        if self._explosion_initialized:
            return

        try:
            # Reserve a dedicated channel for explosions (channel 0)
            # Music uses pygame.mixer.music (separate channel)
            pygame.mixer.set_reserved(1)  # Reserve channel 0
            self.explosion_channel = pygame.mixer.Channel(0)
            self._load_explosion_sounds()
            self._explosion_initialized = True
        except pygame.error as e:
            print(f"⚠️ Unable to initialize explosion manager: {e}")

    def _load_explosion_sounds(self):
        """Loads all explosion sounds from assets/sounds/explosion folder."""
        explosion_dir = os.path.join("assets", "sounds", "explosion")
        full_path = get_resource_path(explosion_dir)

        if not os.path.exists(full_path):
            print(f"⚠️ Explosion folder not found: {full_path}")
            return

        try:
            # List all audio files in the folder
            sound_files = [
                f for f in os.listdir(full_path)
                if f.endswith(('.ogg', '.mp3', '.wav'))
            ]

            if not sound_files:
                print(f"⚠️ No audio files found in {explosion_dir}")
                return

            # Load each sound file
            for sound_file in sound_files:
                sound_path = os.path.join(explosion_dir, sound_file)
                try:
                    sound = pygame.mixer.Sound(get_resource_path(sound_path))
                    self.explosion_sounds.append(sound)
                except Exception as e:
                    print(f"⚠️ Unable to load {sound_file}: {e}")

            if self.explosion_sounds:
                print(f"💥 {len(self.explosion_sounds)} explosion sound(s) loaded")
                self._update_explosion_volume()
            else:
                print("⚠️ No explosion sounds could be loaded")

        except Exception as e:
            print(f"⚠️ Error loading explosion sounds: {e}")

    def _update_explosion_volume(self):
        """Updates the volume of all explosion sounds."""
        if not self.explosion_sounds:
            return

        effects_volume = settings.config_manager.get("volume_effects", 0.7)
        master_volume = settings.config_manager.get("volume_master", 0.8)
        final_volume = effects_volume * master_volume

        for sound in self.explosion_sounds:
            sound.set_volume(final_volume)

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
        self._update_explosion_volume()

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

    def play_explosion_sound(self):
        """
        Plays a random explosion sound.
        Only plays the sound if no explosion sound is already playing.
        """
        # Ensure the manager is initialized
        self._ensure_explosion_initialized()

        if not self.explosion_sounds:
            return  # No sounds available

        # Check if a sound is already playing on the dedicated channel
        if self.explosion_channel and self.explosion_channel.get_busy():
            return  # An explosion sound is already playing, don't play another

        # Select a random sound
        sound = random.choice(self.explosion_sounds)

        # Play the sound on the dedicated channel
        if self.explosion_channel:
            self.explosion_channel.play(sound)
            print("💥 Explosion sound played")

    def is_explosion_playing(self) -> bool:
        """
        Checks if an explosion sound is currently playing.

        Returns:
            True if an explosion sound is playing, False otherwise
        """
        if self.explosion_channel:
            return self.explosion_channel.get_busy()
        return False

    def stop_all_explosions(self):
        """Stops all explosion sounds currently playing."""
        if self.explosion_channel:
            self.explosion_channel.stop()


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

            print("🎚️ Volumes updated")

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
            final_effects_volume = volume_effects * volume_master
            if self.audio_manager.select_sound:
                self.audio_manager.select_sound.set_volume(
                    final_effects_volume)

            print(
                f"🎚️ Volume forcé au démarrage: musique={final_music_volume:.3f}, effets={final_effects_volume:.3f}")

        except Exception as e:
            print(f"⚠️ Erreur lors du chargement du volume: {e}")
            # Fallback: utiliser les valeurs By default
            pygame.mixer.music.set_volume(0.4)  # 0.5 * 0.8
