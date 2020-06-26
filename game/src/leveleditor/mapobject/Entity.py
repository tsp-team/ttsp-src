from panda3d.core import CKeyValues, Vec3

from .MapObject import MapObject
from src.leveleditor.maphelper import HelperFactory

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
        'studio': str
    }

    def __init__(self):
        MapObject.__init__(self)
        self.metaData = None
        self.entityData = {}
        self.helpers = []

    def removeHelpers(self):
        for helper in self.helpers:
            helper.cleanup()
        self.helpers = []

    def updateHelpers(self):
        self.removeHelpers()
        self.addHelpersForClass()

    def addHelpersForClass(self):
        for helperInfo in self.metaData.definitions:
            helper = HelperFactory.createHelper(helperInfo, self)
            if helper:
                self.helpers.append(helper)

    def propertyChanged(self, key, oldValue, newValue):
        if oldValue != newValue:

            if key == "model" or key == "scale":
                # Refresh our helpers if the model changed.
                self.updateHelpers()

            elif key == "origin":
                origin = CKeyValues.to3f(newValue)
                self.np.setPos(origin)

            elif key == "angles":
                angles = CKeyValues.to3f(newValue)
                self.np.setHpr(angles)

    def updateProperties(self, data):
        for key, value in data.items():
            oldValue = self.entityData.get(key, None)
            self.entityData[key] = value
            self.propertyChanged(key, oldValue, value)

    def getPropDataType(self, key):
        try:
            return self.MetaDataType.get(
                self.metaData.property_by_name(key).value_type,
                str)
        except:
            return str

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
        for prop in self.metaData.properties:
            if prop.name in self.MetaDataExclusions or prop.name in self.entityData:
                continue
            self.updateProperties({prop.name: prop.default_value})

    def writeKeyValues(self, kv):
        MapObject.writeKeyValues(self, kv)

        kv.setKeyValue("classname", self.classname)
        if self.isPointEntity():
            # Point entites have origins and angles
            kv.setKeyValue("origin", CKeyValues.toString(self.np.getPos()))
            kv.setKeyValue("angles", CKeyValues.toString(self.np.getHpr()))
        for key, value in self.entityData.items():
            if value is None:
                # str(None) would become "None", which we don't want
                value = ""
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
            if len(value) == 0:
                if dt == int:
                    # Empty strings can't be cast to int
                    value = "0"
            self.updateProperties({key: dt(value)})
