from direct.gui.DirectGui import OnscreenText, OnscreenImage, DirectButton, DGG
from direct.interval.IntervalGlobal import Sequence, Wait, Func

from src.coginvasion.globals import CIGlobals

from panda3d.core import Vec3, TextNode

class ModMainMenu:
    
    def __init__(self):
        self.menuButtons = []
        self.currZ = 0.7
        
    def makeMenuButton(self, text, callback = None, extraArgs = []):
        btn = DirectButton(text_align = TextNode.ALeft, text = text, command = callback,
            extraArgs = extraArgs, relief = None, text0_fg = (1, 1, 1, 1), text1_fg = (0.5, 0.5, 0.5, 1.0),
            text2_fg = (0.5, 0.5, 0.5, 1.0), text3_fg = (1, 1, 1, 1.0), scale = 0.08,
            pos = (0.3, 0, self.currZ), parent = base.a2dBottomLeft, pressEffect = 0)
        self.currZ -= 0.1
        self.menuButtons.append(btn)
        
    def disableButtons(self):
        for btn in self.menuButtons:
            btn['state'] = DGG.DISABLED
            
    def enableButtons(self):
        for btn in self.menuButtons:
            btn['state'] = DGG.NORMAL
        
    def __transitionEffect(self, callback):
        self.disableButtons()
        ival = Sequence(Func(base.fadeOutMusic),
                        Func(base.transitions.irisOut, 0.5),
                        Wait(1.0),
                        Func(callback))
        ival.start()
        
    def __handleCredits(self):
        from src.mod.ModCredits import ModCredits
        ModCredits(self)
        
    def __handleQuit(self):
        import sys
        sys.exit(0)
    
    def create(self):
        CIGlobals.makeLoadingScreen(True)
        base.loadBSPLevel("resources/maps/facility_battle_v2.bsp")
        base.bspLevel.reparentTo(render)
        camera.setPos(77 / 16.0, 776 / 16.0, 8 / 16.0)
        camera.setHpr(0, 0, 0)
        camera.setHpr(camera, Vec3(250 - 90, 10, 0))
        base.camLens.setMinFov(85.0 / (4. / 3.))
        
        self.makeMenuButton("Play", callback = self.__transitionEffect, extraArgs = [base.playGame])
        self.makeMenuButton("Options")
        self.makeMenuButton("Credits", callback = self.__transitionEffect, extraArgs = [self.__handleCredits])
        self.makeMenuButton("Quit", callback = self.__transitionEffect, extraArgs = [self.__handleQuit])
        
        base.accept('b', base.bspLoader.buildCubemaps)
        
        render.show()
        
        CIGlobals.clearLoadingScreen()
        
        base.showMouseCursor()
        
        
        base.transitions.irisIn(0.5)
        
    def shutdown(self):
        for btn in self.menuButtons:
            btn.destroy()
        self.menuButtons = None
        self.currZ = None
        base.camLens.setMinFov(70.0 / (4. / 3.))
        base.cleanupBSPLevel()
        render.hide()
