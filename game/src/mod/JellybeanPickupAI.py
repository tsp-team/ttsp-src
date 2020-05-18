from src.coginvasion.szboss.DistributedEntityAI import DistributedEntityAI

class JellybeanPickupAI(DistributedEntityAI):

    def __init__(self, air, dispatch = None):
        DistributedEntityAI.__init__(self, air, dispatch)
        self.setModel("models/jellybean.bam")
        self.setModelScale(3.0)

    def announceGenerate(self):
        DistributedEntityAI.announceGenerate(self)
        self.sendCurrentPosition()

    def pickup(self):
        if self.getEntityState() == 1:
            return

        avId = self.air.getAvatarIdFromSender()
        av = self.air.doId2do.get(avId)
        av.b_setMoney(av.getMoney() + 10)
        bz = self.air.battleZones[self.zoneId]
        bz.playerCollectMoney(10, avId)

        print("Give money")

        self.setEntityState(1)

    def think(self):
        if self.getEntityState() == 1:
            delta = self.getEntityStateElapsed()
            if delta >= 1.0:
                self.setNextThink(-1)
                self.requestDelete()
