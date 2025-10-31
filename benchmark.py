#!/usr/bin/env python3
"""
Simple benchmark program for Galad Islands

This program measures the performance of basic ECS operations:
- Entity creation
- Component queries
- Memory management
- Simulated unit spawning
"""

import sys
import os
import time
import argparse
import json
import random
from typing import Dict, List, Any
from dataclasses import dataclass
import gc

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import esper
import pygame
from components.core.positionComponent import PositionComponent
from components.core.healthComponent import HealthComponent
from components.core.teamComponent import TeamComponent
from components.core.team_enum import Team
from components.core.velocityComponent import VelocityComponent
from components.core.spriteComponent import SpriteComponent
from components.events.flyChestComponent import FlyingChestComponent
from src.game import GameEngine
from src.factory.unitType import UnitType
from src.factory.unitFactory import UnitFactory
from src.settings.settings import config_manager


@dataclass
class BenchmarkResult:
    """Benchmark result."""
    name: str
    duration: float
    operations: int
    ops_per_second: float
    memory_mb: float


class GaladBenchmark:
    """Simple benchmark for Galad Islands ECS operations."""

    def __init__(self, duration: int = 30, verbose: bool = False):
        self.duration = duration
        self.verbose = verbose
        self.results: List[BenchmarkResult] = []

        # Initialize pygame in headless mode
        pygame.init()
        pygame.display.set_mode((1, 1))

        # Clean up esper
        self._cleanup_esper()

    def _cleanup_esper(self):
        """Cleans up all esper entities."""
        for entity in list(esper._entities.keys()):
            esper.delete_entity(entity, immediate=True)

    def _get_memory_usage(self) -> float:
        """Simple estimation of memory usage."""
        return len(esper._entities) * 0.001  # Rough approximation

    def benchmark_entity_creation(self) -> BenchmarkResult:
        """Entity creation benchmark."""
        if self.verbose:
            print("🔨 Entity creation test...")

        start_time = time.perf_counter()
        operations = 0

        while time.perf_counter() - start_time < self.duration:
            # Create a complete entity
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(random.randint(0, 800), random.randint(0, 600)))
            esper.add_component(entity, HealthComponent(100, 100))
            esper.add_component(entity, TeamComponent(Team.ALLY.value if random.random() > 0.5 else Team.ENEMY.value))
            esper.add_component(entity, VelocityComponent(random.uniform(-1, 1), random.uniform(-1, 1)))
            operations += 1

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Clean up
        self._cleanup_esper()

        return BenchmarkResult(
            name="entity_creation",
            duration=duration,
            operations=operations,
            ops_per_second=operations / duration if duration > 0 else 0,
            memory_mb=self._get_memory_usage()
        )

    def benchmark_component_queries(self) -> BenchmarkResult:
        """Component queries benchmark."""
        if self.verbose:
            print("🔍 Test de requêtes de composants...")

        # Create test entities
        num_entities = 10000
        for i in range(num_entities):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i % 800, i % 600))
            esper.add_component(entity, HealthComponent(100, 100))
            if i % 3 == 0:  # 1/3 entities have a team
                esper.add_component(entity, TeamComponent(Team.ALLY.value))

        start_time = time.perf_counter()
        operations = 0

        while time.perf_counter() - start_time < self.duration:
            # Complex query
            ally_count = 0
            for ent, (pos, health) in esper.get_components(PositionComponent, HealthComponent):
                if esper.has_component(ent, TeamComponent):
                    team = esper.component_for_entity(ent, TeamComponent)
                    if team.team_id == Team.ALLY.value:
                        ally_count += 1
            operations += 1

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Clean up
        self._cleanup_esper()

        return BenchmarkResult(
            name="component_queries",
            duration=duration,
            operations=operations,
            ops_per_second=operations / duration if duration > 0 else 0,
            memory_mb=self._get_memory_usage()
        )

    def benchmark_unit_spawning(self) -> BenchmarkResult:
        """Unit spawning benchmark."""
        if self.verbose:
            print("⚔️  Test de spawn d'unités...")

        unit_types = [UnitType.SCOUT, UnitType.MARAUDEUR, UnitType.LEVIATHAN,
                     UnitType.DRUID, UnitType.ARCHITECT]

        start_time = time.perf_counter()
        operations = 0

        while time.perf_counter() - start_time < self.duration:
            # Tenter de Create a unit
            unit_type = random.choice(unit_types)
            is_enemy = random.choice([True, False])
            x, y = random.randint(50, 750), random.randint(50, 550)

            try:
                unit = UnitFactory.create_unit(unit_type, x, y, is_enemy)
                if unit:
                    operations += 1
            except:
                pass  # Ignore creation errors

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Clean up
        self._cleanup_esper()

        return BenchmarkResult(
            name="unit_spawning",
            duration=duration,
            operations=operations,
            ops_per_second=operations / duration if duration > 0 else 0,
            memory_mb=self._get_memory_usage()
        )

    def benchmark_combat_simulation(self) -> BenchmarkResult:
        """Combat simulation benchmark."""
        if self.verbose:
            print("💥 Test de simulation de combat...")

        # Create units for combat
        num_units = 500
        units = []
        for i in range(num_units):
            entity = esper.create_entity()
            esper.add_component(entity, PositionComponent(i * 2 % 800, i * 2 % 600))
            esper.add_component(entity, HealthComponent(100, 100))
            esper.add_component(entity, TeamComponent(Team.ALLY.value if i < num_units // 2 else Team.ENEMY.value))
            units.append(entity)

        start_time = time.perf_counter()
        operations = 0

        while time.perf_counter() - start_time < self.duration:
            # Simulate combat rounds
            for i in range(0, len(units) - 1, 2):
                unit1, unit2 = units[i], units[i + 1]

                # Check if the units are on opposite teams
                try:
                    team1 = esper.component_for_entity(unit1, TeamComponent)
                    team2 = esper.component_for_entity(unit2, TeamComponent)

                    if team1.team_id != team2.team_id:
                        # Simulated combat
                        health1 = esper.component_for_entity(unit1, HealthComponent)
                        health2 = esper.component_for_entity(unit2, HealthComponent)

                        damage = random.randint(5, 15)
                        health1.currentHealth -= damage
                        health2.currentHealth -= damage

                        operations += 1
                except:
                    pass

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Clean up
        self._cleanup_esper()

        return BenchmarkResult(
            name="combat_simulation",
            duration=duration,
            operations=operations,
            ops_per_second=operations / duration if duration > 0 else 0,
            memory_mb=self._get_memory_usage()
        )

    def benchmark_full_game_simulation(self) -> BenchmarkResult:
        """Benchmark of a complete game simulation with real game window."""
        if self.verbose:
            print("🎮 Test de simulation complète de partie avec fenêtre...")

        # Create a real game window
        try:
            # Create the pygame window
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Galad Islands - Benchmark de Performance")

            # Initialize the game
            # Create an instance of the game engine with the window
            game_engine = GameEngine(window=screen, bg_original=None, select_sound=None)
            game_engine.initialize()  # Initialize the game

            if self.verbose:
                print("✅ Jeu initialisé avec succès")

        except Exception as e:
            if self.verbose:
                print(f"❌ Erreur lors de l'initialisation du jeu: {e}")
            return BenchmarkResult(
                name="full_game_simulation",
                duration=self.duration,
                operations=0,
                ops_per_second=0,
                memory_mb=0
            )

        # Performance statistics
        frame_times = []
        frame_count = 0
        start_time = time.perf_counter()
        clock = pygame.time.Clock()

        # Variables to simulate player activity
        last_unit_spawn = 0
        units_spawned = 0

        try:
            while time.perf_counter() - start_time < self.duration:
                frame_start = time.perf_counter()

                # Calculate delta time as in the real game
                dt = clock.tick(60) / 1000.0

                # Player activity simulation (every 2 seconds)
                current_time = time.perf_counter() - start_time
                if current_time - last_unit_spawn > 2.0:
                    # Simulate a click to Create a unit
                    try:
                        # Random position on the map
                        click_x = random.randint(100, 700)
                        click_y = random.randint(100, 500)

                        # Simulate a mouse click
                        pygame.mouse.set_pos((click_x, click_y))

                        # Ici on pourrait appeler les méthodes du jeu to create units
                        # Mais as it\'s complex, we just count
                        units_spawned += 1
                        last_unit_spawn = current_time

                    except Exception as e:
                        if self.verbose and frame_count % 300 == 0:
                            print(f"Erreur simulation activité: {e}")

                # Game update
                try:
                    game_engine._update_game(dt)
                except Exception as e:
                    if self.verbose and frame_count % 300 == 0:
                        print(f"Erreur mise à jour jeu frame {frame_count}: {e}")

                # Rendering
                try:
                    game_engine._render_game(dt)
                    pygame.display.flip()
                except Exception as e:
                    if self.verbose and frame_count % 300 == 0:
                        print(f"Erreur rendu frame {frame_count}: {e}")

                # Framerate control (60 FPS max)
                clock.tick(60)
                frame_time = time.perf_counter() - frame_start
                frame_times.append(frame_time)
                frame_count += 1

                # Periodic stats display
                if self.verbose and frame_count % 300 == 0:  # every 2 seconds at 60 FPS
                    current_fps = 1.0 / frame_time if frame_time > 0 else 0
                    print(f"Frame {frame_count}: {current_fps:.1f} FPS, "
                          f"Entités: {len(esper._entities)}, Unités spawnées: {units_spawned}")

        except KeyboardInterrupt:
            if self.verbose:
                print("⏹️  Benchmark interrompu par l'utilisateur")
        except Exception as e:
            if self.verbose:
                print(f"❌ Erreur pendant la simulation: {e}")

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Calculate statistics FPS
        if frame_times:
            avg_fps = len(frame_times) / sum(frame_times)
            min_fps = 1.0 / max(frame_times) if frame_times else 0
            max_fps = 1.0 / min(frame_times) if frame_times else 0
        else:
            avg_fps = min_fps = max_fps = 0

        if self.verbose:
            print(f"🎬 Frames totales: {frame_count}")
            print(f"🎯 FPS moyens: {avg_fps:.1f}")
            print(f"📉 FPS minimum: {min_fps:.1f}")
            print(f"📈 FPS maximum: {max_fps:.1f}")
            print(f"⚔️  Unités simulées: {units_spawned}")
            print(f"🏗️  Entités finales: {len(esper._entities)}")

        # Close properly
        try:
            pygame.quit()
        except:
            pass

        # Clean up esper
        self._cleanup_esper()

        return BenchmarkResult(
            name="full_game_simulation",
            duration=duration,
            operations=frame_count,
            ops_per_second=avg_fps,
            memory_mb=self._get_memory_usage()
        )
        """Benchmark des performances of the map avec units et simulation de gameplay."""
        if self.verbose:
            print("🗺️  Test des performances de la map avec simulation de gameplay...")

        # Initialize the map
        try:
            game_state = init_game_map(800, 600)
            grid = game_state["grid"]
            images = game_state["images"]
            camera = game_state["camera"]
        except Exception as e:
            if self.verbose:
                print(f"Erreur lors de l'initialisation de la map: {e}")
            # Return an empty result in case of error
            return BenchmarkResult(
                name="map_performance",
                duration=self.duration,
                operations=0,
                ops_per_second=0,
                memory_mb=0
            )

        # Create units on the map (simple units to avoid errors)
        num_units = 100  # Plus d'units pour un test plus réaliste
        units_created = 0

        # Create basic units directement (sans UnitFactory qui peut échouer)
        for i in range(num_units):
            try:
                entity = esper.create_entity()
                x, y = random.randint(50, 750), random.randint(50, 550)

                # components de base pour une unit
                esper.add_component(entity, PositionComponent(x, y))
                esper.add_component(entity, HealthComponent(100, 100))
                esper.add_component(entity, TeamComponent(Team.ALLY.value if i < num_units // 2 else Team.ENEMY.value))
                esper.add_component(entity, VelocityComponent(
                    currentSpeed=random.uniform(0.5, 2.0),
                    maxUpSpeed=2.0,
                    maxReverseSpeed=-1.0,
                    terrain_modifier=1.0
                ))

                # Add a sprite if possible
                try:
                    # Sprite simple (we avoid errors)
                    pass
                except:
                    pass  # Sprite optionnel

                units_created += 1
            except Exception as e:
                if self.verbose:
                    print(f"Erreur création unité {i}: {e}")
                continue

        if self.verbose:
            print(f"📊 {units_created} unités créées sur la map")

        # Simulate game frames avec logique de gameplay
        start_time = time.perf_counter()
        frame_count = 0
        clock = pygame.time.Clock()

        # Statistiques de simulation
        movements_processed = 0
        collisions_checked = 0
        events_spawned = 0

        while time.perf_counter() - start_time < self.duration:
            dt = clock.tick(60) / 1000.0  # 60 FPS max

            try:
                # Simulation de logique de gameplay basique

                # 1. Mouvement des units (simulation)
                for ent, (pos, vel) in esper.get_components(PositionComponent, VelocityComponent):
                    # Déplacement simple basé sur la vitesse
                    direction = random.uniform(0, 2 * 3.14159)  # Direction aléatoire
                    speed = vel.currentSpeed * dt * 30

                    pos.x += speed * random.uniform(-1, 1)
                    pos.y += speed * random.uniform(-1, 1)

                    # Keep within map limits
                    pos.x = max(0, min(800, pos.x))
                    pos.y = max(0, min(600, pos.y))

                    movements_processed += 1

                # 2. Simple collision checks (every 10 frames)
                if frame_count % 10 == 0:
                    positions = list(esper.get_component(PositionComponent))
                    for i, (ent1, pos1) in enumerate(positions):
                        for ent2, pos2 in positions[i+1:]:
                            # Simple distance
                            dx = pos1.x - pos2.x
                            dy = pos1.y - pos2.y
                            distance = (dx*dx + dy*dy) ** 0.5
                            if distance < 20:  # Collision if < 20 pixels
                                collisions_checked += 1

                # 3. Spawn d'événements aléatoires (coffres volants)
                if random.random() < 0.01:  # 1% chance per frame
                    try:
                        chest_entity = esper.create_entity()
                        x, y = random.randint(50, 750), random.randint(50, 550)
                        esper.add_component(chest_entity, PositionComponent(x, y))
                        esper.add_component(chest_entity, VelocityComponent(0, -1))
                        esper.add_component(chest_entity, FlyingChestComponent(
                            gold_amount=random.randint(25, 100),
                            max_lifetime=random.uniform(3, 8),
                            sink_duration=2.0
                        ))
                        events_spawned += 1
                    except:
                        pass

                # 4. Mise à jour des components volants (FlyingChest)
                for ent, (pos, vel, flying_chest) in esper.get_components(PositionComponent, VelocityComponent, FlyingChestComponent):
                    # Vertical movement
                    pos.y += vel.currentSpeed * dt * 10

                    # Update elapsed time
                    flying_chest.elapsed_time += dt
                    if flying_chest.elapsed_time >= flying_chest.max_lifetime:
                        # Delete entity (simulation)
                        pass  # In a real game, we would do esper.delete_entity

                frame_count += 1

            except Exception as e:
                if self.verbose:
                    print(f"Erreur lors de la simulation frame {frame_count}: {e}")
                break

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Calculer les Average FPS
        avg_fps = frame_count / duration if duration > 0 else 0

        if self.verbose:
            print(f"🎬 Frames simulées: {frame_count}")
            print(f"🎯 FPS moyens: {avg_fps:.1f}")
            print(f"🏃 Mouvements traités: {movements_processed}")
            print(f"💥 Collisions vérifiées: {collisions_checked}")
            print(f"🎁 Événements spawnés: {events_spawned}")

        # Clean up
        self._cleanup_esper()

        return BenchmarkResult(
            name="map_performance",
            duration=duration,
            operations=frame_count,
            ops_per_second=avg_fps,
            memory_mb=self._get_memory_usage()
        )

    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Execute all benchmarks."""
        benchmarks = [
            self.benchmark_entity_creation,
            self.benchmark_component_queries,
            self.benchmark_unit_spawning,
            self.benchmark_combat_simulation,
            self.benchmark_full_game_simulation,
        ]

        results = []
        for benchmark_func in benchmarks:
            try:
                result = benchmark_func()
                results.append(result)
                self.results.append(result)
            except Exception as e:
                print(f"❌ Erreur dans {benchmark_func.__name__}: {e}")
                continue

        return results

    def print_summary(self):
        """Display a summary of results."""
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DES BENCHMARKS GALAD ISLANDS")
        print("="*70)

        total_ops = 0
        total_time = 0

        for result in self.results:
            print(f"\n🔹 {result.name.upper()}:")
            print(f"   ⏱️  Durée: {result.duration:.2f}s")
            print(f"   🔢 Opérations: {result.operations}")
            print(f"   ⚡ Ops/sec: {result.ops_per_second:.0f}")
            print(f"   💾 Mémoire: {result.memory_mb:.2f} MB")

            total_ops += result.operations
            total_time += result.duration

        if self.results:
            avg_ops_per_sec = sum(r.ops_per_second for r in self.results) / len(self.results)
            print(f"\n🎯 MOYENNE GLOBALE: {avg_ops_per_sec:.0f} ops/sec")
            print(f"📈 TOTAL OPÉRATIONS: {total_ops}")
            print(f"⏱️  TEMPS TOTAL: {total_time:.2f}s")

        print("\n✅ Benchmarks terminés!")

    def save_results(self, filename: str):
        """Save results."""
        data = {
            "timestamp": time.time(),
            "duration": self.duration,
            "results": [
                {
                    "name": r.name,
                    "duration": r.duration,
                    "operations": r.operations,
                    "ops_per_second": r.ops_per_second,
                    "memory_mb": r.memory_mb
                }
                for r in self.results
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Benchmark simple pour Galad Islands")
    parser.add_argument("--duration", "-d", type=int, default=10,
                       help="Durée de chaque test en secondes (défaut: 10)")
    parser.add_argument("--output", "-o", type=str,
                       help="Fichier de sortie pour les résultats JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Mode verbeux")
    parser.add_argument("--full-game-only", action="store_true",
                       help="Exécuter seulement le benchmark de simulation complète du jeu")

    args = parser.parse_args()

    print("🚀 Démarrage des benchmarks Galad Islands...")
    print(f"⏱️  Durée par test: {args.duration}s")

    benchmark = GaladBenchmark(duration=args.duration, verbose=args.verbose)
    
    if args.full_game_only:
        print("🎮 Exécution du benchmark de simulation complète du jeu...")
        results = [benchmark.benchmark_full_game_simulation()]
    else:
        results = benchmark.run_all_benchmarks()

    benchmark.print_summary()

    if args.output:
        benchmark.save_results(args.output)
        print(f"\n💾 Résultats sauvegardés dans: {args.output}")


if __name__ == "__main__":
    main()