"""
Processeur pour gérer les sons d'explosion lors des dégâts.
Détecte quand une unité prend des dégâts et joue un son d'explosion.
"""

import esper
from src.components.core.healthComponent import HealthComponent


class ExplosionSoundProcessor(esper.Processor):
    """
    Processeur qui surveille les changements de santé des entités
    et joue un son d'explosion quand des dégâts sont infligés.
    """

    def __init__(self, audio_manager):
        super().__init__()
        self.audio_manager = audio_manager
        self.entity_health_cache = {}  # Cache des HP précédents
        self.debug = True  # Activer pour voir les logs de débogage

    def process(self, **kwargs):
        """
        Vérifie les changements de santé et joue un son d'explosion
        si une entité a perdu des points de vie.
        """
        # Parcourt toutes les entités avec un composant de santé
        for entity, health in esper.get_component(HealthComponent):
            current_health = health.currentHealth

            # Vérifie si on a déjà enregistré cette entité
            if entity in self.entity_health_cache:
                previous_health = self.entity_health_cache[entity]

                # Si l'entité a perdu des HP (et est toujours vivante)
                if current_health < previous_health and current_health > 0:
                    damage_taken = previous_health - current_health
                    if self.debug:
                        print(f"🩸 Entité {entity} a pris {damage_taken} dégâts ({previous_health} -> {current_health})")

                    # Joue un son d'explosion (uniquement si aucun n'est en cours)
                    self.audio_manager.play_explosion_sound()

            # Met à jour le cache avec la santé actuelle
            self.entity_health_cache[entity] = current_health

        # Nettoie le cache des entités supprimées
        self._clean_cache()

    def _clean_cache(self):
        """
        Supprime du cache les entités qui n'existent plus.
        Évite les fuites mémoire.
        """
        # Récupère toutes les entités actuellement vivantes avec HealthComponent
        current_entities = set(entity for entity, _ in esper.get_component(HealthComponent))

        # Supprime les entités qui ne sont plus dans le monde
        entities_to_remove = [
            entity for entity in self.entity_health_cache.keys()
            if entity not in current_entities
        ]

        for entity in entities_to_remove:
            del self.entity_health_cache[entity]
