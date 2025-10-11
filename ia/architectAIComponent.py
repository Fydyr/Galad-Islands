import joblib
import numpy as np
class ArchitectAIComponent:
    def __init__(self, decisionVetoTime: int = 0.01, model: str|None = None):
        self.decisionVetoTime = decisionVetoTime
        self.model = None
        if model is not None:
            self.model = joblib.load(model)
        self.vetoTimeRemaining = 0
        self.currentDecision = None
        self.ACTIONS = [
            'accelerate', 
            'decelerate', 
            'rotate_left', 
            'rotate_right',
            'build_defense_tower',
            'build_attack_tower'
        ]

    def makeDecision(self, dt: float, state: list[float, float, float, float, float, float, int, float]):
        # Placeholder for AI decision logic
        # 'state' can be any data structure representing the environment
        if self.model is not None:
            if self.vetoTimeRemaining == 0:
                self.vetoTimeRemaining = self.decisionVetoTime
                state = np.array([state])
                action_idx = self.model.predict(state)[0]
                self.currentDecision = self.ACTIONS[action_idx]
            # else:
            #     if (self.vetoTimeRemaining - dt) < 0:
            #         self.vetoTimeRemaining = 0
            #     else:
            #         self.vetoTimeRemaining -= -dt

            return self.currentDecision