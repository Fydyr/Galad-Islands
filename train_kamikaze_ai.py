#!/usr/bin/env python3
"""
Script d'entraînement avancé pour l'IA du Kamikaze.
Permet d'entraîner l'IA avec plus de données et de meilleurs paramètres.
"""


import sys
import os
import time
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import esper
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

from src.components.globals import mapComponent
from src.processeurs.KamikazeAiProcessor import KamikazeAiProcessor
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE
from sklearn.ensemble import RandomForestRegressor



class AdvancedKamikazeAiTrainer:
    """Entraîneur avancé pour l'IA du Kamikaze."""

    def __init__(self):
        self.processor = None
        self.data_path = "src/models/kamikaze_ai_training_data.npz"

    def _generate_realistic_grid(self):
        """Génère une grille réaliste en utilisant la vraie logique du jeu (mapComponent.py) et une liste de mines (positions)."""
        grid = mapComponent.creer_grille()
        mapComponent.placer_elements(grid)
        # Extraire les positions des mines à partir de la grille
        mines = []
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == TileType.MINE:
                    # Position centrale de la tuile
                    mines.append({'x': (x + 0.5) * TILE_SIZE, 'y': (y + 0.5) * TILE_SIZE})
        return grid, mines

    def generate_advanced_training_data(self, n_simulations=1000):
        """Génère des données d'entraînement avancées avec plus de simulations et une grille réaliste (îles, nuages, mines)."""
        print(f"🎯 Génération de données avancées: {n_simulations} simulations...")

        esper.clear_database()

        realistic_grid, mines = self._generate_realistic_grid()
        self.processor = KamikazeAiProcessor(grid=realistic_grid, auto_train_model=False)
        # Si besoin, passer les mines via une méthode ou paramètre officiel, sinon ignorer

        states, actions, rewards = [], [], []
        try:
            s, a, r = self.processor.generate_advanced_training_data(n_simulations)
            states.extend(s)
            actions.extend(a)
            rewards.extend(r)
        except KeyboardInterrupt:
            print("\n⏹️ Interruption utilisateur (Ctrl+C) : sauvegarde des données d'entraînement...")
            self._save_training_data([s + [a] for s, a in zip(states, actions)], rewards)
            print("✅ Données sauvegardées après interruption.")
            raise
        except Exception as e:
            print(f"\n💥 Exception inattendue : {e}\nSauvegarde des données d'entraînement...")
            self._save_training_data([s + [a] for s, a in zip(states, actions)], rewards)
            print("✅ Données sauvegardées après crash.")
            raise

        # Sauvegarde automatique si tout s'est bien passé
        if states:
            print("\n💾 Sauvegarde automatique des données d'entraînement...")
            self._save_training_data([s + [a] for s, a in zip(states, actions)], rewards)
            print("✅ Données sauvegardées.")

        print(f"📈 Données générées: {len(states)} exemples")
        print("🎯 Répartition des récompenses:")
        positive = sum(1 for r in rewards if r > 0)
        negative = len(rewards) - positive
        print(f"   Positives: {positive} ({positive/len(rewards)*100:.1f}%)")
        print(f"   Négatives: {negative} ({negative/len(rewards)*100:.1f}%)")

        return [s + [a] for s, a in zip(states, actions)], rewards

    def _save_training_data(self, states_actions, rewards, append=True):
        """Sauvegarde les données d'entraînement dans un fichier, en mode append si demandé."""
        print(f"💾 Sauvegarde des données d'entraînement dans {self.data_path}... (append={append})")
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        if append and os.path.exists(self.data_path):
            # Charger l'existant et concaténer
            data = np.load(self.data_path, allow_pickle=True)
            old_states = data['states_actions'].tolist()
            old_rewards = data['rewards'].tolist()
            states_actions = old_states + states_actions
            rewards = old_rewards + rewards
        np.savez_compressed(self.data_path, states_actions=np.array(states_actions, dtype=object), rewards=np.array(rewards, dtype=object))
        print("✅ Données sauvegardées.")

    def _load_training_data(self):
        """Charge les données d'entraînement depuis un fichier."""
        if not os.path.exists(self.data_path):
            return None, None
        
        print(f"💾 Chargement des données d'entraînement depuis {self.data_path}...")
        data = np.load(self.data_path, allow_pickle=True)
        print(f"✅ Données chargées: {len(data['states_actions'])} exemples.")
        return data['states_actions'].tolist(), data['rewards'].tolist()

    def train_advanced_model(self, n_simulations=3000, use_cached_data=False, only_train_on_existing_data=False, batch_append=True):
        """Entraîne un modèle avancé avec beaucoup de simulations."""
        start_time = time.time()

        print("=" * 70)
        print("🚀 ENTRAÎNEMENT AVANCÉ DE L'IA DU KAMIKAZE")
        print("=" * 70)
        print(f"🎯 Objectif: {n_simulations} simulations")
        print(f"⏰ Temps estimé: ~{n_simulations * 0.01:.1f} secondes")
        print()

        states_actions, rewards = None, None
        if use_cached_data or only_train_on_existing_data:
            states_actions, rewards = self._load_training_data()

        if only_train_on_existing_data:
            if not states_actions or not rewards:
                print("❌ Aucune donnée existante à utiliser pour l'entraînement.")
                return None, None
        else:
            # Générer les données d'entraînement (et append)
            new_states_actions, new_rewards = self.generate_advanced_training_data(n_simulations)
            self._save_training_data(new_states_actions, new_rewards, append=batch_append)
            # Charger toutes les données accumulées
            states_actions, rewards = self._load_training_data()

        print()
        print("🔧 Phase d'entraînement...")

        X = np.array(states_actions)
        y = np.array(rewards)

        # Split des données
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Nouveau modèle : RandomForestRegressor pour plus de robustesse
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(
            n_estimators=40,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        # Évaluation
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        training_time = time.time() - start_time

        print("✅ Entraînement terminé!")
        print()
        print("📊 RÉSULTATS DE LA FORÊT ALÉATOIRE:")
        print("-" * 40)
        print(f"⏰ Temps d'entraînement: {training_time:.2f} secondes")
        print(f"🎯 Erreur quadratique moyenne finale: {mse:.3f}")
        # Affichage robuste des paramètres du modèle
        params = model.get_params() if hasattr(model, 'get_params') else {}
        if 'n_estimators' in params:
            print(f"   - Nombre d'arbres: {params['n_estimators']}")
        if 'max_depth' in params:
            print(f"   - Profondeur max: {params['max_depth']}")
        print(f"   - Échantillons d'entraînement: {len(X_train)}")
        print(f"   - Échantillons de test: {len(X_test)}")
        print()

        # Sauvegarde du modèle sous un nom distinct
        rf_model_path = "src/models/kamikaze_ai_rf_model.pkl"
        joblib.dump(model, rf_model_path)
        print(f"💾 Modèle RandomForest sauvegardé : {rf_model_path}")

        return model, mse


def main():
    """Fonction principale pour l'entraînement avancé."""
    print("🤖 Entraîneur d'IA avancé pour le Kamikaze - Galad Islands")
    print()

    import argparse
    parser = argparse.ArgumentParser(description="Entraînement IA Kamikaze par batchs ou complet.")
    parser.add_argument('--batch', type=int, default=0, help="Nombre de simulations à générer et ajouter (batch). Si 0, pas de génération.")
    parser.add_argument('--train', action='store_true', help="Entraîner le modèle à partir de toutes les données accumulées.")
    parser.add_argument('--nocache', action='store_true', help="Ne pas utiliser les données en cache (force la génération d'un nouveau batch).")
    args = parser.parse_args()

    trainer = AdvancedKamikazeAiTrainer()

    if args.batch > 0:
        print(f"🔥 Génération d'un batch de {args.batch} simulations et ajout aux données...")
        trainer.generate_advanced_training_data(args.batch)
        print("✅ Batch ajouté. Tu peux relancer pour ajouter d'autres batchs.")

    if args.train:
        print("\n� Entraînement du modèle à partir de toutes les données accumulées...")
        model, mse = trainer.train_advanced_model(n_simulations=0, use_cached_data=True, only_train_on_existing_data=True)
        if model is not None:
            print()
            print("🎮 Le modèle avancé du Kamikaze est prêt à être utilisé dans le jeu!")
            print("💡 Le modèle est automatiquement chargé par KamikazeAiProcessor lors de l'initialisation.")
        else:
            print("❌ Entraînement impossible : pas de données.")

    if not args.batch and not args.train:
        print("Utilisation :\n  python train_kamikaze_ai.py --batch 5000   # Génère et ajoute 5000 simulations\n  python train_kamikaze_ai.py --train       # Entraîne le modèle sur toutes les données accumulées\n  (tu peux enchaîner plusieurs batchs avant d'entraîner)")


if __name__ == "__main__":
    main()