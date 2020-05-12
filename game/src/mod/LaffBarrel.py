from src.coginvasion.szboss.DistributedEntity import DistributedEntity
from src.coginvasion.szboss.UseableObject import UseableObject
from src.coginvasion.base.ToontownIntervals import getPulseIval

from direct.interval.IntervalGlobal import Sequence, SoundInterval, Parallel, Func, LerpScaleInterval, LerpPosInterval

class LaffBarrel(DistributedEntity, UseableObject):
    
    StateAvailable = 0
    StateEmpty = 1
    StateGiving = 2
    
    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        UseableObject.__init__(self)
        
        self.barrel = None
        self.gagModel = None
        self.gagNode = None
        self.barrelScale = 0.5
        self.pulseIval = None
        
        self.hasPhysGeom = False
        self.underneathSelf = True
        
    def clearPulseIval(self):
        if self.pulseIval:
            self.pulseIval.finish()
            self.pulseIval = None
        
    def startUse(self):
        UseableObject.startUse(self)
        self.sendUpdate('startUse')
        
    def stopUse(self):
        UseableObject.stopUse(self)
        self.sendUpdate('stopUse')
        
    def giveLaffTo(self, avId):
        plyr = self.cr.doId2do.get(avId, None)
        isLocal = plyr.doId == base.localAvatar.doId
        
        self.clearPulseIval()
        self.pulseIval = getPulseIval(self.barrelRoot, 'barrelPulse', 0.95, 0.2)
        self.pulseIval.start()

        # Spit out ice cream lol
        iceCream = loader.loadModel("phase_4/models/props/icecream.bam")
        iceCream.setPos(self.gagModel.getPos(render))
        iceCream.setScale(self.gagModel.getScale(render))
        iceCream.wrtReparentTo(base.camera if isLocal else plyr)
        iceCream.setTransparency(True)
        iceCream.setAlphaScale(0.6)
        
        if isLocal:
            end = (0, 0, -0.4)
        else:
            end = plyr.getEyePosition()
        
        icIval = Sequence(Parallel(LerpPosInterval(iceCream, duration = 0.5, pos = end),
                                   LerpScaleInterval(iceCream, duration = 0.5, scale = (0.1, 0.1, 0.1))), Func(iceCream.removeNode))
        icIval.start()

    def setEntityState(self, state):
        DistributedEntity.setEntityState(self, state)
        self.clearSequence()
        if state == self.StateEmpty:
            self.setColorScale(0.5, 0.5, 0.5, 1.0)
            self.playSound('empty')
            self.stopSound('start')
            self.stopSound('giveLaff')
        elif state == self.StateAvailable:
            self.setColorScale(1, 1, 1, 1)
        elif state == self.StateGiving:
            self.setSequence(Sequence(SoundInterval(self.getSound('start'), duration = self.getSound('start').length() / 2.0),
                                      Func(self.setSequence, SoundInterval(self.getSound('giveLaff'), duration = self.getSound('giveLaff').length() / 4.0), True)))
        
    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        self.barrelRoot = self.attachNewNode('barrelRoot')
        barrel = self.getModelNP()
        barrel.setScale(self.barrelScale)
        barrel.reparentTo(self.barrelRoot)
        barrel.setHpr(180, 0, 0)
        
        lblBg = barrel.find('**/gagLabelDCS')
        lblBg.setColor(0.15, 0.15, 0.1)
        
        self.gagNode = barrel.attachNewNode('gagNode')
        self.gagNode.setPosHpr(0.0, -2.62, 4.0, 0, 0, 0)
        self.gagNode.setColorScale(0.7, 0.7, 0.6, 1)
        
        self.gagModel = loader.loadModel('phase_4/models/props/icecream.bam')
        self.gagModel.reparentTo(self.gagNode)
        self.gagModel.find('**/p1_2').clearBillboard()
        self.gagModel.setScale(0.6)
        self.gagModel.setPos(0, -0.1, -0.1 - 0.6)
        
        self.addSound('empty', 'phase_4/audio/sfx/MG_sfx_travel_game_square_no_vote_1.ogg')
        self.addSound('giveLaff', 'phase_4/audio/sfx/SZ_DD_treasure.ogg')
        self.addSound('start', 'phase_4/audio/sfx/MG_pairing_match.ogg')
        
        UseableObject.load(self)
