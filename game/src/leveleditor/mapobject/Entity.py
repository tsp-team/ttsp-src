from panda3d.core import CKeyValues, Vec3

from .MapObject import MapObject
from src.leveleditor.maphelper import HelperFactory
from src.leveleditor.fgdtools import PropertyNotFound, FgdEntityProperty

class Entity(MapObject):

    ObjectName = "entity"

    OriginMetaData = FgdEntityProperty("origin", "string", display_name="Origin",
                                       default_value="0 0 0", description="Position of entity")
    AnglesMetaData = FgdEntityProperty("angles", "string", display_name="Angles (Yaw Pitch Roll)",
                                       default_value="0 0 0", description="Angular orientation of entity")
    ScaleMetaData = FgdEntityProperty("scale", "string", display_name="Scale",
                                      default_value="1 1 1", description="Scale of entity")

    MetaDataExclusions = [
        'id',
        'classname',
        'visgroup'
    ]

    MetaDataType = {
        'string': str,
        'integer': int,
        'choices': int,
        'spawnflags': int,
        'studio': str,
        'target_source': str,
        'target_destination': str,
        'target_destinations': str
    }

    DefaultValues = {
        str: "",
        int: 0
    }

    def __init__(self):
        MapObject.__init__(self)
        self.transformProperties = {
            'origin': [self.getOrigin, self.setOrigin, self.OriginMetaData],
            'angles': [self.getAngles, self.setAngles, self.AnglesMetaData],
            'scale': [self.getScale, self.setScale, self.ScaleMetaData]
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
            default = self.DefaultValues[self.getPropDataType(prop.name)]
        return default

    def propertyChanged(self, key, oldValue, newValue):
        if oldValue != newValue:

            if key in self.transformProperties:
                self.transformProperties[key][1](CKeyValues.to3f(newValue))
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
                val = self.getPropDataType(key)(value)
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
            return self.MetaDataType.get(
                self.getPropType(key),
                str)
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
            prop = self.transformProperties[key][0]()
            if asString:
                return CKeyValues.toString(prop)
            else:
                return prop

        prop = self.entityData.get(key, None)
        if asString:
            return str(prop)
        else:
            return prop

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
            if prop.name in self.MetaDataExclusions or prop.name in self.entityData:
                continue
            self.updateProperties({prop.name: self.getPropDefaultValue(prop)})

    def writeKeyValues(self, kv):
        MapObject.writeKeyValues(self, kv)

        kv.setKeyValue("classname", self.classname)
        if self.isPointEntity():
            for key, getset in self.transformProperties.items():
                kv.setKeyValue(key, CKeyValues.toString(getset[0]()))
        for key, value in self.entityData.items():
            kv.setKeyValue(key, str(value))

    def readKeyValues(self, kv):
        MapObject.readKeyValues(self, kv)

        self.setClassname(kv.getValue("classname"))

        for i in range(kv.getNumKeys()):
            key = kv.getKey(i)
            value = kv.getValue(i)
            if key in self.MetaDataExclusions:
                continue
            dt = self.getPropDataType(key)
            self.updateProperties({key: dt(value)})
