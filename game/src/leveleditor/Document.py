from panda3d.core import UniqueIdAllocator, CKeyValues

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.mapobject.World import World
from src.leveleditor.mapobject.Entity import Entity
from src.leveleditor.mapobject import MapObjectFactory
from src.leveleditor.IDGenerator import IDGenerator

models = [
    "models/cogB_robot/cogB_robot.bam",
    "phase_14/models/lawbotOffice/lawbotBookshelf.bam",
    "phase_14/models/lawbotOffice/lawbotTable.bam",
    "models/smiley.egg.pz",
    "phase_14/models/props/creampie.bam",
    "phase_14/models/props/gumballShooter.bam"
]

# Represents the current map that we are working on.
class Document(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.filename = None
        self.unsaved = False
        self.idGenerator = IDGenerator()
        self.world = None
        self.isOpen = False

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
        base.setEditorWindowTitle()

    def close(self):
        if not self.isOpen:
            return

        self.world.delete()
        self.world = None
        self.idGenerator.reset()
        self.filename = None
        self.unsaved = False
        self.isOpen = False

    def __newMap(self):
        self.unsaved = True
        self.idGenerator.reset()
        self.world = World(self.getNextID())
        self.world.generate()
        self.world.reparentTo(base.render)
        self.isOpen = True
        if base.toolMgr.selectTool:
            # Open with the select tool by default
            base.toolMgr.selectTool.toggle()
        base.setEditorWindowTitle()

    def r_open(self, kv, parent = None):
        classDef = MapObjectFactory.MapObjectsByName.get(kv.getName())
        if not classDef:
            return

        id = int(kv.getValue("id"))
        self.reserveID(id)
        obj = classDef(id)
        obj.generate()
        obj.readKeyValues(kv)
        obj.reparentTo(parent)

        if classDef is World:
            self.world = obj

        for i in range(kv.getNumChildren()):
            self.r_open(kv.getChild(i), obj)

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
        # Open with the select tool by default
        base.toolMgr.selectTool.toggle()
        base.setEditorWindowTitle()

    def markSaved(self):
        self.unsaved = False
        base.setEditorWindowTitle()

    def markUnsaved(self):
        self.unsaved = True
        base.setEditorWindowTitle()

    def isUnsaved(self):
        return self.unsaved

    def getMapName(self):
        if not self.filename:
            return "Untitled"
        return self.filename.getBasename()
