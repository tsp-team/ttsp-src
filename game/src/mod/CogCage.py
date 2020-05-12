from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Parallel, Func
from src.coginvasion.szboss.DistributedEntity import DistributedEntity
from src.coginvasion.szboss.UseableObject import UseableObject
from src.coginvasion.globals import CIGlobals

class CogCage(DistributedEntity, UseableObject):
    StateOpened = 1
    StateOpening = 2
    StateClosed = 3
    StateClosing = 4
    
    GateBoneOrigin = (-2.05, 0, 0.31)
    ClosedAngles = (270, 90, 90)
    OpenedAngles = (270, 183, 90)
    
    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        UseableObject.__init__(self, False)
        self.doorHinge = None
        self.shapeGroup = CIGlobals.UseableGroup
        
    def startUse(self):
        self.sendUpdate('requestOpen')
        
    def removeNode(self):
        UseableObject.removeNode(self)
        DistributedEntity.removeNode(self)
        
    def disable(self):
        if self.doorHinge:
            self.doorHinge.removeNode()
        self.doorHinge = None
        DistributedEntity.disable(self)

    def load(self):
        DistributedEntity.load(self)
        UseableObject.load(self)

    def setModel(self, model, animating):
        DistributedEntity.setModel(self, model, animating)

        loader.loadModel("models/cage.bam").find("**/collisions").reparentTo(self.getModelNP())
        self.optimizeModel()
        self.getModelNP().postFlatten()
        self.enableModelCollisions()
        self.getModelNP().find("**/collisions").setCollideMask(CIGlobals.UseableGroup | CIGlobals.WallGroup)
        self.getModelNP().find("**/collisions").setPythonTag('useableObject', self)
        self.doorHinge = self.getModelNP().controlJoint(None, "modelRoot", "Bone")
        self.doorHinge.setPos(self.GateBoneOrigin)
        self.doorHinge.setHpr(self.ClosedAngles)
        self.addSound("door", "phase_5/audio/sfx/CHQ_SOS_cage_door.ogg")
        
    def setEntityState(self, state):
        if state == self.StateClosed:
            self.clearSequence()
            self.doorHinge.setHpr(self.ClosedAngles)
        elif state == self.StateOpened:
            self.clearSequence()
            self.doorHinge.setHpr(self.OpenedAngles)
        elif state == self.StateOpening:
            self.setSequence(Parallel(self.doorHinge.hprInterval(0.5, self.OpenedAngles, self.ClosedAngles, blendType = 'easeIn'), Func(self.playSound, "door")))
        elif state == self.StateClosing:
            self.setSequence(Parallel(self.doorHinge.hprInterval(0.5, self.ClosedAngles, self.OpenedAngles, blendType = 'easeIn'), Func(self.playSound, "door")))
        
