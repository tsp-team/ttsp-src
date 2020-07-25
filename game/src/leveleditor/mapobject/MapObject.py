from panda3d.core import NodePath, CollisionBox, CollisionNode, Vec4, ModelNode, BoundingBox, Vec3
from panda3d.core import Point3, CKeyValues, BitMask32, RenderState, ColorAttrib, CullBinAttrib

from .MapWritable import MapWritable
from src.leveleditor import LEGlobals
from .TransformProperties import OriginProperty, AnglesProperty, ScaleProperty, ShearProperty
from . import MetaData
from .ObjectProperty import ObjectProperty

from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK

BoundsBox3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

BoundsBox2DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 0, 0, 1)),
    CullBinAttrib.make("selected-foreground", 0)
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
        self.children = {}
        self.np = None
        self.boundingBox = BoundingBox(Vec3(-0.5, -0.5, -0.5), Vec3(0.5, 0.5, 0.5))
        self.boundsBox = Box()
        self.boundsBox.addView(GeomView.Lines, VIEWPORT_3D_MASK, state = BoundsBox3DState)
        self.boundsBox.addView(GeomView.Lines, VIEWPORT_2D_MASK, state = BoundsBox2DState)
        self.boundsBox.generateGeometry()
        self.collNp = None

        # Things we need to keep track of when we're stashed.
        self.originalParentId = None
        self.stashed = False
        self.wasSelected = False

        self.properties = {}

        # All MapObjects have transform
        self.addProperty(OriginProperty(self))
        self.addProperty(AnglesProperty(self))
        self.addProperty(ScaleProperty(self))
        self.addProperty(ShearProperty(self))

    # Detaches the object from the scene graph and frees
    # the ID. The object is not actually gone from memory, so it can
    # be restored later.
    def stash(self):
        if self.stashed:
            return

        if self.id is not None:
            base.document.freeID(self.id)
        if self.parent:
            self.originalParentId = self.parent.id
        else:
            self.originalParentId = None
        self.reparentTo(None)

        self.wasSelected = self.selected
        base.selectionMgr.deselect(self)

        self.stashed = True

        for child in self.children.values():
            child.stash()

    # Reattaches the object to the scene graph and reserves
    # the ID.
    def unstash(self):
        if not self.stashed:
            return

        if self.id is not None:
            base.document.reserveID(self.id)
        if self.originalParentId is None:
            self.reparentTo(base.document.root)
        else:
            self.reparentTo(base.document.objectId2object[self.originalParentId])
        self.originalParentId = None
        self.stashed = False

        if self.wasSelected:
            base.selectionMgr.select(self)

        for child in self.children.values():
            child.unstash()

    def hasChildWithID(self, id):
        return id in self.children

    def copy(self, generator):
        raise NotImplementedError

    def paste(self, o, generator):
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

    def unclone(self, o):
        raise NotImplementedError

    #
    # Base copy and paste functions shared by all MapObjects.
    # Each specific MapObject must implement the functions above for their
    # specific functionality.
    #

    def copyProperties(self, props):
        newProps = {}
        for key, prop in props.items():
            newProp = prop.clone(self)
            newProps[key] = newProp
        self.updateProperties(newProps)

    def copyBase(self, other, generator, clone = False):
        if clone and other.id != self.id:
            parent = other.parent
            setPar = other.parent is not None and other.parent.hasChildWithID(other.id) and other.parent.children[other.id] == other
            if setPar:
                other.reparentTo(None)
            other.id = self.id
            if setPar:
                other.reparentTo(parent)
        else:
            other.reparentTo(self.parent)

        for child in self.children.values():
            if clone:
                newChild = child.clone()
            else:
                newChild = child.copy(generator)
            newChild.reparentTo(other)

        other.setClassname(self.classname)
        other.copyProperties(self.properties)
        other.selected = self.selected

    def pasteBase(self, o, generator, performUnclone = False):
        if performUnclone and o.id != self.id:
            parent = self.parent
            setPar = self.parent is not None and self.parent.hasChildWithID(self.id) and self.parent.children[self.id] == self
            if setPar:
                self.reparentTo(None)
            self.id = o.id
            if setPar:
                self.reparentTo(parent)

        for child in o.children.values():
            if performUnclone:
                newChild = child.clone()
            else:
                newChild = child.copy(generator)
            newChild.reparentTo(self)

        self.setClassname(o.classname)
        self.copyProperties(o.properties)
        self.selected = o.selected

    def getName(self):
        return "Object"

    def getDescription(self):
        return "Object in a map."

    def addProperty(self, prop):
        self.properties[prop.name] = prop

    # Returns list of property names with the specified value types.
    def getPropsWithValueType(self, types):
        if isinstance(types, str):
            types = [types]
        props = []
        for propName, prop in self.properties.items():
            if prop.valueType in types:
                props.append(propName)
        return props

    def getPropNativeType(self, key):
        prop = self.properties.get(key, None)
        if not prop:
            return str

        return prop.getNativeType()

    def getPropValueType(self, key):
        prop = self.properties.get(key, None)
        if not prop:
            return "string"

        return prop.valueType

    def getPropDefaultValue(self, prop):
        if isinstance(prop, str):
            prop = self.properties.get(prop, None)

        if not prop:
            return ""

        return prop.defaultValue

    def getPropertyValue(self, key, asString = False, default = ""):
        prop = self.properties.get(key, None)
        if not prop:
            return default

        if asString:
            return prop.getSerializedValue()
        else:
            return prop.getValue()

    def getProperty(self, name):
        return self.properties.get(name, None)

    def updateProperties(self, data):
        for key, value in data.items():
            if not isinstance(value, ObjectProperty):
                # If only a value was specified and not a property object itself,
                # this is an update to an existing property.

                prop = self.properties.get(key, None)
                if not prop:
                    continue

                oldValue = prop.getValue()

                val = prop.getUnserializedValue(value)

                # If the property has a min/max range, ensure the value we want to
                # set is within that range.
                if (not prop.testMinValue(val)) or (not prop.testMaxValue(val)):
                    # Not within range. Use the default value
                    val = prop.defaultValue

                prop.setValue(val)
            else:
                # A property object was given, simply add it to the dict of properties.
                prop = value
                oldValue = prop.getValue()
                val = prop.getValue()
                self.properties[prop.name] = prop

            self.propertyChanged(prop, oldValue, val)

    def propertyChanged(self, prop, oldValue, newValue):
        if oldValue != newValue:
            messenger.send('objectPropertyChanged', [self, prop, newValue])

    def setAbsOrigin(self, origin):
        self.np.setPos(base.render, origin)
        self.transformChanged()

    def setOrigin(self, origin):
        self.np.setPos(origin)
        self.transformChanged()

    def getAbsOrigin(self):
        return self.np.getPos(base.render)

    def getOrigin(self):
        return self.np.getPos()

    def setAngles(self, angles):
        self.np.setHpr(angles)
        self.transformChanged()

    def setAbsAngles(self, angles):
        self.np.setHpr(base.render, angles)
        self.transformChanged()

    def getAbsAngles(self):
        return self.np.getHpr(base.render)

    def getAngles(self):
        return self.np.getHpr()

    def setScale(self, scale):
        self.np.setScale(scale)
        self.transformChanged()

    def setAbsScale(self, scale):
        self.np.setScale(base.render, scale)
        self.transformChanged()

    def getAbsScale(self):
        return self.np.getScale(base.render)

    def getScale(self):
        return self.np.getScale()

    def setShear(self, shear):
        self.np.setShear(shear)
        self.transformChanged()

    def setAbsShear(self, shear):
        self.np.setShear(base.render, shear)
        self.transformChanged()

    def getAbsShear(self):
        return self.np.getShear(base.render)

    def getShear(self):
        return self.np.getShear()

    def transformChanged(self):
        self.recalcBoundingBox()
        messenger.send('objectTransformChanged', [self])

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

        if self.collNp:
            self.collNp.unstash()
            self.collNp.node().clearSolids()
            self.collNp.node().addSolid(CollisionBox(mins, maxs))
            self.collNp.hide(~VIEWPORT_3D_MASK)

        messenger.send('mapObjectBoundsChanged', [self])

    def removePickBox(self):
        if self.collNp:
            self.collNp.removeNode()
            self.collNp = None

    # Called when the object first comes into existence, before the
    # keyvalues are read
    def generate(self):
        self.np = NodePath(ModelNode("mapobject_unknown"))
        self.np.setPythonTag("mapobject", self)
        #self.collNp = self.np.attachNewNode(CollisionNode("pickBox"))
        #self.collNp.node().setIntoCollideMask(LEGlobals.EntityMask)
        #self.collNp.node().setFromCollideMask(BitMask32.allOff())
        #self.collNp.show()

    # Called after the keyvalues have been read for this object
    def announceGenerate(self):
        self.np.setName("mapobject_%s.%i" % (self.classname, self.id))

    def delete(self):
        # Take the children with us
        for child in self.children.values():
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
        self.properties = None
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
        self.children[child.id] = child
        self.recalcBoundingBox()

    def __removeChild(self, child):
        if child.id in self.children:
            del self.children[child.id]
            self.recalcBoundingBox()

    def doWriteKeyValues(self, parent):
        kv = CKeyValues(self.ObjectName, parent)
        self.writeKeyValues(kv)
        for child in self.children.values():
            child.doWriteKeyValues(kv)

    def writeKeyValues(self, keyvalues):
        keyvalues.setKeyValue("id", str(self.id))
        # Write out our object properties
        for name, prop in self.properties.items():
            prop.writeKeyValues(keyvalues)

    def readKeyValues(self, keyvalues):
        self.id = int(keyvalues.getValue("id"))
        base.document.reserveID(self.id)

        for i in range(keyvalues.getNumKeys()):
            key = keyvalues.getKey(i)
            value = keyvalues.getValue(i)
            if MetaData.isPropertyExcluded(key):
                continue
            # Find the property with this name.
            prop = self.properties.get(key, None)
            if not prop:
                # Prop wasn't explicit or part of FGD metadata (if it's an Entity)
                continue

            nativeValue = prop.getUnserializedValue(value)

            # Set the value!
            self.updateProperties({prop.name: nativeValue})
