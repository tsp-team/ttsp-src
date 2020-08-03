from panda3d.core import UniqueIdAllocator, CKeyValues, NodePath

import builtins

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.mapobject.World import World
from src.leveleditor.mapobject.Entity import Entity
from src.leveleditor.mapobject import MapObjectFactory
from src.leveleditor.IDGenerator import IDGenerator
from src.leveleditor.viewport.QuadSplitter import QuadSplitter
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.leveleditor.viewport.Viewport3D import Viewport3D
from src.leveleditor.viewport.ViewportType import VIEWPORT_3D, VIEWPORT_2D_FRONT, VIEWPORT_2D_SIDE, VIEWPORT_2D_TOP

from PyQt5 import QtWidgets

models = [
    "models/cogB_robot/cogB_robot.bam",
    "phase_14/models/lawbotOffice/lawbotBookshelf.bam",
    "phase_14/models/lawbotOffice/lawbotTable.bam",
    "models/smiley.egg.pz",
    "phase_14/models/props/creampie.bam",
    "phase_14/models/props/gumballShooter.bam"
]

class DocumentPage(QtWidgets.QWidget):

    def __init__(self, doc):
        self.doc = doc
        QtWidgets.QWidget.__init__(self)
        base.docTabs.addTab(self, "document")
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.viewports = {}
        self.splitter = QuadSplitter(self)

        self.addViewport(Viewport3D(VIEWPORT_3D, self.splitter, self.doc), 0, 0)
        self.addViewport(Viewport2D(VIEWPORT_2D_FRONT, self.splitter, self.doc), 1, 0)
        self.addViewport(Viewport2D(VIEWPORT_2D_SIDE, self.splitter, self.doc), 1, 1)
        self.addViewport(Viewport2D(VIEWPORT_2D_TOP, self.splitter, self.doc), 0, 1)

        self.layout().addWidget(self.splitter)

    def addViewport(self, vp, row, col):
        vp.initialize()
        self.splitter.addWidget(vp, row, col)
        self.viewports[vp.type] = vp

# Represents the current map that we are working on.
class Document(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.filename = None
        self.unsaved = False
        self.idGenerator = IDGenerator()
        self.world = None
        self.isOpen = False
        self.page = None

    # Called when the document's tab has been switched into.
    def activated(self):
        base.render = self.render
        builtins.render = self.render

    # Called when the document's tab has been switched out of.
    def deactivated(self):
        pass

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

    def close(self):
        if not self.isOpen:
            return

        self.world.delete()
        self.world = None
        self.idGenerator.cleanup()
        self.idGenerator = None
        self.filename = None
        self.unsaved = None
        self.isOpen = None

    def __newMap(self):
        self.unsaved = False
        self.idGenerator.reset()
        self.world = World(self.getNextID())
        self.world.reparentTo(self.render)
        self.isOpen = True
        if base.toolMgr.selectTool:
            # Open with the select tool by default
            base.toolMgr.selectTool.toggle()
        self.updateTabText()

    def updateTabText(self):
        name = self.getMapName()
        if self.unsaved:
            name = "* " + name
        base.docTabs.setTabText(base.docTabs.indexOf(self.page), name)

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

    def open(self, filename = None):
        self.render = NodePath("docRender")
        # Create the page that the document is viewed in.
        self.page = DocumentPage(self)

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
        # Open with the select tool by default
        base.toolMgr.selectTool.toggle()
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
