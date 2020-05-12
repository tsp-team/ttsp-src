from panda3d.core import NodePath

from direct.interval.IntervalGlobal import LerpColorScaleInterval, Sequence, Func
from direct.gui.DirectGui import DirectFrame, DirectWaitBar, OnscreenText, DGG

class WaveGUI(NodePath):

    def __init__(self):
        NodePath.__init__(self, 'wave-gui')
        self.reparentTo(base.a2dBottomCenter)
        self.setBin('fixed', 60)
        self.setTransparency(True, 1)
        self.setAlphaScale(0.75, 1)
        self.setZ(0.1)
        self.frame = DirectFrame(image = 'materials/ui/wave_ui_base.png', parent = self, relief = None, image_scale = (.373, 1, .094))
        self.waveText = OnscreenText(text = "Wave 4", pos = (0, 0.0175, 0), scale = 0.06, parent = self.frame)
        self.progress = DirectWaitBar(scale = (.324, 1, .3), relief = None, barColor = (1, 0.75, 0, 1), parent = self.frame, pos = (0, 0, -0.0293))
        self.progress.setBin('fixed', 61)
        self.progress['range'] = 50
        self.progress['value'] = 35
        self.progressText = OnscreenText(text = str(self.progress['value']) + " / " + str(self.progress['range']),
                                         scale = 0.04, parent = self.frame, pos = (0, -0.04, 0))
        self.progressText.setBin('fixed', 62)
        self.hide()
        
    def doHide(self):
        Sequence(LerpColorScaleInterval(self, 1.0, (1, 1, 1, 0), (1, 1, 1, 0.75), override = 1), Func(self.hide)).start()
        
    def doShow(self):
        Sequence(Func(self.show), LerpColorScaleInterval(self, 1.0, (1, 1, 1, 0.75), (1, 1, 1, 0), override = 1)).start()
        
    def incProgress(self):
        self.adjustProgress(self.progress['value'] + 1)
        
    def adjustForWave(self, waveNum, suits):
        self.waveText['text'] = "Wave {0}".format(waveNum)
        self.progress['range'] = suits
        self.adjustProgress(0)
    
    def adjustProgress(self, progress):
        self.progress['value'] = progress
        self.progressText['text'] = str(self.progress['value']) + " / " + str(self.progress['range'])
        
