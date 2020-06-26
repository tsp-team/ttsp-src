from panda3d.core import Vec3, OrthographicLens, Quat, Point2, Point3, Mat4, OmniBoundingVolume
from panda3d.core import RenderState, FogAttrib, LightAttrib

from .Viewport import Viewport
from .ViewportType import *

from src.leveleditor import LEUtils
from src.leveleditor.grid.Grid2D import Grid2D

from PyQt5 import QtCore

import math

class Viewport2D(Viewport):

    def __init__(self, vpType, window):
        Viewport.__init__(self, vpType, window)
        self.zoom = 0.25
        self.dragging = False
        self.dragCamStart = Point3()
        self.dragCamMouseStart = Point3()

    def initialize(self):
        Viewport.initialize(self)
        self.gizmo.np.setHpr(self.getViewHpr())
        self.camNode.setInitialState(
            RenderState.make(FogAttrib.makeOff(), LightAttrib.makeAllOff()))

    def adjustZoom(self, scrolled = False, delta = 0):
        before = Point3()
        if self.mouseWatcher.hasMouse():
            md = self.mouseWatcher.getMouse()
        else:
            scrolled = False

        if scrolled:
            before = self.viewportToWorld(md, False)
            self.zoom *= math.pow(1.2, float(delta))
            self.zoom = min(256.0, max(0.01, self.zoom))

        self.fixRatio()

        if scrolled:
            after = self.viewportToWorld(md, False)
            self.camera.setPos(self.camera.getPos() - (after - before))

    def wheelUp(self):
        self.adjustZoom(True, 1)

    def wheelDown(self):
        self.adjustZoom(True, -1)

    def mouse2Down(self):
        base.qtApp.setOverrideCursor(QtCore.Qt.ClosedHandCursor)
        self.dragging = True
        mouse = self.mouseWatcher.getMouse()
        self.dragCamStart = self.camera.getPos()
        mouseStart = self.viewportToWorld(mouse, False, True)
        self.dragCamMouseStart = mouseStart

    def mouseMove(self):
        if self.dragging:
            mouse = self.mouseWatcher.getMouse()
            worldPos = self.viewportToWorld(mouse, False, True)
            delta = worldPos - self.dragCamMouseStart
            self.camera.setPos(self.dragCamStart - delta)

    def mouse2Up(self):
        base.qtApp.restoreOverrideCursor()
        self.dragging = False

    def getViewHpr(self):
        return self.spec.viewHpr

    def getViewQuat(self):
        quat = Quat()
        quat.setHpr(self.getViewHpr())

    def getViewMatrix(self):
        quat = Quat()
        quat.setHpr(self.getViewHpr())
        mat = Mat4()
        quat.extractToMatrix(mat)
        return mat

    def viewportToWorld(self, viewport, flatten = True, vec = False):
        world = Viewport.viewportToWorld(self, viewport, vec)
        if flatten:
            return self.flatten(world)
        return world

    def makeGrid(self):
        self.grid = Grid2D(self)
        #self.gridRoot.setHpr(self.getViewHpr())

    def makeLens(self):
        lens = OrthographicLens()
        lens.setNearFar(-10000, 10000)
        lens.setViewHpr(self.getViewHpr())
        lens.setFilmSize(100, 100)

        return lens

    def zeroUnusedCoordinate(self, vec):
        vec[self.spec.unusedCoordinate] = 0

    def flatten(self, point):
        indices = self.spec.flattenIndices
        newPoint = Point3(point[indices[0]], 0, point[indices[1]])

        return newPoint

    def expand(self, point):
        newPoint = Point3(0)
        for i in range(3):
            idx = self.spec.expandIndices[i]
            if idx == -1:
                continue
            newPoint[i] = point[idx]
        return newPoint

    def getGridAxes(self):
        return self.spec.flattenIndices

    def getGizmoAxes(self):
        return self.spec.flattenIndices

    def getUnusedCoordinate(self, point):
        newPoint = Point3(0, 0, 0)
        axis = self.spec.unusedCoordinate
        newPoint[axis] = point[axis]
        return newPoint

    def rotate(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())

        return quat.xform(point)

    def invRotate(self, point):
        quat = Quat()
        quat.setHpr(self.getViewHpr())
        return LEUtils.makeForwardAxis(point, quat)

    def draw(self):
        messenger.send('draw2D', [self])
