from panda3d.core import Point3, TextNode

from direct.gui.DirectGui import OnscreenText
from direct.interval.IntervalGlobal import Sequence, LerpColorScaleInterval, LerpPosInterval, Parallel, Wait

from src.coginvasion.toon.DistributedToon import DistributedToon
from src.coginvasion.avatar.BaseLocalAvatar import BaseLocalAvatar
from src.coginvasion.globals import CIGlobals

from .MoneyGUI import MoneyGUI
from .WaveGUI import WaveGUI
from .WaveReportGUI import WaveReportGUI
from .ModPlayer import ModPlayer
from .ModLocalControls import ModLocalControls
from .CodeGUI import CodeGUI

class ModLocalAvatar(ModPlayer, BaseLocalAvatar):
    neverDisable = 1

    def __init__(self, cr):
        ModPlayer.__init__(self, cr)
        BaseLocalAvatar.__init__(self)
        self.moneyGui = MoneyGUI()
        self.waveGui = WaveGUI()
        self.waveReportGui = WaveReportGUI()
        self.codeGUI = CodeGUI()

    def handleDamage(self, x, y, z):
        BaseLocalAvatar.handleDamage(self, x, y, z)

    def getCodeNumbers(self):
        return []

    def setCodeNumbers(self, nums):
        self.codeGUI.numbers = nums
        self.codeGUI.updateText()

    def d_setView(self, x, y, z, h, p, r):
        self.sendUpdate('setView', [x, y, z, h, p, r])

    def getView(self):
        pos = camera.getPos(render)
        hpr = camera.getHpr(render)
        return [pos[0], pos[1], pos[2],
                hpr[0], hpr[1], hpr[2]]

    def think(self):
        pos = camera.getPos(render)
        hpr = camera.getHpr(render)
        self.d_setView(pos[0], pos[1], pos[2],
                       hpr[0], hpr[1], hpr[2])

    #def getEyePoint(self):
    #    return Point3(0, 0, 10)

    def setMoney(self, money):
        if self.moneyGui:
            self.moneyGui.update(money, self.getMoney())
        ModPlayer.setMoney(self, money)

    def setHealth(self, health):
        self.handleHealthChange(health, self.getHealth())
        ModPlayer.setHealth(self, health)

    def updateAttackAmmo(self, attackId, ammo, maxAmmo, ammo2, maxAmmo2, clip, maxClip):
        ModPlayer.updateAttackAmmo(self, attackId, ammo, maxAmmo, ammo2, maxAmmo2, clip, maxClip)
        BaseLocalAvatar.updateAttackAmmo(self, attackId, ammo, maxAmmo, ammo2, maxAmmo2, clip, maxClip)

    def setupAttacks(self):
        ModPlayer.setupAttacks(self)
        BaseLocalAvatar.setupAttacks(self)

    def setupNameTag(self, tempName = None):
        ModPlayer.setupNameTag(self, tempName)
        self.nametag.unmanage(base.marginManager)
        self.nametag.setActive(0)
        self.nametag.updateAll()

    def setMaxHealth(self, hp):
        DistributedToon.setMaxHealth(self, hp)
        self.laffMeter.updateMeterNewMax(hp)

    def handleHealthChange(self, hp, oldHp):
        BaseLocalAvatar.handleHealthChange(self, hp, oldHp)

        delta = hp - oldHp
        if delta == 0:
            return

        CIGlobals.makeDeltaTextEffect(delta, base.a2dBottomLeft, (0.07, 0, 0.1))

    def primaryFirePress(self):
        if not self.canUseGag():
            return

        ModPlayer.primaryFirePress(self)

    def primaryFireRelease(self):
        if not self.canUseGag():
            return

        ModPlayer.primaryFireRelease(self)

    def secondaryFirePress(self):
        if not self.canUseGag():
            return

        ModPlayer.secondaryFirePress(self)

    def secondaryFireRelease(self):
        if not self.canUseGag():
            return

        ModPlayer.secondaryFireRelease(self)

    def setEquippedAttack(self, gagId):
        ModPlayer.setEquippedAttack(self, gagId)
        BaseLocalAvatar.setEquippedAttack(self, gagId)

    def doVPJumpCameraShake(self):
        from direct.interval.IntervalGlobal import Sequence, Wait, Func
        Sequence(Func(base.cam.setZ, base.cam, 1), Wait(0.15), Func(base.cam.setZ, base.cam, -2), Wait(0.15), Func(base.cam.setZ, base.cam, 1)).start()

    def announceGenerate(self):
        ModPlayer.announceGenerate(self)
        self.setupCamera()
        self.setupControls()
        self.createInvGui()

        #self.moneyGui.createGui()
        #self.moneyGui.update(self.getMoney())

    def disable(self):
        self.stopPlay()
        #self.moneyGui.deleteGui()
        #self.moneyGui = None
        self.destroyControls()
        self.destroyInvGui()
        self.detachCamera()
        if self.smartCamera:
            self.smartCamera.stopUpdateSmartCamera()
            self.smartCamera.deleteSmartCameraCollisions()
            self.smartCamera = None
        ModPlayer.disable(self)

    def setupControls(self):
        self.walkControls = ModLocalControls()
        self.walkControls.setupControls()
        self.walkControls.setMode(ModLocalControls.MThirdPerson)
