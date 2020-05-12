from src.coginvasion.szboss.DistributedEntity import DistributedEntity
from src.coginvasion.szboss.UseableObject import UseableObject
from src.coginvasion.phys import PhysicsUtils
from src.coginvasion.globals import CIGlobals

from panda3d.core import TextNode, Vec3
from libpandabsp import LightingOriginEffect

class KeypadButton(UseableObject):

    def __init__(self, keypad, btn):
        self.keypad = keypad
        self.num = int(btn.getName()[8:])
        UseableObject.__init__(self, False)
        self.setupPhysics(btn)
        self.reparentTo(keypad.getModelNP())
        
    def setupPhysics(self, btn):
        btn.detachNode()
        bodyNode = btn.node()
        UseableObject.setupPhysics(self, bodyNode, True)
        self.stopWaterCheck()
        self.load()
        
    def startUse(self):
        self.keypad.handlePressButton(self.num)
        
    def cleanup(self):
        self.removeNode()
        self.keypad = None
        self.num = None

class Keypad(DistributedEntity):

    def __init__(self, cr):
        DistributedEntity.__init__(self, cr)
        self.buttons = []
        self.text = TextNode("keypad-text")
        self.text.setFont(loader.loadFont("models/fonts/DS-DIGI.TTF"))
        self.text.setTextColor((0, 0, 0, 1))
        self.text.setAlign(TextNode.ACenter)
        self.textNP = None
        
    def clearTextNP(self):
        if self.textNP:
            self.textNP.removeNode()
        self.textNP = None
        
    def setNumbers(self, nums):
        self.clearTextNP()
        lcdWidth = 1.178
        textStr = ""
        for i in range(len(nums)):
            textStr += str(nums[i])
        self.text.setText(textStr)
        self.textNP = self.getModelNP().attachNewNode(self.text.generate())
        self.textNP.setZ(0.44)
        self.textNP.setY(0.21395 * 0.5)
        self.textNP.setH(180)
        self.textNP.hide(CIGlobals.ShadowCameraBitmask)
        self.textNP.setDepthOffset(1, 1)
        mins = Vec3()
        maxs = Vec3()
        self.textNP.calcTightBounds(mins, maxs)
        width = maxs[0] - mins[0]
        scale = min(1.0, lcdWidth / max(width, 0.001))
        self.textNP.setScale(scale * 0.225)
        
    def handlePressButton(self, num):
        self.sendUpdate('pressButton', [num])
        
    def announceGenerate(self):
        DistributedEntity.announceGenerate(self)
        
        self.addSound("press", "sound/buttons/blip1.wav")
        self.addSound("denied", "sound/buttons/button2.wav")
        self.addSound("access", "sound/buttons/button3.wav")
        
        PhysicsUtils.makeBulletCollFromPandaColl(self.getModelNP())
        for np in self.getModelNP().findAllMatches("**/trigger_*"):
            btn = KeypadButton(self, np)
            self.buttons.append(btn)
            
        self.setEffect(LightingOriginEffect.make((0, 0.1, 0)))
            
        #self.getModelNP().setScale(0.5)
            
    def disable(self):
        for btn in self.buttons:
            btn.cleanup()
        self.buttons = None
        self.clearTextNP()
        DistributedEntity.disable(self)
