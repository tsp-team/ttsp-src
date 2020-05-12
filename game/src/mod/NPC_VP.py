# coding: utf-8

from src.coginvasion.avatar.DistributedAvatar import DistributedAvatar
from src.coginvasion.avatar.BaseActivity import BaseActivity
from src.coginvasion.avatar.Activities import *
from direct.interval.IntervalGlobal import ActorInterval, Func, Sequence, SoundInterval, Parallel, LerpHprInterval, Wait
from src.coginvasion.attack.LinearProjectile import LinearProjectile
from src.coginvasion.cog.DistributedSuit import DistributedSuit
from src.coginvasion.cog import SuitGlobals
from src.coginvasion.szboss.goon.NPC_Goon import NPC_Goon
from src.coginvasion.phys.PhysicsNodePath import BasePhysicsObject
from src.coginvasion.avatar.ChatTypes import *
from src.coginvasion.base.Precache import precacheActor, precacheSound, precacheModel, precacheOther

from panda3d.core import Vec3
from libpandabsp import LightingOriginEffect

class Gear(LinearProjectile):
    
    ModelPath = "phase_9/models/char/gearProp.bam"
    ModelScale = 0.15
    
    def announceGenerate(self):
        LinearProjectile.announceGenerate(self)
        vec = (Vec3(*self.linearEnd) - Vec3(*self.linearStart)).normalized()
        models = [self.model]
        for i in range(5):
            newGear = self.model.copyTo(self)
            models.append(newGear)
        
        import random
        for i in range(len(models)):
            gear = models[i]
            gear.lookAt(vec)
            gear.setY(gear, i * -12)
            gear.setX(gear, random.uniform(i * -6, i * 6))
            #if i != 0:
            #    gear.posInterval(self.linearDuration, (, 0, 0), (0, 0, 0), other = gear).start()
            gear.hprInterval(0.5, (360, 0, 0), (0, 0, 0), other = gear).loop()
        #self.flattenStrong()
        
class VPSuit(DistributedSuit):
    pass
    
class VPGoon(NPC_Goon):
    pass

class IdleActivity(BaseActivity):
    
    def doActivity(self):
        return Sequence(Func(self.avatar.loop, "neutral"))
        
class ThrowActivity(BaseActivity):
    
    def doActivity(self):
        
        return Parallel(ActorInterval(self.avatar, "throw"), Func(self.avatar.throwGearsSnd.play))
        
class DamageReact(BaseActivity):
    
    def doActivity(self):
        return Sequence(Func(self.avatar.playSound, "stun"), ActorInterval(self.avatar, "stun"), Func(self.avatar.playSound, "raise"),
                        ActorInterval(self.avatar, "raise"))
                        
class Stun(BaseActivity):
    
    def doActivity(self):
        stunDur = self.avatar.getDuration("stun")
        raiseDur = self.avatar.getDuration("raise")
        waitDur = 10.0 - stunDur - raiseDur
        return Parallel(Sequence(Func(self.avatar.loopSound, "chirp"), Func(self.avatar.playSound, "stun"),
                        ActorInterval(self.avatar, "stun"), Func(self.avatar.loop, "downNeutral"),
                        Wait(waitDur), Func(self.avatar.stopSound, "chirp"), Func(self.avatar.playSound, "raise"),
                        ActorInterval(self.avatar, "raise")),
                        
                        SuitGlobals.createStunInterval(self.avatar, 0, stunDur + waitDur, pos = (2, 0, 0), hpr = (0, 0, 90), scale = 2.5))
                        
class Die(BaseActivity):
    
    def doActivity(self):
        return Sequence(Func(self.avatar.playSound, "stun"), ActorInterval(self.avatar, "stun"), Func(self.avatar.hide))
        
class Jump(BaseActivity):
    
    def doActivity(self):
        return Sequence(Func(self.avatar.playSound, "jumpStart"),
                        ActorInterval(self.avatar, "jump", endFrame = 29),
                        Func(self.avatar.playSound, "jumpEnd"),
                        ActorInterval(self.avatar, "jump", startFrame = 30))

class NPC_VP(DistributedAvatar):
    
    StunSoundPath = "phase_5/audio/sfx/AA_sound_aoogah.ogg"
    ChirpSoundPath = "phase_4/audio/sfx/SZ_TC_bird1.ogg"
    RaiseSoundPath = "phase_9/audio/sfx/CHQ_VP_raise_up.ogg"
    JumpStartSoundPath = "phase_5/audio/sfx/General_throw_miss.ogg"
    JumpEndSoundPath = "phase_3.5/audio/sfx/ENC_cogfall_apart.ogg"
    ThrowGearsSoundPath = "phase_9/audio/sfx/CHQ_VP_frisbee_gears.ogg"
    StatementSoundPath = "phase_9/audio/sfx/Boss_COG_VO_statement.ogg"
    QuestionSoundPath = "phase_9/audio/sfx/Boss_COG_VO_question.ogg"
    GruntSoundPath = "phase_9/audio/sfx/Boss_COG_VO_grunt.ogg"
    DoorOpenSoundPath = "phase_9/audio/sfx/CHQ_VP_door_open.ogg"
    DoorCloseSoundPath = "phase_9/audio/sfx/CHQ_VP_door_close.ogg"
    
    LegsActorDef = ["phase_9/models/char/bossCog-legs-zero.bam",
                       {"neutral": "phase_9/models/char/bossCog-legs-Fb_neutral.bam",
                        "downNeutral": "phase_9/models/char/bossCog-legs-Fb_downNeutral.bam",
                        "throw":   "phase_9/models/char/bossCog-legs-Fb_UpThrow.bam",
                        "stun":    "phase_9/models/char/bossCog-legs-Fb_firstHit.bam",
                        "raise":   "phase_9/models/char/bossCog-legs-Fb_down2Up.bam",
                        "jump":    "phase_9/models/char/bossCog-legs-Fb_jump.bam"}]
    TorsoActorDef = ["phase_9/models/char/sellbotBoss-torso-zero.bam",
                     {"neutral": "phase_9/models/char/bossCog-torso-Fb_neutral.bam",
                        "downNeutral": "phase_9/models/char/bossCog-torso-Fb_downNeutral.bam",
                        "throw":   "phase_9/models/char/bossCog-torso-Fb_UpThrow.bam",
                        "stun":    "phase_9/models/char/bossCog-torso-Fb_firstHit.bam",
                        "raise":    "phase_9/models/char/bossCog-torso-Fb_down2Up.bam",
                        "jump":     "phase_9/models/char/bossCog-torso-Fb_jump.bam"}]
    HeadActorDef = ["phase_9/models/char/sellbotBoss-head-zero.bam",
                    {"neutral": "phase_9/models/char/bossCog-head-Fb_neutral.bam",
                        "downNeutral": "phase_9/models/char/bossCog-head-Fb_downNeutral.bam",
                        "throw":   "phase_9/models/char/bossCog-head-Fb_UpThrow.bam",
                        "stun":    "phase_9/models/char/bossCog-head-Fb_firstHit.bam",
                        "raise":    "phase_9/models/char/bossCog-head-Fb_down2Up.bam",
                        "jump":     "phase_9/models/char/bossCog-head-Fb_jump.bam"}]
                        
    TreadsModel = "phase_9/models/char/bossCog-treads.bam"

    def __init__(self, cr):
        DistributedAvatar.__init__(self, cr)
        
        self.activities = {ACT_NONE: IdleActivity(self),
                           ACT_IDLE:    IdleActivity(self),
                           ACT_VP_THROW: ThrowActivity(self),
                           ACT_VP_STUN:  Stun(self),
                           ACT_VP_DAMAGE_REACT: DamageReact(self),
                           ACT_DIE:     Die(self),
                           ACT_RANGE_ATTACK2:   Jump(self)}
                           
        self.frontDoorIval = None
        self.rearDoorIval = None
        self.throwGearsSnd = None
        self.treads = None
        
        self.addSound("stun", self.StunSoundPath)
        self.addSound("raise", self.RaiseSoundPath)
        self.addSound("jumpStart", self.JumpStartSoundPath)
        self.addSound("jumpEnd", self.JumpEndSoundPath)
        self.addSound("chirp", self.ChirpSoundPath)
        
        self.addSound("statement", self.StatementSoundPath)
        self.addSound("question", self.QuestionSoundPath)
        self.addSound("grunt", self.GruntSoundPath)
        self.chatSoundTable[CHAT_SHORT] = "statement"
        self.chatSoundTable[CHAT_MEDIUM] = "statement"
        self.chatSoundTable[CHAT_LONG] = "statement"
        self.chatSoundTable[CHAT_EXCLAIM] = "statement"
        self.chatSoundTable[CHAT_QUESTION] = "question"
        self.chatSoundTable[CHAT_HOWL] = "statement"
        
    @classmethod
    def doPrecache(cls):
        super(NPC_VP, cls).doPrecache()
        precacheActor(cls.LegsActorDef)
        precacheActor(cls.TorsoActorDef)
        precacheActor(cls.HeadActorDef)
        precacheModel(cls.TreadsModel)
        precacheSound(cls.ThrowGearsSoundPath)
        precacheSound(cls.DoorOpenSoundPath)
        precacheSound(cls.DoorCloseSoundPath)
        precacheSound(cls.StatementSoundPath)
        precacheSound(cls.QuestionSoundPath)
        precacheSound(cls.GruntSoundPath)
        precacheSound(cls.StunSoundPath)
        precacheSound(cls.RaiseSoundPath)
        precacheSound(cls.JumpStartSoundPath)
        precacheSound(cls.JumpEndSoundPath)
        precacheSound(cls.ChirpSoundPath)
        
    def clearFrontDoorIval(self):
        if self.frontDoorIval:
            self.frontDoorIval.finish()
        self.frontDoorIval = None
        
    def clearRearDoorIval(self):
        if self.rearDoorIval:
            self.rearDoorIval.finish()
        self.rearDoorIval = None
                           
    def openFrontDoor(self):
        self.clearFrontDoorIval()
        
        self.frontDoorIval = Parallel(SoundInterval(self.frontDoorOpenSnd),
                                      LerpHprInterval(self.frontDoor, 1, (-90, 0, 0), (-90, 0, -80), blendType = 'easeInOut'))
        self.frontDoorIval.start()
        
    def closeFrontDoor(self):
        self.clearFrontDoorIval()
        
        self.frontDoorIval = Parallel(SoundInterval(self.frontDoorCloseSnd),
                                      LerpHprInterval(self.frontDoor, 1, (-90, 0, -80), (-90, 0, 0), blendType = 'easeInOut'))
        self.frontDoorIval.start()
        
    def openRearDoor(self):
        self.clearRearDoorIval()
        
        self.rearDoorIval = Parallel(SoundInterval(self.rearDoorOpenSnd),
                                      LerpHprInterval(self.rearDoor, 1, (90, 0, 165), (90, 0, 80), blendType = 'easeInOut'))
        self.rearDoorIval.start()
        
    def closeRearDoor(self):
        self.clearRearDoorIval()
        
        self.rearDoorIval = Parallel(SoundInterval(self.rearDoorCloseSnd),
                                      LerpHprInterval(self.rearDoor, 1, (90, 0, 80), (90, 0, 165), blendType = 'easeInOut'))
        self.rearDoorIval.start()
        
    def setupPhysics(self, radius = None, height = None):
        from NPC_VPShared import makeVPPhysics
        bodyNode = makeVPPhysics()
        bodyNode.setPythonTag("avatar", self)

        BasePhysicsObject.setupPhysics(self, bodyNode, True)
        
        self.stopWaterCheck()
        
    def announceGenerate(self):
        self.loadModel(self.LegsActorDef[0], "legs")
        self.loadModel(self.TorsoActorDef[0], "torso")
        self.loadModel(self.HeadActorDef[0], "head")
        self.treads = loader.loadModel(self.TreadsModel)
        self.treads.clearModelNodes()
        self.treads.flattenStrong()
        
        self.loadAnims(self.LegsActorDef[1], "legs")
        self.loadAnims(self.TorsoActorDef[1], "torso")
        self.loadAnims(self.HeadActorDef[1], "head")
        self.headModel = self.getPart("head")
        self.loop("neutral")
        
        self.attach("head", "torso", "joint34")
        self.attach("torso", "legs", "joint_legs")
        self.treads.reparentTo(self.find("**/joint_axle"))
        
        self.throwGearsSnd = base.loadSfxOnNode(self.ThrowGearsSoundPath, self)
        
        self.frontDoor = self.controlJoint(None, "legs", "joint_doorFront")
        self.rearDoor = self.controlJoint(None, "legs", "joint_doorRear")
        self.frontDoor.setR(-80)
        self.rearDoor.setR(80)
        self.rearDoorOpenSnd = base.loadSfxOnNode(self.DoorOpenSoundPath, self.rearDoor)
        self.rearDoorCloseSnd = base.loadSfxOnNode(self.DoorCloseSoundPath, self.rearDoor)
        self.frontDoorOpenSnd = base.loadSfxOnNode(self.DoorOpenSoundPath, self.frontDoor)
        self.frontDoorCloseSnd = base.loadSfxOnNode(self.DoorCloseSoundPath, self.frontDoor)
        
        self.setupNameTag()
        
        # Make sure the VP is in the sun
        self.setEffect(LightingOriginEffect.make((0, 5, 0)))
        
        self.setupPhysics()
        self.nametag3d.setZ(25)
        self.nametag.nametag3d.SCALING_FACTOR = 0.125

        self.startSmooth()
        self.reparentTo(render)
        
    def disable(self):
        self.stopSmooth()
        self.clearFrontDoorIval()
        self.clearRearDoorIval()
        self.headModel = None
        self.throwGearsSnd = None
        self.rearDoorCloseSnd = None
        self.rearDoorOpenSnd = None
        self.frontDoorOpenSnd = None
        self.frontDoorCloseSnd = None
        self.frontDoor = None
        self.rearDoor = None
        self.treads = None
        DistributedAvatar.disable(self)
