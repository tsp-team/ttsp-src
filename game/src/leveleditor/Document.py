from panda3d.core import UniqueIdAllocator, CKeyValues

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.mapobject.World import World
from src.leveleditor.mapobject.Entity import Entity
from src.leveleditor.mapobject.Root import Root
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
        self.idGenerator = None
        self.root = Root()
        self.isOpen = False
        self.objectId2Object = {}
        self.faceId2face = {}

    def createObject(self, classDef, classname = None, id = None, keyValues = None, parent = None):
        obj = classDef()
        if id is None:
            obj.id = self.getNextID()
        else:
            obj.id = id
        obj.generate()
        if keyValues is not None:
            obj.readKeyValues(keyValues)
        obj.announceGenerate()
        if classname is not None:
            obj.setClassname(classname)
        if parent is None:
            parent = self.root
        obj.reparentTo(parent)
        self.objectId2Object[obj.id] = obj
        return obj

    def deleteObject(self, obj):
        self.freeID(obj.id)
        if obj.id in self.objectId2Object:
            del self.objectId2Object[obj.id]
        obj.delete()

    def getNextID(self):
        return self.idGenerator.getNextID()

    def reserveID(self, id):
        self.idGenerator.reserveID(id)

    def freeID(self, id):
        self.idGenerator.freeID(id)

    def getNextFaceID(self):
        return self.idGenerator.getNextFaceID()

    def reserveFaceID(self, id):
        self.idGenerator.reserveFaceID(id)

    def freeFaceID(self, id):
        self.idGenerator.freeFaceID(id)

    def save(self, filename = None):
        # if filename is not none, this is a save-as
        if not filename:
            filename = self.filename

        kv = self.root.doWriteKeyValues()
        kv.write(filename, 4)

        self.filename = filename
        self.unsaved = False
        base.actionMgr.documentSaved()
        base.setEditorWindowTitle()

    def close(self):
        if not self.isOpen:
            return

        self.root.clear()
        self.idGenerator = None
        self.filename = None
        self.unsaved = False
        self.isOpen = False

    def __newMap(self):
        self.unsaved = True
        self.createIDAllocator()
        self.createObject(World)
        self.isOpen = True
        if base.toolMgr.selectTool:
            # Open with the select tool by default
            base.toolMgr.selectTool.toggle()
        base.setEditorWindowTitle()

    def createIDAllocator(self):
        self.idGenerator = IDGenerator()

    def r_open(self, kv, parent = None):
        cls = MapObjectFactory.MapObjectsByName.get(kv.getName())
        if not cls:
            return
        # Give a bogus id so we don't try to allocate an id. The id will be read
        # from the keyvalues
        obj = self.createObject(cls, keyValues = kv, parent = parent, id = -1)
        for i in range(kv.getNumChildren()):
            self.r_open(kv.getChild(i), obj)

        if not parent:
            # Return the root level object (the world)
            return obj

    def open(self, filename = None):
        # if filename is none, this is a new document/map
        if not filename:
            self.__newMap()
            return

        # opening a map from disk, read through the keyvalues and
        # generate the objects
        self.createIDAllocator()
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
