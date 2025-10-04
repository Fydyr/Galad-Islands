"""
Fonctions utilitaires pour accéder aux entités joueur et gérer leur or.
"""
import esper
from src.components.core.playerComponent import PlayerComponent
from src.constants.gameplay import PLAYER_DEFAULT_GOLD
from src.components.core.teamComponent import TeamComponent
from src.components.core.team_enum import Team
from typing import Optional

def get_player_entity(is_enemy: bool = False) -> Optional[int]:
    """Récupère l'entité joueur selon la faction."""
    # Chercher dans les entités existantes avec PlayerComponent et TeamComponent
    for entity, (player_comp, team_comp) in esper._world.get_components(PlayerComponent, TeamComponent):
        if is_enemy and team_comp.team_id == Team.ENEMY:
            return entity
        elif not is_enemy and team_comp.team_id == Team.ALLY:
            return entity
    
    # Si pas trouvé, créer l'entité joueur manquante
    print(f"Création d'une entité joueur {'ennemie' if is_enemy else 'alliée'}")
    entity = esper._world.create_entity()
    esper._world.add_component(entity, PlayerComponent(stored_gold=PLAYER_DEFAULT_GOLD))
    team_value = Team.ENEMY if is_enemy else Team.ALLY
    esper._world.add_component(entity, TeamComponent(team_value))
    return entity

def get_player_gold(is_enemy: bool = False) -> int:
    """Récupère l'or du joueur spécifié."""
    player_entity = get_player_entity(is_enemy)
    
    if player_entity is not None and esper.has_component(player_entity, PlayerComponent):
        player_comp = esper.component_for_entity(player_entity, PlayerComponent)
        return player_comp.stored_gold
    
    print(f"Attention: PlayerComponent non trouvé pour l'entité joueur {'ennemie' if is_enemy else 'alliée'}")
    return 0

def set_player_gold(gold: int, is_enemy: bool = False):
    """Définit l'or du joueur spécifié."""
    player_entity = get_player_entity(is_enemy)
    
    if player_entity is not None and esper.has_component(player_entity, PlayerComponent):
        player_comp = esper.component_for_entity(player_entity, PlayerComponent)
        player_comp.stored_gold = max(0, gold)  # Ne pas permettre d'or négatif
        print(f"Or mis à jour pour {'ennemi' if is_enemy else 'allié'}: {player_comp.stored_gold}")
    else:
        print(f"Attention: PlayerComponent non trouvé pour l'entité joueur {'ennemie' if is_enemy else 'alliée'}")

def add_player_gold(amount: int, is_enemy: bool = False):
    """Ajoute de l'or au joueur spécifié."""
    current_gold = get_player_gold(is_enemy)
    set_player_gold(current_gold + amount, is_enemy)

def spend_player_gold(amount: int, is_enemy: bool = False) -> bool:
    """Dépense l'or du joueur si possible. Retourne True si succès."""
    current_gold = get_player_gold(is_enemy)
    if current_gold >= amount:
        set_player_gold(current_gold - amount, is_enemy)
        return True
    return False