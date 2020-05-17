from panda3d.core import CardMaker, NodePath
from src.coginvasion.szboss.DistributedEntity import DistributedEntity
from direct.interval.IntervalGlobal import Sequence, LerpPosInterval
from src.coginvasion.globals import CIGlobals

from panda3d.bullet import BulletSphereShape, BulletGhostNode
from panda3d.bsp import BloomAttrib

class CodeNumberPickup(DistributedEntity):

    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        self.number = 0
        self.emblem = None
        self.emblemFloat = None
        
    def setNumber(self, num):
        self.number = num
        
    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        cm = CardMaker('emblemCard')
        cm.setFrame(-0.5, 0.5, 0, 1)
        cm.setHasUvs(True)
        cm.setUvRange((0, 0), (1, 1))
        self.emblem = self.attachNewNode(cm.generate())
        self.emblem.setAttrib(BloomAttrib.make(False))
        self.emblem.setBSPMaterial('phase_5/maps/quest_scroll_emblem.mat', 1)
        self.emblem.setBillboardAxis()
        self.emblem.setTransparency(True)
        self.emblem.setScale(2)
        self.emblemFloat = Sequence(LerpPosInterval(self.emblem, 1.0, (0, 0, 0.5), (0, 0, 0), blendType = 'easeInOut'),
                                    LerpPosInterval(self.emblem, 1.0, (0, 0, 0), (0, 0, 0.5), blendType = 'easeInOut'))
        self.emblemFloat.loop()
        self.setupPhysics()
        self.reparentTo(render)
        
    def setupPhysics(self):
        shape = BulletSphereShape(1.0)
        bnode = BulletGhostNode(self.uniqueName('codeNumberPhys'))
        bnode.addShape(shape)
        bnode.setIntoCollideMask(CIGlobals.EventGroup)
        DistributedEntity.setupPhysics(self, bnode, True)
        self.stopWaterCheck()
        self.acceptOnce('enter' + self.uniqueName('codeNumberPhys'), self.__handlePickup)
        
    def __handlePickup(self, into):
        self.sendUpdate('pickup')
        self.hide()
        
    def disable(self):
        self.ignore('enter' + self.uniqueName('codeNumberPhys'))
        self.number = None
        if self.emblemFloat:
            self.emblemFloat.finish()
        self.emblemFloat = None
        if self.emblem:
            self.emblem.removeNode()
        self.emblem = None
        DistributedEntity.disable(self)
        
        
