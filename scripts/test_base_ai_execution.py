#!/usr/bin/env python3
"""Test rapide : vérifier que BaseAi décide une action et peut exécuter l'achat d'un scout."""
import sys
# Ensure project root is on sys.path so imports like 'src.components...' resolve
sys.path.insert(0, '.')
import esper
from src.components.core.baseComponent import BaseComponent
from src.components.core.playerComponent import PlayerComponent
from src.components.core.teamComponent import TeamComponent
from src.ia.BaseAi import BaseAi

# Reset ECS
esper.clear_database()
BaseComponent.reset()
BaseComponent.initialize_bases()

# Créer PlayerComponent pour l'équipe 1
player_entity = esper.create_entity()
player_comp = PlayerComponent(stored_gold=100)
esper.add_component(player_entity, player_comp)
esper.add_component(player_entity, TeamComponent(1))

# Créer instance d'IA pour l'équipe 1
ai = BaseAi(team_id=1)

# Remplacer _spawn_unit par stub pour éviter dépendances
# Ne pas stubber _spawn_unit : utiliser la factory réelle

# Obtenir l'état de jeu actuel et décider
state = ai._get_current_game_state(ai_team_id=1)
print('Etat pour décision:', state)
action = ai._decide_action(state)
print('Action décidée:', action)

# Exécuter l'action
ok = ai._execute_action(action, ai_team_id=1)
print('Execution ok?', ok)
print('Remaining gold:', player_comp.get_gold())

# Vérifier les unités enregistrées dans la base alliée
base_units = BaseComponent.get_base_units(is_enemy=False)
print('Base allied units count:', len(base_units))
print('Base allied units:', base_units)
