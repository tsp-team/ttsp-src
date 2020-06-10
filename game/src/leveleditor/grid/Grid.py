from panda3d.core import LineSegs, NodePath, Vec4, Point3, AntialiasAttrib

from src.coginvasion.globals import CIGlobals

from .GridSettings import GridSettings

# So we only have to generate a grid for a step once.
GridsByStep = {}

class Grid:

    def __init__(self, viewport):
        self.viewport = viewport

        self.gridNp = None

        self.lastStep = 0

        self.updateTask = base.taskMgr.add(self.update, 'gridUpdate')

    def removeCurrentGrid(self):
        if self.gridNp and not self.gridNp.isEmpty():
            self.gridNp.removeNode()
        self.gridNp = None

    def calcZoom(self):
        raise NotImplementedError

    def update(self, task):
        if not GridSettings.EnableGrid:
            self.removeCurrentGrid()
            return task.cont

        zoom = self.calcZoom()
        step = GridSettings.DefaultStep
        low = GridSettings.Low
        high = GridSettings.High
        actualDist = step * zoom
        if GridSettings.HideSmallerToggle:
            while actualDist < GridSettings.HideSmallerThan:
                step *= GridSettings.HideFactor
                actualDist *= GridSettings.HideFactor

        if step == self.lastStep and self.gridNp:
            return task.cont

        self.removeCurrentGrid()

        self.lastStep = step

        if step in GridsByStep:
            self.gridNp = GridsByStep[step].copyTo(self.viewport.gridRoot)
            return task.cont

        segs = LineSegs()
        i = low
        while i <= high:
            color = GridSettings.GridLines
            if i == 0:
                color = GridSettings.ZeroLines
            elif (i % GridSettings.Highlight2Unit) == 0 and GridSettings.Highlight2Toggle:
                color = GridSettings.Highlight2
            elif (i % (step * GridSettings.Highlight1Line) == 0) and GridSettings.Highlight1Toggle:
                color = GridSettings.Highlight1
            segs.setColor(color)
            segs.moveTo(Point3(low, 0, i))
            segs.drawTo(Point3(high, 0, i))
            segs.moveTo(Point3(i, 0, low))
            segs.drawTo(Point3(i, 0, high))
            i += step

        segs.setColor(GridSettings.BoundaryLines)
        # top
        segs.moveTo(Point3(low, 0, high))
        segs.drawTo(Point3(high, 0, high))
        # left
        segs.moveTo(Point3(low, 0, low))
        segs.drawTo(Point3(low, 0, high))
        # right
        segs.moveTo(Point3(high, 0, low))
        segs.drawTo(Point3(high, 0, high))
        # bottom
        segs.moveTo(Point3(low, 0, low))
        segs.drawTo(Point3(high, 0, low))

        np = NodePath(segs.create())
        #np.setAntialias(AntialiasAttrib.MLine)
        #loader.loadModel("models/smiley.egg.pz").reparentTo(np)
        GridsByStep[step] = np
        self.gridNp = np.copyTo(self.viewport.gridRoot)

        return task.cont
