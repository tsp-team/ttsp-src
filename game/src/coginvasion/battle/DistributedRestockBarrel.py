"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedRestockBarrel.py
@author Maverick Liberty
@date February 28, 2016

"""

from panda3d.core import NodePath, TransformState, Point3
from panda3d.bullet import BulletRigidBodyNode, BulletCylinderShape, ZUp

from direct.distributed.DistributedNode import DistributedNode
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import Sequence, LerpScaleInterval, Func

from src.coginvasion.szboss.DistributedEntity import DistributedEntity
from src.coginvasion.globals.CIGlobals import WallGroup, SPRender
from src.coginvasion.gags import GagGlobals

class DistributedRestockBarrel(DistributedEntity, DistributedNode):
    notify = directNotify.newCategory('DistributedRestockBarrel')
    
    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        DistributedNode.__init__(self, cr)
        NodePath.__init__(self, 'restock_barrel')
        self.grabSfx = None
        self.rejectSfx = None
        self.grabSoundPath = 'phase_4/audio/sfx/SZ_DD_treasure.ogg'
        self.rejectSoundPath = 'phase_4/audio/sfx/ring_miss.ogg'
        self.animTrack = None
        self.barrelScale = 0.5
        self.radius = 1.5
        self.height = 4.275
        self.playSoundForRemoteToons = 1
        self.barrel = None
        self.gagNode = None
        self.gagModel = None
        
        # Collision nodes
        self.collSphere = None
        self.collNode = None
        self.collNodePath = None
        
    def load(self):
        DistributedEntity.load(self)
        self.setPos(self.cEntity.getOrigin())
        self.setHpr(self.cEntity.getAngles())
        
    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        DistributedNode.announceGenerate(self)
        self.build()
        
        # Build collisions
        self.collSphere = BulletCylinderShape(self.radius, self.height, ZUp)
        self.collNode = BulletRigidBodyNode(self.uniqueName('barrelSphere'))
        self.collNode.setKinematic(True)
        self.collNode.addShape(self.collSphere, TransformState.makePos(Point3(0, 0, self.height / 2)))
        self.collNode.setIntoCollideMask(WallGroup)
        self.collNodePath = self.attachNewNode(self.collNode)
        base.physicsWorld.attach(self.collNodePath.node())
        self.accept('enter' + self.collNodePath.getName(), self.__handleCollision)
        
        self.reparentTo(render)
        
    def disable(self):
        DistributedEntity.disable(self)
        DistributedNode.disable(self)
        self.ignoreAll()
        
        if self.animTrack:
            self.animTrack.pause()
            self.animTrack = None
        return
    
    def delete(self):
        self.gagNode.removeNode()
        self.barrel.removeNode()
        base.physicsWorld.remove(self.collNode)
        self.collNodePath.removeNode()
        del self.barrel
        del self.gagNode
        del self.grabSfx
        del self.rejectSfx
        del self.grabSoundPath
        del self.rejectSoundPath
        del self.animTrack
        del self.barrelScale
        del self.radius
        del self.height
        del self.playSoundForRemoteToons
        del self.gagModel
        del self.collNode
        del self.collNodePath
        del self.collSphere
        DistributedNode.delete(self)
        DistributedEntity.delete(self)
        
    def setLabel(self, labelId):
        if labelId == 0:
            self.gagModel = loader.loadModel('phase_4/models/props/icecream.bam')
            self.gagModel.reparentTo(self.gagNode)
            self.gagModel.find('**/p1_2').clearBillboard()
            self.gagModel.setScale(0.6)
            self.gagModel.setPos(0, -0.1, -0.1 - 0.6)
        elif labelId == 1:
            purchaseModels = loader.loadModel('phase_4/models/gui/purchase_gui.bam')
            self.gagModel = purchaseModels.find('**/Jar')
            self.gagModel.reparentTo(self.gagNode)
            self.gagModel.setScale(3.0)
            self.gagModel.setPos(0, -0.1, 0)
            purchaseModels.removeNode()
        elif labelId < 1000:
            gagId = labelId - 2
            iconName = GagGlobals.InventoryIconByName.get(self.cr.attackMgr.getAttackName(gagId))
            invModel = loader.loadModel('phase_3.5/models/gui/inventory_icons.bam').find('**/%s' % iconName)
            if invModel:
                self.gagModel = invModel
                self.gagModel.reparentTo(self.gagNode)
                self.gagModel.setScale(13.0)
                self.gagModel.setPos(0, -0.1, 0)
            else:
                self.notify.warning('Failed to find gag label %s.' % (str(labelId)))
        else:
            modelPath = 'phase_4/models/props/icecream.bam'
            
            self.gagModel = loader.loadModel(modelPath)
            self.gagModel.reparentTo(self.gagNode)
            self.gagModel.find('**/p1_2').clearBillboard()
            self.gagModel.setScale(0.6)
            self.gagModel.setPos(0, -0.1, -0.7)
        
    def __handleCollision(self, _ = None):
        self.sendUpdate('requestGrab', [])
        
    def setGrab(self, avId):
        local = (avId == base.localAvatar.getDoId())
        if local:
            self.ignore(self.uniqueName('enterbarrelSphere'))
            self.barrel.setColorScale(0.5, 0.5, 0.5, 1)
        if self.playSoundForRemoteToons or local:
            base.playSfx(self.grabSfx)
        if self.animTrack:
            self.animTrack.finish()
            self.animTrack = None
        self.animTrack = Sequence(
            LerpScaleInterval(self.barrel, 0.2, 1.1 * self.barrelScale, blendType='easeInOut'), 
            LerpScaleInterval(self.barrel, 0.2, self.barrelScale, blendType='easeInOut'), 
            Func(self.reset), 
        name=self.uniqueName('animTrack'))
        self.animTrack.start()
        
    def setReject(self):
        base.playSfx(self.rejectSfx)
        self.notify.warning('Pickup rejected.')
        
    def build(self):
        self.grabSfx = base.audio3d.loadSfx(self.grabSoundPath)
        self.rejectSfx = base.audio3d.loadSfx(self.rejectSoundPath)
        base.audio3d.attachSoundToObject(self.grabSfx, self)
        base.audio3d.attachSoundToObject(self.rejectSfx, self)
        self.barrel = loader.loadModel('phase_4/models/cogHQ/gagTank.bam')
        self.barrel.setScale(self.barrelScale)
        self.barrel.reparentTo(self)
        self.barrel.setH(180)
        
        # Set the label background color.
        lblBg = self.barrel.find('**/gagLabelDCS')
        lblBg.setColor(0.15, 0.15, 0.1)
        
        self.gagNode = self.barrel.attachNewNode('gagNode')
        self.gagNode.setPosHpr(0.0, -2.62, 4.0, 0, 0, 0)
        self.gagNode.setColorScale(0.7, 0.7, 0.6, 1)
        
    def reset(self):
        self.barrel.setScale(self.barrelScale)
        self.accept(self.uniqueName('enterbarrelSphere'), self.__handleCollision)
        
