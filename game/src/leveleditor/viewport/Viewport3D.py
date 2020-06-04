from panda3d.core import WindowProperties, PerspectiveLens, NodePath

from .Viewport import Viewport
from .FlyCam import FlyCam
from src.leveleditor.grid.Grid3D import Grid3D

from PyQt5 import QtWidgets, QtGui, QtCore

class Viewport3D(Viewport):

    def __init__(self, vpType, window):
        Viewport.__init__(self, vpType, window)
        self.flyCam = None

    def initialize(self):
        Viewport.initialize(self)
        self.flyCam = FlyCam(self)

        # Ugh
        base.camera = self.camNp
        base.cam = self.camNp
        base.camNode = self.cam
        base.camLens = self.lens
        base.win = self.win
        base.render2d = NodePath("r2d_dummy")
        base.aspect2d = NodePath("a2d_dummy")
        base.render2dp = NodePath("r2dp_dummy")

    def makeLens(self):
        return PerspectiveLens()

    def makeGrid(self):
        self.grid = Grid3D(self)
        self.gridRoot.setP(-90)

    def getViewportName(self):
        return "3D Perspective"
