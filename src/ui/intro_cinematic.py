"""
Introduction cinematic for Galad Islands
"""

import pygame
import os
import math
import random
from src.functions.resource_path import get_resource_path
from src.settings.localization import t
from src.constants.assets import MUSIC_IN_CINEMATIC


class IntroCinematic:
    """Manages the game's introduction cinematic."""

    def __init__(self, surface, audio_manager=None):
        self.surface = surface
        self.audio_manager = audio_manager
        self.width, self.height = surface.get_size()

        # Load assets
        self._load_assets()

        # Cinematic state
        self.current_scene = 0
        self.scene_timer = 0
        self.global_timer = 0
        self.alpha = 0
        self.skip_requested = False
        self.finished = False

        # Particles for effects
        self.particles = []
        self.stars = [(random.randint(0, self.width), random.randint(0, self.height), random.random()) for _ in range(100)]

        # Scene configuration
        self.scenes = self._create_scenes()

        # Start cinematic music (stop first to restart from beginning)
        if self.audio_manager:
            self.audio_manager.stop_music()
            self.audio_manager.current_music_path = None  # Reset to force reload
            self.audio_manager.play_music(MUSIC_IN_CINEMATIC)

    def _load_assets(self):
        """Load images and fonts."""
        # Background
        bg_path = get_resource_path(os.path.join("assets", "image", "galad_islands_bg2.png"))
        self.bg_image = pygame.image.load(bg_path).convert()

        # Logo
        logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        if os.path.isfile(logo_path):
            self.logo = pygame.image.load(logo_path).convert_alpha()
        else:
            self.logo = None

        # Unit sprites for illustrations
        self.unit_sprites = {}
        units = ["Scout", "Maraudeur", "Leviathan", "Druid", "Architect"]
        for unit in units:
            try:
                ally_path = get_resource_path(os.path.join("assets", "sprites", "units", "ally", f"{unit}.png"))
                enemy_path = get_resource_path(os.path.join("assets", "sprites", "units", "enemy", f"{unit}.png"))
                if os.path.isfile(ally_path):
                    self.unit_sprites[f"ally_{unit.lower()}"] = pygame.image.load(ally_path).convert_alpha()
                if os.path.isfile(enemy_path):
                    self.unit_sprites[f"enemy_{unit.lower()}"] = pygame.image.load(enemy_path).convert_alpha()
            except Exception:
                pass

        # Islands
        try:
            ally_island_path = get_resource_path(os.path.join("assets", "sprites", "terrain", "ally_island.png"))
            enemy_island_path = get_resource_path(os.path.join("assets", "sprites", "terrain", "enemy_island.png"))
            if os.path.isfile(ally_island_path):
                self.ally_island = pygame.image.load(ally_island_path).convert_alpha()
            else:
                self.ally_island = None
            if os.path.isfile(enemy_island_path):
                self.enemy_island = pygame.image.load(enemy_island_path).convert_alpha()
            else:
                self.enemy_island = None
        except Exception:
            self.ally_island = None
            self.enemy_island = None

        # Other sprites
        try:
            cloud_path = get_resource_path(os.path.join("assets", "sprites", "terrain", "cloud.png"))
            if os.path.isfile(cloud_path):
                self.cloud_sprite = pygame.image.load(cloud_path).convert_alpha()
            else:
                self.cloud_sprite = None
        except Exception:
            self.cloud_sprite = None

        # Fonts
        self.title_font = pygame.font.SysFont("Arial", 72, bold=True)
        self.subtitle_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 28)
        self.skip_font = pygame.font.SysFont("Arial", 18, italic=True)
        self.quote_font = pygame.font.SysFont("Arial", 24, italic=True)

    def _create_scenes(self):
        """Create the different scenes of the cinematic."""
        scenes = [
            {
                "duration": 3.5,
                "type": "logo",
                "title": "GALAD ISLANDS",
                "bg_color": (5, 10, 30),
                "fade_in": 1.0,
                "fade_out": 0.5,
            },
            {
                "duration": 6.0,
                "type": "text",
                "title": t("cinematic.islands_title"),
                "text": [
                    t("cinematic.islands_line1"),
                    t("cinematic.islands_line2"),
                ],
                "bg_color": (10, 20, 50),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 6.0,
                "type": "crystal",
                "title": t("cinematic.crystal_title"),
                "text": [
                    t("cinematic.crystal_line1"),
                    t("cinematic.crystal_line2"),
                    t("cinematic.crystal_line3"),
                ],
                "bg_color": (20, 10, 40),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 6.0,
                "type": "conflict",
                "title": t("cinematic.war_title"),
                "text": [
                    t("cinematic.war_line1"),
                    t("cinematic.war_line2"),
                    t("cinematic.war_line3"),
                ],
                "bg_color": (40, 15, 15),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 6.0,
                "type": "attack",
                "title": t("cinematic.attack_title"),
                "text": [
                    t("cinematic.attack_line1"),
                    t("cinematic.attack_line2"),
                    t("cinematic.attack_line3"),
                ],
                "bg_color": (50, 20, 10),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 7.0,
                "type": "faction_dawn",
                "title": t("cinematic.dawn_title"),
                "text": [
                    t("cinematic.dawn_line1"),
                    t("cinematic.dawn_line2"),
                    t("cinematic.dawn_line3"),
                    "",
                    t("cinematic.dawn_motto"),
                ],
                "bg_color": (40, 30, 10),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 7.0,
                "type": "faction_abyss",
                "title": t("cinematic.abyss_title"),
                "text": [
                    t("cinematic.abyss_line1"),
                    t("cinematic.abyss_line2"),
                    t("cinematic.abyss_line3"),
                    t("cinematic.abyss_line4"),
                    "",
                    t("cinematic.abyss_motto"),
                ],
                "bg_color": (20, 10, 40),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 6.0,
                "type": "fortresses",
                "title": t("cinematic.fortresses_title"),
                "text": [
                    t("cinematic.fortresses_line1"),
                    t("cinematic.fortresses_line2"),
                    t("cinematic.fortresses_line3"),
                ],
                "bg_color": (25, 25, 35),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 5.0,
                "type": "units",
                "title": t("cinematic.warriors_title"),
                "text": [
                    t("cinematic.warriors_line1"),
                    t("cinematic.warriors_line2"),
                ],
                "bg_color": (15, 25, 40),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 5.0,
                "type": "enemy_units",
                "title": t("cinematic.enemy_warriors_title"),
                "text": [
                    t("cinematic.enemy_warriors_line1"),
                    t("cinematic.enemy_warriors_line2"),
                    t("cinematic.enemy_warriors_line3"),
                ],
                "bg_color": (25, 10, 20),
                "fade_in": 0.8,
                "fade_out": 0.5,
            },
            {
                "duration": 5.0,
                "type": "call_to_action",
                "title": t("cinematic.mission_title"),
                "text": [
                    t("cinematic.mission_line1"),
                    t("cinematic.mission_line2"),
                    "",
                    t("cinematic.mission_line3"),
                ],
                "bg_color": (10, 20, 50),
                "fade_in": 0.8,
                "fade_out": 1.0,
            },
            {
                "duration": 8.0,
                "type": "credits",
                "title": t("cinematic.credits_title"),
                "text": [
                    t("cinematic.credits_line1"),
                    t("cinematic.credits_line2"),
                    "",
                    t("cinematic.credits_line3"),
                    t("cinematic.credits_line4"),
                    t("cinematic.credits_line5"),
                    "",
                    t("cinematic.credits_line6"),
                    ],
                "bg_color": (5, 5, 15),
                "fade_in": 1.0,
                "fade_out": 1.5,
            },
        ]
        return scenes

    def _spawn_particles(self, x, y, color, count=5, speed=2):
        """Create particles at a given position."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            vel = random.uniform(0.5, speed)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * vel,
                'vy': math.sin(angle) * vel,
                'life': 1.0,
                'color': color,
                'size': random.randint(2, 5)
            })

    def _update_particles(self, dt):
        """Update particles."""
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= dt * 0.5
            if p['life'] <= 0:
                self.particles.remove(p)

    def _draw_particles(self):
        """Draw particles."""
        for p in self.particles:
            color = (*p['color'][:3],)
            size = int(p['size'] * p['life'])
            if size > 0:
                pygame.draw.circle(self.surface, color, (int(p['x']), int(p['y'])), size)

    def update(self, dt):
        """Update cinematic state."""
        if self.finished or self.skip_requested:
            self.finished = True
            return

        self.scene_timer += dt
        self.global_timer += dt
        self._update_particles(dt)

        if self.current_scene >= len(self.scenes):
            self.finished = True
            return

        scene = self.scenes[self.current_scene]

        # Calculate alphas for transitions
        if self.scene_timer < scene["fade_in"]:
            self.alpha = int(255 * (self.scene_timer / scene["fade_in"]))
        elif self.scene_timer > scene["duration"] - scene["fade_out"]:
            remaining = scene["duration"] - self.scene_timer
            self.alpha = int(255 * (remaining / scene["fade_out"]))
        else:
            self.alpha = 255

        # Move to next scene
        if self.scene_timer >= scene["duration"]:
            self.current_scene += 1
            self.scene_timer = 0

    def handle_event(self, event):
        """Handle user events."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                self.skip_requested = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.skip_requested = True

    def draw(self):
        """Draw the current scene."""
        if self.current_scene >= len(self.scenes):
            return

        scene = self.scenes[self.current_scene]

        # Background color based on scene
        bg_color = scene.get("bg_color", (0, 0, 0))
        self.surface.fill(bg_color)

        # Stars in background
        self._draw_stars()

        # Draw based on scene type
        if scene["type"] == "logo":
            self._draw_logo_scene(scene)
        elif scene["type"] == "text":
            self._draw_text_scene(scene)
        elif scene["type"] == "crystal":
            self._draw_crystal_scene(scene)
        elif scene["type"] == "conflict":
            self._draw_conflict_scene(scene)
        elif scene["type"] == "attack":
            self._draw_attack_scene(scene)
        elif scene["type"] == "faction_dawn":
            self._draw_faction_dawn_scene(scene)
        elif scene["type"] == "faction_abyss":
            self._draw_faction_abyss_scene(scene)
        elif scene["type"] == "fortresses":
            self._draw_fortresses_scene(scene)
        elif scene["type"] == "units":
            self._draw_units_scene(scene)
        elif scene["type"] == "enemy_units":
            self._draw_enemy_units_scene(scene)
        elif scene["type"] == "call_to_action":
            self._draw_call_to_action_scene(scene)
        elif scene["type"] == "credits":
            self._draw_credits_scene(scene)

        # Particles
        self._draw_particles()

        # Skip hint
        self._draw_skip_hint()

    def _draw_stars(self):
        """Draw twinkling stars in background."""
        for x, y, phase in self.stars:
            brightness = int(100 + 80 * math.sin(self.global_timer * 2 + phase * 10))
            pygame.draw.circle(self.surface, (brightness, brightness, brightness), (x, y), 1)

    def _draw_logo_scene(self, scene):
        """Draw logo scene with spectacular effect."""
        # Logo at center with zoom effect
        if self.logo:
            scale = 1.0 + 0.1 * math.sin(self.scene_timer * 2)
            size = int(200 * scale)
            logo_scaled = pygame.transform.scale(self.logo, (size, size))
            logo_rect = logo_scaled.get_rect(center=(self.width // 2, self.height // 2 - 50))
            logo_scaled.set_alpha(self.alpha)
            self.surface.blit(logo_scaled, logo_rect)

            # Particles around logo
            if random.random() < 0.3:
                angle = random.uniform(0, 2 * math.pi)
                dist = 120
                px = self.width // 2 + math.cos(angle) * dist
                py = self.height // 2 - 50 + math.sin(angle) * dist
                self._spawn_particles(px, py, (255, 215, 0), 2, 1)

        # Title with glow effect
        glow_intensity = int(50 * abs(math.sin(self.scene_timer * 3)))
        title_color = (255, min(255, 215 + glow_intensity // 2), glow_intensity)
        title_surf = self.title_font.render(scene["title"], True, title_color)
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 + 100))
        self.surface.blit(title_surf, title_rect)

    def _draw_text_scene(self, scene):
        """Draw text scene with floating clouds."""
        # Clouds in background
        if self.cloud_sprite:
            for i in range(3):
                cloud_x = (self.global_timer * 20 + i * 400) % (self.width + 200) - 100
                cloud_y = 100 + i * 80
                cloud_scaled = pygame.transform.scale(self.cloud_sprite, (150, 80))
                cloud_scaled.set_alpha(50)
                self.surface.blit(cloud_scaled, (cloud_x, cloud_y))

        # Title
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 215, 0))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        self.surface.blit(title_surf, title_rect)

        # Text with progressive appearance
        y_offset = self.height // 2
        for i, line in enumerate(scene["text"]):
            delay = i * 0.3
            if self.scene_timer > delay:
                line_alpha = min(255, int(255 * (self.scene_timer - delay) / 0.5))
                line_alpha = min(line_alpha, self.alpha)
                text_surf = self.text_font.render(line, True, (255, 255, 255))
                text_surf.set_alpha(line_alpha)
                text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
                self.surface.blit(text_surf, text_rect)
            y_offset += 40

    def _draw_crystal_scene(self, scene):
        """Draw crystal scene with glowing effect."""
        # Title
        title_surf = self.subtitle_font.render(scene["title"], True, (100, 200, 255))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 4))
        self.surface.blit(title_surf, title_rect)

        # Animated crystal (geometric shape)
        crystal_x = self.width // 2
        crystal_y = self.height // 2 - 30
        pulse = 1 + 0.2 * math.sin(self.scene_timer * 4)

        # Draw stylized crystal
        points = []
        for i in range(6):
            angle = i * math.pi / 3 - math.pi / 2
            r = 40 * pulse if i % 2 == 0 else 25 * pulse
            points.append((
                crystal_x + math.cos(angle) * r,
                crystal_y + math.sin(angle) * r
            ))

        # Glow
        glow_color = (50, 150, 255)
        pygame.draw.polygon(self.surface, glow_color, points)

        # Bright outline
        pygame.draw.polygon(self.surface, (150, 220, 255), points, 2)

        # Crystal particles
        if random.random() < 0.4:
            self._spawn_particles(crystal_x, crystal_y, (100, 200, 255), 3, 3)

        # Text
        y_offset = self.height // 2 + 60
        for i, line in enumerate(scene["text"]):
            delay = i * 0.3
            if self.scene_timer > delay:
                line_alpha = min(255, int(255 * (self.scene_timer - delay) / 0.5))
                line_alpha = min(line_alpha, self.alpha)
                text_surf = self.text_font.render(line, True, (255, 255, 255))
                text_surf.set_alpha(line_alpha)
                text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
                self.surface.blit(text_surf, text_rect)
            y_offset += 35

    def _draw_conflict_scene(self, scene):
        """Draw conflict scene with islands."""
        # Title
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 100, 100))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Islands on each side with movement
        island_y_base = self.height // 2 - 50

        if self.ally_island:
            float_offset = math.sin(self.scene_timer * 1.5) * 10
            island_scaled = pygame.transform.scale(self.ally_island, (130, 130))
            island_scaled.set_alpha(self.alpha)
            self.surface.blit(island_scaled, (self.width // 4 - 65, island_y_base + float_offset))

        if self.enemy_island:
            float_offset = math.sin(self.scene_timer * 1.5 + math.pi) * 10
            island_scaled = pygame.transform.scale(self.enemy_island, (130, 130))
            island_scaled.set_alpha(self.alpha)
            self.surface.blit(island_scaled, (3 * self.width // 4 - 65, island_y_base + float_offset))

        # Lightning between islands
        if self.scene_timer > 1.0:
            # Multiple animated lightning bolts
            for i in range(3):
                if math.sin(self.scene_timer * 5 + i * 2) > 0.7:
                    start_x = self.width // 4 + 65
                    end_x = 3 * self.width // 4 - 65
                    mid_y = island_y_base + 65 + random.randint(-20, 20)

                    # Zigzag lightning
                    points = [(start_x, mid_y)]
                    segments = 5
                    for j in range(1, segments):
                        x = start_x + (end_x - start_x) * j / segments
                        y = mid_y + random.randint(-30, 30)
                        points.append((x, y))
                    points.append((end_x, mid_y))

                    pygame.draw.lines(self.surface, (255, 255, 100), False, points, 2)

        # Text
        y_offset = 2 * self.height // 3 + 20
        for line in scene["text"]:
            text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 35

    def _draw_attack_scene(self, scene):
        """Draw attack scene with fire effects."""
        # Title
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 150, 50))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Falling fire particles
        if random.random() < 0.5:
            x = random.randint(100, self.width - 100)
            self._spawn_particles(x, 150, (255, random.randint(100, 200), 0), 5, 2)

        # Random explosion
        if random.random() < 0.1:
            x = random.randint(200, self.width - 200)
            y = random.randint(200, self.height - 200)
            self._spawn_particles(x, y, (255, 200, 50), 10, 4)

        # Text
        y_offset = self.height // 2
        for line in scene["text"]:
            # Slight shake effect
            shake_x = random.randint(-2, 2) if self.scene_timer > 1 else 0
            shake_y = random.randint(-2, 2) if self.scene_timer > 1 else 0

            text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2 + shake_x, y_offset + shake_y))
            self.surface.blit(text_surf, text_rect)
            y_offset += 40

    def _draw_faction_dawn_scene(self, scene):
        """Draw Fleet of Dawn scene."""
        # Title in golden/sun color
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 200, 50))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Animated rising sun
        sun_y = self.height // 2 - 20 - self.scene_timer * 5
        sun_radius = 50 + int(10 * math.sin(self.scene_timer * 2))

        # Halo
        for r in range(3):
            halo_radius = sun_radius + r * 15
            halo_alpha = 100 - r * 30
            halo_surf = pygame.Surface((halo_radius * 2, halo_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo_surf, (255, 200, 50, halo_alpha), (halo_radius, halo_radius), halo_radius)
            self.surface.blit(halo_surf, (self.width // 2 - halo_radius, sun_y - halo_radius))

        # Sun
        pygame.draw.circle(self.surface, (255, 220, 100), (self.width // 2, int(sun_y)), sun_radius)

        # Flying ally units
        ally_units = ["scout", "maraudeur", "leviathan"]
        for i, unit in enumerate(ally_units):
            key = f"ally_{unit}"
            if key in self.unit_sprites:
                sprite = self.unit_sprites[key]
                size = 50
                sprite_scaled = pygame.transform.scale(sprite, (size, size))
                sprite_scaled.set_alpha(self.alpha)

                # Formation flight
                base_x = self.width // 4 + i * 60
                base_y = self.height // 2 + 50
                float_offset = math.sin(self.scene_timer * 3 + i * 0.5) * 15
                move_x = math.sin(self.scene_timer * 0.5) * 20

                self.surface.blit(sprite_scaled, (base_x + move_x, base_y + float_offset))

        # Text
        y_offset = self.height // 2 + 120
        for line in scene["text"]:
            if line == "":
                y_offset += 15
                continue
            if line.startswith('"'):
                text_surf = self.quote_font.render(line, True, (255, 220, 150))
            else:
                text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 32

    def _draw_faction_abyss_scene(self, scene):
        """Draw Legion of the Abyss scene."""
        # Title in dark/purple color
        title_surf = self.subtitle_font.render(scene["title"], True, (180, 100, 255))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Animated dark vortex
        vortex_x = self.width // 2
        vortex_y = self.height // 2 - 20

        for r in range(5, 0, -1):
            angle_offset = self.scene_timer * (6 - r)
            radius = r * 15

            # Spiral
            for i in range(8):
                angle = i * math.pi / 4 + angle_offset
                px = vortex_x + math.cos(angle) * radius
                py = vortex_y + math.sin(angle) * radius
                pygame.draw.circle(self.surface, (100 + r * 20, 50, 150 + r * 10), (int(px), int(py)), 3)

        # Enemy units
        enemy_units = ["scout", "maraudeur", "leviathan"]
        for i, unit in enumerate(enemy_units):
            key = f"enemy_{unit}"
            if key in self.unit_sprites:
                sprite = self.unit_sprites[key]
                size = 80  # Increased size for better visibility
                sprite_scaled = pygame.transform.scale(sprite, (size, size))
                # Ensure full opacity
                sprite_scaled.set_alpha(min(255, int(self.alpha * 1.2)))

                # Menacing movement
                base_x = 3 * self.width // 4 - 60 + i * 80  # Adjusted spacing for larger sprites
                base_y = self.height // 2 + 50
                float_offset = math.sin(self.scene_timer * 2 + i + math.pi) * 15

                self.surface.blit(sprite_scaled, (base_x, base_y + float_offset))

        # Text
        y_offset = self.height // 2 + 120
        for line in scene["text"]:
            if line == "":
                y_offset += 15
                continue
            if line.startswith('"'):
                text_surf = self.quote_font.render(line, True, (200, 150, 255))
            else:
                text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 32

    def _draw_fortresses_scene(self, scene):
        """Draw fortresses scene."""
        # Title
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 215, 0))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Ally island (Eryndor) with golden aura
        if self.ally_island:
            # Aura
            aura_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            pulse = int(30 + 20 * math.sin(self.scene_timer * 2))
            pygame.draw.circle(aura_surf, (255, 200, 50, pulse), (80, 80), 80)
            self.surface.blit(aura_surf, (self.width // 4 - 80, self.height // 2 - 100))

            island_scaled = pygame.transform.scale(self.ally_island, (120, 120))
            island_scaled.set_alpha(self.alpha)
            float_offset = math.sin(self.scene_timer * 1.5) * 8
            self.surface.blit(island_scaled, (self.width // 4 - 60, self.height // 2 - 80 + float_offset))

            # Label
            label_surf = self.text_font.render("Eryndor", True, (255, 220, 100))
            label_surf.set_alpha(self.alpha)
            label_rect = label_surf.get_rect(center=(self.width // 4, self.height // 2 + 60))
            self.surface.blit(label_surf, label_rect)

        # Enemy island (Barakdur) with purple aura
        if self.enemy_island:
            # Aura
            aura_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            pulse = int(30 + 20 * math.sin(self.scene_timer * 2 + math.pi))
            pygame.draw.circle(aura_surf, (150, 50, 200, pulse), (80, 80), 80)
            self.surface.blit(aura_surf, (3 * self.width // 4 - 80, self.height // 2 - 100))

            island_scaled = pygame.transform.scale(self.enemy_island, (120, 120))
            island_scaled.set_alpha(self.alpha)
            float_offset = math.sin(self.scene_timer * 1.5 + math.pi) * 8
            self.surface.blit(island_scaled, (3 * self.width // 4 - 60, self.height // 2 - 80 + float_offset))

            # Label
            label_surf = self.text_font.render("Barakdur", True, (200, 150, 255))
            label_surf.set_alpha(self.alpha)
            label_rect = label_surf.get_rect(center=(3 * self.width // 4, self.height // 2 + 60))
            self.surface.blit(label_surf, label_rect)

        # Text
        y_offset = 2 * self.height // 3 + 40
        for line in scene["text"]:
            text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 35

    def _draw_units_scene(self, scene):
        """Draw scene presenting the units."""
        # Title
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 215, 0))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Units on parade
        units_to_show = ["scout", "maraudeur", "leviathan", "druid", "architect"]
        unit_spacing = self.width // (len(units_to_show) + 1)

        for i, unit in enumerate(units_to_show):
            key = f"ally_{unit}"
            if key in self.unit_sprites:
                sprite = self.unit_sprites[key]

                # Progressive entry
                delay = i * 0.3
                if self.scene_timer > delay:
                    progress = min(1, (self.scene_timer - delay) / 0.5)

                    size = int(70 * progress)
                    if size > 0:
                        sprite_scaled = pygame.transform.scale(sprite, (size, size))
                        sprite_scaled.set_alpha(int(self.alpha * progress))

                        x = unit_spacing * (i + 1) - size // 2
                        y = self.height // 2 - size // 2

                        # Floating animation
                        float_offset = math.sin(self.scene_timer * 2.5 + i * 0.7) * 12
                        self.surface.blit(sprite_scaled, (x, y + float_offset))

        # Text
        y_offset = 2 * self.height // 3 + 30
        for line in scene["text"]:
            text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 40

    def _draw_enemy_units_scene(self, scene):
        """Draw scene presenting the enemy units."""
        # Title with ominous color
        title_surf = self.subtitle_font.render(scene["title"], True, (200, 100, 150))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 5))
        self.surface.blit(title_surf, title_rect)

        # Enemy units on parade with menacing appearance
        units_to_show = ["scout", "maraudeur", "leviathan", "druid", "architect"]
        unit_spacing = self.width // (len(units_to_show) + 1)

        for i, unit in enumerate(units_to_show):
            key = f"enemy_{unit}"
            if key in self.unit_sprites:
                sprite = self.unit_sprites[key]

                # Progressive entry with slight delay
                delay = i * 0.3
                if self.scene_timer > delay:
                    progress = min(1, (self.scene_timer - delay) / 0.5)

                    size = int(70 * progress)
                    if size > 0:
                        sprite_scaled = pygame.transform.scale(sprite, (size, size))
                        sprite_scaled.set_alpha(int(self.alpha * progress))

                        x = unit_spacing * (i + 1) - size // 2
                        y = self.height // 2 - size // 2

                        # Menacing floating animation (opposite phase from allies)
                        float_offset = math.sin(self.scene_timer * 2.5 + i * 0.7 + math.pi) * 12
                        self.surface.blit(sprite_scaled, (x, y + float_offset))

                        # Dark particles around enemy units
                        if random.random() < 0.1:
                            self._spawn_particles(x + size // 2, y + size // 2 + float_offset, (150, 50, 200), 1, 0.5)

        # Text with warning tone
        y_offset = 2 * self.height // 3 + 30
        for line in scene["text"]:
            text_surf = self.text_font.render(line, True, (255, 200, 200))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 40

    def _draw_call_to_action_scene(self, scene):
        """Draw call to action scene."""
        # Title with dramatic pulsing effect
        pulse = 1 + 0.15 * math.sin(self.scene_timer * 5)
        font_size = int(40 * pulse)
        dynamic_font = pygame.font.SysFont("Arial", font_size, bold=True)

        # Changing color
        r = 255
        g = int(200 + 55 * abs(math.sin(self.scene_timer * 3)))
        b = int(50 * abs(math.sin(self.scene_timer * 3)))

        title_surf = dynamic_font.render(scene["title"], True, (r, g, b))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3))
        self.surface.blit(title_surf, title_rect)

        # Epic particles
        if random.random() < 0.3:
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            self._spawn_particles(x, y, (255, 215, 0), 3, 2)

        # Text
        y_offset = self.height // 2
        for line in scene["text"]:
            if line == "":
                y_offset += 15
                continue
            text_surf = self.text_font.render(line, True, (255, 255, 255))
            text_surf.set_alpha(self.alpha)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_offset))
            self.surface.blit(text_surf, text_rect)
            y_offset += 40

    def _draw_credits_scene(self, scene):
        """Draw credits scene with scrolling effect."""
        # Title with golden color
        title_surf = self.subtitle_font.render(scene["title"], True, (255, 215, 0))
        title_surf.set_alpha(self.alpha)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 4))
        self.surface.blit(title_surf, title_rect)

        # Scrolling text effect
        base_y = self.height // 2 - 50
        scroll_offset = -self.scene_timer * 15  # Slow scrolling upward

        for i, line in enumerate(scene["text"]):
            if line == "":
                continue

            # Calculate y position with scroll
            y_pos = base_y + i * 35 + scroll_offset

            # Only draw if visible on screen
            if -50 < y_pos < self.height + 50:
                # Choose font size based on content
                if i == 0 or i == 1:  # Project title lines
                    text_surf = self.text_font.render(line, True, (255, 255, 150))
                elif line == t("cinematic.credits_line3"):  # "Développé par:"
                    text_surf = self.text_font.render(line, True, (200, 200, 255))
                elif line == t("cinematic.credits_line8"):  # "Merci d'avoir joué !"
                    font_size = int(32 + 5 * abs(math.sin(self.scene_timer * 2)))
                    dynamic_font = pygame.font.SysFont("Arial", font_size, bold=True)
                    text_surf = dynamic_font.render(line, True, (255, 215, 0))
                else:
                    text_surf = self.text_font.render(line, True, (255, 255, 255))

                text_surf.set_alpha(self.alpha)
                text_rect = text_surf.get_rect(center=(self.width // 2, int(y_pos)))
                self.surface.blit(text_surf, text_rect)

        # Add some sparkle particles
        if random.random() < 0.2:
            x = random.randint(100, self.width - 100)
            y = random.randint(100, self.height - 100)
            self._spawn_particles(x, y, (255, 215, 0), 2, 1)

    def _draw_skip_hint(self):
        """Draw skip hint."""
        skip_text = t("cinematic.skip_hint")
        skip_surf = self.skip_font.render(skip_text, True, (100, 100, 100))
        skip_rect = skip_surf.get_rect(bottomright=(self.width - 20, self.height - 20))
        self.surface.blit(skip_surf, skip_rect)

    def run(self):
        """Run the cinematic."""
        clock = pygame.time.Clock()

        while not self.finished:
            dt = clock.tick(60) / 1000.0

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                self.handle_event(event)

            # Update
            self.update(dt)

            # Render
            self.draw()
            pygame.display.update()

        return True


def play_intro_cinematic(surface, audio_manager=None):
    """
    Launch the introduction cinematic.

    Args:
        surface: Pygame surface for display
        audio_manager: Audio manager (optional)

    Returns:
        bool: True if cinematic finished normally,
              False if player wants to quit
    """
    cinematic = IntroCinematic(surface, audio_manager)
    return cinematic.run()
