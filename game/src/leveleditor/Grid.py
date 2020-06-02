from panda3d.core import LineSegs, NodePath, Vec4, Point3

from src.coginvasion.globals import CIGlobals

class Grid:

    def __init__(self):
        self.step = 64
        self.defaultSize = 4
        self.highlight1Toggle = True
        self.highlight1Line = 8
        self.highlight1 = Vec4(115 / 255.0, 115 / 255.0, 115 / 255.0, 1.0)
        self.highlight2Toggle = True
        self.highlight2Unit = 1024
        self.highlight2 = Vec4(100 / 255.0, 46 / 255.0, 0, 1.0)
        self.gridSize = 4
        self.gridSnap = True
        self.gridLines = Vec4(75 / 255.0, 75 / 255.0, 75 / 255.0, 1.0)
        self.zeroLines = Vec4(0 / 255.0, 100 / 255.0, 100 / 255.0, 1.0)
        self.boundaryLines = Vec4(1, 0, 0, 1)
        self.low = -4096
        self.high = 4096
        self.np = render.attachNewNode("gridRoot")
        self.np.setLightOff(1)
        self.np.setFogOff(1)
        self.np.hide(CIGlobals.ShadowCameraBitmask)
        self.enabled = True

    def setEnabled(self, flag):
        if not flag:
            self.np.node().removeAllChildren()
        else:
            self.update()

    def update(self):
        if not self.np.isEmpty():
            self.np.node().removeAllChildren()
        
        segs = LineSegs()
        i = self.low
        while i <= self.high:
            color = self.gridLines
            if i == 0:
                color = self.zeroLines
            elif (i % self.highlight2Unit) == 0 and self.highlight2Toggle:
                color = self.highlight2
            elif (i % (self.step * self.highlight1Line) == 0) and self.highlight1Toggle:
                color = self.highlight1
            segs.setColor(color)
            segs.moveTo(Point3(self.low, i, 0))
            segs.drawTo(Point3(self.high, i, 0))
            segs.moveTo(Point3(i, self.low, 0))
            segs.drawTo(Point3(i, self.high, 0))
            i += self.step

        segs.setColor(self.boundaryLines)
        # top
        segs.moveTo(Point3(self.low, self.high, 0))
        segs.drawTo(Point3(self.high, self.high, 0))
        # left
        segs.moveTo(Point3(self.low, self.low, 0))
        segs.drawTo(Point3(self.low, self.high, 0))
        # right
        segs.moveTo(Point3(self.high, self.low, 0))
        segs.drawTo(Point3(self.high, self.high, 0))
        # bottom
        segs.moveTo(Point3(self.low, self.low, 0))
        segs.drawTo(Point3(self.high, self.low, 0))

        self.np.attachNewNode(segs.create())
