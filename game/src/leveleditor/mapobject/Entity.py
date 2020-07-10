from panda3d.core import CKeyValues, Vec3, Vec4, Vec2

from .MapObject import MapObject
from src.leveleditor.maphelper import HelperFactory
from src.leveleditor.fgdtools import PropertyNotFound, FgdEntityProperty
from . import MetaData

class Entity(MapObject):

    ObjectName = "entity"

    def __init__(self):
        MapObject.__init__(self)
        self.transformProperties = {
            'origin': [self.getOrigin, self.setOrigin, MetaData.OriginMetaData],
            'angles': [self.getAngles, self.setAngles, MetaData.AnglesMetaData],
            'scale': [self.getScale, self.setScale, MetaData.ScaleMetaData]
        }
        self.metaData = None
        self.entityData = {}
        self.helpers = []

    def delete(self):
        self.removeHelpers()
        MapObject.delete(self)

    def select(self):
        MapObject.select(self)
        for helper in self.helpers:
            helper.select()

    def deselect(self):
        MapObject.deselect(self)
        for helper in self.helpers:
            helper.deselect()

    def removeHelpers(self):
        for helper in self.helpers:
            helper.cleanup()
        self.helpers = []

    def updateHelpers(self):
        self.removeHelpers()
        self.addHelpersForClass()
        self.recalcBoundingBox()

    def addHelpersForClass(self):
        for helperInfo in self.metaData.definitions:
            helper = HelperFactory.createHelper(helperInfo, self)
            if helper:
                self.helpers.append(helper)

    def getPropMetaData(self, prop):
        if prop in self.transformProperties:
            return self.transformProperties[prop][2]
        return self.metaData.property_by_name(prop)

    def getPropDefaultValue(self, prop):
        if isinstance(prop, str):
            prop = self.getPropMetaData(prop)

        default = prop.default_value
        if default is None:
            default = MetaData.getDefaultValue(prop.value_type)
        else:
            func = MetaData.getUnserializeFunc(prop.value_type)
            default = func(default)

        return default

    def propertyChanged(self, key, oldValue, newValue):
        if oldValue != newValue:

            if key in self.transformProperties:
                self.transformProperties[key][1](newValue)
                self.recalcBoundingBox()
            else:
                # Check for any helpers that respond to a change
                # in this property.

                for helper in self.helpers:
                    # Does this helper respond to a change in this property by name?
                    if key in helper.ChangeWith:
                        self.updateHelpers()
                        break

                    # How about if it responds to a change in any property
                    # with this type?
                    dt = self.getPropType(key)
                    if dt in helper.ChangeWithType:
                        self.updateHelpers()
                        break

    def updateProperties(self, data):
        for key, value in data.items():
            oldValue = self.getEntityData(key)
            if not key in self.transformProperties:
                # Make sure the value is the correct type
                prop = self.getPropMetaData(key)
                nativeType = MetaData.getNativeType(prop.value_type)
                if not isinstance(value, nativeType):
                    val = MetaData.getUnserializeFunc(prop.value_type)(value)
                else:
                    val = value
                self.entityData[key] = val
            else:
                val = value
            self.propertyChanged(key, oldValue, val)

    # Returns list of property names with the specified value types.
    def getPropsWithDataType(self, types):
        if isinstance(types, str):
            types = [types]
        props = []
        for schema in self.metaData.properties_schema:
            if schema['type'] in types:
                props.append(schema['name'])
        return props

    def getPropDataType(self, key):
        try:
            MetaData.getNativeType(self.getPropType(key))
        except:
            return str

    def getPropType(self, key):
        try:
            return self.getPropMetaData(key).value_type
        except:
            return "string"

    def getClassType(self):
        return self.metaData.class_type

    def isSolidEntity(self):
        return self.metaData.class_type == 'SolidClass'

    def isPointEntity(self):
        return self.metaData.class_type == 'PointClass'

    def getDescription(self):
        return self.metaData.description

    def setOrigin(self, origin):
        self.np.setPos(origin)

    def getOrigin(self):
        return self.np.getPos()

    def setAngles(self, angles):
        self.np.setHpr(angles)

    def getAngles(self):
        return self.np.getHpr()

    def setScale(self, scale):
        self.np.setScale(scale)

    def getScale(self):
        return self.np.getScale()

    def isTransformProperty(self, key):
        return key in self.transformProperties

    def getEntityData(self, key, asString = False):
        # Hard coded transform properties
        if key in self.transformProperties:
            prop = self.transformProperties[key][2]
            value = self.transformProperties[key][0]()
        else:
            prop = self.getPropMetaData(key)
            value = self.entityData.get(key, "")

        if asString:
            return MetaData.getSerializeFunc(prop.value_type)(value)
        else:
            return value

    def setClassname(self, classname):
        MapObject.setClassname(self, classname)
        self.setupMetaData()
        self.setupEntityData()
        self.updateHelpers()

    def setupMetaData(self):
        self.metaData = base.fgd.entity_by_name(self.classname)
        assert self.metaData is not None, "Unknown classname %s" % self.classname

    def setupEntityData(self):
        if not self.metaData:
            return

        # Prune out properties that are not part of this meta data
        currData = dict(self.entityData)
        for key in currData.keys():
            try:
                self.metaData.property_by_name(key)
            except PropertyNotFound:
                del self.entityData[key]

        for prop in self.metaData.properties:
            if MetaData.isPropertyExcluded(prop.name) or prop.name in self.entityData:
                continue
            self.updateProperties({prop.name: self.getPropDefaultValue(prop)})

    def writeKeyValues(self, kv):
        MapObject.writeKeyValues(self, kv)

        kv.setKeyValue("classname", self.classname)
        if self.isPointEntity():
            for key, getset in self.transformProperties.items():
                kv.setKeyValue(key, CKeyValues.toString(getset[0]()))
        for key, value in self.entityData.items():
            # Get the serialize function for this property type and serialize it!
            func = MetaData.getSerializeFunc(self.getPropType(key))
            kv.setKeyValue(key, func(value))

    def readKeyValues(self, kv):
        MapObject.readKeyValues(self, kv)

        self.setClassname(kv.getValue("classname"))

        for i in range(kv.getNumKeys()):
            key = kv.getKey(i)
            value = kv.getValue(i)
            if MetaData.isPropertyExcluded(key):
                continue
            func = MetaData.getUnserializeFunc(self.getPropType(key))
            self.updateProperties({key: func(value)})
