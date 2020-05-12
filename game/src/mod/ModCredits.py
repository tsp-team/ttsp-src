from panda3d.core import VirtualFileSystem, TextNode, Vec3
from direct.gui.DirectGui import OnscreenText, DGG
from direct.interval.IntervalGlobal import Sequence, LerpPosInterval, Func, Wait
from direct.showbase.DirectObject import DirectObject

class ModCredits(DirectObject):

    def __init__(self, menu):
        base.transitions.fadeScreen(1.0)
        vfs = VirtualFileSystem.getGlobalPtr()
        creditsTextStr = vfs.readFile("scripts/credits.txt", True)
        self.creditsText = OnscreenText(text = creditsTextStr,
            fg = (1, 1, 1, 1), align = TextNode.ACenter, mayChange = False, scale = 0.06)
        self.creditsText.reparentTo(aspect2d, DGG.FADE_SORT_INDEX + 1)
        self.creditsText.setZ(-1)
        self.ival = Sequence(LerpPosInterval(self.creditsText, 20.0, (0, 0, 2.6), (0, 0, -1.0)), Func(self.done))
        self.ival.start()
        self.acceptOnce('space', self.done)
        self.menu = menu
        
    def done(self):
        self.creditsText.destroy()
        self.creditsText = None
        self.ival.pause()
        self.ival = None
        base.transitions.irisIn(0.5)
        self.menu.enableButtons()
        self.menu = None
        self.ignore('space')
