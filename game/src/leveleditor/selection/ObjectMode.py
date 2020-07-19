from panda3d.core import GeomNode

from .SelectionMode import SelectionMode
from .SelectionType import SelectionType
from src.leveleditor.objectproperties.ObjectPropertiesWindow import ObjectPropertiesWindow
from src.leveleditor import LEGlobals

_ObjectPropertiesWindow = None

# Object selection mode: selects individual MapObjects (Entity, Solid, etc), ignoring groups
class ObjectMode(SelectionMode):

    Type = SelectionType.Objects
    Key = "mapobject"
    Mask = GeomNode.getDefaultCollideMask() | LEGlobals.EntityMask

    def __init__(self, mgr):
        SelectionMode.__init__(self, mgr)
        self.objectProperties = ObjectMode.getObjectPropertiesWindow(mgr)

    def onSelectionsChanged(self):
        self.objectProperties.updateForSelection()

    @staticmethod
    def getObjectPropertiesWindow(mgr):
        global _ObjectPropertiesWindow
        if not _ObjectPropertiesWindow:
            _ObjectPropertiesWindow = ObjectPropertiesWindow(mgr)
        return _ObjectPropertiesWindow
