import joblib
import numpy as np
class ArchitectAIComponent:
    def __init__(self, decisionVetoTime: int = 0.00):
        self.decisionVetoTime = decisionVetoTime
        self.vetoTimeRemaining = 0
        self.currentDecision = None

    def setVetoMax(self):
        self.vetoTimeRemaining = self.decisionVetoTime


    # def makeDecision(self, dt: float, state: list[float, float, float, float, float, float, int, float]):
    #     # Placeholder for AI decision logic
    #     # 'state' can be any data structure representing the environment
    #     if self.model is not None:
    #         if self.vetoTimeRemaining == 0:
    #             self.vetoTimeRemaining = self.decisionVetoTime
    #             state = np.array([state])
    #             action_idx = self.model.predict(state)[0]
    #             self.currentDecision = self.ACTIONS[action_idx]
    #             return self.ACTIONS[action_idx]
    #         else:
    #         #     if (self.vetoTimeRemaining - dt) < 0:
    #         #         self.vetoTimeRemaining = 0
    #         #     else:
    #         #         self.vetoTimeRemaining -= -dt

    #             return self.currentDecision