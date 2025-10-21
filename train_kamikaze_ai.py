#!/usr/bin/env python3
"""
Script d'entraînement avancé pour l'IA du Kamikaze (nouvelle génération).
Ce script est maintenant autonome et contient toute la logique de simulation
et d'entraînement, séparée du processeur de jeu.
"""

from src.components.globals import mapComponent as global_map_component
from src.processeurs.KamikazeAiProcessor import KamikazeAiProcessor
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE
import sys
import os
import time
from pathlib import Path
import random
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.ensemble import RandomForestRegressor
import esper
from tqdm import tqdm

from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.teamComponent import TeamComponent

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class AdvancedKamikazeAiTrainer:
    """Entraîneur avancé pour l'IA du Kamikaze avec progression et robustesse."""

    def __init__(self):
        self.data_path = "src/models/kamikaze_ai_training_data.npz"
        self.world_map = None

    def _generate_realistic_grid(self):
        grid = global_map_component.creer_grille()
        global_map_component.placer_elements(grid)
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
            f"🎯 Génération de {n_simulations} simulations pour l'IA Kamikaze...")
        esper.clear_database()
        self.world_map, mines = self._generate_realistic_grid()
        all_states, all_rewards = [], []

        try:
            states, rewards = self._run_simulations(n_simulations, mines)
            if states is not None:
                all_states.extend(states)
                all_rewards.extend(rewards)

        except KeyboardInterrupt:
            print("\n⏹️ Interruption utilisateur : sauvegarde en cours...")
        except Exception as e:
            print(f"💥 Erreur inattendue : {e}")

        if all_states:
            print("💾 Sauvegarde des données générées...")
            self._save_training_data(all_states, all_rewards)
        else:
            print("⚠️ Aucune donnée générée !")

        print(f"📈 Données générées : {len(all_states)} exemples")
        if all_rewards:
            pos = sum(1 for r in all_rewards if r > 0)
            neg = len(all_rewards) - pos if len(all_rewards) > 0 else 0
            print(f"   ✅ Positives : {pos} ({pos/len(all_rewards)*100:.1f}%" if len(all_rewards) > 0 else "0.0%")
            print(f"   ❌ Négatives : {neg} ({neg/len(all_rewards)*100:.1f}%" if len(all_rewards) > 0 else "0.0%")
        return all_states, all_rewards

    def _run_simulations(self, n_simulations, mines):
        """Exécute les simulations pour générer les données."""
        all_states = []
        all_rewards = []
        for _ in tqdm(range(n_simulations), desc="Simulations Kamikaze", ncols=80):
            # Position de l'unité (début aléatoire dans une zone "sûre")
            unit_pos = None
            while unit_pos is None or self.world_map[int(unit_pos.y // TILE_SIZE)][int(unit_pos.x // TILE_SIZE)] != 0:
                unit_pos = PositionComponent(x=random.uniform(100, 500), y=random.uniform(
                    100, 1400), direction=random.uniform(0, 360))

            # Cible (priorité sur les cibles importantes, sinon aléatoire)
            target_pos = None
            if random.random() < 0.7:
                target_pos = PositionComponent(x=1800, y=750)
            else:
                while target_pos is None or self.world_map[int(target_pos.y // TILE_SIZE)][int(target_pos.x // TILE_SIZE)] != 0:
                    target_pos = PositionComponent(x=random.uniform(1000, 1600), y=random.uniform(400, 1100))

            # Obstacles (mines, nuages, îles) : liste de tuples (x, y)
            obstacles = [(random.uniform(100, 1900), random.uniform(100, 1400)) for _ in range(random.randint(2, 6))]
            
            # Générer des menaces mobiles (projectiles)
            threats = []
            for _ in range(random.randint(1, 4)): # 1 à 4 menaces
                # Point de départ de la menace, souvent entre l'unité et la cible
                spawn_point = (np.array([unit_pos.x, unit_pos.y]) + np.array([target_pos.x, target_pos.y])) / 2.0
                spawn_point += np.random.rand(2) * 400 - 200 # Ajout d'un peu d'aléatoire

                # La menace vise approximativement la position de départ de l'unité
                direction_to_unit = np.array([unit_pos.x, unit_pos.y]) - spawn_point
                if np.linalg.norm(direction_to_unit) > 0:
                    direction_to_unit /= np.linalg.norm(direction_to_unit)
                threats.append({'pos': spawn_point, 'vel': direction_to_unit})

            # Simule la trajectoire
            states, rewards = self._simulate_trajectory(unit_pos, target_pos, obstacles, threats.copy())
            all_states.extend(states)
            all_rewards.extend(rewards)
        return all_states, all_rewards

    def _simulate_trajectory(self, unit_pos, target_pos, obstacles, threats):
        """Simule une trajectoire, pénalise les collisions et le blocage."""
        states, rewards = [], []
        boost_cooldown = 0.0
        speed = 50.0
        max_steps = 150
        threat_speed = 30.0 # Vitesse des projectiles ennemis

        pos = np.array([unit_pos.x, unit_pos.y], dtype=float)
        target = np.array([target_pos.x, target_pos.y], dtype=float)
        
        # Logique de cible mobile
        target_speed = 15.0  # Vitesse de la cible, plus lente que le kamikaze
        target_velocity = np.random.rand(2) * 2 - 1
        target_velocity /= np.linalg.norm(target_velocity)

        last_distance = np.linalg.norm(target - pos)
        stuck_counter = 0

        directions = [np.array([1, 0]), np.array([-1, 0]), np.array([0, 1]), np.array([0, -1]),
                      np.array([1, 1]), np.array([-1, 1]), np.array([1, -1]), np.array([-1, -1])]
        
        map_width_pixels = len(self.world_map[0]) * TILE_SIZE if self.world_map and self.world_map[0] else 1920
        map_height_pixels = len(self.world_map) * TILE_SIZE if self.world_map else 1500

        for step in range(max_steps):
            if boost_cooldown <= 0 and random.random() < 0.1:
                action = "boost"
                boost_cooldown = 10
                current_speed = speed * 2.0
            else:
                action = "move"
                current_speed = speed

            # Mettre à jour la position de la cible mobile
            if random.random() < 0.05: # 5% de chance de changer de direction
                target_velocity = np.random.rand(2) * 2 - 1
                target_velocity /= np.linalg.norm(target_velocity)
            
            target += target_velocity * target_speed * 0.1 # 0.1 est le pas de temps de simulation
            # Contraindre la cible à rester dans les limites de la carte
            target[0] = np.clip(target[0], 0, map_width_pixels)
            target[1] = np.clip(target[1], 0, map_height_pixels)

            # Mettre à jour la position des menaces
            for threat in threats:
                threat['pos'] += threat['vel'] * threat_speed * 0.1

            dir_vec = random.choice(directions)
            new_pos = pos + dir_vec * (current_speed * 0.1)

            collided = any(abs(new_pos[0] - ox) < TILE_SIZE and abs(new_pos[1] - oy) < TILE_SIZE for (ox, oy) in obstacles)

            dist = np.linalg.norm(target - new_pos)
            reward = 0.0

            if collided:
                reward -= 5.0
            elif dist < last_distance:
                reward += 1.0
            else:
                reward -= 0.5

            for threat in threats:
                if np.linalg.norm(new_pos - threat['pos']) < 100:
                    reward -= 2.0

            if dist < 50:
                reward += 10.0
                states.append([pos[0], pos[1], target[0], target[1], current_speed, dist, step / max_steps])
                rewards.append(reward)
                break

            if abs(dist - last_distance) < 1e-3:
                stuck_counter += 1
            else:
                stuck_counter = 0

            if stuck_counter > 10:
                reward -= 3.0
                break

            states.append([pos[0], pos[1], target[0], target[1], current_speed, dist, step / max_steps])
            rewards.append(reward)

            pos = new_pos
            last_distance = dist
            if boost_cooldown > 0:
                boost_cooldown -= 1

        return states, rewards

    def _save_training_data(self, states, rewards, append=True):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

        final_states = list(states)
        final_rewards = list(rewards)
        
        if append and os.path.exists(self.data_path):
            try:
                data = np.load(self.data_path, allow_pickle=True)
                old_states = data['states'].tolist() if 'states' in data and isinstance(data['states'], np.ndarray) else []
                old_rewards = data['rewards'].tolist() if 'rewards' in data and isinstance(data['rewards'], np.ndarray) else []
                
                final_states = old_states + final_states
                final_rewards = old_rewards + final_rewards
            except (IOError, ValueError, KeyError) as e:
                print(f"⚠️ Avertissement : Impossible de charger les données existantes. Le fichier sera écrasé. Erreur: {e}")

        np.savez_compressed(self.data_path,
                            states=np.array(final_states, dtype=object),
                            rewards=np.array(final_rewards, dtype=float))
        print(f"✅ Données sauvegardées dans {self.data_path}.")


    def _load_training_data(self):
        if not os.path.exists(self.data_path):
            return [], []
        data = np.load(self.data_path, allow_pickle=True)
        states = data['states'].tolist() if 'states' in data else []
        rewards = data['rewards'].tolist() if 'rewards' in data else []
        return states, rewards


    def train_advanced_model(self, use_cached_data=True):
        print("🚀 Entraînement du modèle Kamikaze (Random Forest)...")
        start_time = time.time()

        X, y = [], []
        
        if use_cached_data:
            X, y = self._load_training_data()
            if not X or not y:
                print("⚠️ Données mises en cache vides ou corrompues.")

        if not X or not y:
            print("❌ Aucune donnée disponible, génération forcée de 1000 exemples...")
            X, y = self.generate_advanced_training_data(n_simulations=1000)

        # Vérification de la cohérence des données
        if not X or not y:
            print("❌ Les données d'entraînement sont vides. Impossible d'entraîner le modèle.")
            return None, None
        elif len(X) != len(y):
            print(f"❌ Incohérence : X ({len(X)}) et y ({len(y)}) n'ont pas la même longueur.")
            return None, None

        X, y = np.array(X, dtype=object), np.array(y, dtype=float)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

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
