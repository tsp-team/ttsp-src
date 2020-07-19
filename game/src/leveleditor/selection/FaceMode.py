from .SelectionMode import SelectionMode
from .SelectionType import SelectionType, SelectionModeTransform
from src.leveleditor.ui.FaceEditSheet import FaceEditSheet
from src.leveleditor import MaterialPool

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
        self.faceEditSheet = FaceEditSheet(self)
        self.activeMaterial = MaterialPool.getMaterial("materials/dev/dev_measuregeneric01b.mat")

    def enable(self):
        SelectionMode.enable(self)
        # Right click on face to apply active material
        self.accept('mouse3', self.applyActiveMaterial)

    def applyActiveMaterial(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is3D():
            return

        entries = vp.click(self.Mask)
        if not entries or len(entries) == 0:
            return

        for i in range(len(entries)):
            entry = entries[i]
            faceNp = entry.getIntoNodePath().findNetPythonTag(self.Key)
            if not faceNp.isEmpty():
                face = faceNp.getPythonTag(self.Key)
                face.setMaterial(self.activeMaterial)
                break

    def onSelectionsChanged(self):
        if self.mgr.getNumSelectedObjects() == 0:
            self.faceEditSheet.hide()
        else:
            self.faceEditSheet.updateForSelection()
            self.faceEditSheet.show()
