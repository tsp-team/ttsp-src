"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedPlayerToon.py
@author Maverick Liberty/Brian Lach
@date June 15, 2018

This is to get away from the legacy way of having all Toons in the game, including NPCs,
share the same code.

"""

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.interval.IntervalGlobal import Sequence, Wait, Func, SoundInterval
from direct.interval.IntervalGlobal import Parallel, LerpPosInterval, LerpQuatInterval, LerpHprInterval

from .DistributedPlayerToonShared import DistributedPlayerToonShared
from src.coginvasion.toon.DistributedToon import DistributedToon
from src.coginvasion.gags.backpack.Backpack import Backpack
from src.coginvasion.gags import GagGlobals
from src.coginvasion.globals import ChatGlobals
from src.coginvasion.phys import PhysicsUtils

class DistributedPlayerToon(DistributedToon, DistributedPlayerToonShared):
    notify = directNotify.newCategory('DistributedPlayerToon')

    def __init__(self, cr):
        try:
            self.DistributedPlayerToon_initialized
            return
        except:
            self.DistributedPlayerToon_initialized = 1
        DistributedToon.__init__(self, cr)
        DistributedPlayerToonShared.__init__(self)
        self.role = None
        self.ghost = 0
        self.puInventory = []
        self.equippedPU = -1
        self.backpack = Backpack(self)
        self.battleMeter = None

        # Quest-related variables.
        self.quests = ""
        self.tier = None
        self.questHistory = None

        self.busy = 1
        self.friends = None
        self.tutDone = 0
        self.hoodsDiscovered = []
        self.teleportAccess = []
        self.lastHood = 0
        self.defaultShard = 0
        self.tunnelTrack = None
        self.trackExperience = dict(GagGlobals.DefaultTrackExperiences)
        return

    def getHealth(self):
        return DistributedPlayerToonShared.getHealth(self)

    def getMaxHealth(self):
        return DistributedPlayerToonShared.getMaxHealth(self)

    def stopSmooth(self):
        DistributedToon.stopSmooth(self)
        localAvatarReachable = (hasattr(base, 'localAvatar') and base.localAvatar)
        if localAvatarReachable and self.doId != base.localAvatar.doId:
            self.resetTorsoRotation()

    def announceHealthAndPlaySound(self, level, hp, extraId = -1):
        DistributedToon.announceHealth(self, level, hp, extraId)
        hpSfx = base.audio3d.loadSfx('phase_11/audio/sfx/LB_toonup.ogg')
        base.audio3d.attachSoundToObject(hpSfx, self)
        SoundInterval(hpSfx, node = self).start()
        del hpSfx

    def setChat(self, chat):
        chat = ChatGlobals.filterChat(chat, self.animal)
        DistributedToon.setChat(self, chat)

    def goThroughTunnel(self, toZone, inOrOut, requestStatus = None):
        pass

    def setDefaultShard(self, shardId):
        self.defaultShard = shardId

    def getDefaultShard(self):
        return self.defaultShard

    def setLastHood(self, zoneId):
        self.lastHood = zoneId

    def b_setLastHood(self, zoneId):
        self.sendUpdate('setLastHood', [zoneId])
        self.setLastHood(zoneId)

    def getLastHood(self):
        return self.lastHood

    def setTeleportAccess(self, array):
        self.teleportAccess = array

    def getTeleportAccess(self):
        return self.teleportAccess

    def setHoodsDiscovered(self, array):
        self.hoodsDiscovered = array

    def b_setHoodsDiscovered(self, array):
        self.sendUpdate('setHoodsDiscovered', [array])
        self.setHoodsDiscovered(array)

    def getHoodsDiscovered(self):
        return self.hoodsDiscovered

    def setTutorialCompleted(self, value):
        self.tutDone = value

    def getTutorialCompleted(self):
        return self.tutDone

    def setFriendsList(self, friends):
        self.friends = friends

    def getFriendsList(self):
        return self.friends

    def setBusy(self, busy):
        self.busy = busy

    def getBusy(self):
        return self.busy

    def setTier(self, tier):
        self.tier = tier

    def getTier(self):
        return self.tier

    def setQuestHistory(self, array):
        self.questHistory = array

    def getQuestHistory(self):
        return self.questHistory

    def setQuests(self, dataStr):
        self.quests = dataStr

    def getQuests(self):
        return self.quests

    def d_createBattleMeter(self):
        self.sendUpdate('makeBattleMeter', [])

    def b_createBattleMeter(self):
        self.makeBattleMeter()
        self.d_createBattleMeter()

    def d_cleanupBattleMeter(self):
        self.sendUpdate('destroyBattleMeter', [])

    def b_cleanupBattleMeter(self):
        self.destroyBattleMeter()
        self.d_cleanupBattleMeter()

    def makeBattleMeter(self):
        if self.getHealth() < self.getMaxHealth():
            if not self.battleMeter:
                self.battleMeter = LaffOMeter()
                r, g, b, _ = self.getHeadColor()
                animal = self.getAnimal()
                maxHp = self.getMaxHealth()
                hp = self.getHealth()
                self.battleMeter.generate(r, g, b, animal, maxHP = maxHp, initialHP = hp)
                self.battleMeter.reparentTo(self)
                self.battleMeter.setZ(self.getHeight() + 5)
                self.battleMeter.setScale(0.5)
                self.battleMeter.start()

    def destroyBattleMeter(self):
        if self.battleMeter:
            self.battleMeter.stop()
            self.battleMeter.disable()
            self.battleMeter.delete()
            self.battleMeter = None

    def setEquippedPU(self, index):
        self.equippedPU = index

    def getEquippedPU(self):
        return self.equippedPU

    def setPUInventory(self, array):
        self.puInventory = array

    def getPUInventory(self):
        return self.puInventory

    def setGhost(self, value):
        self.ghost = value
        self.handleGhost(value)

    def d_setGhost(self, value):
        self.sendUpdate("setGhost", [value])

    def b_setGhost(self, value):
        self.d_setGhost(value)
        self.setGhost(value)

    def getGhost(self):
        return self.ghost

    def getBackpack(self):
        return self.backpack

    def setEquippedAttack(self, attackID):
        try:
            self.backpack.setCurrentGag(attackID)
        except:
            # If we couldn't do this, it means that the avatar was most likely disabled.
            pass
        DistributedToon.setEquippedAttack(self, attackID)

    def getCurrentGag(self):
        return self.getEquippedAttack()

    def setLoadout(self, gagIds):
        if self.backpack:
            loadout = []
            for i in range(len(gagIds)):
                gagId = gagIds[i]
                gag = self.backpack.getGagByID(gagId)
                if gag:
                    loadout.append(gag)
            self.backpack.setLoadout(loadout)

    def setBackpackAmmo(self, netString):
        if len(self.attackIds) != 0 or len(self.attacks) != 0:
            self.cleanupAttacks()
            self.clearAttackIds()
        return self.backpack.updateSuppliesFromNetString(netString)

    def getBackpackAmmo(self):
        if self.backpack:
            return self.backpack.netString
        return GagGlobals.getDefaultBackpack().toNetString()

    def setTrackExperience(self, netString):
        self.trackExperience = GagGlobals.getTrackExperienceFromNetString(netString)
        if GagGlobals.processTrackData(self.trackExperience, self.backpack) and self == base.localAvatar:
            if base.localAvatar.invGui:
                base.localAvatar.reloadInvGui()

    def getTrackExperience(self):
        return GagGlobals.trackExperienceToNetString(self.trackExperience)

    def updateAttackAmmo(self, gagId, ammo, maxAmmo, ammo2, maxAmmo2, clip, maxClip):
        if self.useBackpack():
            self.backpack.setSupply(gagId, ammo)
        else:
            DistributedToon.updateAttackAmmo(self, gagId, ammo, maxAmmo, ammo2, maxAmmo2, clip, maxClip)

    def setMoney(self, money):
        self.money = money

    def getMoney(self):
        return self.money

    def setAccessLevel(self, value):
        pass

    def getAccessLevel(self):
        return 0

    def disable(self):
        if self.tunnelTrack:
            self.ignore(self.tunnelTrack.getDoneEvent())
            self.tunnelTrack.finish()
            self.tunnelTrack = None
        self.role = None
        self.ghost = None
        self.puInventory = None
        self.equippedPU = None
        if self.backpack:
            self.backpack.cleanup()
            self.backpack = None
        self.firstTimeChangingHP = None
        self.quests = None
        self.tier = None
        self.questHistory = None
        self.busy = None
        self.friends = None
        self.tutDone = None
        self.hoodsDiscovered = None
        self.teleportAccess = None
        self.lastHood = None
        self.defaultShard = None
        self.trackExperience = None
        self.destroyBattleMeter()
        DistributedToon.disable(self)

    def delete(self):
        try:
            self.DistributedPlayerToon_deleted
        except:
            self.DistributedPlayerToon_deleted = 1
            DistributedPlayerToonShared.delete(self)

            del self.tunnelTrack
            del self.role
            del self.ghost
            del self.puInventory
            del self.equippedPU
            del self.backpack
            del self.quests
            del self.tier
            del self.questHistory
            del self.busy
            del self.friends
            del self.tutDone
            del self.hoodsDiscovered
            del self.teleportAccess
            del self.lastHood
            del self.defaultShard
            del self.trackExperience
            del self.battleMeter
            DistributedToon.delete(self)
        return
