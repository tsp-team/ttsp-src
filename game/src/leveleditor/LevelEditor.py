from panda3d.core import WindowProperties, NativeWindowHandle, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, CollisionTraverser
from panda3d.core import TextNode, Filename, KeyboardButton, ButtonRegistry
from panda3d.core import CullBinManager, GraphicsEngine, GraphicsPipeSelection
from panda3d.core import TransformState, RenderState, DataGraphTraverser
from panda3d.core import ClockObject, TrueClock
from panda3d.direct import throwNewFrame

import builtins

from direct.showbase.DirectObject import DirectObject
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.MessengerGlobal import messenger
from direct.showbase.EventManagerGlobal import eventMgr

from src.coginvasion.base.CogInvasionLoader import CogInvasionLoader

from src.leveleditor.viewport.QuadSplitter import QuadSplitter
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.leveleditor.viewport.Viewport3D import Viewport3D
from src.leveleditor.viewport.ViewportType import *
from src.leveleditor.viewport.ViewportManager import ViewportManager
from src.leveleditor.tools.ToolManager import ToolManager
from src.leveleditor.selection.SelectionManager import SelectionManager
from src.leveleditor.selection.SelectionType import SelectionType
from src.leveleditor.actions.ActionManager import ActionManager
from src.leveleditor.brushes.BrushManager import BrushManager
from src.leveleditor import LEUtils, LEGlobals
from src.leveleditor.grid.GridSettings import GridSettings
from src.leveleditor.Document import Document
from src.leveleditor.ui import About
from src.leveleditor.actions.ChangeSelectionMode import ChangeSelectionMode
from src.leveleditor.ui.ModelBrowser import ModelBrowser
from src.leveleditor.ui.MaterialBrowser import MaterialBrowser
from src.leveleditor.menu.MenuManager import MenuManager
from src.leveleditor.menu.KeyBind import KeyBind

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
from src.leveleditor.fgdtools import FgdParse, FgdWrite

import builtins
import time

class LevelEditorWindow(QtWidgets.QMainWindow, DirectObject):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        DirectObject.__init__(self)

        self.dockLocations = {
            "right": QtCore.Qt.RightDockWidgetArea,
            "left": QtCore.Qt.LeftDockWidgetArea,
            "top": QtCore.Qt.TopDockWidgetArea,
            "bottom": QtCore.Qt.BottomDockWidgetArea
        }

        from src.leveleditor.ui.mainwindow import Ui_LevelEditor
        self.ui = Ui_LevelEditor()
        self.ui.setupUi(self)

        self.setWindowTitle(LEGlobals.AppName)

        base.leftBar = self.ui.leftBar
        base.statusBar = self.ui.statusbar

        self.selectedLabel = self.addPaneLabel(300, "No selection.")
        self.coordsLabel = self.addPaneLabel(100)
        self.zoomLabel = self.addPaneLabel(90)
        self.gridSnapLabel = self.addPaneLabel(135)

        self.toolBar = self.ui.leftBar
        self.toolBar.setIconSize(QtCore.QSize(48, 48))
        base.toolBar = self.toolBar

        base.menuBar = self.ui.menubar

        self.docTabs = self.ui.documentTabs
        base.docTabs = self.docTabs

        self.docTabs.currentChanged.connect(self.__docTabChanged)

        """
        self.ui.actionAbout.triggered.connect(self.__showAbout)
        self.ui.actionSave.triggered.connect(self.__save)
        self.ui.actionSaveAs.triggered.connect(self.__saveAs)
        self.ui.actionClose.triggered.connect(self.__close)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionOpen.triggered.connect(self.__open)
        self.ui.actionNew_Map.triggered.connect(self.__close)
        self.ui.actionUndo.triggered.connect(self.__undo)
        self.ui.actionRedo.triggered.connect(self.__redo)

        selectionModeActions = {
            SelectionType.Groups: self.ui.actionGroups, SelectionType.Objects: self.ui.actionObjects,
            SelectionType.Faces: self.ui.actionFaces, SelectionType.Vertices: self.ui.actionVertices
        }
        self.selectionModeActions = selectionModeActions
        self.ui.actionGroups.setChecked(True)
        selectionModeGroup = QtWidgets.QActionGroup(self.ui.topBar)
        for mode, action in selectionModeActions.items():
            selectionModeGroup.addAction(action)
            action.toggled.connect(lambda checked, mode=mode: self.__maybeSetSelelectionMode(checked, mode))
        """

        self.accept('actionTriggered', self.__onActionTriggered)

    def __onActionTriggered(self, keybind, checked):
        if keybind == KeyBind.Undo:
            self.__undo()
        elif keybind == KeyBind.Redo:
            self.__redo()

    def __docTabChanged(self, index):
        if base.document:
            base.document.deactivated()

        page = self.docTabs.widget(index)
        page.doc.activated()
        base.document = page.doc

    def __maybeSetSelelectionMode(self, checked, mode):
        if checked:
            base.actionMgr.performAction("Change selection mode", ChangeSelectionMode(mode))

    def __undo(self):
        base.actionMgr.undo()

    def __redo(self):
        base.actionMgr.redo()

    def addDockWindow(self, dockWidget, location = "right"):
        location = self.dockLocations[location]
        dockWidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        self.addDockWidget(location, dockWidget, QtCore.Qt.Vertical)
        return dockWidget

    def addPaneLabel(self, width = 100, text = ""):
        lbl = QtWidgets.QLabel(text)
        lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        lbl.setFrameStyle(QtWidgets.QLabel.Panel)
        lbl.setFrameShadow(QtWidgets.QLabel.Sunken)
        lbl.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        lbl.setMaximumWidth(width)

        self.ui.statusbar.addPermanentWidget(lbl)
        return lbl

    def askSaveIfUnsaved(self):
        if base.document.unsaved:
            msg = QMessageBox(parent = self, icon = QMessageBox.Warning)
            msg.setWindowTitle(LEGlobals.AppName)
            msg.setModal(True)
            msg.setText("Do you want to save changes to '%s' before closing?" % base.document.getMapName())
            msg.setInformativeText("Your changes will be lost if you don't save them.")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Save)

            ret = msg.exec_()

            if ret == QMessageBox.Save:
                return self.__save()
            elif ret == QMessageBox.Cancel:
                return False
            elif ret == QMessageBox.Discard:
                # Not saving the changes
                return True

        return True

    def __close(self, openBlank = True):
        if not self.askSaveIfUnsaved():
            # User decided against closing
            return False
        base.document.close()
        if openBlank:
            # We are never actually without a document.
            # When we close the current document, open a blank one.
            base.document.open()
        return True

    def __save(self):
        if not base.document.filename:
            return self.doSaveAs()

        base.document.save()
        return True

    def __saveAs(self):
        return self.doSaveAs()

    def doSaveAs(self):
        selectedFilename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save As')
        if len(selectedFilename[0]) == 0:
            # Save as was cancelled
            return False
        # Convert to a panda filename
        filename = Filename.fromOsSpecific(selectedFilename[0])
        base.document.save(filename)
        return True

    def __open(self):
        selectedFilename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open', filter=('Panda3D map file (*.pmap)'))
        if len(selectedFilename[0]) == 0:
            # Save as was cancelled
            return False
        # Convert to a panda filename
        filename = Filename.fromOsSpecific(selectedFilename[0])
        # Open it!
        base.openDocument(filename)
        return True

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
        if not self.__close():
            event.ignore()
            return

        event.accept()
        base.running = False

class LevelEditorApp(QtWidgets.QApplication):

    def __init__(self):
        QtWidgets.QApplication.__init__(self, [])

        pixmap = QtGui.QPixmap("resources/icons/foundry-splash.png")
        splash = QtWidgets.QSplashScreen(self.primaryScreen(), pixmap, QtCore.Qt.WindowStaysOnTopHint)
        splash.show()
        self.processEvents()

        self.setWindowIcon(QtGui.QIcon("resources/icons/foundry.ico"))

        style = QtWidgets.QStyleFactory.create("fusion")
        self.setStyle(style)
        accent = QtGui.QColor(255, 134, 59)
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
        dark_palette.setColor(QtGui.QPalette.Link, accent)
        dark_palette.setColor(QtGui.QPalette.Highlight, accent)
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        dark_palette.setColor(QtGui.QPalette.Shadow, QtCore.Qt.black)
        self.setPalette(dark_palette)

        self.window = LevelEditorWindow()
        splash.finish(self.window)
        self.window.show()

class LevelEditor(DirectObject):
    notify = directNotify.newCategory("Foundry")

    def __init__(self):
        DirectObject.__init__(self)

        ###################################################################
        # Minimal emulation of ShowBase glue code. Note we're not using
        # ShowBase because there's too much going on in there that assumes
        # too much (one camera, one lens, one aspect2d, lots of bloat).

        self.graphicsEngine = GraphicsEngine.getGlobalPtr()
        self.pipe = GraphicsPipeSelection.getGlobalPtr().makeDefaultPipe()
        if not self.pipe:
            self.notify.error("No graphics pipe is available!")
            return

        self.taskMgr = taskMgr
        self.eventMgr = eventMgr
        builtins.eventMgr = self.eventMgr

        self.globalClock = ClockObject.getGlobalClock()
        # Since we have already started up a TaskManager, and probably
        # a number of tasks; and since the TaskManager had to use the
        # TrueClock to tell time until this moment, make sure the
        # globalClock object is exactly in sync with the TrueClock.
        trueClock = TrueClock.getGlobalPtr()
        self.globalClock.setRealTime(trueClock.getShortTime())
        self.globalClock.tick()
        builtins.globalClock = self.globalClock

        self.loader = CogInvasionLoader(self)
        self.graphicsEngine.setDefaultLoader(self.loader.loader)
        builtins.loader = self.loader

        self.dgTrav = DataGraphTraverser()

        self.taskMgr.add(self.__gbcLoop, "garbageCollectStates", sort = 46)
        self.taskMgr.add(self.__dataLoop, "dataLoop", sort = -50)
        self.taskMgr.add(self.__igLoop, "igLoop", sort = 50)

        self.dataRoot = NodePath("data")
        self.hidden = NodePath("hidden")

        self.aspect2d = NodePath("aspect2d")
        builtins.aspect2d = self.aspect2d

        self.messenger = messenger
        builtins.messenger = self.messenger

        builtins.base = self
        builtins.taskMgr = self.taskMgr
        builtins.hidden = self.hidden

        self.eventMgr.restart()

        ###################################################################

        self.clickTrav = CollisionTraverser()

        # All open documents.
        self.documents = []
        # The focused document.
        self.document = None

        TextNode.setDefaultFont(loader.loadFont("resources/models/fonts/consolas.ttf"))

        self.initialize()

    def __gbcLoop(self, task):
        TransformState.garbageCollect()
        RenderState.garbageCollect()
        return task.cont

    def __dataLoop(self, task):
        self.dgTrav.traverse(self.dataRoot.node())
        return task.cont

    def __igLoop(self, task):
        self.graphicsEngine.renderFrame()
        throwNewFrame()
        return task.cont

    def openDocument(self, filename):
        doc = Document()
        doc.open(filename)
        self.documents.append(doc)
        base.docTabs.addTab(doc.page, "")
        doc.updateTabText()
        base.docTabs.setCurrentWidget(doc.page)

    def clickTraverse(self, np, handler, travRoot = None):
        self.clickTrav.addCollider(np, handler)
        if not travRoot:
            travRoot = self.render
        self.clickTrav.traverse(travRoot)
        self.clickTrav.removeCollider(np)

    def snapToGrid(self, point):
        if GridSettings.GridSnap:
            return LEUtils.snapToGrid(GridSettings.DefaultStep, point)
        return point

    def initialize(self):
        self.loader.mountMultifiles()
        self.loader.mountMultifile("resources/mod.mf")

        self.fgd = FgdParse('resources/phase_14/etc/cio.fgd')
        self.qtApp = LevelEditorApp()
        self.qtWindow = self.qtApp.window
        self.menuMgr = MenuManager()
        self.menuMgr.addMenuItems()
        ToolManager.addToolActions()
        # Open a blank document
        self.openDocument(None)
        #self.qtApp.window.ui.actionToggleGrid.setChecked(GridSettings.EnableGrid)
        #self.qtApp.window.ui.actionToggleGrid.toggled.connect(self.__toggleGrid)
        ##self.qtApp.window.ui.actionGridSnap.setChecked(GridSettings.GridSnap)
        #self.qtApp.window.ui.actionGridSnap.toggled.connect(self.__gridSnap)
        #self.qtApp.window.ui.actionIncreaseGridSize.triggered.connect(self.__incGridSize)
        #self.qtApp.window.ui.actionDecreaseGridSize.triggered.connect(self.__decGridSize)
        self.adjustGridText()
        self.brushMgr = BrushManager()
        self.modelBrowser = ModelBrowser(None)
        self.materialBrowser = MaterialBrowser(None)

        self.brushMgr.addBrushes()

    def __gridSnap(self):
        GridSettings.GridSnap = not GridSettings.GridSnap
        self.adjustGridText()

    def __toggleGrid(self):
        GridSettings.EnableGrid = not GridSettings.EnableGrid
        self.adjustGridText()

    def __incGridSize(self):
        GridSettings.DefaultStep *= 2
        GridSettings.DefaultStep = min(256, GridSettings.DefaultStep)
        self.adjustGridText()

    def __decGridSize(self):
        GridSettings.DefaultStep //= 2
        GridSettings.DefaultStep = max(1, GridSettings.DefaultStep)
        self.adjustGridText()

    def adjustGridText(self):
        text = "Snap: %s Grid: %i" % ("On" if GridSettings.GridSnap else "Off", GridSettings.DefaultStep)
        self.qtApp.window.gridSnapLabel.setText(text)

    def run(self):
        self.running = True
        while self.running:
            self.qtApp.processEvents()
            self.taskMgr.step()
