class ArchitectAIComponent:
    def __init__(self, decisionVetoTime: int = 0.80):
        self.decisionVetoTime = decisionVetoTime
        self.vetoTimeRemaining = 0
        self.currentDecision = None
        self.build_cooldown = 4.0
        self.build_cooldown_remaining = 0.0

    def setVetoMax(self):
        self.vetoTimeRemaining = self.decisionVetoTime

    def start_build_cooldown(self):
        """Starts the build cooldown timer."""
        self.build_cooldown_remaining = self.build_cooldown
