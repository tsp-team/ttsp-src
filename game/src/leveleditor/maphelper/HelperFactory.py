from .ModelHelper import ModelHelper
from .SpriteHelper import SpriteHelper
from .LightHelper import LightHelper

# Map helpers by entity class definitions in the fgd file.
Helpers = {
    "studio": ModelHelper,
    "studioprop": ModelHelper,
    "lightprop": ModelHelper,
    "iconsprite": SpriteHelper,
    "pointlight": LightHelper
}

def createHelper(helperInfo, mapObject):
    helperCls = Helpers.get(helperInfo['name'])
    if helperCls:
        helper = helperCls(mapObject)
        helper.generate(helperInfo)
        return helper
    return None
