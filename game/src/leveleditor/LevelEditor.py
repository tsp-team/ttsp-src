from panda3d.core import WindowProperties, NativeWindowHandle, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, CollisionTraverser
from panda3d.core import TextNode, Filename

from src.coginvasion.base.BSPBase import BSPBase
from src.leveleditor.viewport.QuadSplitter import QuadSplitter
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.leveleditor.viewport.Viewport3D import Viewport3D
from src.leveleditor.viewport.ViewportType import *
from src.leveleditor.viewport.ViewportManager import ViewportManager
from src.leveleditor.tools.ToolManager import ToolManager
from src.leveleditor import LEUtils
from src.leveleditor.grid.GridSettings import GridSettings
from src.leveleditor.Document import Document
from src.leveleditor.ui import About
from .EntityEdit import EntityEdit

from PyQt5 import QtWidgets, QtCore, QtGui
from fgdtools import FgdParse

import builtins

class LevelEditorSubWind(QtWidgets.QWidget):

    def __init__(self, area):
        QtWidgets.QWidget.__init__(self, area)
        area.addSubWindow(self)
        self.layout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("")


        self.splitter = QuadSplitter(self)

        self.layout.addWidget(self.splitter)

        self.setLayout(self.layout)

        self.showMaximized()

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
        self.splitter.addWidget(vp2df, 1, 0)
        self.splitter.addWidget(vp2ds, 1, 1)
        self.splitter.addWidget(vp2dt, 0, 1)

class LevelEditorWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        from src.leveleditor.ui.mainwindow import Ui_LevelEditor
        self.ui = Ui_LevelEditor()
        self.ui.setupUi(self)

        self.toolBar = self.ui.leftBar
        self.toolGroup = QtWidgets.QActionGroup(self.ui.leftBar)

        self.gameViewWind = LevelEditorSubWind(self.ui.gameViewArea)

        self.ui.actionAbout.triggered.connect(self.__showAbout)
        self.ui.actionSave.triggered.connect(self.__save)
        self.ui.actionSaveAs.triggered.connect(self.__saveAs)

    def __save(self):
        if not base.document.filename:
            self.doSaveAs()
            return

        base.document.save()

    def __saveAs(self):
        self.doSaveAs()

    def doSaveAs(self):
        selectedFilename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save As')
        if len(selectedFilename[0]) == 0:
            # Save as was cancelled
            return
        # Convert to a panda filename
        filename = Filename.fromOsSpecific(selectedFilename[0])
        base.document.save(filename)

    def __showAbout(self):
        dlg = QtWidgets.QDialog(self)
        ui = About.Ui_Dialog()
        ui.setupUi(dlg)
        img = QtWidgets.QLabel(dlg)
        img.setAlignment(QtCore.Qt.AlignCenter)
        img.setPixmap(QtGui.QPixmap('resources/maps/flippy-hammer.png'))
        ui.gridLayout.addWidget(img, 4, 0, 1, 1)
        dlg.setModal(True)
        dlg.show()

    def closeEvent(self, event):
        base.running = False

class LevelEditorApp(QtWidgets.QApplication):

    def __init__(self):
        QtWidgets.QApplication.__init__(self, [])

        self.setWindowIcon(QtGui.QIcon("resources/icons/hammer.ico"))

        self.setStyle("fusion")
        dark_palette = QtGui.QPalette()
        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(68, 68, 68))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(82, 82, 82))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(68, 68, 68))
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.black)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(68, 68, 68))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(76, 130, 168))
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(76, 130, 168))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Shadow, QtCore.Qt.black)
        self.setPalette(dark_palette)

        self.window = LevelEditorWindow()
        self.window.show()

class LevelEditor(BSPBase):

    def __init__(self):

        self.gsg = None

        self.viewportTitle = ""
        self.mapNameTitle = ""

        BSPBase.__init__(self)

        #self.setFrameRateMeter(True)

        #toon.setY(10)

        #base.enableMouse()

        TextNode.setDefaultFont(loader.loadFont("resources/models/fonts/consolas.ttf"))

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

        #from src.leveleditor.mapobject.MapObject import MapObject
        #mo = MapObject()
        #mo.setClassname("prop_static")
        #toon.setX(4)

        self.entityEdit = None

        #render.setScale(1 / 16.0)

        base.setBackgroundColor(0, 0, 0)

    def setEditorWindowTitle(self, viewportTitle = None):
        if viewportTitle is None:
            viewportTitle = self.viewportTitle

        mapName = self.document.getMapName()
        if self.document.unsaved:
            mapName += " *"

        if len(viewportTitle):
    	    self.qtApp.window.gameViewWind.setWindowTitle(mapName + " - " + viewportTitle)
        else:
            self.qtApp.window.gameViewWind.setWindowTitle(mapName)

        self.viewportTitle = viewportTitle

    def snapToGrid(self, point):
        if GridSettings.GridSnap:
            return LEUtils.snapToGrid(GridSettings.DefaultStep, point)
        return point

    def initialize(self):
        self.loader.mountMultifiles()
        self.loader.mountMultifile("resources/mod.mf")

        self.fgd = FgdParse('resources/phase_14/etc/cio.fgd')
        self.viewportMgr = ViewportManager()
        self.toolMgr = ToolManager()
        self.qtApp = LevelEditorApp()
        self.qtApp.window.gameViewWind.addViewports()
        self.qtApp.window.ui.actionToggleGrid.setChecked(GridSettings.EnableGrid)
        self.qtApp.window.ui.actionToggleGrid.toggled.connect(self.__toggleGrid)
        self.qtApp.window.ui.actionIncreaseGridSize.triggered.connect(self.__incGridSize)
        self.qtApp.window.ui.actionDecreaseGridSize.triggered.connect(self.__decGridSize)
        BSPBase.initialize(self)

        # Open a blank document
        self.document = Document()
        self.document.open()

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
