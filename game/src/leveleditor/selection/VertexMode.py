from .SelectionMode import SelectionMode
from .SelectionType import SelectionModeTransform, SelectionType

from src.leveleditor import LEGlobals

class VertexMode(SelectionMode):

    Type = SelectionType.Vertices
    Mask = LEGlobals.VertexMask
    Key = "solidvertex"
    CanDelete = False
    CanDuplicate = False
    TransformBits = SelectionModeTransform.Translate

    def onSelectionsChanged(self):
        pass
