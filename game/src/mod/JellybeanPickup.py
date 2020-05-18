from src.coginvasion.szboss.DistributedEntity import DistributedEntity

class JellybeanPickup(DistributedEntity):

    Colors = [(1, 0, 0, 1),
    (0, 0, 1, 1),
    (0, 1, 0, 1),
    (1, 0, 1, 1),
    (0, 1, 1, 1),
    (1, 1, 0, 1)]

    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        self.rot = None

    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)

        self.addSound("pickup", "sound/items/jellybean_pickup.ogg")

        import random
        color = random.choice(self.Colors)
        self.getModelNP().setColorScale(color, 1)

        from direct.interval.IntervalGlobal import LerpHprInterval
        self.rot = LerpHprInterval(self.getModelNP(), 1.0, (360, 0, 0), (0, 0, 0))
        self.rot.loop()

        from src.coginvasion.globals import CIGlobals
        from panda3d.bullet import BulletSphereShape, BulletGhostNode
        sph = BulletSphereShape(0.5)
        body = BulletGhostNode(self.uniqueName('jellybean-trigger'))
        body.addShape(sph)
        body.setIntoCollideMask(CIGlobals.EventGroup)
        self.setupPhysics(body, True)
        self.acceptOnce('enter' + self.uniqueName('jellybean-trigger'), self.__enterJellybeanTrigger)

    def __enterJellybeanTrigger(self, entry):
        print("Requesting money")
        self.playSound("pickup")
        self.hide()
        self.sendUpdate('pickup')

    def disable(self):
        self.ignore('enter' + self.uniqueName('jellybean-trigger'))
        if self.rot:
            self.rot.finish()
        self.rot = None
        DistributedEntity.disable(self)
