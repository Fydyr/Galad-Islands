"""Manager for saving and loading AI models."""

import os
import logging
from typing import Optional, TYPE_CHECKING

# Avoid circular import using TYPE_CHECKING
if TYPE_CHECKING:
    from src.processeurs.aiLeviathanProcessor import AILeviathanProcessor

logger = logging.getLogger(__name__)


class AIModelManager:
    """
    Centralized manager for saving and loading AI models.

    This manager allows to:
    - Automatically save the model at regular intervals
    - Load a pre-trained model on startup
    - Manage multiple model versions
    """

    DEFAULT_MODEL_DIR = "models"
    DEFAULT_MODEL_NAME = "leviathan_ai.pkl"
    BACKUP_MODEL_NAME = "leviathan_ai_backup.pkl"
    AUTO_SAVE_INTERVAL = 300.0  # Sauvegarder toutes les 5 minutes (300 secondes)

    def __init__(self, ai_processor: "AILeviathanProcessor", model_dir: Optional[str] = None):
        """
        Initializes the model manager.

        Args:
            ai_processor: AI processor containing the model
            model_dir: Directory for saving models (optional)
        """
        self.ai_processor = ai_processor
        self.model_dir = model_dir or self.DEFAULT_MODEL_DIR
        self.model_path = os.path.join(self.model_dir, self.DEFAULT_MODEL_NAME)
        self.backup_path = os.path.join(self.model_dir, self.BACKUP_MODEL_NAME)

        # Créer le répertoire s'il n'existe pas
        # Create the directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)

        # Timer for auto-saving
        self.time_since_last_save = 0.0
        self.auto_save_enabled = True

        # Load the model on startup if it exists
        self.load_model_if_exists()

    def load_model_if_exists(self) -> bool:
        """
        Loads a pre-trained model if it exists.

        Returns:
            True if a model was loaded, False otherwise
        """
        if os.path.exists(self.model_path):
            try:
                self.ai_processor.load_model(self.model_path)
                logger.info(f"AI model loaded from: {self.model_path}")
                return True
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                # Attempt to load the backup
                if os.path.exists(self.backup_path):
                    try:
                        self.ai_processor.load_model(self.backup_path)
                        logger.info(f"Backup model loaded from: {self.backup_path}")
                        return True
                    except Exception as e2:
                        logger.error(f"Error loading backup model: {e2}")
                return False
        else:
            logger.info("No pre-trained model found, starting with a new model.")
            return False

    def save_model(self, backup: bool = False) -> bool:
        """
        Saves the current model.

        Args:
            backup: If True, saves to the backup file

        Returns:
            True if saving was successful, False otherwise
        """
        save_path = self.backup_path if backup else self.model_path

        try:
            self.ai_processor.save_model(save_path)
            logger.info(f"AI model saved to: {save_path}")
            self.time_since_last_save = 0.0
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def auto_save(self, dt: float) -> bool:
        """
        Manages the automatic saving of the model.

        Args:
            dt: Delta time (time elapsed since the last frame)

        Returns:
            True if a save was performed, False otherwise
        """
        if not self.auto_save_enabled:
            return False

        self.time_since_last_save += dt

        if self.time_since_last_save >= self.AUTO_SAVE_INTERVAL:
            logger.info(f"Auto-saving model after {self.time_since_last_save:.1f}s")

            # First, save to the backup file
            backup_success = self.save_model(backup=True)

            # Then, save to the main file if the backup was successful
            if backup_success:
                return self.save_model(backup=False)

            return False

        return False

    def get_model_stats(self) -> dict:
        """
        Returns statistics for the current model.

        Returns:
            A dictionary containing the statistics
        """
        stats = self.ai_processor.get_statistics()
        stats['model_path'] = self.model_path
        stats['auto_save_enabled'] = self.auto_save_enabled
        stats['time_until_next_save'] = self.AUTO_SAVE_INTERVAL - self.time_since_last_save
        return stats

    def set_auto_save_enabled(self, enabled: bool):
        """Enables or disables auto-saving."""
        self.auto_save_enabled = enabled
        logger.info(f"Auto-save {'enabled' if enabled else 'disabled'}")

    def create_snapshot(self, name: str) -> bool:
        """
        Creates a snapshot (copy) of the current model with a custom name.

        Args:
            name: Name of the snapshot (without extension)

        Returns:
            True if the snapshot was created, False otherwise
        """
        snapshot_path = os.path.join(self.model_dir, f"{name}.pkl")
        try:
            self.ai_processor.save_model(snapshot_path)
            logger.info(f"Snapshot created: {snapshot_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return False
