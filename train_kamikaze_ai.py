#!/usr/bin/env python3
"""
Script d'entraînement avancé pour l'IA du Kamikaze (version mise à jour).
Optimisé pour la nouvelle version du KamikazeAiProcessor (évitemment, pathfinding, steering réaliste).
"""

from src.settings.settings import TILE_SIZE
from src.constants.map_tiles import TileType
from src.processeurs.KamikazeAiProcessor import KamikazeAiProcessor
from src.components.globals import mapComponent
import sys
import os
import time
from pathlib import Path
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
import esper

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class AdvancedKamikazeAiTrainer:
    """Entraîneur avancé pour l'IA du Kamikaze (nouvelle génération)."""

    def __init__(self):
        self.data_path = "src/models/kamikaze_ai_training_data.npz"
        self.processor = None

    def _generate_realistic_grid(self):
        grid = mapComponent.creer_grille()
        mapComponent.placer_elements(grid)
        mines = []
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == TileType.MINE:
                    mines.append({
                        'x': (x + 0.5) * TILE_SIZE,
                        'y': (y + 0.5) * TILE_SIZE
                    })
        return grid, mines

    def generate_advanced_training_data(self, n_simulations=1000):
        print(
            f"🎯 Génération de {n_simulations} simulations pour le Kamikaze AI...")

        esper.clear_database()
        grid, mines = self._generate_realistic_grid()
        self.processor = KamikazeAiProcessor(grid=grid, auto_train_model=False)

        states, actions, rewards = [], [], []

        try:
            for _ in range(n_simulations):
                s, a, r = self.processor.generate_training_sample()
                if s is not None:
                    states.append(s)
                    actions.append(a)
                    rewards.append(r)
        except KeyboardInterrupt:
            print("\n⏹️ Interruption utilisateur : sauvegarde des données en cours...")
        except Exception as e:
            print(f"💥 Erreur inattendue : {e}")

        if states:
            print("💾 Sauvegarde des données générées...")
            self._save_training_data(
                [s + [a] for s, a in zip(states, actions)], rewards)

        print(f"📈 Données générées : {len(states)} exemples")
        pos = sum(1 for r in rewards if r > 0)
        neg = len(rewards) - pos
        print(f"   ✅ Positives : {pos} ({pos/len(rewards)*100:.1f}%)")
        print(f"   ❌ Négatives : {neg} ({neg/len(rewards)*100:.1f}%)")

        return [s + [a] for s, a in zip(states, actions)], rewards

    def _save_training_data(self, states_actions, rewards, append=True):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        if append and os.path.exists(self.data_path):
            data = np.load(self.data_path, allow_pickle=True)
            old_states = data['states_actions'].tolist()
            old_rewards = data['rewards'].tolist()
            states_actions = old_states + states_actions
            rewards = old_rewards + rewards
        np.savez_compressed(self.data_path, states_actions=np.array(
            states_actions, dtype=object), rewards=np.array(rewards, dtype=object))
        print(f"✅ Données sauvegardées dans {self.data_path}.")

    def _load_training_data(self):
        if not os.path.exists(self.data_path):
            return None, None
        data = np.load(self.data_path, allow_pickle=True)
        return data['states_actions'].tolist(), data['rewards'].tolist()

    def train_advanced_model(self, use_cached_data=True):
        print("🚀 Entraînement du modèle Kamikaze (Random Forest)...")
        start_time = time.time()

        X, y = None, None
        if use_cached_data:
            X, y = self._load_training_data()
        if not X or not y:
            print("❌ Aucune donnée disponible, génération forcée de 1000 exemples...")
            X, y = self.generate_advanced_training_data(1000)

        X, y = np.array(X, dtype=object), np.array(y, dtype=float)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(
            n_estimators=60,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train.tolist(), y_train)
        mse = mean_squared_error(y_test, model.predict(X_test.tolist()))

        print(
            f"✅ Entraînement terminé en {time.time()-start_time:.2f}s | MSE: {mse:.4f}")

        model_path = "src/models/kamikaze_ai_rf_model.pkl"
        joblib.dump(model, model_path)
        print(f"💾 Modèle sauvegardé dans {model_path}")
        return model, mse


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Entraînement avancé du Kamikaze AI.")
    parser.add_argument('--batch', type=int, default=0,
                        help="Nombre de simulations à générer.")
    parser.add_argument('--train', action='store_true',
                        help="Entraîner le modèle.")
    args = parser.parse_args()

    trainer = AdvancedKamikazeAiTrainer()

    if args.batch > 0:
        trainer.generate_advanced_training_data(args.batch)

    if args.train:
        trainer.train_advanced_model()

    if not args.batch and not args.train:
        print("Utilisation :\n  python train_kamikaze_ai.py --batch 2000\n  python train_kamikaze_ai.py --train")


if __name__ == "__main__":
    main()
