from direct.gui.DirectGui import DirectFrame, DirectLabel, OnscreenText
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpScaleInterval, Func, Wait, LerpColorScaleInterval

from panda3d.core import NodePath

class WaveReportGUI(NodePath):
    
    def __init__(self):
        NodePath.__init__(self, 'wave-report-gui')
        self.setBin('fixed', 60)
        self.setTransparency(True, 1)
        self.setAlphaScale(0.75)
        self.reparentTo(aspect2d)
        
        self.popupSound = base.loadSfx("phase_3/audio/sfx/GUI_balloon_popup.ogg")
        
        self.widgets = []
        
        self.frame = DirectFrame(image = 'materials/ui/wave_report_base.png', image_scale = (.395 * 1.3, 1, .311 * 1.3), relief = None, parent = self)
        self.completeText = OnscreenText(text = "Wave 1 Complete", parent = self.frame, pos = (0, 0.29, 0))
        self.hide()
        
    def doHide(self):
        Sequence(LerpColorScaleInterval(self, 1.0, (1, 1, 1, 0), (1, 1, 1, 0.75), override = 1), Func(self.hide)).start()
        
    def doShow(self):
        Sequence(Func(self.show), LerpColorScaleInterval(self, 1.0, (1, 1, 1, 0.75), (1, 1, 1, 0), override = 1)).start()
    
    def getPulseIval(self, node, scale = 1, duration = 0.25):
        return Sequence(LerpScaleInterval(node, duration, scale * 1.1, 0.001, blendType = 'easeOut'), LerpScaleInterval(node, duration / 2.0, scale))
        
    def showReport(self, wavenum, stats):
        for w in self.widgets:
            w.destroy()
        self.widgets = []
        
        self.doShow()
        
        self.completeText['text'] = "Wave {0} Complete".format(wavenum)
        
        track = Sequence()
        track.append(Wait(1.0))
        
        y = 0.19
        for key, value in stats.items():
            statNameText = DirectLabel(text = key, text_scale = 0.06, parent = self.frame, relief = None)
            statNameText.setPos(0, 0, y)
            statNameText.setScale(0.0001)
            statText = DirectLabel(text = str(value), text_scale = 0.04, parent = self.frame, relief = None)
            statText.setPos(0, 0, y - 0.05)
            statText.setScale(0.0001)
            statNameTrack = self.getPulseIval(statNameText)
            statTrack = self.getPulseIval(statText)
            track.append(Func(self.popupSound.play))
            track.append(Func(statNameTrack.start))
            track.append(Wait(0.25))
            track.append(Func(self.popupSound.play))
            track.append(Func(statTrack.start))
            track.append(Wait(0.25))
            self.widgets.append(statNameText)
            self.widgets.append(statText)
            y -= 0.12
            
        track.append(Wait(5.0))
        track.append(Func(self.hideReport))
            
        track.start()
        
    def hideReport(self):
        self.doHide()
