from panda3d.core import Vec3, TransformState
from panda3d.bullet import BulletGhostNode, BulletBoxShape

from direct.interval.IntervalGlobal import Sequence, LerpPosInterval

from src.coginvasion.base.Precache import precacheModel, precacheSound
from src.coginvasion.szboss.DistributedEntity import DistributedEntity
from src.coginvasion.globals import CIGlobals

class CogStomper(DistributedEntity):
    StateStomp  = 0
    StateRaise  = 1
    StateUp     = 2
    StateDown   = 3
    
    StomperModelPath = "phase_9/models/cogHQ/square_stomper.bam"
    RaiseSoundPath = "phase_9/audio/sfx/CHQ_FACT_stomper_raise.ogg"
    BigStompSoundPath = "phase_9/audio/sfx/CHQ_FACT_stomper_large.ogg"
    SmallStompSoundPath = "phase_9/audio/sfx/CHQ_FACT_stomper_med.ogg"

    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        self.height = 1.0
        self.raiseSpeed = 1
        self.stompSpeed = 1
        self.scale = Vec3(1)
        self.moveDir = Vec3.up()
        
    @classmethod
    def doPrecache(cls):
        super(cls, CogStomper).doPrecache()
        precacheModel(cls.StomperModelPath)
        precacheSound(cls.RaiseSoundPath)
        precacheSound(cls.BigStompSoundPath)
        precacheSound(cls.SmallStompSoundPath)
        
    def setData(self, height, stompSpeed, raiseSpeed, scale):#, moveDir):
        self.height = height
        self.raiseSpeed = raiseSpeed
        self.stompSpeed = stompSpeed
        self.scale = Vec3(*scale)
        #self.moveDir = Vec3(*moveDir)
        
    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        
        self.getModelNP().find("**/shaft").setSy(self.height / 16.0)
        self.optimizeModel()
        
        self.enableModelCollisions()
        
        if self.scale.length() >= 5:
            self.addSound("stomp", self.BigStompSoundPath)
        else:
            self.addSound("stomp", self.SmallStompSoundPath)
        self.addSound("raise", self.RaiseSoundPath)
    
    def disable(self):
        self.height = None
        self.raiseSpeed = None
        self.stompSpeed = None
        self.scale = None
        self.moveDir = None
        DistributedEntity.disable(self)
        
    def getUpPosition(self):
        up = Vec3(self.height / 16.0)
        up.componentwiseMult(self.moveDir)
        return up
    
    def setEntityState(self, state):
        DistributedEntity.setEntityState(self, state)
        
        if state == self.StateDown:
            self.clearSequence()
            self.setPos(self.cEntity.getOrigin())
            self.playSound("stomp")
            base.emitShake(self, 0.5)
            
        elif state == self.StateUp:
            self.stopSound("raise")
            self.clearSequence()
            self.setPos(self.cEntity.getOrigin() + self.getUpPosition())
            
        elif state == self.StateStomp:
            self.setSequence(
                LerpPosInterval(self, self.height / self.stompSpeed, self.cEntity.getOrigin(),
                                self.cEntity.getOrigin() + self.getUpPosition())
            )
            
        elif state == self.StateRaise:
            self.loopSound("raise")
            self.setSequence(
                LerpPosInterval(self, self.height / self.raiseSpeed,
                                self.cEntity.getOrigin() + self.getUpPosition(),
                                self.cEntity.getOrigin())
            )
