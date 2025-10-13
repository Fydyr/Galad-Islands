#!/usr/bin/env python3
"""Simulateur visuel minimal IA vs IA (headful) pour debug et observation.
Affiche deux bases, unités représentées par cercles, et une bannière Self-Play.
Touches: espace = pause, +/- vitesse.
"""
import sys
import random
import time
from collections import deque

sys.path.insert(0, '.')

import pygame
import esper
import argparse
from src.components.core.baseComponent import BaseComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.components.core.healthComponent import HealthComponent
from src.ia.BaseAi import BaseAi
from src.constants.gameplay import UNIT_COSTS

# Configuration rapide
WIDTH, HEIGHT = 800, 480
FPS = 30

# Colors
COLOR_BG = (24, 30, 40)
COLOR_ALLY = (80, 180, 240)
COLOR_ENEMY = (240, 100, 100)
COLOR_BASE = (200, 200, 200)
COLOR_TEXT = (240, 240, 240)
BANNER_COLOR = (30, 30, 30)

# Entités visuels
class VisualUnit:
    UNIT_STATS = {
        # action_id: (letter, hp, dmg, speed, radius)
        1: ('S', 10, 4, 80, 6),   # Scout (light, ranged)
        2: ('A', 20, 6, 50, 8),   # Architect (support)
        3: ('M', 30, 8, 60, 9),   # Maraudeur (melee)
        4: ('L', 80, 16, 24, 14), # Léviathan (tank)
        5: ('D', 18, 5, 48, 8),   # Druide (ranged)
        6: ('K', 12, 12, 70, 7),  # Kamikaze (suicide)
    }

    def __init__(self, team, pos, target_x, unit_type=1):
        self.team = team
        self.x, self.y = pos
        self.target_x = target_x
        self.type_id = unit_type
        letter, hp, dmg, speed, radius = self.UNIT_STATS.get(unit_type, ('?', 10, 3, 60, 6))
        self.letter = letter
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.speed = speed
        self.radius = radius
        # combat properties
        # portée et cooldown dépendant du type (simple heuristique)
        if unit_type in (1, 5):
            self.range = 140
            self.cooldown = 0.8
        elif unit_type == 4:
            self.range = 40
            self.cooldown = 1.4
        elif unit_type == 6:
            self.range = 20
            self.cooldown = 0.2
        else:
            self.range = 60
            self.cooldown = 1.0
        self._cd = 0.0

    def update(self, dt):
        dir = 1 if self.team == 'ally' else -1
        # cooldown progression
        self._cd = max(0.0, self._cd - dt)
        # movement will be controlled by higher-level logic (targeting)
        # fallback movement
        self.x += dir * self.speed * dt * 0.6

    def draw(self, surf):
        col = COLOR_ALLY if self.team == 'ally' else COLOR_ENEMY
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.radius)
        # health bar
        hpw = max(2, int(self.radius * 2 * (self.hp / max(1, self.max_hp))))
        pygame.draw.rect(surf, (0, 0, 0), (int(self.x - self.radius), int(self.y - self.radius - 6), self.radius*2, 4))
        pygame.draw.rect(surf, (20, 220, 120), (int(self.x - self.radius), int(self.y - self.radius - 6), hpw, 4))
        # letter
        lab = font.render(self.letter, True, (10, 10, 10))
        surf.blit(lab, (int(self.x - lab.get_width() // 2), int(self.y - lab.get_height() // 2)))

# Helper : clear esper world if present
try:
    esper.clear_database()
except Exception:
    pass

# Init pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Fake Self-Play Visual')
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 18)
bigfont = pygame.font.SysFont('arial', 22, bold=True)

# Initialize world/bases
BaseComponent.reset()
BaseComponent.initialize_bases()
ally_base = BaseComponent.get_ally_base()
enemy_base = BaseComponent.get_enemy_base()

# Ensure player components
def ensure_player(team_id, start_gold=150):
    for ent, (p, t) in esper.get_components(PlayerComponent, TeamComponent):
        if t.team_id == team_id:
            p.set_gold(start_gold)
            return ent, p
    e = esper.create_entity()
    pc = PlayerComponent(stored_gold=start_gold)
    esper.add_component(e, pc)
    esper.add_component(e, TeamComponent(team_id))
    return e, pc

ally_ent, ally_player = ensure_player(1, 150)
enemy_ent, enemy_player = ensure_player(2, 150)

if ally_base is not None:
    if not esper.has_component(ally_base, HealthComponent):
        esper.add_component(ally_base, HealthComponent(currentHealth=2500, maxHealth=2500))
else:
    print('Warning: ally_base entity not found')

if enemy_base is not None:
    if not esper.has_component(enemy_base, HealthComponent):
        esper.add_component(enemy_base, HealthComponent(currentHealth=2500, maxHealth=2500))
else:
    print('Warning: enemy_base entity not found')

# Instantiate AIs
ai_ally = BaseAi(team_id=1)
ai_enemy = BaseAi(team_id=2)
ai_ally.enabled = True
ai_enemy.enabled = True

# Visual lists
visual_units = []
projectiles = []  # chaque projectile: dict{x,y,tx,ty,dmg,team,life}
particle_queue = deque(maxlen=2000)

running = True
paused = False
sim_speed = 1.0
turn_time_accum = 0.0
TURN_INTERVAL = 0.5  # seconds between AI decision cycles

def screen_coords_for_base(is_enemy):
    if is_enemy:
        return WIDTH - 120, HEIGHT // 2
    return 120, HEIGHT // 2

# Arg parsing (optionnel pour exécution courte)
parser = argparse.ArgumentParser()
parser.add_argument('--run-secs', type=float, default=0.0, help='Si >0, ferme après N secondes')
args = parser.parse_args()

# Main loop
last_time = time.time()
start_time = last_time
while running:
    now = time.time()
    dt = (now - last_time) * sim_speed
    last_time = now

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                sim_speed = max(0.1, sim_speed - 0.1)
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                sim_speed = min(4.0, sim_speed + 0.1)

    if not paused:
        turn_time_accum += dt
        # Update visual units
        for u in visual_units:
            u.update(dt)
        # Remove off-screen units
        visual_units = [u for u in visual_units if 0 <= u.x <= WIDTH]

        if turn_time_accum >= TURN_INTERVAL:
            turn_time_accum = 0.0
            # Two AIs decide
            for ai in (ai_ally, ai_enemy):
                team = ai.default_team_id
                state = ai._get_current_game_state(team)
                if state is None:
                    continue
                action = ai._decide_action(state)
                executed = ai._execute_action(action, team)
                # If a unit was spawned, create a visual unit
                if executed and action != 0:
                    # scout cost; choose spawn side
                    # map AI action to visual unit type (simple mapping)
                    action_to_type = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6}
                    unit_type = action_to_type.get(action, 1)
                    if team == 1:
                        sx, sy = screen_coords_for_base(False)
                        visual_units.append(VisualUnit('ally', (sx + 30, sy + random.randint(-40, 40)), WIDTH-60, unit_type=unit_type))
                    else:
                        sx, sy = screen_coords_for_base(True)
                        visual_units.append(VisualUnit('enemy', (sx - 30, sy + random.randint(-40, 40)), 60, unit_type=unit_type))

            # Targeting & ranged firing
            for u in visual_units:
                # find nearest enemy unit
                enemies = [v for v in visual_units if v.team != u.team]
                target = None
                bestd = 1e9
                for e in enemies:
                    d = abs(e.x - u.x)
                    if d < bestd:
                        bestd = d
                        target = e

                # If there is a target and in range, shoot (respect cooldown)
                if target is not None and bestd <= u.range:
                    if u._cd <= 0.0:
                        # create projectile
                        proj = {'x': u.x, 'y': u.y, 'tx': target.x, 'ty': target.y, 'dmg': u.dmg, 'team': u.team, 'life': 1.5}
                        projectiles.append(proj)
                        u._cd = u.cooldown
                else:
                    # otherwise advance towards enemy base
                    dir = 1 if u.team == 'ally' else -1
                    u.x += dir * u.speed * TURN_INTERVAL * 0.5

            # Update projectiles
            new_projs = []
            for p in projectiles:
                # simple linear interpolation toward target
                step = 320 * TURN_INTERVAL
                dx = p['tx'] - p['x']
                dy = p['ty'] - p['y']
                dist = (dx*dx + dy*dy) ** 0.5
                if dist <= step or dist < 4:
                    # impact: find nearest enemy unit from target point
                    hit = None
                    bestd = 1e9
                    for u in visual_units:
                        if u.team == p['team']:
                            continue
                        d = abs(u.x - p['tx'])
                        if d < bestd and d < 18:
                            bestd = d
                            hit = u
                    if hit is not None:
                        hit.hp -= p['dmg']
                    else:
                        # hit base if in zone
                        if p['team'] == 'ally' and enemy_base is not None and p['tx'] >= WIDTH - 100:
                            hc = esper.component_for_entity(enemy_base, HealthComponent)
                            if hc:
                                hc.currentHealth -= p['dmg']
                        if p['team'] == 'enemy' and ally_base is not None and p['tx'] <= 100:
                            hc = esper.component_for_entity(ally_base, HealthComponent)
                            if hc:
                                hc.currentHealth -= p['dmg']
                    # projectile consumed
                else:
                    # move towards target
                    nx = p['x'] + dx/dist * step
                    ny = p['y'] + dy/dist * step
                    p['x'] = nx
                    p['y'] = ny
                    p['life'] -= TURN_INTERVAL
                    if p['life'] > 0:
                        new_projs.append(p)
            projectiles = new_projs

            # Units reaching the base: apply special behaviors (scout suicide, etc.)
            survivors = []
            for u in visual_units:
                reached = False
                if u.team == 'ally' and u.x >= WIDTH - 80:
                    reached = True
                    # special: Scout (type 1) self-destructs on base impact
                    if u.type_id == 1:
                        if enemy_base is not None:
                            hc = esper.component_for_entity(enemy_base, HealthComponent)
                            if hc:
                                dmg = u.dmg * 3
                                hc.currentHealth -= dmg
                                particle_queue.append(('boom', u.x, u.y))
                        # unit destroyed
                        u.hp = 0
                    else:
                        if enemy_base is not None:
                            hc = esper.component_for_entity(enemy_base, HealthComponent)
                            if hc:
                                hc.currentHealth -= u.dmg
                        u.hp = 0

                if u.team == 'enemy' and u.x <= 80:
                    reached = True
                    if u.type_id == 1:
                        if ally_base is not None:
                            hc = esper.component_for_entity(ally_base, HealthComponent)
                            if hc:
                                dmg = u.dmg * 3
                                hc.currentHealth -= dmg
                                particle_queue.append(('boom', u.x, u.y))
                        u.hp = 0
                    else:
                        if ally_base is not None:
                            hc = esper.component_for_entity(ally_base, HealthComponent)
                            if hc:
                                hc.currentHealth -= u.dmg
                        u.hp = 0

                if u.hp > 0 and not reached:
                    survivors.append(u)

            visual_units = survivors

            # Income
            for ent, (p, t) in esper.get_components(PlayerComponent, TeamComponent):
                p.add_gold(random.randint(12, 28))

    # Drawing
    screen.fill(COLOR_BG)

    # Draw bases
    abx, aby = screen_coords_for_base(False)
    ebx, eby = screen_coords_for_base(True)
    pygame.draw.rect(screen, COLOR_BASE, (abx - 36, aby - 40, 72, 80), border_radius=6)
    pygame.draw.rect(screen, COLOR_BASE, (ebx - 36, eby - 40, 72, 80), border_radius=6)
    # draw base labels
    ally_units = len(BaseComponent.get_base_units(is_enemy=False))
    enemy_units = len(BaseComponent.get_base_units(is_enemy=True))
    ally_gold = ally_player.get_gold()
    enemy_gold = enemy_player.get_gold()
    ally_hp = None
    enemy_hp = None
    if ally_base is not None and esper.has_component(ally_base, HealthComponent):
        ally_hp = esper.component_for_entity(ally_base, HealthComponent).currentHealth
    if enemy_base is not None and esper.has_component(enemy_base, HealthComponent):
        enemy_hp = esper.component_for_entity(enemy_base, HealthComponent).currentHealth

    screen.blit(bigfont.render('ALLY', True, COLOR_ALLY), (abx - 26, aby - 56))
    screen.blit(bigfont.render('ENEMY', True, COLOR_ENEMY), (ebx - 34, eby - 56))

    # Draw units
    for u in visual_units:
        u.draw(screen)

    # Banner
    banner_rect = pygame.Rect(0, 0, WIDTH, 36)
    pygame.draw.rect(screen, BANNER_COLOR, banner_rect)
    banner_text = 'IA vs IA — Contrôle joueur désactivé | Espace: pause | +/-: vitesse | vitesse={:.1f}'.format(sim_speed)
    screen.blit(font.render(banner_text, True, COLOR_TEXT), (12, 8))

    # HUD info
    ally_units_count = len([u for u in visual_units if u.team == 'ally'])
    enemy_units_count = len([u for u in visual_units if u.team == 'enemy'])

    def calculate_pressure(my_units, other_units, my_base_hp_ratio):
        pressure = 0
        disadvantage = other_units - my_units
        if disadvantage > 4:
            pressure = 2
        elif disadvantage > 1:
            pressure = 1
        
        if my_base_hp_ratio < 0.8 and pressure < 2:
            pressure += 1
        return pressure

    ally_hp_ratio = (ally_hp / 2500) if ally_hp is not None else 1.0
    enemy_hp_ratio = (enemy_hp / 2500) if enemy_hp is not None else 1.0
    ally_pressure = calculate_pressure(ally_units_count, enemy_units_count, ally_hp_ratio)
    enemy_pressure = calculate_pressure(enemy_units_count, ally_units_count, enemy_hp_ratio)

    hud_ally = f'Ally gold: {ally_gold} | Units: {ally_units_count} | HP: {ally_hp if ally_hp is not None else "?"} | Pression subie: {ally_pressure}'
    hud_enemy = f'Enemy gold: {enemy_gold} | Units: {enemy_units_count} | HP: {enemy_hp if enemy_hp is not None else "?"} | Pression subie: {enemy_pressure}'
    screen.blit(font.render(hud_ally, True, COLOR_TEXT), (12, HEIGHT - 48))
    screen.blit(font.render(hud_enemy, True, COLOR_TEXT), (12, HEIGHT - 28))

    pygame.display.flip()
    clock.tick(FPS)
    # auto-exit si demandé
    if args.run_secs and (now - start_time) >= args.run_secs:
        running = False

pygame.quit()
print('Terminé')
