from src.coginvasion.avatar.DistributedAvatarAI import DistributedAvatarAI
from src.coginvasion.cog.ai.AIGlobal import *
from src.coginvasion.avatar.AvatarTypes import *
from src.coginvasion.avatar.Activities import *
from src.coginvasion.globals import CIGlobals
from src.coginvasion.attack.LinearProjectileAI import LinearProjectileAI
from src.coginvasion.globals import CIGlobals
from src.coginvasion.phys.WorldColliderAI import WorldColliderAI
from src.coginvasion.cog.DistributedSuitAI import DistributedSuitAI
from src.coginvasion.szboss.goon.NPC_GoonAI import NPC_GoonAI
from src.coginvasion.phys.PhysicsNodePathAI import BasePhysicsObjectAI
from src.coginvasion.cog.ai.tasks.BaseTaskAI import BaseTaskAI
from src.coginvasion.cog.ai.ScheduleResultsAI import *
from src.coginvasion.attack.TakeDamageInfo import TakeDamageInfo
from src.coginvasion.phys import PhysicsUtils
from src.coginvasion.avatar.RulesAndResponsesAI import RulesAndResponsesAI

from direct.interval.IntervalGlobal import Sequence, Wait, Func
from panda3d.core import Vec3, TransformState

from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode

from src.coginvasion.attack.TakeDamageInfo import TakeDamageInfo
from src.coginvasion.battle.SoundEmitterSystemAI import SOUND_COMBAT, SOUND_VP_JUMP

from src.mod import ModGlobals

class Task_MakeExplosions(BaseTaskAI):
    
    def __init__(self, npc):
        BaseTaskAI.__init__(self, npc)
        self.lastExplosionTime = 0.0
        self.explosionDelay = 0.0
        self.explosions = 0
        
    def runTask(self):
        now = globalClock.getFrameTime()
        if now - self.lastExplosionTime < self.explosionDelay:
            return SCHED_CONTINUE
            
        x = random.uniform(7, -7)
        y = random.uniform(8, -8)
        z = random.uniform(1, 20)
        self.npc.battleZone.tempEnts.makeExplosion(self.npc.getPos() + self.npc.getQuat().xform((x, y, z)), random.uniform(1, 2))
        self.lastExplosionTime = now
        self.explosionDelay = 0.35#random.uniform(0.3, 0.6)
        self.explosions += 1
        
        if self.explosions >= 10:
            return SCHED_COMPLETE
            
        return SCHED_CONTINUE

class GearAI(LinearProjectileAI):
    
    def doInitCollider(self):
        WorldColliderAI.__init__(self, "gearCollider", 1.0, needSelfInArgs = True,
                          useSweep = True, resultInArgs = True, startNow = False,
                          mask = CIGlobals.WorldGroup | CIGlobals.CharacterGroup)
        self.world = self.air.getPhysicsWorld(self.zoneId)
        
class BaseVPEnemy:
    
    def __init__(self, vp):
        self.vp = vp
        
        self.rearOrFront = 0
        
        self.schedules.update(
        
            {
                "VP_EXIT"   :   Schedule(
                    [
                        Task_StopMoving(self),
                        Task_StopAttack(self),
                        Task_Func(self.sendUpdate, ['doScaleUp']),
                        Task_Func(self.addExitWaypoint),
                        Task_RunPath(self, snapIdeal = True),
                        Task_AwaitMovement(self),
                        Task_Func(self.resetFwdSpeed),
                        Task_Func(self.setAutoTarget)
                    ],
                    interruptMask = COND_SCHEDULE_DONE|COND_TASK_FAILED
                )
            }
            
        )
        
        self.makeScheduleNames()
        
    def setAutoTarget(self):
        if self.isDead():
            return
            
        if not self.target:
            avs = []
            from src.coginvasion.toon.DistributedToonAI import DistributedToonAI
            for obj in self.air.doId2do.values():
                if isinstance(obj, DistributedToonAI):
                    avs.append(obj)
            target, relationship = self.getBestVisibleTarget(avs)
            self.pushTarget(self.target)
            self.setConditions(COND_NEW_TARGET|COND_SEE_TARGET)
            self.target = AITarget(target, relationship)
            self.target.lastKnownPosition = self.target.entity.getPos(render)
        self.setNPCState(STATE_COMBAT, True)
        self.changeSchedule(self.getScheduleByName("CHASE_TARGET"))
        
    def addExitWaypoint(self):
        vpos = self.getPos()
        quat = self.getQuat()
        if self.rearOrFront == 0:
            endPos = vpos + quat.xform((0, 11, 0))
        else:
            endPos = vpos + quat.xform((0, -11, 0))
        
        # Snap to floor
        result = PhysicsUtils.rayTestClosestNotMe(self, endPos + (0, 0, 0.5), endPos - (0, 0, 20), 
            CIGlobals.WorldGroup, self.getBattleZone().getPhysicsWorld())
        if result:
            endPos = result.getHitPos()
        
        self.motor.setWaypoints([endPos])
        self.motor.setFwdSpeed(5.0)
        
    def delete(self):
        self.vp = None
        self.rearOrFront = None
        
class VPSuitAI(DistributedSuitAI, BaseVPEnemy):
    
    def __init__(self, air, vp):
        DistributedSuitAI.__init__(self, air)
        BaseVPEnemy.__init__(self, vp)
        
    def delete(self):
        BaseVPEnemy.delete(self)
        DistributedSuitAI.delete(self)
        
    def monitorHealth(self, task):
        ret = DistributedSuitAI.monitorHealth(self, task)
        if self.isDead():
            try:
                self.vp.suitDie()
            except:
                pass
            return task.done
        return ret
        
class VPGoonAI(NPC_GoonAI, BaseVPEnemy):
    
    def __init__(self, air, vp):
        NPC_GoonAI.__init__(self, air, vp.getBattleZone())
        BaseVPEnemy.__init__(self, vp)
        
    def setNPCState(self, state, makeIdeal = True):
        if state == STATE_DEAD:
            try:
                self.vp.suitDie()
            except:
                pass
        NPC_GoonAI.setNPCState(self, state, makeIdeal)
        
    def delete(self):
        BaseVPEnemy.delete(self)
        NPC_GoonAI.delete(self)

class NPC_VPAI(DistributedAvatarAI, BaseNPCAI):
    
    AvatarType = AVATAR_SUIT
    Relationships = {
        AVATAR_SUIT: RELATIONSHIP_FRIEND,
        AVATAR_TOON: RELATIONSHIP_HATE
    }
    
    StunDamage = 100
    StunDecayRate = 7.5
    
    def __init__(self, air, dispatch = None):
        DistributedAvatarAI.__init__(self, air, dispatch)
        BaseNPCAI.__init__(self, dispatch)
        self.torsoYaw = 0.0
        
        self.name = "Senior V.P.\nSellbot"
        
        self.surfaceProp = "metal"
        
        self.schedules.update(
        
        {
            "OPENING_SPEECH"    :   Schedule(
                [
                    Task_Func(self.setCanStun, [False]),
                    Task_Wait(3.0),
                    Task_FaceIdeal(self),
                    Task_Speak(self, 1.0, ["What's this?! The captive has escaped! I order you back to your cage!"]),
                    Task_Wait(3.0),
                    Task_Func(self.makeIdealYawToPlayer),
                    Task_FaceIdeal(self),
                    Task_Speak(self, 1.0, ["And who is this? How did you get in here?!"]),
                    Task_Wait(3.0),
                    Task_Speak(self, 1.0, ["Wait a minute, they have Gags!"]),
                    Task_Wait(2.5),
                    Task_Speak(self, 1.0, ["Cogs... ATTACK!!"]),
                    Task_Wait(2.0),
                    Task_Func(self.dispatchOutput, ["OnFinishOpeningSpeech"]),
                    Task_Func(self.setCanStun, [True]),
                    Task_SuggestState(self, STATE_IDLE)
                ],
                interruptMask = COND_SCHEDULE_DONE|COND_TASK_FAILED
            ),
            "RANGE_ATTACK1" :   Schedule(
                [
                    Task_StopMoving(self),
                    Task_StopAttack(self),
                    Task_FaceTarget(self),
                    Task_SetActivity(self, ACT_VP_THROW),
                    Task_Wait(0.15),
                    Task_Func(self.throwGearsAtTarget),
                    Task_AwaitActivity(self)
                ]
            ),
            
            "RANGE_ATTACK2" :   Schedule(
                [
                    Task_StopMoving(self),
                    Task_StopAttack(self),
                    Task_SetActivity(self, ACT_RANGE_ATTACK2),
                    Task_Func(self.emitJumpSound),
                    Task_Wait(1.25),
                    Task_Func(self.doJump),
                    Task_AwaitActivity(self)
                ],
                interruptMask = COND_SCHEDULE_DONE | COND_TASK_FAILED
            ),
            
            "DAMAGE_REACT"  :   Schedule(
                [
                    Task_Func(self.setCanStun, [False]),
                    Task_StopMoving(self),
                    Task_StopAttack(self),
                    Task_SetActivity(self, ACT_VP_DAMAGE_REACT),
                    Task_AwaitActivity(self),
                    Task_SetActivity(self, ACT_NONE),
                    Task_Func(self.setCanStun, [True])
                ],
                interruptMask = COND_SCHEDULE_DONE|COND_TASK_FAILED
            ),
            
            "STUN"  :   Schedule(
                [
                    Task_Func(self.setStunned, [True]),
                    Task_StopMoving(self),
                    Task_StopAttack(self),
                    Task_SetActivity(self, ACT_VP_STUN),
                    Task_AwaitActivity(self),
                    Task_SetActivity(self, ACT_NONE),
                    Task_Func(self.setStunned, [False])
                ],
                interruptMask = COND_SCHEDULE_DONE|COND_TASK_FAILED
            ),
            
            "DIE"   :   Schedule(
                [
                    Task_StopMoving(self),
                    Task_StopAttack(self),
                    Task_SetActivity(self, ACT_DIE),
                    Task_MakeExplosions(self),
                    Task_AwaitActivity(self),
                    Task_Func(self.requestDelete)
                ],
                interruptMask = COND_SCHEDULE_DONE|COND_TASK_FAILED
            ),
        }
        
        )
        
        self.isStunned = False
        self.canStun = True
        self.currStunDamage = 0
        
        self.actTable = {ACT_NONE: ACT_IDLE}
        self.activities = {ACT_VP_THROW:    0.833333333333,
                           ACT_IDLE:        -1,
                           ACT_NONE:        -1,
                           ACT_VP_DAMAGE_REACT:     5.5,
                           ACT_VP_STUN: 10.0,
                           ACT_DIE:         3.5,
                           ACT_RANGE_ATTACK2: 3.0}
                           
        self.setHeight(5)
        self.hitboxData[1] = 10
                           
        self.version = 1
        
        self.lastSpawnTime = 0.0
        self.spawnIval = 0.0
        self.doorTime = 0.0
        self.doorState = 0
        
        self.maxSuits = 5
        self.numSuits = 0
        
        self.lastAttackTime = 0.0
        self.attackIval = 0.0
        
        self.idealYaw = 180
        
    def setStunned(self, flag):
        self.isStunned = flag
        
    def setCanStun(self, flag):
        self.canStun = flag
        
    def delete(self):
        self.torsoYaw = None
        self.version = None
        self.lastSpawnTime = None
        self.spawnIval = None
        self.doorTime = None
        self.doorState = None
        self.maxSuits = None
        self.numSuits = None
        self.lastAttackTime = None
        self.attackIval = None
        self.stopPosHprBroadcast()
        BaseNPCAI.delete(self)
        DistributedAvatarAI.delete(self)
        
    def Damage(self):
        if self.version == 3:
            self.canStun = False
            self.b_setHealth(0)
            return
            
        self.battleZone.tempEnts.makeExplosion(self.getPos() + (0, 0, 20.28), 2)
        self.changeSchedule(self.getScheduleByName("DAMAGE_REACT"))
        self.isStunned = False
        self.currStunDamage = 0
        self.version += 1
        self.getAttackIval()
        
    def canMove(self):
        return False
        
    def getSpawnIval(self):
        if self.version <= 2:
            self.spawnIval = random.uniform(4.0, 7.0)
        elif self.version == 3:
            self.spawnIval = random.uniform(3.0, 6.0)
        
    def getVersionSuitLevels(self):
        if self.version == 1:
            return [1, 5]
        elif self.version == 2:
            return [4, 8]
        elif self.version == 3:
            return [9, 12]
            
    def suitDie(self):
        self.numSuits -= 1
        
    def spawnDoorSuit(self, rearOrFront):
        
        import random
        
        if self.version == 1:
            suitOrGoon = 1
        elif self.version == 2:
            # 25% chance of goon on version 2
            suitOrGoon = random.randint(0, 3)
        elif self.version == 3:
            # 33% on version 3
            suitOrGoon = random.randint(0, 2)
        else:
            suitOrGoon = 1
        
        if suitOrGoon != 0:
            from src.coginvasion.cog.DistributedSuitAI import DistributedSuitAI
            from src.coginvasion.cog import Dept, SuitBank, Variant
            from src.coginvasion.attack.Attacks import ATTACK_BOMB, ATTACK_FIRED
            
            level, availableSuits = SuitBank.chooseLevelAndGetAvailableSuits(
                self.getVersionSuitLevels(), Dept.SALES, False)

            plan = random.choice(availableSuits)
            suit = VPSuitAI(self.air, self)
            if level >= 5:
                suit.attackIds.append(ATTACK_FIRED)
            if level >= 10:
                suit.attackIds.append(ATTACK_BOMB)
            suit.rearOrFront = rearOrFront
            suit.setNPCState(STATE_SCRIPT)
            suit.setPos(self.getPos())
            suit.setHpr(self.getHpr())
            suit.setBattleZone(self.dispatch)
            variant = Variant.NORMAL
            suit.setLevel(level)
            suit.setSuit(plan, variant)
            suit.generateWithRequired(self.dispatch.zoneId)
            suit.b_setPlace(self.dispatch.zoneId)
            suit.b_setName(plan.getName())
            suit.spawnGeneric()
            self.numSuits += 1
            suit.changeSchedule(suit.getScheduleByName("VP_EXIT"), False)
            
        else:
            goon = VPGoonAI(self.air, self)
            goon.rearOrFront = rearOrFront
            goon.setNPCState(STATE_IDLE)
            goon.setPos(self.getPos())
            goon.setHpr(self.getHpr())
            goon.setBattleZone(self.dispatch)
            goon.generateWithRequired(self.dispatch.zoneId)
            self.numSuits += 1
            goon.changeSchedule(goon.getScheduleByName("VP_EXIT"), False)
        
    def takeDamage(self, dmgInfo):
        # If we hit the top part of the VP...
        if (self.canStun) and (not self.isStunned) and (dmgInfo.hitNode == self.bodyNPs[1]):
            self.currStunDamage += dmgInfo.damageAmount
        
    def getViewOrigin(self):
        return self.getPos(render) + (0, 0, self.getHeight())
                           
    def onGearHit(self, contact, collider, intoNP):
        avNP = intoNP.getParent()
        currProj = collider.getPos(render)
        dmgInfo = TakeDamageInfo(self, -1,
                                 10,
                                 currProj, collider.getInitialPos())
    
        for obj in base.air.avatars[self.getBattleZone().zoneId]:
            if (CIGlobals.isAvatar(obj) and obj.getKey() == avNP.getKey()):

                obj.takeDamage(dmgInfo)
                break
                           
    def throwGearsAtTarget(self):
        if not self.target:
            return
        
        startPos = self.getPos(render) + (0, 0, 17)
        targetPos = self.target.entity.getViewOrigin()
        toTarget = (targetPos - startPos).normalized()
        endPos = CIGlobals.extrude(startPos, 100, toTarget)
        
        gear = GearAI(self.air)
        gear.setLinear(2.5, startPos,
                endPos, globalClockDelta.getFrameNetworkTime())
        gear.generateWithRequired(self.getBattleZone().zoneId)
        gear.addHitCallback(self.onGearHit)
        gear.addExclusion(self)
        
        self.emitSound(SOUND_COMBAT, self.getViewOrigin(), duration = 0.5)
        
    def emitJumpSound(self):
        self.emitSound(SOUND_VP_JUMP, self.getViewOrigin(), volume = 3)
        RulesAndResponsesAI.setGlobalRule("VPJumping")
        
    def doJump(self):
        
        self.emitSound(SOUND_COMBAT, self.getViewOrigin(), volume = 3.0)
        
        for av in self.air.avatars[self.getBattleZone().zoneId]:
            if self.battleZone.getGameRules().canDamage(self, av, None):
                result = False
                if av.doId == ModGlobals.LocalAvatarID:
                    # Check if on ground
                    result = PhysicsUtils.rayTestClosestNotMe(av, av.getPos() + (0, 0, 0.1), av.getPos() - (0, 0, 0.3),
                                                             CIGlobals.FloorGroup, self.battleZone.physicsWorld)
                else:
                    if av.getActivity()[0] != ACT_JUMP:
                        result = True
                        av.onHitByVPJump()
                if result:
                    # On ground, damage
                    dmgInfo = TakeDamageInfo(self, -1, 10, av.getPos(), self.getPos())
                    av.takeDamage(dmgInfo)
                    if av.doId == ModGlobals.LocalAvatarID:
                        av.sendUpdateToAvatarId(av.doId, 'doVPJumpCameraShake', [])
        
    def getYaw(self):
        return self.torsoYaw
        
    def setYaw(self, yaw):
        self.torsoYaw = yaw
        self.sendUpdate('updateAttachment',
            ["__Actor_torso", 0, 0, 0, self.torsoYaw,
             0, 0, globalClockDelta.getFrameNetworkTime()])
             
    def getAttackIval(self):
        if self.version == 1:
            self.attackIval = random.uniform(5.0, 10.0)
        elif self.version == 2:
            self.attackIval = random.uniform(3.5, 7.0)
        elif self.version == 3:
            self.attackIval = random.uniform(3.5, 6.0)
             
    def checkAttacks(self, distSqr):
        """
        Builds a list of usable attacks for a target entity.
        """

        self.clearConditions(COND_CAN_RANGE_ATTACK1|COND_CAN_RANGE_ATTACK2)
        
        now = globalClock.getFrameTime()
        if now - self.lastAttackTime >= self.attackIval:
            attack = random.random()
            if attack <= 0.7 and distSqr <= 50*50:
                # Throw gears
                self.setConditions(COND_CAN_RANGE_ATTACK1)
            else:
                # Jump
                self.setConditions(COND_CAN_RANGE_ATTACK2)
                
    def getEyePosition(self):
        return (0, 0, 20.28)
                
    def getSchedule(self):
        
        if self.npcState == STATE_NONE:
            return None

        elif self.npcState == STATE_IDLE:
            if self.hasConditions(COND_HEAR_SOMETHING):
                return self.getScheduleByName("ALERT_FACE")
            return self.getScheduleByName("IDLE_STAND")

        elif self.npcState == STATE_ALERT:
            if self.hasConditions(COND_HEAR_SOMETHING):
                return self.getScheduleByName("ALERT_FACE")
            return self.getScheduleByName("IDLE_STAND")

        elif self.npcState == STATE_COMBAT:
            if self.hasConditions(COND_TARGET_DEAD):
                self.clearTarget()
                if self.getTarget():
                    self.clearConditions(COND_TARGET_DEAD)
                    return self.getSchedule()
                else:
                    self.setNPCState(STATE_ALERT)
                    return self.getSchedule()
            if self.hasConditions(COND_NEW_TARGET) and not self.hasMemory(MEMORY_COMBAT_WAKE):
                return self.getScheduleByName("WAKE_ANGRY")
            elif not self.hasConditions(COND_SEE_TARGET):
                if not self.hasConditions(COND_TARGET_OCCLUDED):
                    return self.getScheduleByName("COMBAT_FACE")
            else:
                if self.hasConditions(COND_CAN_RANGE_ATTACK1) and self.isFacingIdeal():
                    self.lastAttackTime = globalClock.getFrameTime()
                    self.getAttackIval()
                    return self.getScheduleByName("RANGE_ATTACK1")
                elif self.hasConditions(COND_CAN_RANGE_ATTACK2):
                    self.lastAttackTime = globalClock.getFrameTime()
                    self.getAttackIval()
                    return self.getScheduleByName("RANGE_ATTACK2")
                elif not self.isFacingIdeal():
                    return self.getScheduleByName("COMBAT_FACE")

        elif self.npcState == STATE_DEAD:
            return self.getScheduleByName("DIE")


        return None
        
    def think(self):
        DistributedAvatarAI.think(self)
        
        dt = globalClock.getDt()
        
        if not self.isStunned and self.canStun:
            if self.currStunDamage >= self.StunDamage:
                self.changeSchedule(self.getScheduleByName("STUN"))
                self.currStunDamage = 0
            else:
                self.currStunDamage = max(0, self.currStunDamage - (self.StunDecayRate * dt))
                
        print self.currStunDamage
        
        now = globalClock.getFrameTime()
        if (now - self.lastSpawnTime >= self.spawnIval and
        not self.isDead() and self.numSuits < self.maxSuits and self.npcState != STATE_SCRIPT):
            rearOrFront = random.randint(0, 1)
            if rearOrFront == 0:
                ival = Sequence(Func(self.sendUpdate, 'openRearDoor'),
                                Func(self.spawnDoorSuit, rearOrFront),
                                Wait(4.0), Func(self.sendUpdate, 'closeRearDoor'))
            else:
                ival = Sequence(Func(self.sendUpdate, 'openFrontDoor'),
                                Func(self.spawnDoorSuit, rearOrFront),
                                Wait(4.0), Func(self.sendUpdate, 'closeFrontDoor'))
            ival.start()
            self.lastSpawnTime = now
            self.getSpawnIval()
            
    def makeIdealYawToPlayer(self):
        plyr = self.air.doId2do.get(ModGlobals.LocalAvatarID)
        self.makeIdealYaw(plyr.getPos())
            
    def setupPhysics(self, radius = None, height = None):
        from NPC_VPShared import makeVPPhysics
        bodyNode, upperNode = makeVPPhysics(True)
        
        BasePhysicsObjectAI.setupPhysics(self, bodyNode, True)
        self.attachPhysicsNode(upperNode, self.bodyNP)
        
    def announceGenerate(self):
        DistributedAvatarAI.announceGenerate(self)
        if self.cEntity:
            self.setPos(self.cEntity.getOrigin())
            self.setHpr(self.cEntity.getAngles())
        self.startPosHprBroadcast()
        self.enableThink()
        self.setNPCState(STATE_SCRIPT)
        self.startAI()
        self.changeSchedule(self.getScheduleByName("OPENING_SPEECH"), False)
