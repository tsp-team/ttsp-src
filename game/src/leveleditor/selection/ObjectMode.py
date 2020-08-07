from panda3d.core import GeomNode

from .SelectionMode import SelectionMode
from .SelectionType import SelectionType
from src.leveleditor.objectproperties.ObjectPropertiesWindow import ObjectPropertiesWindow
from src.leveleditor import LEGlobals
from src.leveleditor.menu.KeyBind import KeyBind

_ObjectPropertiesWindow = None

# Object selection mode: selects individual MapObjects (Entity, Solid, etc), ignoring groups
class ObjectMode(SelectionMode):

    Type = SelectionType.Objects
    Key = "mapobject"
    Mask = GeomNode.getDefaultCollideMask() | LEGlobals.EntityMask
    KeyBind = KeyBind.SelectObjects
    Icon = "resources/icons/editor-select-objects.png"
    Name = "Objects"
    Desc = "Select individual objects"

    def __init__(self, mgr):
        SelectionMode.__init__(self, mgr)
        self.objectProperties = ObjectMode.getObjectPropertiesWindow()

    def cleanup(self):
        self.objectProperties = None
        SelectionMode.cleanup(self)

    def onSelectionsChanged(self):
        self.objectProperties.updateForSelection()

    @staticmethod
    def getObjectPropertiesWindow():
        global _ObjectPropertiesWindow
        if not _ObjectPropertiesWindow:
            _ObjectPropertiesWindow = ObjectPropertiesWindow()
        return _ObjectPropertiesWindow
