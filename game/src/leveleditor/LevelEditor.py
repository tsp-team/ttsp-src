from panda3d.core import WindowProperties, NativeWindowHandle, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, CollisionTraverser

from src.coginvasion.base.BSPBase import BSPBase
from src.leveleditor.viewport.QuadSplitter import QuadSplitter
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.leveleditor.viewport.Viewport3D import Viewport3D
from src.leveleditor.viewport.ViewportType import *
from src.leveleditor.viewport.ViewportManager import ViewportManager
from src.leveleditor.tools.ToolManager import ToolManager
from src.leveleditor import LEUtils
from src.leveleditor.grid.GridSettings import GridSettings
from .EntityEdit import EntityEdit

from PyQt5 import QtWidgets, QtCore, QtGui
from fgdtools import FgdParse

import builtins

class LevelEditorSubWind(QtWidgets.QWidget):

    def __init__(self, area):
        QtWidgets.QWidget.__init__(self, area)
        area.addSubWindow(self)
        self.layout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Game View")
        self.resize(640, 480)

        self.splitter = QuadSplitter(self)

        self.layout.addWidget(self.splitter)

        self.setLayout(self.layout)

        self.show()

    def addViewports(self):
        vp3d = Viewport3D(VIEWPORT_3D, self.splitter)
        vp3d.initialize()
        vp2df = Viewport2D(VIEWPORT_2D_FRONT, self.splitter)
        vp2df.initialize()
        vp2ds = Viewport2D(VIEWPORT_2D_SIDE, self.splitter)
        vp2ds.initialize()
        vp2dt = Viewport2D(VIEWPORT_2D_TOP, self.splitter)
        vp2dt.initialize()

        self.splitter.addWidget(vp3d, 0, 0)
        self.splitter.addWidget(vp2df, 0, 1)
        self.splitter.addWidget(vp2ds, 1, 0)
        self.splitter.addWidget(vp2dt, 1, 1)

class LevelEditorWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        from src.leveleditor.ui.mainwindow import Ui_LevelEditor
        self.ui = Ui_LevelEditor()
        self.ui.setupUi(self)

        self.toolBar = self.ui.leftBar
        self.toolGroup = QtWidgets.QActionGroup(self.ui.leftBar)

        self.gameViewWind = LevelEditorSubWind(self.ui.gameViewArea)

    def closeEvent(self, event):
        base.running = False

class LevelEditorApp(QtWidgets.QApplication):

    def __init__(self):
        QtWidgets.QApplication.__init__(self, [])
        
        self.setStyle("Fusion")


        dark_palette = QtGui.QPalette()

        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

        self.setPalette(dark_palette)

        self.setStyleSheet("QToolTip { color: #000000 }")
        
        self.window = LevelEditorWindow()
        self.window.show()

class LevelEditor(BSPBase):

    def __init__(self):
        
        self.gsg = None
        
        BSPBase.__init__(self)
        self.loader.mountMultifiles()
        self.loader.mountMultifile("resources/mod.mf")
        
        #toon.setY(10)

        #base.enableMouse()

        from panda3d.core import DirectionalLight, AmbientLight
        dlight = DirectionalLight('dlight')
        dlight.setColor((2.5, 2.5, 2.5, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(165 - 180, -60, 0)
        render.setLight(dlnp)
        self.dlnp = dlnp
        alight = AmbientLight('alight')
        alight.setColor((0.4, 0.4, 0.4, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)

        # Timer to run the panda mainloop
        #self.mainloopTimer = QtCore.QTimer()
        #self.mainloopTimer.timeout.connect(self.taskMgr.step)
        #self.mainloopTimer.setSingleShot(False)

        self.fgd = FgdParse('resources/phase_14/etc/cio.fgd')        

        self.mapRoot = render.attachNewNode('mapRoot')
        self.mapRoot.setScale(16.0)

        #from src.leveleditor.mapobject.MapObject import MapObject
        #mo = MapObject()
        #mo.setClassname("prop_static")
        #toon.setX(4)

        self.entityEdit = None

        #render.setScale(1 / 16.0)

        base.setBackgroundColor(0, 0, 0)
    
    def snapToGrid(self, point):
        if GridSettings.GridSnap:
            return LEUtils.snapToGrid(GridSettings.DefaultStep, point)
        return point

    def initialize(self):
        self.viewportMgr = ViewportManager()
        self.toolMgr = ToolManager()
        self.qtApp = LevelEditorApp()
        self.qtApp.window.gameViewWind.addViewports()
        self.qtApp.window.ui.actionToggleGrid.setChecked(GridSettings.EnableGrid)
        self.qtApp.window.ui.actionToggleGrid.toggled.connect(self.__toggleGrid)
        self.qtApp.window.ui.actionIncreaseGridSize.triggered.connect(self.__incGridSize)
        self.qtApp.window.ui.actionDecreaseGridSize.triggered.connect(self.__decGridSize)
        BSPBase.initialize(self)

    def __toggleGrid(self):
        GridSettings.EnableGrid = not GridSettings.EnableGrid

    def __incGridSize(self):
        GridSettings.DefaultStep *= 2
        GridSettings.DefaultStep = min(256, GridSettings.DefaultStep)

    def __decGridSize(self):
        GridSettings.DefaultStep //= 2
        GridSettings.DefaultStep = max(1, GridSettings.DefaultStep)

    def editEntity(self, ent):
        self.entityEdit = EntityEdit(ent)

    def initStuff(self):
        BSPBase.initStuff(self)
        self.camLens.setMinFov(70.0 / (4./3.))
        self.camLens.setNearFar(0.1, 10000)
        #self.shaderGenerator.setSunLight(self.dlnp)

        self.toolMgr.addTools()

    def run(self):
        self.running = True
        while self.running:
            self.qtApp.processEvents()
            self.taskMgr.step()