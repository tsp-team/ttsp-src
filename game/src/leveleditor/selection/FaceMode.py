from .SelectionMode import SelectionMode
from .SelectionType import SelectionType, SelectionModeTransform
from src.leveleditor.ui.FaceEditSheet import FaceEditSheet

from src.leveleditor import LEGlobals

class FaceMode(SelectionMode):

    Type = SelectionType.Faces
    TransformBits = SelectionModeTransform.Off
    CanDelete = False
    CanDuplicate = False
    Key = "solidface"
    Mask = LEGlobals.FaceMask

    def __init__(self, mgr):
        SelectionMode.__init__(self, mgr)
        self.faceEditSheet = FaceEditSheet()

    def onSelectionsChanged(self):
        if self.mgr.getNumSelectedObjects() == 0:
            self.faceEditSheet.hide()
        else:
            self.faceEditSheet.updateForSelection()
            self.faceEditSheet.show()
