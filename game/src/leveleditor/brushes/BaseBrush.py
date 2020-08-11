from PyQt5 import QtWidgets

from src.leveleditor.math.Plane import Plane
from src.leveleditor.mapobject.Solid import Solid
from src.leveleditor.mapobject.SolidFace import SolidFace
from src.leveleditor.mapobject.SolidVertex import SolidVertex

class BaseBrush:
    Name = "Brush"
    CanRound = True

    def __init__(self):
        self.controls = []
        self.controlsGroup = QtWidgets.QGroupBox(self.Name + " Options")
        self.controlsGroup.setLayout(QtWidgets.QFormLayout())

    def addControl(self, ctrl):
        if ctrl.label:
            self.controlsGroup.layout().addRow(ctrl.label, ctrl.control)
        else:
            self.controlsGroup.layout().addRow(ctrl.control)
        self.controls.append(ctrl)
        return ctrl

    def create(self, generator, mins, maxs, material, roundDecimals):
        raise NotImplementedError

    def makeSolid(self, generator, faces, material):
        solid = Solid(generator.getNextID())
        for arr in faces:
            face = SolidFace(generator.getNextFaceID(),
                             Plane.fromVertices(arr[0], arr[1], arr[2]),
                             solid)
            face.setMaterial(material)
            for vert in arr:
                face.vertices.append(SolidVertex(vert, face))
            solid.faces.append(face)

        solid.setToSolidOrigin()
        solid.alignTexturesToFaces()
        solid.generateFaces()
        solid.recalcBoundingBox()

        return solid
