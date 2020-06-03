from panda3d.core import LineSegs, NodePath, Vec4, Point3

from src.coginvasion.globals import CIGlobals

class Grid:

    def __init__(self):
        self.step = 64
        self.defaultStep = 64
        self.highlight1Toggle = True
        self.highlight1Line = 8
        self.highlight1 = Vec4(115 / 255.0, 115 / 255.0, 115 / 255.0, 1.0)
        self.highlight2Toggle = True
        self.highlight2Unit = 1024
        self.highlight2 = Vec4(100 / 255.0, 46 / 255.0, 0, 1.0)
        self.gridSnap = True
        self.gridLines = Vec4(75 / 255.0, 75 / 255.0, 75 / 255.0, 1.0)
        self.zeroLines = Vec4(0 / 255.0, 100 / 255.0, 100 / 255.0, 1.0)
        self.boundaryLines = Vec4(1, 0, 0, 1)
        self.hideSmallerToggle = True
        self.hideSmallerThan = 4
        self.hideFactor = 8
        self.low = -4096
        self.high = 4096
        self.np = render.attachNewNode("gridRoot")
        self.np.setLightOff(1)
        self.np.setFogOff(1)
        self.np.hide(CIGlobals.ShadowCameraBitmask)
        self.enabled = True

        self.gridNp = None

        self.gridsByStep = {}

        self.lastStep = self.step

        base.qtApp.window.ui.actionToggleGrid.setChecked(self.enabled)
        base.qtApp.window.ui.actionToggleGrid.toggled.connect(self.setEnabled)
        base.qtApp.window.ui.actionIncreaseGridSize.triggered.connect(self.incGridSize)
        base.qtApp.window.ui.actionDecreaseGridSize.triggered.connect(self.decGridSize)

        taskMgr.add(self.update, 'gridUpdate')

    def incGridSize(self):
        self.step *= 2
        self.step = min(256, self.step)

    def decGridSize(self):
        self.step //= 2
        self.step = max(1, self.step)

    def setEnabled(self, flag):
        self.enabled = flag

    def removeCurrentGrid(self):
        if self.gridNp and not self.gridNp.isEmpty():
            self.gridNp.reparentTo(NodePath())
        self.gridNp = None

    def update(self, task):
        if not self.enabled:
            self.removeCurrentGrid()
            return task.cont
        
        z = max(int(abs(base.camera.getZ() * 16)), 0.001)
        zoom = CIGlobals.clamp(10000 / z, 0.001, 256)
        step = self.step
        low = self.low
        high = self.high
        actualDist = self.step * zoom
        if self.hideSmallerToggle:
            while actualDist < self.hideSmallerThan:
                step *= self.hideFactor
                actualDist *= self.hideFactor

        if step == self.lastStep and self.gridNp:
            return task.cont

        self.removeCurrentGrid()

        self.lastStep = step

        if step in self.gridsByStep:
            self.gridNp = self.gridsByStep[step]
            self.gridNp.reparentTo(self.np)
            return task.cont
        
        segs = LineSegs()
        i = low
        while i <= high:
            color = self.gridLines
            if i == 0:
                color = self.zeroLines
            elif (i % self.highlight2Unit) == 0 and self.highlight2Toggle:
                color = self.highlight2
            elif (i % (step * self.highlight1Line) == 0) and self.highlight1Toggle:
                color = self.highlight1
            segs.setColor(color)
            segs.moveTo(Point3(low, i, 0))
            segs.drawTo(Point3(high, i, 0))
            segs.moveTo(Point3(i, low, 0))
            segs.drawTo(Point3(i, high, 0))
            i += step

        segs.setColor(self.boundaryLines)
        # top
        segs.moveTo(Point3(low, high, 0))
        segs.drawTo(Point3(high, high, 0))
        # left
        segs.moveTo(Point3(low, low, 0))
        segs.drawTo(Point3(low, high, 0))
        # right
        segs.moveTo(Point3(high, low, 0))
        segs.drawTo(Point3(high, high, 0))
        # bottom
        segs.moveTo(Point3(low, low, 0))
        segs.drawTo(Point3(high, low, 0))

        np = NodePath(segs.create())
        self.gridsByStep[step] = np
        np.reparentTo(self.np)
        self.gridNp = np

        return task.cont
