import esper
from src.components.special.speScoutComponent import SpeScout
from src.components.special.speMaraudeurComponent import SpeMaraudeur
from src.components.special.speLeviathanComponent import SpeLeviathan
from src.components.special.speDruidComponent import SpeDruid
from src.components.special.speArchitectComponent import SpeArchitect
from src.components.special.speKamikazeComponent import SpeKamikazeComponent
from src.components.special.isVinedComponent import isVinedComponent
from src.processeurs.ability.VineProcessor import VineProcessor
from src.components.core.radiusComponent import RadiusComponent

class CapacitiesSpecialesProcessor(esper.Processor):
    def process(self, dt, **kwargs):
        # Scout : manœuvre d'évasion (invincibilité)
        for ent, speScout in esper.get_component(SpeScout):
            speScout.update(dt)
        
        # Maraudeur : bouclier de mana (réduction dégâts)
        for ent, speMaraudeur in esper.get_component(SpeMaraudeur):
            speMaraudeur.update(dt)
        
        # Leviathan : seconde salve (instantané, cooldown)
        for ent, speLeviathan in esper.get_component(SpeLeviathan):
            speLeviathan.update(dt)
        
        # Druid : lierre volant (immobilisation)
        for ent, speDruid in esper.get_component(SpeDruid):
            speDruid.update(dt)

        # Kamikaze : boost de vitesse
        for ent, speKamikaze in esper.get_component(SpeKamikazeComponent):
            speKamikaze.update(dt)

        for ent, isVined in esper.get_component(isVinedComponent):
            VineProcessor.update(dt, ent, isVined)
        
        # Architect : rechargement automatique (effet de zone)
        for ent, speArchitect in esper.get_component(SpeArchitect):
            speArchitect.update(dt)
            
            # Si la capacité est active, applique le boost de rechargement
            if speArchitect.is_active and speArchitect.affected_units:
                for unit_id in speArchitect.affected_units:
                    try:
                        if esper.has_component(unit_id, RadiusComponent):
                            radius = esper.component_for_entity(unit_id, RadiusComponent)
                            
                            # Applique le facteur de rechargement (divise par 2)
                            if radius.cooldown > 0:
                                radius.cooldown -= dt * speArchitect.reload_factor
                                if radius.cooldown < 0:
                                    radius.cooldown = 0
                    except:
                        pass

        # Gérer le cooldown de base (soin/attaque) pour all units
        # qui n'ont pas déjà été affectées par l'Architecte ce tick.
        for ent, radius in esper.get_component(RadiusComponent):
            # Si l'entity est l'architecte lui-même OU n'est pas affectée par un architecte
            is_architect = esper.has_component(ent, SpeArchitect)
            is_affected = False
            if not is_architect:
                 # (Logique complexe pour Check siaffecté... simplifions)
                 # On applique simplement le cooldown à tout le monde.
                 # L'architecte ajoutera une réduction *supplémentaire*.
                 pass

            if radius.cooldown > 0:
                old_cooldown = radius.cooldown
                radius.cooldown -= dt  # Utiliser dt, c'est plus précis
                if radius.cooldown < 0:
                    radius.cooldown = 0
                # Log for Leviathan only (entity with SpeLeviathan component)
                if esper.has_component(ent, SpeLeviathan) and int(old_cooldown) != int(radius.cooldown):
                    print(f"[DEBUG] CapacitiesSpecialesProcessor - Entity {ent} radius.cooldown: {old_cooldown:.1f} -> {radius.cooldown:.1f} (dt={dt:.3f})")