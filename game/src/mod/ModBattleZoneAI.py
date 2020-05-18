from src.coginvasion.battle.DistributedBattleZoneAI import DistributedBattleZoneAI

from src.mod import ModGlobals
from src.mod.ModRulesAI import ModRulesAI

import random

class ModBattleZoneAI(DistributedBattleZoneAI):

    MapFormatString = "resources/maps/{0}.bsp"

    WavesLevel = "waves"

    def __init__(self, air):
        DistributedBattleZoneAI.__init__(self, air)
        self.lost = False

        self.batchSpawn = None

        self.waveNum = 0
        self.waveSuitsRemaining = 0
        self.waveStartTime = 0.0
        self.waveStats = {0:{}}
        self.stats = {}

        self.levelPrefix = ""

        self.numberDropped = False
        self.codeWasUsed = False
        self.numberPickUpTime = 0.0
        self.getNumberIval()

        self.numberIdx = 0
        self.numbers = [[1, 5, 9, 3], [2, 9, 4, 1],
                        [3, 0, 1, 0], [4, 8, 9, 2]]

    def getNumberIval(self):
        self.numberIval = random.uniform(30, 60)

    def codeUsed(self):
        plyr = self.air.doId2do.get(ModGlobals.LocalAvatarID)
        plyr.clearCodeNumbers()
        self.numberIdx += 1

    def wasFullCodeFound(self):
        if self.numberIdx > 2:
            return True
        return len(self.numbers[self.numberIdx]) == 0

    def numberWasPickedUp(self):
        self.numberDropped = False
        self.numberPickUpTime = globalClock.getFrameTime()
        del self.numbers[self.numberIdx][0]
        self.getNumberIval()

    def dropNumber(self, pos):
        if not self.hasNumberToDrop():
            return

        self.numberDropped = True
        num = self.numbers[self.numberIdx][0]

        from src.mod.CodeNumberPickupAI import CodeNumberPickupAI
        p = CodeNumberPickupAI(self.air, self)
        p.number = num
        p.setPos(pos)
        p.generateWithRequired(self.zoneId)

    def hasNumberToDrop(self):
        now = globalClock.getFrameTime()
        delta = now - self.numberPickUpTime
        return self.numberIdx <= 2 and not self.numberDropped and delta >= self.numberIval and not self.wasFullCodeFound()

    def isLevelType(self, lprefix):
        return self.levelPrefix == lprefix

    def loadBSPLevel(self, lfile, transition = False):
        from panda3d.core import Filename
        self.levelPrefix = Filename.fromOsSpecific(lfile).getBasenameWoExtension().split('_')[0].lower()
        DistributedBattleZoneAI.loadBSPLevel(self, lfile, transition)

        if self.isLevelType(self.WavesLevel):
            spawns = self.bspLoader.findAllEntities("batch_cog_spawner")
            if len(spawns) > 0:
                self.batchSpawn = spawns[0]

    def setWaveStat(self, key, value):
        self.waveStats[self.waveNum][key] = value

    def getWaveStat(self, key):
        return self.waveStats[self.waveNum].get(key, 0)

    def incWaveStat(self, key, value):
        self.setWaveStat(key, self.getWaveStat(key) + value)

    def playerCollectMoney(self, amount, avId):
        self.incWaveStat('moneyCollected', amount)

    def playerDealDamage(self, dmg, avId):
        self.incWaveStat('damageDealt', dmg)

    def playerTakeDamage(self, dmg, avId):
        self.incWaveStat('damageTaken', dmg)

    def beginWaveLater(self, wavenum, delay = 10.0):
        taskMgr.doMethodLater(delay, self.beginWave, "beginWave", [wavenum], appendTask = False)

    def getMaxHealthForWave(self, wavenum):
        return min(137, wavenum * 15)

    def beginWave(self, wavenum):
        self.waveNum = wavenum
        self.waveSuitsRemaining = self.getMaxSuitsForWave(wavenum)
        self.waveStartTime = globalClock.getFrameTime()

        localAv = self.getAvatarInstance(ModGlobals.LocalAvatarID).avatar
        localAv.b_setMaxHealth(self.getMaxHealthForWave(wavenum))

        self.waveStats[self.waveNum] = {}

        from src.coginvasion.arcade.BatchCogSpawnerAI import BatchCogSpawnerAI
        BatchCogSpawnerAI.MaxSuits = self.waveSuitsRemaining
        BatchCogSpawnerAI.NumSuits = 0

        assert self.batchSpawn
        self.batchSpawn.ivalMin /= wavenum
        self.batchSpawn.ivalMin = max(1.0, self.batchSpawn.ivalMin)
        self.batchSpawn.ivalMax /= wavenum
        self.batchSpawn.ivalMax = max(1.0, self.batchSpawn.ivalMax)
        self.batchSpawn.Start()

        self.sendUpdate('beginWave', [wavenum, self.waveSuitsRemaining])

    def endWave(self):
        assert self.batchSpawn
        self.batchSpawn.Stop()

        now = globalClock.getFrameTime()
        self.setWaveStat('time', now - self.waveStartTime)

        self.stats['waves'] = self.stats.get('waves', 0) + 1
        # Add wave stats onto game stats
        for key, value in self.waveStats[self.waveNum].items():
            self.stats[key] = self.stats.get(key, 0) + value

        print("Wave stats:", self.waveStats[self.waveNum])
        print("Game stats:", self.stats)

        self.sendUpdate('updateWaveStats', [self.getWaveStat('damageDealt'),
                                            self.getWaveStat('damageTaken'),
                                            self.getWaveStat('cogsDestroyed'),
                                            self.getWaveStat('moneyCollected'),
                                            self.getWaveStat('time')])

        self.sendUpdate('updateGameStats', [self.stats.get('damageDealt', 0),
                                            self.stats.get('damageTaken', 0),
                                            self.stats.get('cogsDestroyed', 0),
                                            self.stats.get('moneyCollected', 0),
                                            self.stats.get('time', 0),
                                            self.stats.get('waves', 0)])
        self.sendUpdate('endWave')

        self.beginWaveLater(self.waveNum + 1)

    def getWaveNum(self):
        return self.waveNum

    def getMaxSuitsForWave(self, wavenum):
        return wavenum * 10

    def deadSuit(self, suitId):
        suit = self.air.doId2do.get(suitId)
        self.dropNumber(suit.getPos())
        #jbPos = suit.getPos(render)
        #jb = self.air.createObjectByName("JellybeanPickupAI")
        #jb.setPos(jbPos + (0, 0, 0.5))
        #jb.generateWithRequired(self.zoneId)

    def suitHPAtZero(self, suitId):
        if self.isLevelType(self.WavesLevel):
            self.waveSuitsRemaining -= 1
            self.sendUpdate('incWaveProgress')
            self.incWaveStat('cogsDestroyed', 1)
            if self.waveSuitsRemaining == 0:
                self.endWave()

    def delete(self):
        print("BZone delete")
        self.lost = None
        DistributedBattleZoneAI.delete(self)

    def shutdown(self):
        """Called from client when they are leaving the game, time to shutdown."""
        print("Shutdown!")
        self.air.shutdown()

    def handleAvatarLeave(self, avatar, reason):
        DistributedBattleZoneAI.handleAvatarLeave(self, avatar, reason)

        if hasattr(self, 'watchingAvatarIds') and len(self.watchingAvatarIds) == 0:
            self.requestDelete()
            self.air.shutdown()

    def generate(self):
        DistributedBattleZoneAI.generate(self)

        from src.coginvasion.deathmatch.DistributedGagPickupAI import DistributedGagPickupAI
        from src.coginvasion.szboss.InfoBgm import InfoBgm
        from src.coginvasion.szboss.DistributedSZBossToonAI import DistributedSZBossToonAI
        from src.coginvasion.szboss.DistributedSZBossSuitAI import DistributedSZBossSuitAI
        from src.coginvasion.szboss.ScriptedSequenceAI import ScriptedSequenceAI
        from src.coginvasion.szboss.ScriptedSpeechAI import ScriptedSpeechAI
        from src.coginvasion.szboss.goon.NPC_GoonAI import NPC_GoonAI
        from src.coginvasion.cogoffice.AIEntities import SuitSpawn
        from src.coginvasion.battle.DistributedHPBarrelAI import DistributedHPBarrelAI
        from src.coginvasion.arcade.BatchCogSpawnerAI import BatchCogSpawnerAI
        from src.mod.CogStomperAI import CogStomperAI
        from src.mod.CogCageAI import CogCageAI
        from src.mod.NPC_VPAI import NPC_VPAI
        from src.mod.KeypadAI import KeypadAI
        from src.mod.LaffBarrelAI import LaffBarrelAI
        self.bspLoader.linkServerEntityToClass("gag_pickup", DistributedGagPickupAI)
        self.bspLoader.linkServerEntityToClass("npc_toon", DistributedSZBossToonAI)
        self.bspLoader.linkServerEntityToClass("npc_suit", DistributedSZBossSuitAI)
        self.bspLoader.linkServerEntityToClass("scripted_sequence", ScriptedSequenceAI)
        self.bspLoader.linkServerEntityToClass("scripted_speech", ScriptedSpeechAI)
        self.bspLoader.linkServerEntityToClass("cogoffice_suitspawn", SuitSpawn)
        self.bspLoader.linkServerEntityToClass("batch_cog_spawner", BatchCogSpawnerAI)
        self.bspLoader.linkServerEntityToClass("item_laffbarrel", DistributedHPBarrelAI)
        self.bspLoader.linkServerEntityToClass("cog_stomper", CogStomperAI)
        self.bspLoader.linkServerEntityToClass("cog_cage", CogCageAI)
        self.bspLoader.linkServerEntityToClass("npc_goon", NPC_GoonAI)
        self.bspLoader.linkServerEntityToClass("npc_vp", NPC_VPAI)
        self.bspLoader.linkServerEntityToClass("item_keypad", KeypadAI)
        self.bspLoader.linkServerEntityToClass("mod_item_laffbarrel", LaffBarrelAI)

    def update(self):
        if not self.lost and ("facility" in self.map or self.map == "test_vp"):
            flippy = self.bspLoader.getPyEntityByTargetName("flippy")
            localAv = self.getAvatarInstance(ModGlobals.LocalAvatarID).avatar
            if (flippy and flippy.died) or (localAv.isDead()):
                print("Player loses")
                self.sendUpdate('lose', [int(localAv.isDead())])
                self.lost = True

    def makeGameRules(self):
        return ModRulesAI(self)

    def loadedMap(self):
        DistributedBattleZoneAI.loadedMap(self)

        print("Loaded map from client!!!!")

        if not self.mapWasTransitionedTo:
            avId = self.air.getAvatarIdFromSender()
            inst = self.getAvatarInstance(avId)
            if inst:
                self.gameRules.respawnPlayer(inst.avatar)

                if self.batchSpawn and self.isLevelType(self.WavesLevel):
                    self.beginWaveLater(1)

        if self.map == "facility_battle_v2":
            self.numbers = []
            keypads = self.bspLoader.findAllEntities("item_keypad")
            keypads.sort(key = lambda keypad: keypad.getCEntity().getTargetname())
            for i in range(len(keypads)):
                keypad = keypads[i]
                self.numbers.append(list(keypad.code))
            print self.numbers

    def addAvatar(self, avId, andUpdateAvatars = 0):
        DistributedBattleZoneAI.addAvatar(self, avId, andUpdateAvatars)

        # yikes
        #
        # This makes the local avatar be correctly registered under the
        # battle zone since there is a dependency-cycle between them.
        av = self.air.doId2do.get(avId)
        if av:
            self.air.removeAvatar(av)
            self.air.addAvatar(av)
