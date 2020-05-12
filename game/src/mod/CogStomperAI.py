from panda3d.core import Vec3, NodePath, TransformState
from panda3d.bullet import BulletGhostNode, BulletBoxShape

from direct.interval.IntervalGlobal import Sequence, LerpPosInterval

from src.coginvasion.szboss.DistributedEntityAI import DistributedEntityAI
from src.coginvasion.globals import CIGlobals
from src.coginvasion.attack.TakeDamageInfo import TakeDamageInfo
from src.coginvasion.phys import PhysicsUtils
from src.coginvasion.attack.DamageTypes import DMG_FORCE

class CogStomperAI(DistributedEntityAI):
    StateStomp  = 0
    StateRaise  = 1
    StateUp     = 2
    StateDown   = 3
    
    def __init__(self, air, dispatch):
        DistributedEntityAI.__init__(self, air, dispatch)
        self.height = 1.0
        self.stompSpeed = 1
        self.raiseSpeed = 1
        self.timeOnGround = 0.0
        self.timeInAir = 0.0
        self.damage = 20
        self.scale = Vec3(1)
        self.floorColl = None
        self.damaged = []
        self.moveDir = Vec3.up()
        self.stomped = False
        self.startDelay = 0.0
        
    def getData(self):
        return [self.height, self.stompSpeed, self.raiseSpeed, [self.scale[0], self.scale[1], self.scale[2]]]
    
    def loadEntityValues(self):
        self.height = self.getEntityValueFloat("height")
        self.stompSpeed = self.getEntityValueFloat("stompSpeed")
        self.raiseSpeed = self.getEntityValueFloat("raiseSpeed")
        self.timeOnGround = self.getEntityValueFloat("timeOnGround")
        self.timeInAir = self.getEntityValueFloat("timeInAir")
        self.damage = self.getEntityValueInt("damage")
        self.scale = self.getEntityValueVector("scale")
        self.startDelay = self.getEntityValueFloat("startDelay")
        
    def Stomp(self):
        self.b_setEntityState(self.StateStomp)
        
    def Raise(self):
        self.b_setEntityState(self.StateRaise)
        
    def load(self):
        DistributedEntityAI.load(self)
        self.setHpr(self.cEntity.getAngles())
        self.setPos(self.cEntity.getOrigin())

        self.setModel("phase_9/models/cogHQ/square_stomper.bam")
        self.setModelScale(self.scale)
        self.getModelNP().find("**/shaft").setSy(self.height / 16.0)
        
        self.optimizeModel()
        
        box = BulletBoxShape((self.scale[1], 1.0, self.scale[0]))
        gh = BulletGhostNode('trigger_hurt')
        gh.addShape(box, TransformState.makePos((0, -0.5, 0)))
        self.floorColl = self.getModelNP().attachNewNode(gh)
        self.floorColl.setCollideMask(CIGlobals.WallGroup|CIGlobals.CharacterGroup)
        
        self.enableModelCollisions()

        for bNP in self.getModelNP().findAllMatches("**/+BulletRigidBodyNode"):
            bNP.setSurfaceProp("metal")
            
        self.b_setEntityState(self.StateUp)
        
    def getUpPosition(self):
        up = Vec3(self.height / 16.0)
        up.componentwiseMult(self.moveDir)
        return up
        
    def setEntityState(self, state):
        DistributedEntityAI.setEntityState(self, state)

        if state == self.StateDown:
            self.stomped = False
            self.clearSequence()
            self.setPos(self.cEntity.getOrigin())
            self.dispatchOutput("OnStomp")
            
        elif state == self.StateUp:
            self.clearSequence()
            self.setPos(self.cEntity.getOrigin() + self.getUpPosition())
            self.dispatchOutput("OnRaise")
            
        elif state == self.StateStomp:
            self.damaged = []
            self.setSequence(
                LerpPosInterval(self, self.height / self.stompSpeed, self.cEntity.getOrigin(),
                                self.cEntity.getOrigin() + self.getUpPosition())
            )

        elif state == self.StateRaise:
            self.setSequence(
                LerpPosInterval(self, self.height / self.raiseSpeed,
                                self.cEntity.getOrigin() + self.getUpPosition(),
                                self.cEntity.getOrigin())
            )
        
    def think(self):
        elapsed = self.getEntityStateElapsed()
        state = self.getEntityState()
        
        if state == self.StateUp:
            if self.timeInAir >= 0 and elapsed >= (self.timeInAir + self.startDelay):
                self.b_setEntityState(self.StateStomp)
                
        elif state == self.StateDown:
            if self.timeOnGround >= 0 and elapsed >= self.timeOnGround:
                self.b_setEntityState(self.StateRaise)
                
            if not self.stomped:
                self.stomped = True
                
                result = self.dispatch.getPhysicsWorld().contactTest(self.floorColl.node())
                for contact in result.getContacts():
                    node = contact.getNode1()
                    if node == self.floorColl.node():
                        node = contact.getNode0()
                    if node.isOfType(BulletGhostNode.getClassType()):
                        continue
                    avNP = NodePath(node).getParent()
                    for obj in self.air.avatars[self.dispatch.zoneId]:
                        if (CIGlobals.isAvatar(obj) and obj.getKey() == avNP.getKey() and
                            obj not in self.damaged):

                            if self.damage != -1:
                                obj.takeDamage(TakeDamageInfo(self, damageAmount = self.damage, damageType = DMG_FORCE))
                            else:
                                obj.takeDamage(TakeDamageInfo(self, damageAmount = obj.getHealth(), damageType = DMG_FORCE))
                                
                            self.damaged.append(obj)
                            
                            break
                
                
        elif state == self.StateStomp:
            self.startDelay = 0.0
            if elapsed >= self.height / self.stompSpeed:
                self.b_setEntityState(self.StateDown)
                
        elif state == self.StateRaise:
            if elapsed >= self.height / self.raiseSpeed:
                self.b_setEntityState(self.StateUp)
                
    def unload(self):
        self.dispatch.getPhysicsWorld().remove(self.floorColl.node())
        self.damaged = None
        self.height = None
        self.stompSpeed = None
        self.raiseSpeed = None
        self.timeOnGround = None
        self.timeInAir = None
        self.damage = None
        self.startDelay = None
        DistributedEntityAI.unload(self)
