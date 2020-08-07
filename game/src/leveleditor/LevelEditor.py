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
from src.leveleditor.menu import KeyBinds

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
from src.leveleditor.fgdtools import FgdParse, FgdWrite

import builtins
import time

stylesheet = """

QPushButton:hover {
    background-color: rgb(204, 91, 12);
    color: rgb(25, 25, 25);
    border-color: rgb(255, 134, 59);
}

QToolButton:hover {
    background-color: rgb(204, 91, 12);
    color: rgb(25, 25, 25);
    border-color: rgb(255, 134, 59);
}

QToolButton:checked {
    background-color: rgb(204, 91, 12);
    color: rgb(25, 25, 25);
    border-color: rgb(255, 134, 59);
}

"""

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
        self.docTabs.tabCloseRequested.connect(self.__reqClose)

    def __reqClose(self, index):
        doc = self.docTabs.widget(index).doc
        self.__close(doc)

    def initialize(self):
        base.menuMgr.connect(KeyBind.FileNew, self.__new)
        base.menuMgr.connect(KeyBind.FileOpen, self.__open)
        base.menuMgr.connect(KeyBind.FileClose, self.__close)
        base.menuMgr.connect(KeyBind.FileSave, self.__save)
        base.menuMgr.connect(KeyBind.FileSaveAll, self.__saveAll)
        base.menuMgr.connect(KeyBind.FileSaveAs, self.__saveAs)
        base.menuMgr.connect(KeyBind.FileCloseAll, self.__closeAll)
        base.menuMgr.connect(KeyBind.Undo, self.__undo)
        base.menuMgr.connect(KeyBind.Redo, self.__redo)

    def __new(self):
        base.openDocument(None)

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

    def __closeAll(self):
        for doc in base.documents:
            if not self.__close(doc):
                return False

        return True

    def __close(self, doc = None):
        if not doc:
            doc = base.document

        if not self.askSaveIfUnsaved(doc):
            # User decided against closing
            return False
        base.closeDocument(doc)
        return True

    def __docTabChanged(self, index):
        if base.document:
            base.document.deactivated()
        base.document = None

        page = self.docTabs.widget(index)
        if not page:
            return
        page.doc.activated()
        base.document = page.doc

    def __maybeSetSelelectionMode(self, checked, mode):
        if checked:
            base.actionMgr.performAction("Change selection mode", ChangeSelectionMode(mode))

    def __undo(self):
        base.actionMgr.undo()

    def __redo(self):
        base.actionMgr.redo()

    def addDockWindow(self, dockWidget, location = "left"):
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

    def askSaveIfUnsaved(self, doc):
        if doc.unsaved:
            msg = QMessageBox(parent = self, icon = QMessageBox.Warning)
            msg.setWindowTitle(LEGlobals.AppName)
            msg.setModal(True)
            msg.setText("Do you want to save changes to '%s' before closing?" % doc.getMapName())
            msg.setInformativeText("Your changes will be lost if you don't save them.")
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Save)

            ret = msg.exec_()

            if ret == QMessageBox.Save:
                return self.__save(doc)
            elif ret == QMessageBox.Cancel:
                return False
            elif ret == QMessageBox.Discard:
                # Not saving the changes
                return True

        return True

    def __save(self, doc = None):
        if not doc:
            doc = base.document

        if not doc.filename:
            return self.doSaveAs(doc)

        doc.save()
        return True

    def __saveAll(self):
        for doc in base.documents:
            if not self.__save(doc):
                return False

        return True

    def __saveAs(self, doc = None):
        if not doc:
            doc = base.document
        return self.doSaveAs(doc)

    def doSaveAs(self, doc):
        selectedFilename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save As')
        if len(selectedFilename[0]) == 0:
            # Save as was cancelled
            return False
        # Convert to a panda filename
        filename = Filename.fromOsSpecific(selectedFilename[0])
        doc.save(filename)
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
        if not self.__closeAll():
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

        self.setStyle("Fusion")

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(103, 103, 103))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(86, 86, 86))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(46, 46, 46))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(46, 46, 46))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(27, 27, 27))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 134, 59))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 134, 59))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Link, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(103, 103, 103))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(86, 86, 86))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(46, 46, 46))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(46, 46, 46))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(27, 27, 27))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 134, 59))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.HighlightedText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 134, 59))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Link, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Button, brush)
        brush = QtGui.QBrush(QtGui.QColor(103, 103, 103))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Light, brush)
        brush = QtGui.QBrush(QtGui.QColor(86, 86, 86))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Midlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Dark, brush)
        brush = QtGui.QBrush(QtGui.QColor(46, 46, 46))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Mid, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.BrightText, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(27, 27, 27))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Shadow, brush)
        brush = QtGui.QBrush(QtGui.QColor(189, 189, 189))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, brush)
        brush = QtGui.QBrush(QtGui.QColor(34, 34, 34))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 134, 59))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Link, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 69, 69))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.AlternateBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 220))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipBase, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ToolTipText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        self.setPalette(palette)

        self.setStyleSheet(stylesheet)

        self.window = LevelEditorWindow()
        splash.finish(self.window)
        self.window.show()

class LevelEditor(DirectObject):
    notify = directNotify.newCategory("Foundry")

    DocActions = [
        KeyBind.FileSave,
        KeyBind.FileSaveAll,
        KeyBind.FileSaveAs,
        KeyBind.FileClose,
        KeyBind.FileCloseAll,
        KeyBind.Undo,
        KeyBind.Redo,
        KeyBind.ViewQuads,
        KeyBind.View3D,
        KeyBind.ViewXY,
        KeyBind.ViewYZ,
        KeyBind.ViewXZ,
        KeyBind.Toggle2DGrid,
        KeyBind.Toggle3DGrid,
        KeyBind.ToggleGridSnap,
        KeyBind.IncGridSize,
        KeyBind.DecGridSize
    ]

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

        self.taskMgr = taskMgr
        builtins.taskMgr = self.taskMgr

        self.dgTrav = DataGraphTraverser()

        self.dataRoot = NodePath("data")
        self.hidden = NodePath("hidden")

        self.aspect2d = NodePath("aspect2d")
        builtins.aspect2d = self.aspect2d

        # Messages that are sent regardless of the active document.
        self.messenger = messenger
        builtins.messenger = self.messenger

        builtins.base = self
        builtins.hidden = self.hidden

        ###################################################################

        self.clickTrav = CollisionTraverser()

        # All open documents.
        self.documents = []
        # The focused document.
        self.document = None

        TextNode.setDefaultFont(loader.loadFont("resources/models/fonts/consolas.ttf"))

        self.initialize()

    def __docLoop(self):
        if self.document:
            self.document.step()

    def __gbcLoop(self):
        TransformState.garbageCollect()
        RenderState.garbageCollect()

    def __dataLoop(self):
        self.dgTrav.traverse(self.dataRoot.node())

    def __igLoop(self):
        self.graphicsEngine.renderFrame()
        throwNewFrame()

    def openDocument(self, filename):
        doc = Document()
        self.documents.append(doc)
        base.docTabs.addTab(doc.page, "")
        base.docTabs.setCurrentWidget(doc.page)
        doc.open(filename)
        doc.updateTabText()

        if len(self.documents) == 1:
            self.enableDocActions()

    def closeDocument(self, doc):
        self.docTabs.removeTab(self.docTabs.indexOf(doc.page))
        doc.close()
        self.documents.remove(doc)
        if len(self.documents) == 0:
            self.disableDocActions()

    def enableDocActions(self):
        for act in self.DocActions:
            self.menuMgr.enableAction(act)

    def disableDocActions(self):
        for act in self.DocActions:
            self.menuMgr.disableAction(act)

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
        SelectionManager.addModeActions()
        self.qtWindow.initialize()
        # Open a blank document
        #self.openDocument(None)
        self.adjustGridText()
        self.brushMgr = BrushManager()
        self.modelBrowser = ModelBrowser(None)
        self.materialBrowser = MaterialBrowser(None)

        self.menuMgr.connect(KeyBind.ToggleGridSnap, self.__gridSnap)
        self.menuMgr.connect(KeyBind.IncGridSize, self.__incGridSize)
        self.menuMgr.connect(KeyBind.DecGridSize, self.__decGridSize)
        self.menuMgr.connect(KeyBind.Toggle2DGrid, self.__toggleGrid)
        self.menuMgr.connect(KeyBind.Toggle3DGrid, self.__toggleGrid3D)
        self.menuMgr.connect(KeyBind.ViewQuads, self.__viewQuads)
        self.menuMgr.connect(KeyBind.View3D, self.__view3D)
        self.menuMgr.connect(KeyBind.ViewXY, self.__viewXY)
        self.menuMgr.connect(KeyBind.ViewXZ, self.__viewXZ)
        self.menuMgr.connect(KeyBind.ViewYZ, self.__viewYZ)

        self.menuMgr.action(KeyBind.ToggleGridSnap).setChecked(GridSettings.GridSnap)
        self.menuMgr.action(KeyBind.Toggle2DGrid).setChecked(GridSettings.EnableGrid)
        self.menuMgr.action(KeyBind.Toggle3DGrid).setChecked(GridSettings.EnableGrid3D)

        self.brushMgr.addBrushes()

    def __viewQuads(self):
        self.document.page.arrangeInQuadLayout()

    def __view3D(self):
        self.document.page.focusOnViewport(VIEWPORT_3D)

    def __viewXY(self):
        self.document.page.focusOnViewport(VIEWPORT_2D_TOP)

    def __viewYZ(self):
        self.document.page.focusOnViewport(VIEWPORT_2D_SIDE)

    def __viewXZ(self):
        self.document.page.focusOnViewport(VIEWPORT_2D_FRONT)

    def __gridSnap(self):
        GridSettings.GridSnap = not GridSettings.GridSnap
        self.adjustGridText()

    def __toggleGrid(self):
        GridSettings.EnableGrid = not GridSettings.EnableGrid
        self.adjustGridText()

    def __toggleGrid3D(self):
        GridSettings.EnableGrid3D = not GridSettings.EnableGrid3D
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
            self.__gbcLoop()
            self.__dataLoop()
            self.__docLoop()
            self.taskMgr.step()
            self.__igLoop()
