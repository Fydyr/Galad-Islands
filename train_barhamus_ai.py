#!/usr/bin/env python3
"""
Script de pré-entraînement pour l'IA Barhamus (Maraudeur Zeppelin).
Simule des combats tactiques pour entraîner le modèle de décision.
Son entrainement en jeu existe toujours mais permet d'avoir une base plus solide et éviter de prendre trop en performance.
"""
import sys
import os
import time
import random
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier
import pickle
from sklearn.preprocessing import StandardScaler
import joblib

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Importer les composants nécessaires
from src.ia.ia_barhamus import BarhamusAI
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.constants.map_tiles import TileType
from src.settings.settings import TILE_SIZE
from src.components.globals.mapComponent import creer_grille, placer_elements
from src.functions.resource_path import get_resource_path
from src.ia.ia_barhamus import get_app_data_path

class BarhamusTrainer:
    """Entraîneur pour l'IA Barhamus avec simulation de combats tactiques."""

    def __init__(self):
        self.map_width = 50  # 50 tiles
        self.map_height = 50  # 50 tiles
        self.tile_size = TILE_SIZE
        self.max_simulation_time = 300.0  # 5 minutes max par simulation
        self.time_step = 0.1  # 100ms par step

        # Chemin des modèles
        self.models_dir = get_app_data_path()
        self.pretrained_model_path = os.path.join(self.models_dir, "barhamus_pretrained.pkl")

        # Statistiques d'entraînement
        self.total_experiences = 0
        self.successful_trainings = 0

    def create_mock_world(self):
        """Crée un monde simulé basique pour les tests."""
        class MockWorld:
            def __init__(self, trainer):
                self.trainer = trainer
                self.entities = {}
                self.components = {}

            def has_component(self, entity, component_type):
                return entity in self.components and component_type in self.components[entity]

            def component_for_entity(self, entity, component_type):
                if self.has_component(entity, component_type):
                    return self.components[entity][component_type]
                return None

            def create_entity(self):
                entity_id = len(self.entities)
                self.entities[entity_id] = {}
                self.components[entity_id] = {}
                return entity_id

            def get_component(self, component_type):
                """Simule esper.get_component"""
                results = []
                for entity_id, entity_components in self.components.items():
                    if component_type in entity_components:
                        results.append((entity_id, entity_components[component_type]))
                return results

            def get_components(self, *component_types):
                """Simule esper.get_components"""
                results = []
                for entity_id, entity_components in self.components.items():
                    components = []
                    for comp_type in component_types:
                        if comp_type in entity_components:
                            components.append(entity_components[comp_type])
                        else:
                            break
                    else:
                        results.append((entity_id, tuple(components)))
                return results

        return MockWorld(self)

    def create_barhamus_entity(self, world, x, y, team_id=1):
        """Crée une entité Barhamus avec tous les composants nécessaires."""
        entity = world.create_entity()

        # Position
        pos = PositionComponent()
        pos.x = x
        pos.y = y
        pos.direction = 0.0
        world.components[entity][PositionComponent] = pos

        # Vélocité
        vel = VelocityComponent()
        vel.currentSpeed = 0.0
        vel.maxUpSpeed = 5.0
        vel.maxReverseSpeed = 3.0
        world.components[entity][VelocityComponent] = vel

        # Santé
        health = HealthComponent()
        health.currentHealth = 100
        health.maxHealth = 100
        world.components[entity][HealthComponent] = health

        # Équipe
        team = TeamComponent()
        team.team_id = team_id
        world.components[entity][TeamComponent] = team

        # Composant spécial Maraudeur
        spe = SpeMaraudeur()
        spe.is_active = False
        spe.cooldown_timer = 0.0
        world.components[entity][SpeMaraudeur] = spe

        return entity

    def create_enemy_entity(self, world, x, y, team_id=2):
        """Crée une entité ennemie basique."""
        entity = world.create_entity()

        # Position
        pos = PositionComponent()
        pos.x = x
        pos.y = y
        pos.direction = 0.0
        world.components[entity][PositionComponent] = pos

        # Santé
        health = HealthComponent()
        health.currentHealth = 80
        health.maxHealth = 80
        world.components[entity][HealthComponent] = health

        # Équipe
        team = TeamComponent()
        team.team_id = team_id
        world.components[entity][TeamComponent] = team

        return entity

    def generate_tactical_scenarios(self, n_per_scenario=500):
        """Génère des scénarios tactiques pour l'entraînement."""
        scenarios = []
        experiences = []

        print("🎯 Génération des scénarios tactiques...")

        # Scénario 1: Combat rapproché défensif
        print("  → Combat rapproché défensif")
        for _ in range(n_per_scenario):
            world = self.create_mock_world()
            barhamus = self.create_barhamus_entity(world, 500, 500, 1)

            # Ennemis proches
            enemies = []
            for i in range(random.randint(2, 4)):
                angle = random.uniform(0, 2 * np.pi)
                distance = random.uniform(200, 400)
                x = 500 + distance * np.cos(angle)
                y = 500 + distance * np.sin(angle)
                enemy = self.create_enemy_entity(world, x, y, 2)
                enemies.append(enemy)

            scenario = {
                'world': world,
                'barhamus': barhamus,
                'enemies': enemies,
                'description': 'combat_rapproche_defensif',
                'expected_strategy': 'defensive'
            }
            scenarios.append(scenario)

        # Scénario 2: Combat à distance offensif
        print("  → Combat à distance offensif")
        for _ in range(n_per_scenario):
            world = self.create_mock_world()
            barhamus = self.create_barhamus_entity(world, 500, 500, 1)

            # Ennemis lointains
            enemies = []
            for i in range(random.randint(1, 3)):
                angle = random.uniform(0, 2 * np.pi)
                distance = random.uniform(800, 1200)
                x = 500 + distance * np.cos(angle)
                y = 500 + distance * np.sin(angle)
                enemy = self.create_enemy_entity(world, x, y, 2)
                enemies.append(enemy)

            scenario = {
                'world': world,
                'barhamus': barhamus,
                'enemies': enemies,
                'description': 'combat_distance_offensif',
                'expected_strategy': 'aggressive'
            }
            scenarios.append(scenario)

        # Scénario 3: Embuscade tactique
        print("  → Embuscade tactique")
        for _ in range(n_per_scenario):
            world = self.create_mock_world()
            barhamus = self.create_barhamus_entity(world, 500, 500, 1)

            # Un ennemi isolé
            enemy = self.create_enemy_entity(world, 800, 300, 2)
            enemies = [enemy]

            scenario = {
                'world': world,
                'barhamus': barhamus,
                'enemies': enemies,
                'description': 'embuscade_tactique',
                'expected_strategy': 'tactical'
            }
            scenarios.append(scenario)

        # Scénario 4: Fuite défensive
        print("  → Fuite défensive")
        for _ in range(n_per_scenario):
            world = self.create_mock_world()
            barhamus = self.create_barhamus_entity(world, 500, 500, 1)

            # Santé basse, ennemis nombreux
            health = world.components[barhamus][HealthComponent]
            health.currentHealth = random.uniform(20, 40)

            enemies = []
            for i in range(random.randint(3, 6)):
                angle = random.uniform(0, 2 * np.pi)
                distance = random.uniform(300, 600)
                x = 500 + distance * np.cos(angle)
                y = 500 + distance * np.sin(angle)
                enemy = self.create_enemy_entity(world, x, y, 2)
                enemies.append(enemy)

            scenario = {
                'world': world,
                'barhamus': barhamus,
                'enemies': enemies,
                'description': 'fuite_defensive',
                'expected_strategy': 'defensive'
            }
            scenarios.append(scenario)

        return scenarios

    def _create_real_grid(self):
        """Crée une vraie grille de jeu avec tous les éléments."""
        grid = creer_grille()  # Grille vide remplie de SEA
        placer_elements(grid)  # Place les bases, îles, mines, nuages
        return grid

    def _get_enemies_in_range(self, world, pos, entity, range_distance):
        """Retourne les ennemis à portée."""
        enemies_in_range = []
        team = world.components[entity][TeamComponent]

        for enemy_entity, components in world.components.items():
            if TeamComponent in components and components[TeamComponent].team_id != team.team_id:
                if PositionComponent in components:
                    enemy_pos = components[PositionComponent]
                    distance = np.sqrt((pos.x - enemy_pos.x)**2 + (pos.y - enemy_pos.y)**2)
                    if distance <= range_distance:
                        enemies_in_range.append(enemy_entity)

        return enemies_in_range

    def train_barhamus_model(self, n_scenarios=1000, n_iterations=3):
        """Entraîne le modèle Barhamus avec les scénarios générés."""
        print("\n🚀 PRÉ-ENTRAÎNEMENT DE L'IA BARHAMUS")
        print("=" * 60)

        all_experiences = []
        autosave_path = os.path.join(self.models_dir, "barhamus_training_autosave.pkl")

        # Reprise si autosave existant
        if os.path.exists(autosave_path):
            print(f"⚠️ Fichier autosave {autosave_path} détecté. Reprise possible.")
            try:
                with open(autosave_path, 'rb') as f:
                    all_experiences = pickle.load(f)
                print(f"➡️ Reprise avec {len(all_experiences)} expériences déjà collectées.")
            except Exception as e:
                print(f"Erreur lors du chargement du fichier autosave : {e}")

        try:
            # Créer une seule IA pour collecter les données
            ai_collector = BarhamusAI(entity=0)
            ai_collector.grid = self._create_real_grid()
            
            # Restaurer les données depuis l'autosave si elles existent
            X = [exp['state'] for exp in all_experiences]
            y = [exp['action'] for exp in all_experiences]
            all_experiences.clear() # Vider pour éviter la redondance mémoire

            for iteration in range(n_iterations):
                print(f"\n🔄 Itération {iteration + 1}/{n_iterations}")

                # Générer des scénarios
                print("🎯 Génération des scénarios tactiques...")
                scenarios = self.generate_tactical_scenarios(n_per_scenario=n_scenarios // 4)
                print(f"  ✓ {len(scenarios)} scénarios générés")

                total_scenarios = len(scenarios)
                for i, scenario in enumerate(scenarios):
                    if (i + 1) % (total_scenarios // 4 or 1) == 0:
                        print(f"  Simulation: {i + 1}/{total_scenarios} scénarios ({(i + 1) * 100 // total_scenarios}%)")
                    
                    # Extraire l'état et l'action attendue
                    world = scenario['world']
                    barhamus_entity = scenario['barhamus']
                    pos = world.components[barhamus_entity][PositionComponent]
                    health = world.components[barhamus_entity][HealthComponent]
                    team = world.components[barhamus_entity][TeamComponent]
                    
                    state = ai_collector._analyze_situation(world, pos, health, team)
                    
                    # Utiliser la logique par défaut pour déterminer la "meilleure" action pour ce scénario
                    action = ai_collector._get_default_action(state)
                    
                    X.append(state)
                    y.append(action)
                    
                    # Sauvegarde périodique
                    if len(X) % 5000 == 0 and len(X) > 0:
                        experiences_to_save = [{'state': s, 'action': a} for s, a in zip(X, y)]
                        with open(autosave_path, 'wb') as f:
                            pickle.dump(experiences_to_save, f)
                        print(f"💾 Sauvegarde auto: {len(X)} expériences")

                print(f"  ✓ Itération {iteration + 1} terminée: {len(X)} expériences totales")

        except KeyboardInterrupt:
            print("\n⏹️ Interruption utilisateur (Ctrl+C) : sauvegarde des expériences...")
            experiences_to_save = [{'state': s, 'action': a} for s, a in zip(X, y)]
            with open(autosave_path, 'wb') as f:
                pickle.dump(experiences_to_save, f)
            print(f"✅ Expériences sauvegardées dans {autosave_path}")
            raise
        except Exception as e:
            print(f"\n💥 Exception inattendue : {e}\nSauvegarde des expériences...")
            experiences_to_save = [{'state': s, 'action': a} for s, a in zip(X, y)]
            with open(autosave_path, 'wb') as f:
                pickle.dump(experiences_to_save, f)
            print(f"✅ Expériences sauvegardées dans {autosave_path}")
            raise
        finally:
            if X:
                print("\n💾 Sauvegarde automatique des expériences...")
                experiences_to_save = [{'state': s, 'action': a} for s, a in zip(X, y)]
                with open(autosave_path, 'wb') as f:
                    pickle.dump(experiences_to_save, f)
                print(f"✅ Expériences sauvegardées dans {autosave_path}")

        print(f"\n📈 Total expériences collectées: {len(X)}")

        if len(X) < 100:
            print("⚠️ Pas assez d'expériences pour entraîner le modèle.")
            return None, None

        # Préparer les données d'entraînement

        X = np.array(X)
        y = np.array(y)

        # Calculer les poids basés sur les récompenses
        weights = np.ones(len(X))  # Poids uniformes, car nous n'utilisons plus de récompenses complexes

        print(f"  Dimensions: {X.shape[0]} échantillons, {X.shape[1]} features")

        # Split train/test
        X_train, X_test, y_train, y_test, weights_train, weights_test = train_test_split(
            X, y, weights, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )

        # Entraîner le modèle
        print("\n🎯 Entraînement du modèle Decision Tree...")
        model = DecisionTreeClassifier(
            random_state=42,
            max_depth=8,
            min_samples_split=20,
            min_samples_leaf=10
        )

        model.fit(X_train, y_train, sample_weight=weights_train)

        # Évaluer le modèle
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"✅ Précision du modèle: {accuracy:.3f}")

        # Entraîner le scaler
        print("\n🔧 Entraînement du scaler...")
        scaler = StandardScaler()
        scaler.fit(X_train)

        # Sauvegarder le modèle et le scaler dans un seul fichier compatible avec BarhamusAI
        os.makedirs(self.models_dir, exist_ok=True)
        model_data = {
            'decision_tree': model,
            'scaler': scaler,
            'is_trained': True
        }
        with open(self.pretrained_model_path, "wb") as f:
            pickle.dump(model_data, f)
        print(f"💾 Modèle et scaler sauvegardés: {self.pretrained_model_path}")

        print("=" * 60)
        print("✨ PRÉ-ENTRAÎNEMENT BARHAMUS TERMINÉ !")
        print("🎮 L'IA Barhamus est maintenant pré-entraînée et prête à jouer !")

        return model, scaler

def main():
    print("🤖 Pré-entraîneur IA Barhamus pour Galad Islands\n")
    import argparse
    parser = argparse.ArgumentParser(description='Pré-entraîneur IA Barhamus pour Galad Islands.')
    parser.add_argument('--n_scenarios', type=int, default=2000, help='Nombre de scénarios par type (défaut: 2000)')
    parser.add_argument('--n_iterations', type=int, default=5, help='Nombre d\'itérations d\'entraînement (défaut: 5)')
    parser.add_argument('--seed', type=int, default=42, help='Graine aléatoire pour reproductibilité (défaut: 42)')
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    trainer = BarhamusTrainer()
    model, scaler = trainer.train_barhamus_model(
        n_scenarios=args.n_scenarios,
        n_iterations=args.n_iterations
    )

    if model and scaler:
        print("\n🎮 Le modèle pré-entraîné est prêt à être utilisé dans le jeu!")
        print("💡 L'IA Barhamus chargera automatiquement le modèle si disponible.")
        print("🔄 Elle continuera à apprendre en jeu si l'option 'désactiver apprentissage IA' n'est pas cochée.")

if __name__ == "__main__":
    main()