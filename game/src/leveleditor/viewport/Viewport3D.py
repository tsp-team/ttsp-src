from panda3d.core import WindowProperties, PerspectiveLens, NodePath, Fog, Vec4, Point3, LineSegs, TextNode

from .Viewport import Viewport
from .FlyCam import FlyCam
from src.leveleditor.grid.Grid3D import Grid3D

from PyQt5 import QtWidgets, QtGui, QtCore

class Viewport3D(Viewport):

    def __init__(self, vpType, window):
        Viewport.__init__(self, vpType, window)
        self.flyCam = None

    def mouseMove(self):
        base.qtWindow.coordsLabel.setText("")

    def tick(self):
        Viewport.tick(self)
        if self.gizmo:
            quat = render.getQuat(self.cam)
            self.gizmo.xNp.lookAt(quat.getRight())
            self.gizmo.yNp.lookAt(quat.getForward())
            self.gizmo.zNp.lookAt(quat.getUp())

    def initialize(self):
        Viewport.initialize(self)
        self.flyCam = FlyCam(self)

        # Ugh
        base.camera = self.camera
        base.cam = self.cam
        base.camNode = self.camNode
        base.camLens = self.lens
        base.win = self.win
        base.gsg = self.win.getGsg()

        # Set a default camera position + angle
        self.camera.setPos(193, 247, 124)
        self.camera.setHpr(143, -18, 0)

    def makeLens(self):
        return PerspectiveLens()

    def makeGrid(self):
        self.grid = Grid3D(self)
        #self.gridRoot.setP(-90)

        # Use a fog effect to fade out the 3D grid with distance.
        # This hides the ugly banding and aliasing you see on the grid
        # from a distance, and looks quite nice.
        gridFog = Fog('gridFog')
        gridFog.setColor(self.ClearColor)
        gridFog.setExpDensity(0.0015)
        self.gridRoot.setFog(gridFog)

    def getGridAxes(self):
        # Show X and Y on the grid
        return (0, 1)

    def getGizmoAxes(self):
        return (0, 1, 2)

    def expand(self, point):
        return Point3(point[0], point[2], 0)

    def draw(self):
        messenger.send('draw3D', [self])
