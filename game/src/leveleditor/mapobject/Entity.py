from panda3d.core import CKeyValues, Vec3

from .MapObject import MapObject
from src.leveleditor.maphelper import HelperFactory
from src.leveleditor.fgdtools import PropertyNotFound

class Entity(MapObject):

    ObjectName = "entity"

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

    def getPropDefaultValue(self, prop):
        if isinstance(prop, str):
            prop = self.metaData.property_by_name(prop)

        default = prop.default_value
        if default is None:
            default = self.DefaultValues[self.getPropDataType(prop.name)]
        return default

    def propertyChanged(self, key, oldValue, newValue):
        if oldValue != newValue:

            if key == "origin":
                origin = CKeyValues.to3f(newValue)
                self.np.setPos(origin)

            elif key == "angles":
                angles = CKeyValues.to3f(newValue)
                self.np.setHpr(angles)

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
            oldValue = self.entityData.get(key, None)
            self.entityData[key] = value
            self.propertyChanged(key, oldValue, value)

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
            return self.metaData.property_by_name(key).value_type
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
            # Point entites have origins and angles
            kv.setKeyValue("origin", CKeyValues.toString(self.np.getPos()))
            kv.setKeyValue("angles", CKeyValues.toString(self.np.getHpr()))
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
