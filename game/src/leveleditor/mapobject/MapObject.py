from panda3d.core import NodePath, CollisionBox, CollisionNode, Vec4
from panda3d.core import Point3, CKeyValues

from direct.showbase.DirectObject import DirectObject

from src.leveleditor import LEGlobals

entPropertyExclusions = [
    'classname',
    'id'
]

# Map object aka entity
class MapObject(DirectObject):

    def __init__(self, keyvalues = None):
        self._id = 0
        self.selected = False
        self.classname = ""
        self.parent = None
        self.np = None

        self.modelNp = None

        self.fgd = None
        self.entProperties = {}

        self.collBox = None
        self.collNp = None

        self.boundsVis = None
        self.boundsColor = Vec4(1, 1, 0, 1)

        if keyvalues:
            self.readKeyValues(keyvalues)

        self.setupNode()

    def setClassname(self, classname):
        self.classname = classname
        self.entProperties = {}
        self.fgd = base.fgd.entity_by_name(classname)
        assert self.fgd is not None, "Unknown classname %s" % classname
        
        for prop in self.fgd.schema['properties']:
            if prop['name'] in entPropertyExclusions:
                continue
            self.entProperties[prop['name']] = prop['default_value']

        self.entPropertiesModified()

    def clearModel(self):
        if self.modelNp:
            self.modelNp.removeNode()
        self.modelNp = None

    def setModel(self, path):
        self.clearModel()
        self.modelNp = loader.loadModel(path)
        self.modelNp.reparentTo(self.np)
        self.recalcBounds()

    def entPropertyModified(self, name):
        prop = self.fgd.property_by_name(name)
        data = self.entProperties[name]
        if prop.value_type == 'studio':
            self.setModel(data)
        elif name == 'scale':
            self.np.setScale(CKeyValues.to3f(data))
            self.recalcBounds()

    def entPropertiesModified(self, names = None):
        if names is None:
            names = self.entProperties.keys()

        for name in names:
            self.entPropertyModified(name)

    def recalcBounds(self):
        if self.collNp:
            self.collNp.removeNode()
        if self.boundsVis:
            self.boundsVis.removeNode()

        mins = Point3()
        maxs = Point3()
        self.np.calcTightBounds(mins, maxs)

        self.boundsVis = NodePath(LEGlobals.makeCubeOutline(mins, maxs, self.boundsColor))
        self.boundsVis.setLightOff(1)
        self.boundsVis.setFogOff(1)

        self.collBox = CollisionBox(mins, maxs)
        collNode = CollisionNode('collBox')
        collNode.addSolid(self.collBox)
        self.collNp = self.np.attachNewNode(collNode)
        self.collNp.setCollideMask(LEGlobals.EntityMask)
        self.collNp.setPythonTag("mapobject", self)

    def select(self):
        self.selected = True

        self.recalcBounds()
        self.boundsVis.reparentTo(self.np)

    def deselect(self):
        self.selected = False

        if self.boundsVis:
            self.boundsVis.reparentTo(NodePath())

    def setupNode(self):
        self.np = NodePath("mapobject.%s.%i" % (self.classname, self._id))
        # FIXME
        self.np.reparentTo(base.mapRoot)

    def writeKeyValues(self, keyvalues):
        keyvalues["id"] = str(self._id)
        keyvalues["classname"] = self.classname

    def readKeyValues(self, keyvalues):
        self._id = int(kevalues["id"])
        self.classname = keyvalues["classname"]