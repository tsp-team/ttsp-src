from .ObjectMode import ObjectMode
from .SelectionType import SelectionType
from src.leveleditor.menu.KeyBind import KeyBind

class GroupsMode(ObjectMode):

    Type = SelectionType.Groups
    KeyBind = KeyBind.SelectGroups
    Icon = "resources/icons/editor-select-groups.png"
    Name = "Groups"
    Desc = "Select object groups"
    ToolOnly = False
