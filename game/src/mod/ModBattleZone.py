from src.coginvasion.battle.DistributedBattleZone import DistributedBattleZone

from src.mod.Jukebox import Jukebox
from src.mod.ModRules import ModRules

from collections import OrderedDict

class ModBattleZone(DistributedBattleZone):

    MapFormatString = "resources/maps/{0}.bsp"

    def doPrecacheMap(self):
        if base.config.GetBool('precache-assets', False):
            base.transitions.noTransitions()
            camera.setY(-10)
            base.precacheStuff()

    def __init__(self, cr):
        DistributedBattleZone.__init__(self, cr)
        self.jukebox = Jukebox()
        self.waveNum = 0

        self.waveStats = OrderedDict()

    def updateWaveStats(self, damageDealt, damageTaken, cogsDestroyed,
                        moneyCollected, time):

        minutes = int(time) / 60
        seconds = int(time) % 60
        timeStr = "{0} Minute".format(minutes)
        if minutes != 1:
            timeStr += "s"
        timeStr += " {0} Seconds".format(seconds)

        self.waveStats = OrderedDict([("Time", timeStr),
                                      ("Damage Dealt", damageDealt),
                                      ("Damage Taken", damageTaken),
                                      ("Cogs Destroyed", cogsDestroyed),
                                      ("Jellybeans Collected", moneyCollected)])

    def updateGameStats(self, damageDealt, damageTaken, cogsDestroyed,
                        moneyCollected, time, waves):
        pass

    def d_loadedMap(self):
        DistributedBattleZone.d_loadedMap(self)

        #self.jukebox.shuffle()
        #self.jukebox.play()

    def beginWave(self, waveNum, suits):
        self.jukebox.shuffle()
        self.jukebox.play()
        base.localAvatar.waveGui.adjustForWave(waveNum, suits)
        base.localAvatar.waveGui.doShow()
        self.waveNum = waveNum

    def incWaveProgress(self):
        base.localAvatar.waveGui.incProgress()

    def endWave(self):
        self.jukebox.fadeOut()
        base.localAvatar.waveGui.doHide()
        base.localAvatar.waveReportGui.showReport(self.waveNum, self.waveStats)

    def d_shutdown(self):
        print("sending shutdown")
        self.sendUpdate('shutdown')

    def makeGameRules(self):
        return ModRules(self)

    def lose(self, youDied):
        base.lose()
        if youDied:
            base.localAvatar.b_setAnimState('died')
            base.localAvatar.stopPlay()
            base.localAvatar.doFirstPersonCameraTransition()

    def respawn(self):
        self.gameRules.onPlayerRespawn()
