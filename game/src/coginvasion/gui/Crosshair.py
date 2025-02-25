from direct.gui.DirectGui import DirectFrame

class CrosshairData:

    def __init__(self, wantCrosshair = True, crosshairTex = 'phase_14/maps/crosshair_4.png',
                 crosshairScale = 1, crosshairRot = 0):
        self.wantCrosshair = wantCrosshair
        self.crosshairTex = crosshairTex
        self.crosshairScale = crosshairScale
        self.crosshairRot = crosshairRot

    def cleanup(self):
        del self.wantCrosshair
        del self.crosshairTex
        del self.crosshairScale
        del self.crosshairRot

class Crosshair(DirectFrame):

    def __init__(self):
        DirectFrame.__init__(self, parent = aspect2d)
        self.setBin('fixed', 59)
        self.setTransparency(True)
        self.currData = None

    def setCrosshair(self, dat):
        self.currData = dat
        self['image'] = dat.crosshairTex
        self['image_scale'] = 0.05 * dat.crosshairScale
        self['image_hpr'] = (0, 0, dat.crosshairRot)

    def show(self):
        if (not self.currData or
        not hasattr(self.currData, 'wantCrosshair') or
        not self.currData.wantCrosshair):
            self.hide()
            return
        DirectFrame.show(self)
