# src/processeurs/ai/druidAIProcessor.py

import esper as es
import math
from typing import Tuple

# --- Imports des composants du jeu ---
from src.components.core.velocityComponent import VelocityComponent
from src.components.core.positionComponent import PositionComponent
from src.components.core.healthComponent import HealthComponent
from src.components.special.speDruidComponent import SpeDruid
from src.components.core.radiusComponent import RadiusComponent

# --- Imports des classes de l'IA ---
from src.sklearn.druidAiController import DruidAIComponent
from src.sklearn.decision.actionEvaluator import ActionType

# --- Constantes ---
DRUID_HEAL_AMOUNT = 20

# --- Fonctions utilitaires ---
def calculate_angle_to_target(source_pos: Tuple[float, float], target_pos: Tuple[float, float]) -> float:
    """
    Calcule l'angle en degrés de la source vers la cible.
    Cette fonction est adaptée à la logique de votre movementProcessor.
    Le towerProcessor calcule (source - target), ce qui est inhabituel.
    Une direction standard est (target - source). Testons avec le standard.
    """
    delta_x = target_pos[0] - source_pos[0]
    delta_y = target_pos[1] - source_pos[1]
    return math.degrees(math.atan2(delta_y, delta_x))

class DruidAIProcessor(es.Processor):
    """
    Ce processeur exécute les décisions prises par l'IA du Druid
    en modifiant les composants de l'entité dans le monde du jeu.
    """
    def process(self, dt):
        # Récupère toutes les entités ayant un composant IA de Druid
        for entity, (ai_component,) in es.get_components(DruidAIComponent):
            
            # 1. DÉCISION : Laisse le cerveau de l'IA choisir la meilleure action
            result = ai_component.decision_maker.update(entity)
            if not result:
                continue

            action, params = result
            
            # Affiche la décision de l'IA dans la console pour le debug
            print(f"[IA Druid {entity}] Décision: {action.type.name}, Params: {params}")

            # --- 2. ACTION : Traduction des décisions en modifications de composants ---
            
            # On s'assure que l'entité a les composants de base pour agir
            if not es.has_component(entity, PositionComponent) or not es.has_component(entity, VelocityComponent):
                continue
            
            pos = es.component_for_entity(entity, PositionComponent)
            vel = es.component_for_entity(entity, VelocityComponent)

            # --- GESTION DU MOUVEMENT ---
            if action.type in [ActionType.MOVE_TO_ALLY, ActionType.RETREAT, ActionType.KITE]:
                destination = params.get('position')
                if destination:
                    # Calculer la direction vers la destination
                    angle = calculate_angle_to_target((pos.x, pos.y), destination)
                    pos.direction = angle
                    
                    # Mettre le vaisseau en mouvement à pleine vitesse
                    vel.currentSpeed = vel.maxUpSpeed
            
            elif action.type == ActionType.HOLD_POSITION:
                # Arrêter le mouvement
                vel.currentSpeed = 0.0

            # --- GESTION DES CAPACITÉS ---
            elif action.type == ActionType.HEAL:
                target_id = params.get('target')
                if target_id and es.has_component(entity, RadiusComponent) and es.entity_exists(target_id):
                    radius_comp = es.component_for_entity(entity, RadiusComponent)
                    if radius_comp.cooldown <= 0 and es.has_component(target_id, HealthComponent):
                        # Déclenche le cooldown du Druid
                        radius_comp.cooldown = radius_comp.bullet_cooldown 
                        
                        # Applique le soin directement sur la cible
                        target_health = es.component_for_entity(target_id, HealthComponent)
                        target_health.currentHealth = min(target_health.maxHealth, target_health.currentHealth + DRUID_HEAL_AMOUNT)
                        
                        print(f"IA Druid ({entity}): Soigne la cible {target_id} de {DRUID_HEAL_AMOUNT} PV.")

            elif action.type == ActionType.VINE:
                target_id = params.get('target')
                if target_id and es.has_component(entity, SpeDruid) and es.entity_exists(target_id):
                    druid_spec = es.component_for_entity(entity, SpeDruid)
                    if druid_spec.can_cast_ivy():
                        # Utilise l'événement 'special_vine_event' que votre jeu gère déjà
                        # pour créer le projectile de lierre.
                        es.dispatch_event('special_vine_event', entity, target_id)
                        
                        # Le cooldown est géré par la logique interne de SpeDruidComponent
                        # après que le projectile est lancé.
                        print(f"IA Druid ({entity}): Lance un lierre sur {target_id}")