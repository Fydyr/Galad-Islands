import math
import esper
from src.components.core.towerComponent import TowerComponent, TowerType
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.core.teamComponent import TeamComponent


class TowerProcessor(esper.Processor):
    """Processor unifié pour gérer le comportement de tous les types de tours."""
    def __init__(self):
        super().__init__()

    def process(self, dt: float = 0.016):
        # Process all towers with the unified component
        for ent, (tower, pos, team) in esper.get_components(TowerComponent, PositionComponent, TeamComponent):
            tower.update_cooldown(dt)
            
            if not tower.can_attack():
                continue

            target = None
            min_dist = float('inf')
            
            for e2, (p2, t2, hp2) in esper.get_components(PositionComponent, TeamComponent, HealthComponent):
                # Defense towers attack enemies
                if tower.is_defense_tower():
                    if t2.team_id == team.team_id:
                        continue
                # Heal towers heal allies
                elif tower.is_heal_tower():
                    if t2.team_id != team.team_id:
                        continue
                    if hp2.currentHealth >= hp2.maxHealth:
                        continue
                    # Exclude towers from healing (no tower-to-tower healing)
                    if esper.has_component(e2, TowerComponent):
                        continue
                else:
                    continue  # Unknown tower type
                
                dist = math.hypot(p2.x - pos.x, p2.y - pos.y)
                if dist <= tower.range and dist < min_dist:
                    min_dist = dist
                    target = hp2

            if target is not None:
                if tower.is_defense_tower() and tower.damage is not None:
                    target.currentHealth = max(0, target.currentHealth - tower.damage)
                elif tower.is_heal_tower() and tower.heal_amount is not None:
                    target.currentHealth = min(target.maxHealth, target.currentHealth + tower.heal_amount)
                
                tower.trigger_action()
