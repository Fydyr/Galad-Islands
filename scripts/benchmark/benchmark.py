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
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import gc
import cProfile
import pstats
import io
import csv
import platform
import psutil
from datetime import datetime
from contextlib import contextmanager

# Add project root directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

import esper
import pygame
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.spriteComponent import SpriteComponent
from src.components.events.flyChestComponent import FlyingChestComponent
from src.game import GameEngine
from src.factory.unitType import UnitType
from src.factory.unitFactory import UnitFactory
from src.settings.settings import config_manager
from src.ia.BaseAi import BaseAi
from src.ia.KamikazeAi import KamikazeAiProcessor
from src.processeurs.ai.DruidAIProcessor import DruidAIProcessor
from src.processeurs.ai.architectAIProcessor import ArchitectAIProcessor
from src.processeurs.ai.aiLeviathanProcessor import AILeviathanProcessor
from src.ia.ia_maraudeur import MaraudeurAI


# Global variables to store original AI processor methods and stats
original_ai_methods = {}
ai_stats = {
    'kamikaze_ai': {'total_time': 0.0, 'calls': 0},
    'druid_ai': {'total_time': 0.0, 'calls': 0},
    'architect_ai': {'total_time': 0.0, 'calls': 0},
    'leviathan_ai': {'total_time': 0.0, 'calls': 0},
}


# Cette fonction sera définie localement dans benchmark_full_game_simulation


@dataclass
class BenchmarkResult:
    """Benchmark result."""
    name: str
    duration: float
    operations: int
    ops_per_second: float
    memory_mb: float


class GameProfiler:
    """Profiler pour mesurer l'impact de chaque système du jeu."""
    
    def __init__(self):
        self.timers = {}
        self.call_counts = {}
        self.peak_times = {}
        
    @contextmanager
    def profile_section(self, section_name: str):
        """Context manager pour profiler une section."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            
            if section_name not in self.timers:
                self.timers[section_name] = 0.0
                self.call_counts[section_name] = 0
                self.peak_times[section_name] = 0.0
                
            self.timers[section_name] += elapsed
            self.call_counts[section_name] += 1
            self.peak_times[section_name] = max(self.peak_times[section_name], elapsed)
    
    def get_stats(self, total_time: float) -> Dict[str, Any]:
        """Retourne les statistiques de profilage."""
        stats = {}
        for section, total_section_time in self.timers.items():
            percentage = (total_section_time / total_time * 100) if total_time > 0 else 0
            avg_time_ms = (total_section_time / self.call_counts[section] * 1000) if self.call_counts[section] > 0 else 0
            peak_time_ms = self.peak_times[section] * 1000
            
            stats[section] = {
                'total_time': total_section_time,
                'percentage': percentage,
                'call_count': self.call_counts[section],
                'avg_time_ms': avg_time_ms,
                'peak_time_ms': peak_time_ms
            }
        
        return stats
    
    def reset(self):
        """Reset toutes les statistiques."""
        self.timers.clear()
        self.call_counts.clear()
        self.peak_times.clear()


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

    def _get_system_info(self) -> Dict[str, Any]:
        """Collecte les informations système pour l'export CSV."""
        try:
                from src.settings.settings import config_manager
                return {
                'timestamp': datetime.now().isoformat(),
                'os': platform.system(),
                'os_version': platform.release(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'cpu_freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'cpu_freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'cpu_usage_percent': psutil.cpu_percent(interval=0.1),
                'memory_usage_percent': psutil.virtual_memory().percent,
                'vsync': config_manager.get('vsync', True),
                'max_fps': int(config_manager.get('max_fps', 60)),
            }
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Erreur collecte info système: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'os': 'unknown',
                'os_version': 'unknown',
                'python_version': platform.python_version(),
                'cpu_count': 0,
                'cpu_count_logical': 0,
                'cpu_freq_current': 0,
                'cpu_freq_max': 0,
                'memory_total_gb': 0,
                'memory_available_gb': 0,
                'cpu_usage_percent': 0,
                'memory_usage_percent': 0,
            }

    def export_to_csv(self, result: BenchmarkResult, profiler_stats: Optional[Dict[str, Any]] = None, 
                     ai_stats: Optional[Dict[str, Dict[str, Any]]] = None, filename: Optional[str] = None) -> str:
        """Exporte les résultats de benchmark dans un fichier CSV avec informations système."""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.csv"
        
        # Préparer les données
        system_info = self._get_system_info()
        
        # Créer l'enregistrement principal
        row_data = {
            **system_info,
            'benchmark_name': result.name,
            'duration_s': result.duration,
            'total_frames': result.operations,
            'fps_average': result.ops_per_second,
            'memory_mb': result.memory_mb,
        }
        
        # Ajouter les stats de profilage si disponibles
        if profiler_stats:
            for section, stats in profiler_stats.items():
                row_data[f'profile_{section}_total_s'] = stats.get('total_time', 0)
                row_data[f'profile_{section}_calls'] = stats.get('call_count', 0)
                row_data[f'profile_{section}_avg_ms'] = stats.get('avg_time_ms', 0)
                row_data[f'profile_{section}_peak_ms'] = stats.get('peak_time_ms', 0)
                row_data[f'profile_{section}_percent'] = stats.get('percentage', 0)
        
        # Ajouter les stats IA si disponibles
        if ai_stats:
            for ai_type, stats in ai_stats.items():
                row_data[f'ai_{ai_type}_total_s'] = stats.get('time', 0)
                row_data[f'ai_{ai_type}_calls'] = stats.get('calls', 0)
                if stats.get('calls', 0) > 0:
                    row_data[f'ai_{ai_type}_avg_ms'] = (stats.get('time', 0) / stats.get('calls', 1)) * 1000
                else:
                    row_data[f'ai_{ai_type}_avg_ms'] = 0
        
        # Vérifier si le fichier existe pour les headers
        file_exists = os.path.exists(filename)
        
        # Écrire dans le CSV
        try:
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted(row_data.keys()))
                
                # Écrire les headers si nouveau fichier
                if not file_exists:
                    writer.writeheader()
                
                # Écrire les données
                writer.writerow(row_data)
            
            if self.verbose:
                print(f"📊 Résultats exportés vers: {filename}")
            
            return filename
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Erreur export CSV: {e}")
            return ""

    def export_combined_maraudeur_results(self, results: List[BenchmarkResult]) -> str:
        """Export combined Maraudeur ML comparison results to CSV."""
        import csv
        from datetime import datetime
        import psutil
        import platform
        import sys
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"maraudeur_comparison_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # En-tête avec informations système
                writer.writerow(['=== MARAUDEUR ML COMPARISON BENCHMARK ==='])
                writer.writerow(['Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(['System', platform.system(), platform.release()])
                writer.writerow(['Python', sys.version.split()[0]])
                writer.writerow(['CPU', f"{psutil.cpu_count(logical=False)} cores ({psutil.cpu_count(logical=True)} logical)"])
                
                try:
                    cpu_freq = psutil.cpu_freq()
                    if cpu_freq:
                        writer.writerow(['CPU Frequency', f"{cpu_freq.current:.0f} MHz (max: {cpu_freq.max:.0f} MHz)"])
                except:
                    writer.writerow(['CPU Frequency', 'N/A'])
                
                memory = psutil.virtual_memory()
                writer.writerow(['Memory', f"{memory.total / (1024**3):.1f} GB total, {memory.available / (1024**3):.1f} GB available"])
                writer.writerow(['CPU Usage', f"{psutil.cpu_percent(interval=1):.1f}%"])
                writer.writerow(['Memory Usage', f"{memory.percent:.1f}%"])
                writer.writerow([])  # Ligne vide
                
                # En-tête des données de comparaison
                writer.writerow(['Configuration', 'FPS', 'Total Frames', 'Duration (s)', 'Memory (MB)'])
                
                # Données pour chaque configuration
                for result in results:
                    config_name = result.name or "Unknown"
                    if "default" in config_name:
                        config_name = "Défaut (ML désactivé)"
                    elif "with_ml" in config_name:
                        config_name = "ML activé"
                    
                    writer.writerow([
                        config_name,
                        f"{result.ops_per_second:.1f}",
                        result.operations,
                        f"{result.duration:.1f}",
                        f"{result.memory_mb:.1f}"
                    ])
                
                # Calcul et affichage de la comparaison
                if len(results) >= 2:
                    default_result = results[0]  # Défaut
                    ml_result = results[1]       # ML activé
                    
                    fps_diff = ml_result.ops_per_second - default_result.ops_per_second
                    fps_percent = (fps_diff / default_result.ops_per_second) * 100 if default_result.ops_per_second > 0 else 0
                    
                    writer.writerow([])  # Ligne vide
                    writer.writerow(['=== ANALYSE ==='])
                    writer.writerow(['Métrique', 'Défaut (ML off)', 'ML activé', 'Différence (%)', 'Amélioration'])
                    writer.writerow([
                        'FPS',
                        f"{default_result.ops_per_second:.1f}",
                        f"{ml_result.ops_per_second:.1f}",
                        f"{fps_percent:+.1f}%",
                        "Oui" if fps_percent > 5 else "Non" if fps_percent < -5 else "Négligeable"
                    ])
                    
                    frames_diff = ml_result.operations - default_result.operations
                    frames_percent = (frames_diff / default_result.operations) * 100 if default_result.operations > 0 else 0
                    writer.writerow([
                        'Frames totales',
                        default_result.operations,
                        ml_result.operations,
                        f"{frames_percent:+.1f}%",
                        "Oui" if frames_percent > 5 else "Non" if frames_percent < -5 else "Négligeable"
                    ])
            
            if self.verbose:
                print(f"📊 Comparaison Maraudeur exportée vers: {filename}")
                
                # Lancer automatiquement le script de lecture
                try:
                    import subprocess
                    subprocess.run([sys.executable, "read_benchmark_csv.py", filename], check=True)
                except Exception as e:
                    print(f"Note: Script de lecture non disponible: {e}")
            
            return filename
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Erreur export CSV combiné: {e}")
            return ""

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
            print("🔍 Component query test...")

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
            print("⚔️  Unit spawning test...")

        unit_types = [UnitType.SCOUT, UnitType.MARAUDEUR, UnitType.LEVIATHAN,
                     UnitType.DRUID, UnitType.ARCHITECT]

        start_time = time.perf_counter()
        operations = 0

        while time.perf_counter() - start_time < self.duration:
            # Try to create a unit
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
            print("💥 Combat simulation test...")

        # Create units for combat (réduit de 500 à 100 pour éviter OOM)
        num_units = 100
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

    def benchmark_full_game_simulation(self, num_ai_teams: int = 0, enable_profiling: bool = False, 
                                      disable_maraudeur_learning: bool = False, export_csv: bool = False) -> BenchmarkResult:
        """Benchmark of a complete game simulation with real game window and optional AI teams.
        
        Args:
            num_ai_teams: Number of AI teams to activate (0, 1, or 2)
            enable_profiling: Enable detailed performance profiling
            disable_maraudeur_learning: Disable machine learning for Maraudeur AI (performance test)
        """
        if self.verbose:
            print(f"🎮 Full game simulation test with {num_ai_teams} AI team(s)...")

        # Create a real game window
        try:
            # Ensure pygame is properly initialized
            if not pygame.get_init():
                pygame.init()
            
            # Ensure font is initialized
            if not pygame.font.get_init():
                pygame.font.init()
            
            # Create a controlled pygame window of 800x600 to avoid large display sizes in CI
            vsync_enabled = False
            try:
                from src.settings.settings import config_manager
                vsync_enabled = bool(config_manager.get('vsync', True))
            except Exception:
                vsync_enabled = False

            flags = pygame.RESIZABLE | pygame.DOUBLEBUF
            try:
                # Use explicit vsync if supported by SDL/driver
                screen = pygame.display.set_mode((800, 600), flags, vsync=1 if vsync_enabled else 0)
            except TypeError:
                # fallback if vsync kw is not supported
                screen = pygame.display.set_mode((800, 600), flags)
            pygame.display.set_caption(f"Galad Islands - Benchmark ({num_ai_teams} AI)")

            # Initialize the game
            # Create an instance of the game engine with the window
            game_engine = GameEngine(window=screen, bg_original=None, select_sound=None)
            game_engine.initialize()  # Initialize the game

            # Initialize AI teams if requested
            ai_teams = []
            if num_ai_teams >= 1:
                ai_team_1 = BaseAi(team_id=1)
                ai_team_1.enabled = True
                ai_team_1.self_play_mode = (num_ai_teams == 2)
                ai_teams.append(ai_team_1)
                if self.verbose:
                    print(f"✅ AI Team 1 initialized")
                    
            if num_ai_teams >= 2:
                ai_team_2 = BaseAi(team_id=2)
                ai_team_2.enabled = True
                ai_team_2.self_play_mode = True
                ai_teams.append(ai_team_2)
                if self.verbose:
                    print(f"✅ AI Team 2 initialized")

            # --- SPECIAL: If no AI teams requested, remove any pre-registered AI processors
            # from esper to ensure a clean "0 AI" benchmark (some processors may still
            # be registered by the game during initialization). We keep a list so we can
            # restore them afterwards.
            removed_processors: List = []
            if num_ai_teams == 0:
                try:
                    for proc in list(esper._processors):
                        # Identify AI processors by class name or BaseAi instances
                        clsname = proc.__class__.__name__
                        if 'AI' in clsname or 'Ai' in clsname or isinstance(proc, BaseAi):
                            removed_processors.append(proc)
                            try:
                                esper._processors.remove(proc)
                            except Exception:
                                # Best effort: ignore if already removed
                                pass

                    if self.verbose:
                        print(f"🔕 Removed {len(removed_processors)} AI processors for 0-AI benchmark")
                except Exception as e:
                    if self.verbose:
                        print(f"⚠️  Warning while disabling AI processors: {e}")
                    # Also remove any entities that carry AI-specific components so they won't
                    # skew the 0-AI benchmark (clear allied/enemy AI-controlled units)
                    try:
                        from src.components.ai.DruidAiComponent import DruidAiComponent
                        from src.components.ai.architectAIComponent import ArchitectAIComponent
                        from src.components.ai.aiLeviathanComponent import AILeviathanComponent
                        from src.components.core.KamikazeAiComponent import KamikazeAiComponent
                        from src.components.core.aiEnabledComponent import AIEnabledComponent

                        ai_components = [DruidAiComponent, ArchitectAIComponent, AILeviathanComponent,
                                         KamikazeAiComponent, AIEnabledComponent]

                        removed_entities = 0
                        for comp in ai_components:
                            try:
                                for ent, _ in list(esper.get_component(comp)):
                                    try:
                                        esper.delete_entity(ent)
                                        removed_entities += 1
                                    except Exception:
                                        pass
                            except Exception:
                                # If a component isn't present or get_component fails, continue
                                pass

                        if self.verbose:
                            print(f"🗑️  Removed {removed_entities} entities that had AI components for 0-AI benchmark")
                    except Exception:
                        # Non-blocking: if imports or deletes fail, continue
                        pass

            # Configurer l'apprentissage du Maraudeur si demandé
            original_learning_setting = config_manager.get("disable_ai_learning", False)
            
            if disable_maraudeur_learning:
                # Désactiver l'apprentissage via le config manager
                config_manager.set_disable_ai_learning(True)
                
                if self.verbose:
                    print("🧠 Apprentissage Maraudeur désactivé pour le test de performance")
            else:
                # S'assurer que l'apprentissage est activé
                config_manager.set_disable_ai_learning(False)
            
            if self.verbose:
                print("✅ Game initialized successfully")

        except Exception as e:
            if self.verbose:
                print(f"❌ Error during game initialization: {e}")
            return BenchmarkResult(
                name=f"full_game_simulation_{num_ai_teams}_ai",
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
        
        # Progressive unit spawning for AI stress test
        spawn_config = {
            'max_units_per_ai': 10,  # 10 unités par IA (sauf base)
            'spawn_interval': 1.5,   # Une unité toutes les 1.5 secondes
            'last_spawn_time': 0,
            'units_spawned_per_team': {Team.ALLY: 0, Team.ENEMY: 0}
        }
        
        # AI performance tracking - separated by type
        ai_stats = {
            'base_ai': {'time': 0.0, 'calls': 0},
            'kamikaze_ai': {'time': 0.0, 'calls': 0},
            'druid_ai': {'time': 0.0, 'calls': 0},
            'architect_ai': {'time': 0.0, 'calls': 0},
            'leviathan_ai': {'time': 0.0, 'calls': 0},
            'maraudeur_ai': {'time': 0.0, 'calls': 0},
            'scout_ai': {'time': 0.0, 'calls': 0},
            'rapid_ai': {'time': 0.0, 'calls': 0},
            'other_ai': {'time': 0.0, 'calls': 0},
        }
        
        # Initialize profiler
        profiler = GameProfiler() if enable_profiling else None
        cprofile_data = None
        original_process_methods = {}
        pr = None
        
        if enable_profiling:
            pr = cProfile.Profile()
            pr.enable()
        
        def patch_processors_for_profiling():
            """Patch tous les processeurs IA pour mesurer leurs performances"""
            if not enable_profiling or not profiler:
                return
                
            for processor in esper._processors:
                if hasattr(processor, 'process') and ('AI' in processor.__class__.__name__ or 'Ai' in processor.__class__.__name__):
                    # Identifier le type d'IA
                    ai_type = 'other_ai'
                    if isinstance(processor, KamikazeAiProcessor):
                        ai_type = 'kamikaze_ai'
                    elif isinstance(processor, DruidAIProcessor):
                        ai_type = 'druid_ai'
                    elif isinstance(processor, ArchitectAIProcessor):
                        ai_type = 'architect_ai'
                    elif isinstance(processor, AILeviathanProcessor):
                        ai_type = 'leviathan_ai'
                    elif 'Scout' in processor.__class__.__name__:
                        ai_type = 'scout_ai'
                    elif 'Rapid' in processor.__class__.__name__:
                        ai_type = 'rapid_ai'
                    
                    # Sauvegarder la méthode originale
                    if processor not in original_process_methods:
                        original_process_methods[processor] = processor.process
                    
                    # Créer une version profilée
                    def create_profiled_process(original_method, section_name, stats_key):
                        def profiled_process(*args, **kwargs):
                            start_time = time.perf_counter()
                            try:
                                if profiler:
                                    with profiler.profile_section(section_name):
                                        result = original_method(*args, **kwargs)
                                else:
                                    result = original_method(*args, **kwargs)
                                
                                # Mettre à jour les stats AI
                                ai_stats[stats_key]['calls'] += 1
                                return result
                            finally:
                                ai_stats[stats_key]['time'] += time.perf_counter() - start_time
                        return profiled_process
                    
                    # Appliquer le patch
                    processor.process = create_profiled_process(
                        original_process_methods[processor], 
                        ai_type,
                        ai_type
                    )
        
        def restore_ai_processors():
            """Restaurer les méthodes process originales"""
            for processor, original_method in original_process_methods.items():
                processor.process = original_method
        
        # Get references to all AI processors from esper
        def get_ai_processors():
            """Get all registered AI processors from esper"""
            ai_procs = {
                'base': [],
                'kamikaze': [],
                'druid': [],
                'architect': [],
                'leviathan': [],
                'scout': [],
                'other': []
            }
            
            for processor in esper._processors:
                if isinstance(processor, BaseAi):
                    ai_procs['base'].append(processor)
                elif isinstance(processor, KamikazeAiProcessor):
                    ai_procs['kamikaze'].append(processor)
                elif isinstance(processor, DruidAIProcessor):
                    ai_procs['druid'].append(processor)
                elif isinstance(processor, ArchitectAIProcessor):
                    ai_procs['architect'].append(processor)
                elif isinstance(processor, AILeviathanProcessor):
                    ai_procs['leviathan'].append(processor)
                elif 'Scout' in processor.__class__.__name__:
                    ai_procs['scout'].append(processor)
                elif 'AI' in processor.__class__.__name__ or 'Ai' in processor.__class__.__name__:
                    ai_procs['other'].append(processor)
            
            return ai_procs

        # Apply AI profiling patches after game initialization  
        original_maraudeur_update = None
        if enable_profiling:
            patch_processors_for_profiling()
            
            # Patch aussi la méthode _update_all_maraudeur_ais du GameEngine
            if hasattr(game_engine, '_update_all_maraudeur_ais'):
                original_maraudeur_update = game_engine._update_all_maraudeur_ais
                
                def patched_maraudeur_update(es, dt):
                    start_time = time.perf_counter()
                    result = original_maraudeur_update(es, dt)
                    end_time = time.perf_counter()
                    
                    ai_stats['maraudeur_ai']['time'] += (end_time - start_time)
                    ai_stats['maraudeur_ai']['calls'] += 1
                    
                    return result
                
                game_engine._update_all_maraudeur_ais = patched_maraudeur_update

        try:
            while time.perf_counter() - start_time < self.duration:
                frame_start = time.perf_counter()

                # Calculate delta time as in the real game
                dt = clock.tick(60) / 1000.0

                # Measure AI performance by type
                ai_processors = get_ai_processors()
                
                # Update Base AI avec profilage détaillé
                for ai in ai_teams:
                    ai_start = time.perf_counter()
                    try:
                        if profiler:
                            with profiler.profile_section("base_ai"):
                                ai.process(dt)
                        else:
                            ai.process(dt)
                        ai_stats['base_ai']['calls'] += 1
                    except Exception as e:
                        if self.verbose and frame_count % 300 == 0:
                            print(f"Base AI error: {e}")
                    ai_stats['base_ai']['time'] += time.perf_counter() - ai_start

                # Progressive unit spawning for AI stress test
                current_time = time.perf_counter() - start_time
                if (ai_teams and 
                    current_time - spawn_config['last_spawn_time'] > spawn_config['spawn_interval']):
                    
                    # Check if we can spawn more units for any team
                    for team in [Team.ALLY, Team.ENEMY]:
                        if spawn_config['units_spawned_per_team'][team] < spawn_config['max_units_per_ai']:
                            try:
                                # Types d'unités disponibles (sauf base)
                                unit_types = [UnitType.SCOUT, UnitType.MARAUDEUR, UnitType.DRUID, 
                                             UnitType.ARCHITECT, UnitType.LEVIATHAN, UnitType.KAMIKAZE]
                                
                                # Choisir un type d'unité au hasard
                                unit_type = random.choice(unit_types)
                                
                                # Position aléatoire selon l'équipe
                                if team == Team.ALLY:
                                    x = random.randint(50, 300)   # Côté gauche
                                    y = random.randint(100, 500)
                                    is_enemy = False
                                else:
                                    x = random.randint(500, 750)  # Côté droit  
                                    y = random.randint(100, 500)
                                    is_enemy = True
                                
                                # Créer l'unité avec PositionComponent
                                from components.core.positionComponent import PositionComponent
                                position = PositionComponent(x, y)
                                unit = UnitFactory(unit_type, is_enemy, position)
                                if unit:
                                    spawn_config['units_spawned_per_team'][team] += 1
                                    spawn_config['last_spawn_time'] = current_time
                                    
                                    if self.verbose and frame_count % 300 == 0:
                                        total_spawned = sum(spawn_config['units_spawned_per_team'].values())
                                        print(f"🎯 Unités spawned: {total_spawned}/20 (Team {team.name}: {spawn_config['units_spawned_per_team'][team]}/10)")
                                    
                                    break  # Une unité à la fois
                                    
                            except Exception as e:
                                if self.verbose:
                                    print(f"❌ Erreur spawn unité {unit_type} pour {team.name}: {e}")

                # Player activity simulation (every 2 seconds) - only if no AI
                if not ai_teams:
                    current_time = time.perf_counter() - start_time
                    if current_time - last_unit_spawn > 2.0:
                        # Simulate a click to create a unit
                        try:
                            # Random position on the map
                            click_x = random.randint(100, 700)
                            click_y = random.randint(100, 500)

                            # Simulate a mouse click
                            pygame.mouse.set_pos((click_x, click_y))

                            # Here we could call game methods to create units
                            # But since it's complex, we just count
                            units_spawned += 1
                            last_unit_spawn = current_time

                        except Exception as e:
                            if self.verbose and frame_count % 300 == 0:
                                print(f"Activity simulation error: {e}")

                # Game update avec profilage
                if profiler:
                    with profiler.profile_section("game_update"):
                        try:
                            game_engine._update_game(dt)
                        except Exception as e:
                            if self.verbose and frame_count % 300 == 0:
                                print(f"Game update error frame {frame_count}: {e}")
                else:
                    try:
                        game_engine._update_game(dt)
                    except Exception as e:
                        if self.verbose and frame_count % 300 == 0:
                            print(f"Game update error frame {frame_count}: {e}")

                # Rendering avec profilage
                if profiler:
                    with profiler.profile_section("rendering"):
                        try:
                            game_engine._render_game(dt)
                        except Exception as e:
                            if self.verbose and frame_count % 300 == 0:
                                print(f"Rendering error frame {frame_count}: {e}")
                    
                    with profiler.profile_section("display_flip"):
                        pygame.display.flip()
                else:
                    try:
                        game_engine._render_game(dt)
                        pygame.display.flip()
                    except Exception as e:
                        if self.verbose and frame_count % 300 == 0:
                            print(f"Rendering error frame {frame_count}: {e}")

                # Framerate control (60 FPS max)
                clock.tick(60)
                frame_time = time.perf_counter() - frame_start
                frame_times.append(frame_time)
                frame_count += 1

                # Periodic stats display
                if self.verbose and frame_count % 300 == 0:  # every 5 seconds at 60 FPS
                    current_fps = 1.0 / frame_time if frame_time > 0 else 0
                    total_ai_time = sum(stat['time'] for stat in ai_stats.values())
                    ai_avg_time = (total_ai_time / frame_count * 1000) if frame_count > 0 else 0
                    print(f"Frame {frame_count}: {current_fps:.1f} FPS, "
                          f"Entities: {len(esper._entities)}, "
                          f"AI avg: {ai_avg_time:.2f}ms/frame")

        except KeyboardInterrupt:
            if self.verbose:
                print("⏹️  Benchmark interrupted by user")
        except Exception as e:
            if self.verbose:
                print(f"❌ Error during simulation: {e}")

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Stop profiling
        if enable_profiling and pr is not None:
            pr.disable()
            cprofile_data = pstats.Stats(pr).strip_dirs().sort_stats('cumulative')

        # Calculate FPS statistics
        if frame_times:
            avg_fps = len(frame_times) / sum(frame_times)
            min_fps = 1.0 / max(frame_times) if frame_times else 0
            max_fps = 1.0 / min(frame_times) if frame_times else 0
        else:
            avg_fps = min_fps = max_fps = 0

        # Calculate AI statistics
        total_ai_time = sum(stat['time'] for stat in ai_stats.values())
        total_ai_calls = sum(stat['calls'] for stat in ai_stats.values())
        ai_percentage = (total_ai_time / duration * 100) if duration > 0 else 0
        ai_avg_ms = (total_ai_time / frame_count * 1000) if frame_count > 0 else 0

        if self.verbose:
            print(f"\n📊 PERFORMANCE SUMMARY ({num_ai_teams} AI)")
            print(f"🎬 Total frames: {frame_count}")
            print(f"🎯 Average FPS: {avg_fps:.1f}")
            print(f"📉 Minimum FPS: {min_fps:.1f}")
            print(f"📈 Maximum FPS: {max_fps:.1f}")
            
            if ai_teams or total_ai_calls > 0:
                print(f"\n🤖 AI PERFORMANCE BREAKDOWN:")
                print(f"   Total AI calls: {total_ai_calls}")
                print(f"   Total AI time: {total_ai_time:.3f}s ({ai_percentage:.1f}% of total)")
                print(f"   AI avg time: {ai_avg_ms:.2f}ms/frame")
                print(f"\n   📋 BY TYPE:")
                for ai_type, stats in ai_stats.items():
                    if stats['calls'] > 0:
                        pct = (stats['time'] / total_ai_time * 100) if total_ai_time > 0 else 0
                        avg_ms = (stats['time'] / stats['calls'] * 1000) if stats['calls'] > 0 else 0
                        print(f"   • {ai_type:15s}: {stats['calls']:6d} calls, "
                              f"{stats['time']:6.3f}s ({pct:5.1f}%), "
                              f"avg {avg_ms:.2f}ms/call")
            else:
                print(f"⚔️  Simulated units: {units_spawned}")
            
            # Detailed profiling results
            if profiler:
                print(f"\n🔍 DETAILED PERFORMANCE PROFILING:")
                profile_stats = profiler.get_stats(duration)
                sorted_stats = sorted(profile_stats.items(), key=lambda x: x[1]['percentage'], reverse=True)
                
                print(f"{'System':<20} {'%':<6} {'Total':<8} {'Calls':<7} {'Avg ms':<8} {'Peak ms':<8}")
                print("-" * 65)
                for section, stats in sorted_stats:
                    print(f"{section:<20} {stats['percentage']:5.1f}% "
                          f"{stats['total_time']:7.3f}s {stats['call_count']:6d} "
                          f"{stats['avg_time_ms']:7.2f} {stats['peak_time_ms']:7.2f}")
                
                # Top 10 most expensive functions from cProfile
                if cprofile_data:
                    print(f"\n🎯 TOP 10 MOST EXPENSIVE FUNCTIONS:")
                    print("-" * 60)
                    cprofile_data.print_stats(40)
            
            print(f"🏗️  Final entities: {len(esper._entities)}")

        # Restore AI processors
        if enable_profiling:
            restore_ai_processors()

        # Restore any processors we removed for the 0-AI run
        try:
            if 'removed_processors' in locals() and removed_processors:
                for p in removed_processors:
                    try:
                        # Avoid duplicates
                        if p not in esper._processors:
                            esper._processors.append(p)
                    except Exception:
                        pass
                if self.verbose:
                    print(f"🔁 Restored {len(removed_processors)} AI processors after 0-AI benchmark")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Error while restoring removed processors: {e}")
            
        # Restaurer les méthodes patchées
        if enable_profiling and original_maraudeur_update and hasattr(game_engine, '_update_all_maraudeur_ais'):
            game_engine._update_all_maraudeur_ais = original_maraudeur_update
            
        # Restaurer la configuration d'apprentissage originale
        if 'original_learning_setting' in locals():
            config_manager.set_disable_ai_learning(original_learning_setting)

        # Close properly
        try:
            # Don't quit pygame completely, just close the display
            # to allow multiple benchmark runs
            pygame.display.quit()
        except:
            pass

        # Clean up esper
        self._cleanup_esper()

        # Créer le résultat
        result = BenchmarkResult(
            name=f"full_game_simulation_{num_ai_teams}_ai",
            duration=duration,
            operations=frame_count,
            ops_per_second=avg_fps,
            memory_mb=self._get_memory_usage()
        )

        # Exporter vers CSV si profilage activé
        if enable_profiling and export_csv:
            try:
                profiler_stats_for_csv = None
                if profiler:
                    profiler_stats_for_csv = profiler.get_stats(duration)
                
                csv_filename = self.export_to_csv(
                    result=result,
                    profiler_stats=profiler_stats_for_csv,
                    ai_stats=ai_stats
                )
                
                if self.verbose and csv_filename:
                    print(f"📋 Données exportées dans: {csv_filename}")
                    
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Erreur export CSV: {e}")

        return result

    def benchmark_map_simulation(self) -> BenchmarkResult:
        """Map performance benchmark with units and gameplay simulation."""
        if self.verbose:
            print("🗺️  Map performance test with gameplay simulation...")

        # Initialize the map
        try:
            game_state = init_game_map(800, 600)
            grid = game_state["grid"]
            images = game_state["images"]
            camera = game_state["camera"]
        except Exception as e:
            if self.verbose:
                print(f"Error during map initialization: {e}")
            # Return an empty result in case of error
            return BenchmarkResult(
                name="map_performance",
                duration=self.duration,
                operations=0,
                ops_per_second=0,
                memory_mb=0
            )

        # Create units on the map (simple units to avoid errors)
        num_units = 100  # More units for a more realistic test
        units_created = 0

        # Create basic units directly (without UnitFactory which can fail)
        for i in range(num_units):
            try:
                entity = esper.create_entity()
                x, y = random.randint(50, 750), random.randint(50, 550)

                # Basic components for a unit
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
                    # Simple sprite (we avoid errors)
                    pass
                except:
                    pass  # Optional sprite

                units_created += 1
            except Exception as e:
                if self.verbose:
                    print(f"Unit creation error {i}: {e}")
                continue

        if self.verbose:
            print(f"📊 {units_created} units created on the map")

        # Simulate game frames with gameplay logic
        start_time = time.perf_counter()
        frame_count = 0
        clock = pygame.time.Clock()

        # Simulation statistics
        movements_processed = 0
        collisions_checked = 0
        events_spawned = 0

        while time.perf_counter() - start_time < self.duration:
            dt = clock.tick(60) / 1000.0  # 60 FPS max

            try:
                # Basic gameplay logic simulation

                # 1. Unit movement (simulation)
                for ent, (pos, vel) in esper.get_components(PositionComponent, VelocityComponent):
                    # Simple movement based on speed
                    direction = random.uniform(0, 2 * 3.14159)  # Random direction
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

                # 3. Spawn random events (flying chests)
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

                # 4. Update flying components (FlyingChest)
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
                    print(f"Error during simulation frame {frame_count}: {e}")
                break

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Calculate average FPS
        avg_fps = frame_count / duration if duration > 0 else 0

        if self.verbose:
            print(f"🎬 Simulated frames: {frame_count}")
            print(f"🎯 Average FPS: {avg_fps:.1f}")
            print(f"🏃 Movements processed: {movements_processed}")
            print(f"💥 Collisions checked: {collisions_checked}")
            print(f"🎁 Events spawned: {events_spawned}")

        # Clean up
        self._cleanup_esper()

        return BenchmarkResult(
            name="map_performance",
            duration=duration,
            operations=frame_count,
            ops_per_second=avg_fps,
            memory_mb=self._get_memory_usage()
        )

    def run_all_benchmarks(self, export_csv: bool = False, enable_profiling: bool = False) -> List[BenchmarkResult]:
        """Execute all benchmarks."""
        benchmarks = [
            self.benchmark_entity_creation,
            self.benchmark_component_queries,
            self.benchmark_unit_spawning,
            self.benchmark_combat_simulation,
        ]

        results = []
        for benchmark_func in benchmarks:
            try:
                result = benchmark_func()
                results.append(result)
                self.results.append(result)
                
                # Export CSV si demandé
                if export_csv:
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        csv_filename = f"{result.name}_{timestamp}.csv"
                        self.export_to_csv(result, filename=csv_filename)
                        print(f"   💾 CSV exporté: {csv_filename}")
                    except Exception as e:
                        if self.verbose:
                            print(f"   ⚠️  Erreur export CSV: {e}")
                
                # Nettoyage agressif de mémoire entre tests
                gc.collect()
                
            except Exception as e:
                print(f"❌ Error in {benchmark_func.__name__}: {e}")
                import traceback
                if self.verbose:
                    traceback.print_exc()
                continue

        return results
    
    def run_ai_benchmarks(self) -> List[BenchmarkResult]:
        """Execute AI-focused benchmarks with increasing AI complexity."""
        print("\n🤖 RUNNING AI PERFORMANCE BENCHMARKS")
        print("="*70)
        
        ai_configs = [
            (0, "No AI (baseline)"),
            (1, "1 AI team"),
            (2, "2 AI teams (AI vs AI)")
        ]
        
        results = []
        for num_ai, description in ai_configs:
            print(f"\n🔹 Testing: {description}")
            try:
                result = self.benchmark_full_game_simulation(num_ai_teams=num_ai, export_csv=False)
                results.append(result)
                self.results.append(result)
            except Exception as e:
                print(f"❌ Error with {description}: {e}")
                continue
        
        return results

    def run_maraudeur_learning_benchmark(self, export_csv: bool = False) -> List[BenchmarkResult]:
        """Compare Maraudeur performance with and without machine learning."""
        print("\n🧠 MARAUDEUR LEARNING IMPACT BENCHMARK")
        print("="*70)
        print("Compares performance with default config vs ML enabled for Maraudeur AI")
        
        results = []
        
        # Test 1 : Avec paramètres par défaut (apprentissage désactivé par défaut)
        print(f"\n🔹 Test 1: Maraudeur avec paramètres par défaut (ML désactivé)")
        result_default = self.benchmark_full_game_simulation(
            num_ai_teams=2, 
            enable_profiling=True,
            disable_maraudeur_learning=True,  # Paramètres par défaut du config
            export_csv=False  # Pas d'export individuel
        )
        result_default.name = "maraudeur_default_config"
        results.append(result_default)
        
        # Pause entre les tests pour éviter les interférences
        import time
        time.sleep(2)
        
        # Test 2 : Avec apprentissage activé (pour comparer l'impact)
        print(f"\n🔹 Test 2: Maraudeur avec apprentissage ML activé")
        result_with_ml = self.benchmark_full_game_simulation(
            num_ai_teams=2,
            enable_profiling=True, 
            disable_maraudeur_learning=False,  # Activer l'apprentissage
            export_csv=False  # Pas d'export individuel
        )
        result_with_ml.name = "maraudeur_with_ml"
        results.append(result_with_ml)
        
        # Analyser et afficher les différences
        print(f"\n📊 COMPARAISON DES PERFORMANCES:")
        print(f"{'Métrique':<25} {'Défaut (ML off)':<15} {'ML activé':<15} {'Différence':<15}")
        print("-" * 70)
        
        fps_diff = result_with_ml.ops_per_second - result_default.ops_per_second
        fps_percent = (fps_diff / result_default.ops_per_second) * 100 if result_default.ops_per_second > 0 else 0
        
        print(f"{'FPS Moyen':<25} {result_default.ops_per_second:<15.1f} {result_with_ml.ops_per_second:<15.1f} {fps_percent:<15.1f}%")
        
        frames_diff = result_with_ml.operations - result_default.operations  
        frames_percent = (frames_diff / result_default.operations) * 100 if result_default.operations > 0 else 0
        
        print(f"{'Frames totales':<25} {result_default.operations:<15} {result_with_ml.operations:<15} {frames_percent:<15.1f}%")
        
        # Conclusion
        print(f"\n💡 CONCLUSION:")
        if fps_percent > 5:
            print(f"✅ Activer l'apprentissage améliore les performances de {fps_percent:.1f}%")
        elif fps_percent < -5:
            print(f"⚠️  Activer l'apprentissage réduit les performances de {abs(fps_percent):.1f}%")
        else:
            print(f"📊 Impact négligeable de l'apprentissage sur les performances ({fps_percent:.1f}%)")
            
        # Exporter les résultats combinés si demandé
        if export_csv:
            try:
                self.export_combined_maraudeur_results(results)
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Erreur export CSV combiné: {e}")
        
        return results

    def print_summary(self):
        """Display a summary of results."""
        print("\n" + "="*70)
        print("📊 GALAD ISLANDS BENCHMARKS SUMMARY")
        print("="*70)

        total_ops = 0
        total_time = 0

        for result in self.results:
            print(f"\n🔹 {result.name.upper()}:")
            print(f"   ⏱️  Duration: {result.duration:.2f}s")
            print(f"   🔢 Operations: {result.operations}")
            print(f"   ⚡ Ops/sec: {result.ops_per_second:.0f}")
            print(f"   💾 Memory: {result.memory_mb:.2f} MB")

            total_ops += result.operations
            total_time += result.duration

        if self.results:
            avg_ops_per_sec = sum(r.ops_per_second for r in self.results) / len(self.results)
            print(f"\n🎯 GLOBAL AVERAGE: {avg_ops_per_sec:.0f} ops/sec")
            print(f"📈 TOTAL OPERATIONS: {total_ops}")
            print(f"⏱️  TOTAL TIME: {total_time:.2f}s")

        print("\n✅ Benchmarks completed!")

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
    parser = argparse.ArgumentParser(description="Simple benchmark for Galad Islands")
    parser.add_argument("--duration", "-d", type=int, default=10,
                       help="Duration of each test in seconds (default: 10)")
    parser.add_argument("--output", "-o", type=str,
                       help="Output file for JSON results")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose mode")
    parser.add_argument("--no-vsync", action="store_true",
                       help="Disable vsync during benchmark runs (may improve CPU-limited profiling)")
    parser.add_argument("--max-fps", type=int, default=None,
                       help="Override max FPS during the benchmark (0 = unlimited)")
    parser.add_argument("--full-game-only", action="store_true",
                       help="Run only the full game simulation benchmark")
    parser.add_argument("--ai-benchmark", action="store_true",
                       help="Run AI performance comparison (0, 1, 2 AI teams)")
    parser.add_argument("--maraudeur-benchmark", action="store_true",
                       help="Compare Maraudeur performance with/without ML learning")
    parser.add_argument("--num-ai", type=int, choices=[0, 1, 2],
                       help="Number of AI teams for full game benchmark (0-2)")
    parser.add_argument("--profile", action="store_true",
                       help="Enable detailed performance profiling")
    parser.add_argument("--export-csv", action="store_true",
                       help="Export results to CSV file (only with --profile)")

    args = parser.parse_args()

    print("🚀 Starting Galad Islands benchmarks...")
    print(f"⏱️  Duration per test: {args.duration}s")
    if args.profile:
        print("🔍 Detailed profiling enabled")

    benchmark = GaladBenchmark(duration=args.duration, verbose=args.verbose)

    # Apply benchmark-specific config override if requested
    try:
        if args.no_vsync:
            from src.settings.settings import config_manager
            config_manager.set("vsync", False)
            config_manager.save_config()
            if args.verbose:
                print("🔧 VSync disabled for benchmark run")
        if args.max_fps is not None:
            from src.settings.settings import config_manager
            config_manager.set("max_fps", int(args.max_fps))
            config_manager.save_config()
            if args.verbose:
                print(f"🔧 Max FPS set to {args.max_fps} for benchmark run")
    except Exception:
        # Non-critical: continue without overrides if any issue occurs
        pass

    if args.ai_benchmark:
        print("🤖 Running AI performance comparison...")
        results = benchmark.run_ai_benchmarks()
    elif args.maraudeur_benchmark:
        print("🧠 Running Maraudeur learning impact comparison...")
        results = benchmark.run_maraudeur_learning_benchmark(export_csv=args.export_csv)
    elif args.full_game_only:
        num_ai = args.num_ai if args.num_ai is not None else 0
        print(f"🎮 Running full game simulation with {num_ai} AI team(s)...")
        results = [benchmark.benchmark_full_game_simulation(num_ai_teams=num_ai, enable_profiling=args.profile, export_csv=args.export_csv)]
    else:
        results = benchmark.run_all_benchmarks(export_csv=args.export_csv, enable_profiling=args.profile)

    benchmark.print_summary()

    if args.output:
        benchmark.save_results(args.output)
        print(f"\n💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main()