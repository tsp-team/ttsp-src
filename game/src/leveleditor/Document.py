from panda3d.core import UniqueIdAllocator, CKeyValues, NodePath, LightRampAttrib, AsyncTaskManager
from panda3d.bsp import BSPShaderGenerator

import builtins

from direct.showbase.DirectObject import DirectObject
from direct.showbase.Messenger import Messenger
from direct.task.Task import TaskManager
from direct.showbase.EventManager import EventManager

from src.coginvasion.globals import ShaderGlobals

from src.leveleditor.mapobject.World import World
from src.leveleditor.mapobject.Entity import Entity
from src.leveleditor.mapobject import MapObjectFactory
from src.leveleditor.IDGenerator import IDGenerator
from src.leveleditor.viewport.QuadSplitter import QuadSplitter
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.leveleditor.viewport.Viewport3D import Viewport3D
from src.leveleditor.viewport.ViewportType import VIEWPORT_3D, VIEWPORT_2D_FRONT, VIEWPORT_2D_SIDE, VIEWPORT_2D_TOP
from src.leveleditor.selection.SelectionManager import SelectionManager
from src.leveleditor.viewport.ViewportManager import ViewportManager
from src.leveleditor.actions.ActionManager import ActionManager
from src.leveleditor.tools.ToolManager import ToolManager

from PyQt5 import QtWidgets

models = [
    "models/cogB_robot/cogB_robot.bam",
    "phase_14/models/lawbotOffice/lawbotBookshelf.bam",
    "phase_14/models/lawbotOffice/lawbotTable.bam",
    "models/smiley.egg.pz",
    "phase_14/models/props/creampie.bam",
    "phase_14/models/props/gumballShooter.bam"
]

class DocumentWidget(QtWidgets.QWidget):

    QuadArrangement = {
        VIEWPORT_3D: (0, 0),
        VIEWPORT_2D_FRONT: (1, 0),
        VIEWPORT_2D_SIDE: (1, 1),
        VIEWPORT_2D_TOP: (0, 1)
    }

    def __init__(self, doc, win):
        self.doc = doc
        self.win = win
        QtWidgets.QWidget.__init__(self, win)
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.viewports = {}
        self.splitter = QuadSplitter(self)

        vp3d = Viewport3D(VIEWPORT_3D, self.splitter, self.doc)
        self.addViewport(vp3d)
        self.doc.gsg = vp3d.win.getGsg()
        vp2df = Viewport2D(VIEWPORT_2D_FRONT, self.splitter, self.doc)
        self.addViewport(vp2df)
        self.doc.gsg2D = vp2df.win.getGsg()
        self.addViewport(Viewport2D(VIEWPORT_2D_SIDE, self.splitter, self.doc))
        self.addViewport(Viewport2D(VIEWPORT_2D_TOP, self.splitter, self.doc))

        self.arrangeInQuadLayout()

    def arrangeInQuadLayout(self):
        for vpType, xy in self.QuadArrangement.items():
            vp = self.viewports[vpType]
            vp.enable()
            self.layout().removeWidget(vp)
            self.splitter.addWidget(vp, *xy)

        self.layout().addWidget(self.splitter)
        self.splitter.setParent(self)

    def focusOnViewport(self, type):
        for vp in self.viewports.values():
            vp.disable()
            self.layout().removeWidget(vp)
            vp.setParent(None)

        vp = self.viewports[type]
        vp.enable()
        vp.setParent(self)
        self.layout().addWidget(vp)

        self.layout().removeWidget(self.splitter)
        self.splitter.setParent(None)

    def cleanup(self):
        self.doc = None
        self.win = None
        self.viewports = None
        self.splitter.cleanup()
        self.splitter = None
        self.viewports = None
        self.deleteLater()

    def addViewport(self, vp):
        vp.initialize()
        self.viewports[vp.type] = vp

class DocumentWindow(QtWidgets.QMdiSubWindow):

    def __init__(self, doc):
        QtWidgets.QMdiSubWindow.__init__(self, base.docArea)
        self.doc = doc
        self.docWidget = DocumentWidget(doc, self)
        self.setWidget(self.docWidget)

    def arrangeInQuadLayout(self):
        self.docWidget.arrangeInQuadLayout()

    def focusOnViewport(self, vp):
        self.docWidget.focusOnViewport(vp)

    def closeEvent(self, event):
        if not base.reqCloseDocument(self.doc):
            event.ignore()
            return

    def cleanup(self):
        self.docWidget.cleanup()
        self.docWidget = None
        self.doc = None
        self.deleteLater()

# Represents a single map document we have open.
class Document(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.filename = None
        self.unsaved = False
        self.idGenerator = IDGenerator()
        self.world = None
        self.isOpen = False
        self.gsg = None
        self.gsg2D = None
        self.shaderGenerators = []

        self.numlights = 0

        # Each document has its own message bus, task manager, and event manager.
        self.taskMgr = TaskManager()
        self.taskMgr.mgr = AsyncTaskManager("documentTaskMgr")
        self.messenger = Messenger(self.taskMgr)
        self.eventMgr = EventManager(messenger = self.messenger, taskMgr = self.taskMgr)
        self.messenger.setEventMgr(self.eventMgr)

        self.render = NodePath("docRender")
        self.render.setAttrib(LightRampAttrib.makeIdentity())
        self.render.setShaderAuto()

        self.viewportMgr = ViewportManager(self)
        self.toolMgr = ToolManager(self)
        self.selectionMgr = SelectionManager(self)
        self.actionMgr = ActionManager(self)

        # Create the page that the document is viewed in.
        self.page = DocumentWindow(self)
        self.createShaderGenerator()

        self.toolMgr.addTools()

        self.eventMgr.restart()

    def step(self):
        #print("Stepping", self)
        self.taskMgr.step()

    # Called when the document's tab has been switched into.
    def activated(self):
        # Move document constructs into global space so we don't have to directly
        # reference the document for them.
        base.render = self.render
        base.viewportMgr = self.viewportMgr
        base.toolMgr = self.toolMgr
        base.selectionMgr = self.selectionMgr
        base.actionMgr = self.actionMgr
        builtins.render = self.render

        messenger.send('documentActivated', [self])

    # Called when the document's tab has been switched out of.
    def deactivated(self):
        messenger.send('documentDeactivated', [self])

    def getNextID(self):
        return self.idGenerator.getNextID()

    def reserveID(self, id):
        self.idGenerator.reserveID(id)

    def getNextFaceID(self):
        return self.idGenerator.getNextFaceID()

    def reserveFaceID(self, id):
        self.idGenerator.reserveFaceID(id)

    def save(self, filename = None):
        # if filename is not none, this is a save-as
        if not filename:
            filename = self.filename

        kv = CKeyValues()
        self.world.doWriteKeyValues(kv)
        kv.write(filename, 4)

        self.filename = filename
        self.unsaved = False
        base.actionMgr.documentSaved()
        self.updateTabText()

    def close(self):
        if not self.isOpen:
            return

        self.toolMgr.cleanup()
        self.toolMgr = None

        self.world.delete()
        self.world = None
        self.idGenerator.cleanup()
        self.idGenerator = None
        self.filename = None
        self.unsaved = None
        self.isOpen = None
        self.gsg = None
        self.gsg2D = None
        self.shaderGenerators = None

        self.viewportMgr.cleanup()
        self.viewportMgr = None
        self.actionMgr.cleanup()
        self.actionMgr = None
        self.selectionMgr.cleanup()
        self.selectionMgr = None

        self.eventMgr.shutdown()
        self.eventMgr = None
        self.messenger = None
        self.taskMgr.destroy()
        self.taskMgr = None

        self.render.removeNode()
        self.render = None

        self.page.cleanup()
        self.page = None

    def __newMap(self):
        self.unsaved = False
        self.idGenerator.reset()
        self.world = World(self.getNextID())
        self.world.reparentTo(self.render)
        self.isOpen = True
        self.toolMgr.switchToSelectTool()
        self.updateTabText()

    def updateTabText(self):
        title = self.getMapTitle()
        self.page.setWindowTitle(title)
        base.setWindowSubTitle(title)

    def r_open(self, kv, parent = None):
        classDef = MapObjectFactory.MapObjectsByName.get(kv.getName())
        if not classDef:
            return
        id = int(kv.getValue("id"))
        self.reserveID(id)
        obj = classDef(id)
        obj.readKeyValues(kv)
        obj.reparentTo(parent)

        if classDef is World:
            self.world = obj

        for i in range(kv.getNumChildren()):
            self.r_open(kv.getChild(i), obj)

    def getViewport(self, type):
        return self.page.docWidget.viewports[type]

    def createShaderGenerator(self):
        for gsg, vp in [(self.gsg, self.getViewport(VIEWPORT_3D)), (self.gsg2D, self.getViewport(VIEWPORT_2D_FRONT))]:
            shgen = BSPShaderGenerator(vp.win, gsg, vp.camera, self.render)
            gsg.setShaderGenerator(shgen)
            for shader in ShaderGlobals.getShaders():
                shgen.addShader(shader)
            self.shaderGenerators.append(shgen)

    def open(self, filename = None):
        # if filename is none, this is a new document/map
        if not filename:
            self.__newMap()
            return

        # opening a map from disk, read through the keyvalues and
        # generate the objects
        self.idGenerator.reset()
        root = CKeyValues.load(filename)
        for i in range(root.getNumChildren()):
            self.r_open(root.getChild(i))
        self.unsaved = False
        self.filename = filename
        self.isOpen = True
        self.toolMgr.switchToSelectTool()
        self.updateTabText()

    def markSaved(self):
        self.unsaved = False
        self.updateTabText()

    def markUnsaved(self):
        self.unsaved = True
        self.updateTabText()

    def isUnsaved(self):
        return self.unsaved

    def getMapName(self):
        if not self.filename:
            return "Untitled"
        return self.filename.getBasename()

    def getMapTitle(self):
        name = self.getMapName()
        if self.unsaved:
            name += " *"
        return name

    def updateAllViews(self, now = False):
        for vp in self.viewportMgr.viewports:
            vp.updateView(now)

    def update2DViews(self, now = False):
        for vp in self.viewportMgr.viewports:
            if vp.is2D():
                vp.updateView(now)

    def update3DViews(self, now = False):
        for vp in self.viewportMgr.viewports:
            if vp.is3D():
                vp.updateView(now)
