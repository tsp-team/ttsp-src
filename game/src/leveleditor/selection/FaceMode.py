from .SelectionMode import SelectionMode
from .SelectionType import SelectionType, SelectionModeTransform
from src.leveleditor.ui.FaceEditSheet import FaceEditSheet
from src.leveleditor import MaterialPool
from src.leveleditor.menu.KeyBind import KeyBind

from src.leveleditor import LEGlobals

_FaceEditSheet = None

class FaceMode(SelectionMode):

    Type = SelectionType.Faces
    TransformBits = SelectionModeTransform.Off
    CanDelete = False
    CanDuplicate = False
    Key = "solidface"
    Mask = LEGlobals.FaceMask
    KeyBind = KeyBind.SelectFaces
    Icon = "resources/icons/editor-select-faces.png"
    Name = "Faces"
    Desc = "Select solid faces"

    @staticmethod
    def getFaceEditSheet():
        global _FaceEditSheet
        if not _FaceEditSheet:
            _FaceEditSheet = FaceEditSheet()
        return _FaceEditSheet

    def getTranslatedSelections(self, mode):
        if mode in [SelectionType.Groups, SelectionType.Objects]:
            # Select each face of each solid we currently have selected
            faces = []
            for obj in self.mgr.selectedObjects:
                if obj.ObjectName == "solid":
                    faces += obj.faces
            return faces
        else:
            return []

    def activate(self):
        SelectionMode.activate(self)

        self.accept('faceMaterialChanged', FaceMode.getFaceEditSheet().faceMaterialChanged)
        # Right click on face to apply active material
        self.accept('mouse3', self.applyActiveMaterial)

    def deactivate(self):
        FaceMode.getFaceEditSheet().hide()
        SelectionMode.deactivate(self)

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
                face.setMaterial(MaterialPool.ActiveMaterial)
                break

    def onSelectionsChanged(self):
        if self.mgr.getNumSelectedObjects() == 0:
            FaceMode.getFaceEditSheet().hide()
        else:
            FaceMode.getFaceEditSheet().updateForSelection()
            FaceMode.getFaceEditSheet().show()
