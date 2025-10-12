#!/usr/bin/env python3
"""

Script d'entraînement pour l'IA du Kamikaze.
Ce script force le ré-entraînement du modèle de l'IA du Kamikaze.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import esper
from src.processeurs.UnitAiProcessor import UnitAiProcessor

def train_kamikaze_model():
    """
    Force le ré-entraînement du modèle de l'IA du Kamikaze.
    """
    print("=" * 70)
    print("🚀 ENTRAÎNEMENT FORCÉ DE L'IA DU KAMIKAZE")
    print("=" * 70)

    # Supprimer l'ancien modèle s'il existe
    model_path = "src/models/kamikaze_ai_model.pkl"
    if os.path.exists(model_path):
        os.remove(model_path)
        print(f"🗑️ Ancien modèle supprimé : {model_path}")

    # Initialiser esper pour que la simulation fonctionne
    esper.clear_database()

    # Créer une grille factice pour l'initialisation du processeur
    # Une grille 30x30 avec quelques îles pour un entraînement plus réaliste
    dummy_grid = [[0 for _ in range(30)] for _ in range(30)]
    dummy_grid[15][15] = 2 # Ajouter une île au milieu
    
    # L'initialisation du UnitAiProcessor va maintenant déclencher l'entraînement
    # car le modèle n'existe plus.
    trainer = UnitAiProcessor(grid=dummy_grid)

    print("\n✅ Entraînement terminé. Le nouveau modèle est prêt à être utilisé.")

if __name__ == "__main__":
    train_kamikaze_model()