from panda3d.core import NodePath, CollisionBox, CollisionNode, Vec4, ModelNode, BoundingBox, Vec3
from panda3d.core import Point3, CKeyValues

from .MapWritable import MapWritable
from src.leveleditor import LEGlobals

# Base class for any object in the map (brush, entity, etc)
class MapObject(MapWritable):

    ObjectName = "object"

    def __init__(self):
        MapWritable.__init__(self)
        self.id = None
        self.selected = False
        self.classname = ""
        self.parent = None
        self.children = []
        self.np = None
        self.boundingBox = BoundingBox(Vec3(-0.5, -0.5, -0.5), Vec3(0.5, 0.5, 0.5))

    def setClassname(self, classname):
        self.classname = classname

    def recalcBoundingBox(self):
        mins = Point3()
        maxs = Point3()
        self.np.calcTightBounds(mins, maxs)
        self.boundingBox = BoundingBox(mins, maxs)

    # Called when the object first comes into existence, before the
    # keyvalues are read
    def generate(self):
        self.np = NodePath(ModelNode("mapobject_unknown"))
        self.np.setPythonTag("mapobject", self)

    # Called after the keyvalues have been read for this object
    def announceGenerate(self):
        self.np.setName("mapobject_%s.%i" % (self.classname, self.id))

    def delete(self):
        # Take the children with us
        for child in self.children:
            base.document.deleteObject(child)
        self.children = None

        self.reparentTo(None)
        self.np.removeNode()
        self.np = None
        self.entityData = None
        self.metaData = None

    def __clearParent(self):
        if self.parent:
            self.parent.__removeChild(self)
            self.np.reparentTo(NodePath())
            self.parent = None

    def __setParent(self, other):
        self.parent = other
        if self.parent:
            self.parent.__addChild(self)
            self.np.reparentTo(self.parent.np)

    def reparentTo(self, other):
        self.__clearParent()
        self.__setParent(other)

    def __addChild(self, child):
        if not child in self.children:
            self.children.append(child)
            self.recalcBoundingBox()

    def __removeChild(self, child):
        if child in self.children:
            self.children.remove(child)
            self.recalcBoundingBox()

    def doWriteKeyValues(self, parent):
        kv = CKeyValues(self.ObjectName, parent)
        self.writeKeyValues(kv)
        for child in self.children:
            child.doWriteKeyValues(kv)

    def writeKeyValues(self, keyvalues):
        keyvalues.setKeyValue("id", str(self.id))
        keyvalues.setKeyValue("classname", self.classname)

    def readKeyValues(self, keyvalues):
        self.id = int(keyvalues.getKeyValue("id"))
        self.classname = keyvalues.getKeyValue("classname")
