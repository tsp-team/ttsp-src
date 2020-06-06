from panda3d.core import Vec3, OrthographicLens, Quat, Point2, Point3, Mat4

from .Viewport import Viewport
from .ViewportType import *

from src.leveleditor import LEUtils
from src.leveleditor.grid.Grid2D import Grid2D

from PyQt5 import QtCore

class Viewport2D(Viewport):

    def __init__(self, vpType, window):
        Viewport.__init__(self, vpType, window)
        self.names = {
            VIEWPORT_2D_TOP: "2D Top",
            VIEWPORT_2D_FRONT: "2D Front",
            VIEWPORT_2D_SIDE: "2D Side"
        }

        self.dragging = False
        self.dragCamStart = Point3()
        self.dragCamMouseStart = Point3()

    def wheelUp(self):
        self.adjustZoom(True, 1)

    def wheelDown(self):
        self.adjustZoom(True, -1)

    def mouse2Down(self):
        self.setCursor(QtCore.Qt.DragMoveCursor)
        self.dragging = True
        mouse = self.mouseWatcher.getMouse()
        self.dragCamStart = self.camera.getPos()
        mouseStart = self.viewportToWorld(mouse)
        self.dragCamMouseStart = mouseStart

    def mouseMove(self):
        if self.dragging:
            mouse = self.mouseWatcher.getMouse()
            worldPos = self.viewportToWorld(mouse)
            delta = worldPos - self.dragCamMouseStart
            self.camera.setPos(self.dragCamStart - delta)

    def mouse2Up(self):
        self.setCursor(QtCore.Qt.ArrowCursor)
        self.dragging = False

    def getViewHpr(self):
        if self.type == VIEWPORT_2D_FRONT:
            return Vec3(90, 0, 0)
        elif self.type == VIEWPORT_2D_SIDE:
            return Vec3(0, 0, 0)
        elif self.type == VIEWPORT_2D_TOP:
            return Vec3(0, -90, 0)
        
        return None

    def getViewQuat(self):
        quat = Quat()
        quat.setHpr(self.getViewHpr())

    def getViewMatrix(self):
        quat = Quat()
        quat.setHpr(self.getViewHpr())
        mat = Mat4()
        quat.extractToMatrix(mat)
        return mat

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
            vec[1] = 0.0
        elif self.type == VIEWPORT_2D_FRONT:
            vec[0] = 0.0
        elif self.type == VIEWPORT_2D_TOP:
            vec[2] = 0.0

    def flatten(self, point):
        if self.type == VIEWPORT_2D_TOP:
            return Point3(point[0], point[1], 0)
        elif self.type == VIEWPORT_2D_FRONT:
            return Point3(point[1], point[2], 0)
        elif self.type == VIEWPORT_2D_SIDE:
            return Point3(point[0], point[2], 0)

    def expand(self, point):
        if self.type == VIEWPORT_2D_TOP:
            return Point3(point[0], point[1], 0)
        elif self.type == VIEWPORT_2D_FRONT:
            return Point3(0, point[0], point[1])
        elif self.type == VIEWPORT_2D_SIDE:
            return Point3(point[0], 0, point[1])

    def getUnusedCoordinate(self, point):
        if self.type == VIEWPORT_2D_TOP:
            return Point3(0, 0, point[2])
        elif self.type == VIEWPORT_2D_SIDE:
            return Point3(0, point[1], 0)
        elif self.type == VIEWPORT_2D_FRONT:
            return Point3(point[0], 0, 0)

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
        return self.names.get(self.type, "2D Unknown")