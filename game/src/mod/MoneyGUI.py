"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file MoneyGUI.py
@author Brian Lach
@date August 06, 2014

"""

from panda3d.core import NodePath

from direct.gui.DirectGui import DirectFrame, OnscreenImage, DirectLabel

from src.coginvasion.base import ToontownIntervals
from src.coginvasion.globals import CIGlobals

class MoneyGUI:

    def createGui(self):
        self.deleteGui()
        self.root = base.a2dBottomLeft.attachNewNode('moneyroot')
        self.root.setScale(0.8)
        self.root.setBin('gui-popup', 60)
        self.frame = DirectFrame(parent=self.root, pos=(0.43, 0, 0.16))
        gui = loader.loadModel("phase_3.5/models/gui/jar_gui.bam")
        self.jar = OnscreenImage(image=gui, scale=0.5, parent=self.frame)
        mf = loader.loadFont("phase_3/models/fonts/MickeyFont.bam")
        self.money_lbl = DirectLabel(text="", text_font=mf, text_fg=(1,1,0,1), parent=self.jar, text_scale=0.2, relief=None, pos=(0, 0, -0.1))
        gui.remove_node()

    def deleteGui(self):
        if hasattr(self, 'jar'):
            self.jar.destroy()
            del self.jar
        if hasattr(self, 'money_lbl'):
            self.money_lbl.destroy()
            del self.money_lbl
        if hasattr(self, 'frame'):
            self.frame.destroy()
            del self.frame

    def update(self, newMoney, oldMoney = 0):
        delta = newMoney - oldMoney
        if delta != 0:
            CIGlobals.makeDeltaTextEffect(delta, base.a2dBottomLeft, (0.173, 0, 0.12))
            if delta > 0:
                ToontownIntervals.start(ToontownIntervals.getPulseLargerIval(self.frame, 'money-effect'))
            else:
                ToontownIntervals.start(ToontownIntervals.getPulseSmallerIval(self.frame, 'money-effect'))
            
        if hasattr(self, 'money_lbl'):
            if newMoney <= 0:
                self.money_lbl['text_fg'] = (1, 0, 0, 1)
            else:
                self.money_lbl['text_fg'] = (1, 1, 0, 1)
            self.money_lbl['text'] = str(newMoney)
