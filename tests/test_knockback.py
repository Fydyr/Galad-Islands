import esper
import math
from src.components.core.positionComponent import PositionComponent
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.canCollideComponent import CanCollideComponent
from src.processeurs.collisionProcessor import CollisionProcessor


def test_knockback_applied_to_entity():
    # Setup minimal esper world
    # Note: using global esper functions from the project
    # Create a collision processor with a fake small grid
    grid = [[0 for _ in range(10)] for _ in range(10)]
    cp = CollisionProcessor(graph=grid)

    # Create an entity that will 'collide' with an island
    ent = esper.create_entity()
    pos = PositionComponent(x=100.0, y=100.0, direction=0.0)
    vel = VelocityComponent(currentSpeed=20.0, maxUpSpeed=50.0)
    esper.add_component(ent, pos)
    esper.add_component(ent, vel)
    esper.add_component(ent, CanCollideComponent())

    # Simulate a terrain collision by calling _apply_knockback directly
    cp._apply_knockback(ent, pos, vel, magnitude=30.0, stun_duration=0.5)

    # After knockback, speed should be zero and stun_timer present
    assert getattr(vel, 'currentSpeed', 0) == 0
    assert getattr(vel, 'stun_timer', 0) > 0
    # Position should have moved (receded along x because direction=0)
    assert pos.x < 100.0

    # Cleanup any entities
    try:
        esper.delete_entity(ent)
    except Exception:
        pass
