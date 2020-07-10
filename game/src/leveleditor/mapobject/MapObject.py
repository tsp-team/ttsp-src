from panda3d.core import NodePath, CollisionBox, CollisionNode, Vec4, ModelNode, BoundingBox, Vec3
from panda3d.core import Point3, CKeyValues, BitMask32, RenderState, ColorAttrib

from .MapWritable import MapWritable
from src.leveleditor import LEGlobals

from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK

BoundsBox3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

BoundsBox2DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 0, 0, 1))
)

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
        self.boundsBox = Box()
        self.boundsBox.addView(GeomView.Lines, VIEWPORT_3D_MASK, state = BoundsBox3DState)
        self.boundsBox.addView(GeomView.Lines, VIEWPORT_2D_MASK, state = BoundsBox2DState)
        self.boundsBox.generateGeometry()
        self.collNp = None

    def showBoundingBox(self):
        self.boundsBox.np.reparentTo(self.np)

    def hideBoundingBox(self):
        self.boundsBox.np.reparentTo(NodePath())

    def select(self):
        self.selected = True
        self.showBoundingBox()
        #self.np.setColorScale(1, 0, 0, 1)

    def deselect(self):
        self.selected = False
        self.hideBoundingBox()
        #self.np.setColorScale(1, 1, 1, 1)

    def setClassname(self, classname):
        self.classname = classname

    def fixBounds(self, mins, maxs):
        # Ensures that the bounds are not flat on any axis
        sameX = mins.x == maxs.x
        sameY = mins.y == maxs.y
        sameZ = mins.z == maxs.z

        invalid = False

        if sameX:
            # Flat horizontal
            if sameY and sameZ:
                invalid = True
            elif not sameY:
                mins.x = mins.y
                maxs.x = maxs.y
            elif not sameZ:
                mins.x = mins.z
                maxs.x = maxs.z

        if sameY:
            # Flat forward/back
            if sameX and sameZ:
                invalid = True
            elif not sameX:
                mins.y = mins.x
                maxs.y = maxs.x
            elif not sameZ:
                mins.y = mins.z
                maxs.y = maxs.z

        if sameZ:
            if sameX and sameY:
                invalid = True
            elif not sameX:
                mins.z = mins.x
                maxs.z = maxs.x
            elif not sameY:
                mins.z = mins.y
                maxs.z = maxs.y

        return [invalid, mins, maxs]

    def recalcBoundingBox(self):
        if not self.np:
            return

        # Don't have the picker box or selection visualization contribute to the
        # calculation of the bounding box.
        if self.collNp:
            self.collNp.stash()
        self.hideBoundingBox()

        # Calculate a bounding box relative to ourself
        mins = Point3()
        maxs = Point3()
        self.np.calcTightBounds(mins, maxs, self.np)

        invalid, mins, maxs = self.fixBounds(mins, maxs)
        if invalid:
            mins = Point3(-8)
            maxs = Point3(8)

        self.boundingBox = BoundingBox(mins, maxs)
        self.boundsBox.setMinMax(mins, maxs)
        if self.selected:
            self.showBoundingBox()
            base.selectionMgr.updateSelectionBounds()

        if self.collNp:
            self.collNp.unstash()
            self.collNp.node().clearSolids()
            self.collNp.node().addSolid(CollisionBox(mins, maxs))
            self.collNp.hide(~VIEWPORT_3D_MASK)

    def removePickBox(self):
        if self.collNp:
            self.collNp.removeNode()
            self.collNp = None

    # Called when the object first comes into existence, before the
    # keyvalues are read
    def generate(self):
        self.np = NodePath(ModelNode("mapobject_unknown"))
        self.np.setPythonTag("mapobject", self)
        self.collNp = self.np.attachNewNode(CollisionNode("pickBox"))
        self.collNp.node().setIntoCollideMask(LEGlobals.EntityMask)
        self.collNp.node().setFromCollideMask(BitMask32.allOff())
        #self.collNp.show()

    # Called after the keyvalues have been read for this object
    def announceGenerate(self):
        self.np.setName("mapobject_%s.%i" % (self.classname, self.id))

    def delete(self):
        # Take the children with us
        for child in self.children:
            base.document.deleteObject(child)
        self.children = None

        # if we are selected, deselect
        base.selectionMgr.deselect(self)

        if self.boundsBox:
            self.boundsBox.cleanup()
            self.boundsBox = None

        self.removePickBox()

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
        self.id = int(keyvalues.getValue("id"))
        base.document.reserveID(self.id)
        self.classname = keyvalues.getValue("classname")
