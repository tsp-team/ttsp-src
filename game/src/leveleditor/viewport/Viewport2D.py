from panda3d.core import Vec3, OrthographicLens, Quat, Point2, Point3, Mat4

from .Viewport import Viewport
from .ViewportType import *

from src.leveleditor import LEUtils
from src.leveleditor.grid.Grid2D import Grid2D

from PyQt5 import QtCore

import math

class Viewport2D(Viewport):

    def __init__(self, vpType, window):
        Viewport.__init__(self, vpType, window)
        self.dragging = False
        self.dragCamStart = Point3()
        self.dragCamMouseStart = Point3()


    def adjustZoom(self, scrolled = False, delta = 0):
        before = Point3()
        if self.mouseWatcher.hasMouse():
            md = self.mouseWatcher.getMouse()
        else:
            scrolled = False

        if scrolled:
            before = self.viewportToWorld(md)
            self.zoom *= math.pow(1.2, float(delta))
            self.zoom = min(256.0, max(0.01, self.zoom))

        self.fixRatio()

        if scrolled:
            after = self.viewportToWorld(md)
            self.cam.setPos(self.cam.getPos() - (after - before))

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
        if self.type in VIEWPORT_VIEW_HPR:
            return VIEWPORT_VIEW_HPR[self.type]

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
        if self.type in VIEWPORT_AXIS_UNUSED:
            vec[VIEWPORT_AXIS_UNUSED[self.type]] = 0

    def flatten(self, point):
        unused = self.zeroUnusedCoordinate(point)
        args = []
        for axis in point:
            if axis == unused:
                continue
            args.append(axis)
        return Point3(*args, 0)

    def expand(self, point):
        # TODO: fix this, if statements bad
        if self.type == VIEWPORT_2D_TOP:
            return Point3(point[0], point[1], 0)
        elif self.type == VIEWPORT_2D_FRONT:
            return Point3(0, point[0], point[1])
        elif self.type == VIEWPORT_2D_SIDE:
            return Point3(point[0], 0, point[1])

    def getUnusedCoordinate(self, point):
        new_point = Point3(0, 0, 0)
        new_point[self.type] = point[self.type]
        return new_point

    def rotate(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())

        return quat.xform(point)

    def invRotate(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())
        return LEUtils.makeForwardAxis(point, quat)

    def getViewportName(self):
        return VIEWPORT_NAMES.get(self.type, "2D Unknown")

    def draw(self):
        messenger.send('draw2D', [self])
