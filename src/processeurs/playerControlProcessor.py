import esper
from components.properties.playerSelectedComponent import PlayerSelectedComponent
from components.properties.positionComponent import PositionComponent
from components.properties.velocityComponent import VelocityComponent

class PlayerControlProcessor(esper.Processor):
    def __init__(self, input_managers):
        """
        input_managers : dictionnaire {player_id: input_manager}
        """
        self.input_managers = input_managers

    def process(self):
        # Pour chaque entité sélectionnée par un joueur
        for entity, selected in esper.get_component(PlayerSelectedComponent):
            player_id = selected.player_id

            # Récupère l'input manager du joueur
            input_manager = self.input_managers.get(player_id)
            if not input_manager:
                continue

            pressed = input_manager.get_pressed_keys()
            if pressed:
                if esper.has_component(entity, PositionComponent) and esper.has_component(entity, VelocityComponent):
                    velocity = esper.component_for_entity(entity, VelocityComponent)

                    # Exemple de gestion des touches
                    velocity.x = 0
                    velocity.y = 0
                    if 'up' in pressed:
                        velocity.y = -1
                    if 'down' in pressed:
                        velocity.y = 1
                    if 'left' in pressed:
                        velocity.x = -1
                    if 'right' in pressed:
                        velocity.x = 1