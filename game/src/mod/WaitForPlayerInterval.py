from direct.interval.IntervalGlobal import Interval
from src.mod import ModGlobals
from panda3d.direct import CInterval

class WaitForPlayerInterval(Interval):

    def __init__(self, me, distance = 5.0):
        Interval.__init__(self, 'waitForPlayerIval', 999999, False)

        self.distance = distance
        self.me = me
        self.player = base.air.doId2do.get(ModGlobals.LocalAvatarID)

    def privStep(self, t):
        Interval.privStep(self, t)
        print("privStep:", t)
        if self.me.getDistance(self.player) <= self.distance:
            print("Close enough!")
            self.state = CInterval.SFinal
            self.finish()
            self.intervalDone()
        else:
            print("Too far!")
