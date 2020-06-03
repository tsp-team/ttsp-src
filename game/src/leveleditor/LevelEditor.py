from panda3d.core import WindowProperties, NativeWindowHandle, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, CollisionTraverser

from src.coginvasion.base.BSPBase import BSPBase
from src.leveleditor.Grid import Grid
from src.leveleditor.FlyCam import FlyCam
from .EntityEdit import EntityEdit

from PyQt5 import QtWidgets, QtCore, QtGui
from fgdtools import FgdParse

import builtins

class LevelEditorSubWind(QtWidgets.QWidget):

    def __init__(self, area):
        QtWidgets.QWidget.__init__(self)
        area.addSubWindow(self)
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)
        self.setWindowTitle("3D View")
        self.resize(640, 480)
        self.show()
        
    def resizeEvent(self, event):
        if not hasattr(builtins, 'base'):
            return
        if not hasattr(base, 'win'):
            return

        props = WindowProperties()
        props.setSize(event.size().width(), event.size().height())
        base.win.requestProperties(props)

class LevelEditorWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        from src.leveleditor.ui.mainwindow import Ui_LevelEditor
        self.ui = Ui_LevelEditor()
        self.ui.setupUi(self)

        self.toolBar = self.ui.leftBar
        self.toolGroup = QtWidgets.QActionGroup(self.ui.leftBar)

        self.gameViewWind = LevelEditorSubWind(self.ui.gameViewArea)

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

        self.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

        self.window = LevelEditorWindow()
        self.window.show()

class LevelEditor(BSPBase):

    def __init__(self):
        self.qtApp = LevelEditorApp()

        BSPBase.__init__(self)
        self.loader.mountMultifiles()
        self.loader.mountMultifile("resources/mod.mf")

        # Collision stuff for selecting out of the viewport.
        self.clickRay = CollisionRay()
        self.clickNode = CollisionNode('viewportClickRay')
        self.clickNode.addSolid(self.clickRay)
        self.clickNP = NodePath(self.clickNode)
        self.clickQueue = CollisionHandlerQueue()
        self.clickTrav = CollisionTraverser()
        self.clickTrav.addCollider(NodePath(self.clickNode), self.clickQueue)
        
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
        self.mainloopTimer = QtCore.QTimer()
        self.mainloopTimer.timeout.connect(self.taskMgr.step)
        self.mainloopTimer.setSingleShot(False)

        self.fgd = FgdParse('resources/phase_14/etc/cio.fgd')

        self.currentTool = None
        self.grid = Grid()
        #self.grid.update()
        self.flyCam = FlyCam()

        self.tools = []

        self.mapRoot = render.attachNewNode('mapRoot')
        self.mapRoot.setScale(16.0)

        from src.leveleditor.mapobject.MapObject import MapObject
        mo = MapObject()
        mo.setClassname("prop_static")
        #toon.setX(4)

        self.entityEdit = None

        #render.setScale(1 / 16.0)

        base.setBackgroundColor(0, 0, 0)

    def editEntity(self, ent):
        self.entityEdit = EntityEdit(ent)

    def click(self, mask):
        if not self.mouseWatcherNode.hasMouse():
            return None

        self.clickNP.reparentTo(base.camera)
        self.clickRay.setFromLens(self.camNode, self.mouseWatcherNode.getMouse())
        self.clickNode.setFromCollideMask(mask)
        self.clickQueue.clearEntries()
        self.clickTrav.traverse(self.mapRoot)
        self.clickQueue.sortEntries()
        self.clickNP.reparentTo(NodePath())
        return self.clickQueue.getEntries()

    def addTool(self, toolInst):
        toolInst.createButton()
        self.tools.append(toolInst)

    def addTools(self):
        from src.leveleditor.tools.SelectTool import SelectTool
        from src.leveleditor.tools.EntityTool import EntityTool
        self.addTool(SelectTool())
        self.addTool(EntityTool())

        self.qtApp.window.toolBar.addActions(self.qtApp.window.toolGroup.actions())

    def initStuff(self):
        BSPBase.initStuff(self)
        self.camLens.setMinFov(70.0 / (4./3.))
        self.camLens.setNearFar(0.1, 10000)
        #self.shaderGenerator.setSunLight(self.dlnp)

        self.addTools()

    def openDefaultWindow(self, *args, **kwargs):
        props = WindowProperties.getDefault()
        props.setParentWindow(int(self.qtApp.window.gameViewWind.winId()))
        props.setOpen(True)
        props.setForeground(True)
        props.setOrigin(0, 0)
        kwargs['props'] = props
        BSPBase.openDefaultWindow(self, *args, **kwargs)

    def run(self):
        self.mainloopTimer.start(0)
        self.qtApp.exec_()