from src.coginvasion.szboss.DistributedEntityAI import DistributedEntityAI

class LaffBarrelAI(DistributedEntityAI):
    StateAvailable = 0
    StateEmpty = 1
    StateGiving = 2
    
    def __init__(self, air, dispatch = None):
        DistributedEntityAI.__init__(self, air, dispatch)
        self.hp = 100
        self.maxHp = 100
        self.avId = None
        self.lastGive = 0.0
        self.giveIval = 0.09
        
    def announceGenerate(self):
        DistributedEntityAI.announceGenerate(self)
        self.b_setModel('phase_4/models/cogHQ/gagTank.bam')
        
    def loadEntityValues(self):
        self.hp = self.getEntityValueInt('maxHeal')
        self.maxHp = self.hp
        
    def hasHP(self):
        return self.hp > 0
        
    def setIdleState(self):
        if self.hasHP():
            self.b_setEntityState(self.StateAvailable)
        else:
            self.b_setEntityState(self.StateEmpty)
        
    def startUse(self):
        if self.avId is not None:
            return
            
        if not self.hasHP():
            self.d_playSound('empty')
            return
            
        self.avId = self.air.getAvatarIdFromSender()
        self.b_setEntityState(self.StateGiving)
        
    def stopUse(self):
        avId = self.air.getAvatarIdFromSender()
        if avId == self.avId:
            self.avId = None
            self.setIdleState()
        
    def think(self):
        DistributedEntityAI.think(self)
        
        now = globalClock.getFrameTime()
        state = self.getEntityState()
        elapsed = self.getEntityStateElapsed()
        if state == self.StateGiving:
            giveElapsed = now - self.lastGive
            if giveElapsed >= self.giveIval:
                if self.avId:
                    self.sendUpdate('giveLaffTo', [self.avId])
                    av = self.air.doId2do.get(self.avId, None)
                    if av:
                        av.heal(1)
                        self.hp -= 1
                        self.lastGive = now
                        if not self.hasHP():
                            self.setIdleState()
                            return
                    else:
                        self.setIdleState()
                        return
            
    
