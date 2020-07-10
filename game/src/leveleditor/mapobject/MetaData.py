# Filename: MetaData.py
# Author:  Brian Lach (July 10, 2020)
# Purpose: Provides info about entity metadata types and how to serialize/unserialize them.

from panda3d.core import Vec3, Vec4, Vec2, CKeyValues

from src.leveleditor.fgdtools import FgdEntityProperty

# Hard coded properties for entity transform
OriginMetaData = FgdEntityProperty("origin", "vec3", display_name="Origin",
                                    default_value="0 0 0", description="Position of entity")
AnglesMetaData = FgdEntityProperty("angles", "vec3", display_name="Angles (Yaw Pitch Roll)",
                                    default_value="0 0 0", description="Angular orientation of entity")
ScaleMetaData = FgdEntityProperty("scale", "vec3", display_name="Scale",
                                  default_value="1 1 1", description="Scale of entity")

MetaDataExclusions = [
    'id',
    'classname',
    'visgroup'
]

# (type, unserialize func, serialize func, default value)
MetaDataType = {
    'string': (str, str, str, ""),
    'float': (float, float, str, 0.0),
    'color255': (Vec4, CKeyValues.to4f, CKeyValues.toString, Vec4(255, 255, 255, 255)),
    'vec3': (Vec3, CKeyValues.to3f, CKeyValues.toString, Vec3(0, 0, 0)),
    'vec4': (Vec4, CKeyValues.to4f, CKeyValues.toString, Vec4(0, 0, 0, 0)),
    'vec2': (Vec2, CKeyValues.to2f, CKeyValues.toString, Vec2(0, 0)),
    'integer': (int, int, str, 0),
    'choices': (int, int, str, 0),
    'spawnflags': (int, int, str, 0),
    'studio': (str, str, str, ""),
    'target_source': (str, str, str, ""),
    'target_destination': (str, str, str, ""),
    'target_destinations': (str, str, str, "")
}

def getMetaDataType(valueType):
    return MetaDataType[valueType]

def getNativeType(typeName):
    return MetaDataType[typeName][0]

def getUnserializeFunc(typeName):
    return MetaDataType[typeName][1]

def getSerializeFunc(typeName):
    return MetaDataType[typeName][2]

def getDefaultValue(typeName):
    return MetaDataType[typeName][3]

def isPropertyExcluded(propName):
    return propName in MetaDataExclusions
