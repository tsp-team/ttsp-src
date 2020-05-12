from src.coginvasion.szboss.DistributedEntityAI import DistributedEntityAI

class CodeNumberPickupAI(DistributedEntityAI):

    def __init__(self, air, dispatch = None):
        DistributedEntityAI.__init__(self, air, dispatch)
        self.number = 0
        
    def announceGenerate(self):
        DistributedEntityAI.announceGenerate(self)
        self.sendCurrentPosition()
        
    def setNumber(self, num):
        self.number = num
        
    def getNumber(self):
        return self.number
        
    def pickup(self):
        avId = self.air.getAvatarIdFromSender()
        plyr = self.air.doId2do.get(avId)
        plyr.addCodeNumber(self.number)
        plyr.battleZone.numberWasPickedUp()
        self.requestDelete()
        
    def delete(self):
        del self.number
        DistributedEntityAI.delete(self)
