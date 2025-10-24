class ArchitectAIComponent:
    def __init__(self, decisionVetoTime: int = 0.00):
        self.decisionVetoTime = decisionVetoTime
        self.vetoTimeRemaining = 0
        self.currentDecision = None

    def setVetoMax(self):
        self.vetoTimeRemaining = self.decisionVetoTime
