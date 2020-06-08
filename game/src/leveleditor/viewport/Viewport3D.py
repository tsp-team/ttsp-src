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
        self.gridRoot.setP(-90)

    def draw(self):
        messenger.send('draw3D', [self])
