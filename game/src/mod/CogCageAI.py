from src.coginvasion.szboss.DistributedEntityAI import DistributedEntityAI
from src.coginvasion.phys import PhysicsUtils

class CogCageAI(DistributedEntityAI):
    
    StateOpened = 1
    StateOpening = 2
    StateClosed = 3
    StateClosing = 4
    
    def __init__(self, air, dispatch):
        DistributedEntityAI.__init__(self, air, dispatch)
        self.entState = self.StateClosed
        
    def requestOpen(self):
        if self.entState == self.StateClosed:
            self.OpenCage()
        
    def load(self):
        DistributedEntityAI.load(self)
        
        self.setModel("models/cage.bam", True)
        self.setModelScale(self.getEntityValueVector("scale"))
        self.optimizeModel()
        self.enableModelCollisions()
        
    def setEntityState(self, state):
        DistributedEntityAI.setEntityState(self, state)
        if state == self.StateOpened:
            self.dispatchOutput("OnOpenCage")
        
    def think(self):
        elapsed = self.getEntityStateElapsed()
        state = self.getEntityState()
        
        if state == self.StateOpening:
            if elapsed >= 0.5:
                self.b_setEntityState(self.StateOpened)
        elif state == self.StateClosing:
            if elapsed >= 0.5:
                self.b_setEntityState(self.StateClosed)
                
    def OpenCage(self):
        self.b_setEntityState(self.StateOpening)
        
    def CloseCage(self):
        self.b_setEntityState(self.StateClosing)
