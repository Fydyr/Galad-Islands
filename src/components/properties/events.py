import random
import pygame


# classe de base pour les événements du jeu. 
# elle sert de modèle pour des événements spécifiques comme Tempête, Vague de bandits, Kraken et Coffre volant.
class GameEvent:
    def __init__(self, name, chance):
        self.name = name
        self.chance = chance

    # retourne true si l'évènement doit se déclencher en fonction de sa probabilité
    def should_trigger(self):
        return random.random() < self.chance
    
    # méthode à surcharger dans les classes enfants pour définir ce qui se passe quand l'événement est activé
    def trigger(self, game_state):
        pass

class Tempete(GameEvent):
    def __init__(self):
        super().__init__("Tempête", 0.15)
        self.degats = 30
        self.duree = 20  # secondes
        self.cooldown = 3  # secondes
        self.radius = 4

    def trigger(self, game_state):
        # Ajoute la logique pour placer la tempête et infliger des dégâts
        print("Tempête déclenchée !")

class VagueBandits(GameEvent):
    def __init__(self):
        super().__init__("Vague de bandits", 0.25)
        self.degats = 20
        self.radius = 5
        self.nb_bateaux = random.randint(1, 6)

    def trigger(self, game_state):
        print("Vague de bandits déclenchée !")

class Kraken(GameEvent):
    def __init__(self):
        super().__init__("Kraken", 0.10)
        self.degats = 70
        self.nb_tentacules = random.randint(2, 6)

    def trigger(self, game_state):
        print("Kraken déclenché !")

class CoffreVolant(GameEvent):
    def __init__(self):
        super().__init__("Coffre volant", 0.20)
        self.gold_min = 10
        self.gold_max = 20
        self.duree = 20  # secondes
        self.nb_coffres = random.randint(2, 5)

    def trigger(self, game_state):
        print("Coffre volant déclenché !")

# Pour gérer les événements dans la boucle principale :
ALL_EVENTS = [Tempete(), VagueBandits(), Kraken(), CoffreVolant()]

def trigger_random_event(game_state):
    for event in ALL_EVENTS:
        if event.should_trigger():
            event.trigger(game_state)
            break  # Un seul événement à la fois

# game_state est un objet ou dict représentant l'état du jeu (à adapter selon ton architecture)
    