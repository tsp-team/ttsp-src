from panda3d.core import Vec3, OrthographicLens, Quat

from .Viewport import Viewport
from .ViewportType import *

from src.leveleditor import LEUtils
from src.leveleditor.grid.Grid2D import Grid2D

class Viewport2D(Viewport):

    def __init__(self, vpType, window):
        Viewport.__init__(self, vpType, window)
        self.names = {
            VIEWPORT_2D_TOP: "2D Top",
            VIEWPORT_2D_FRONT: "2D Front",
            VIEWPORT_2D_SIDE: "2D Side"
        }

    def initialize(self):
        Viewport.initialize(self)
        self.accept('wheel_up', self.zoomIn)
        self.accept('wheel_down', self.zoomOut)

    def zoomIn(self):
        if self.mouseWatcher.hasMouse():
            self.adjustZoom(True, 1)

    def zoomOut(self):
        if self.mouseWatcher.hasMouse():
            self.adjustZoom(True, -1)

    def getViewHpr(self):
        if self.vpType == VIEWPORT_2D_FRONT:
            return Vec3(0, 0, 0)
        elif self.vpType == VIEWPORT_2D_SIDE:
            return Vec3(90, 0, 0)
        elif self.vpType == VIEWPORT_2D_TOP:
            return Vec3(0, -90, 0)
        
        return None

    def makeGrid(self):
        self.grid = Grid2D(self)
        self.gridRoot.setHpr(self.getViewHpr())

    def makeLens(self):
        lens = OrthographicLens()
        lens.setNearFar(-10000, 10000)
        lens.setViewHpr(self.getViewHpr())
        lens.setFilmSize(100, 100)

        return lens

    def zeroUnusedCoordinate(self, vec):
        if self.type == VIEWPORT_2D_SIDE:
            vec[0] = 0.0
        elif self.type == VIEWPORT_2D_FRONT:
            vec[1] = 0.0
        elif self.type == VIEWPORT_2D_TOP:
            vec[2] = 0.0

    def rotate(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())

        return quat.xform(point)

    def invRotate(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())
        return LEUtils.makeForwardAxis(point, quat)

    def flatten(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())
        return LEUtils.zeroParallelAxis(point, quat)

    def getViewportName(self):
        self.names.get(self.type, "2D Unknown")