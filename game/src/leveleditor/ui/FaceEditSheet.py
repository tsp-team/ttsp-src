from panda3d.core import Filename

from .Ui_FaceEditSheet import Ui_FaceEditSheet
from src.leveleditor import MaterialPool

from PyQt5 import QtWidgets, QtCore

class FaceEditSheet(QtWidgets.QDockWidget):

    def __init__(self):
        QtWidgets.QDockWidget.__init__(self)
        self.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.setWindowTitle("Face Edit Sheet")
        sheet = QtWidgets.QWidget()
        ui = Ui_FaceEditSheet()
        ui.setupUi(sheet)
        self.setWidget(sheet)
        self.ui = ui

        self.face = None

        self.ui.textureScaleXSpin.valueChanged.connect(self.__xScaleChanged)
        self.ui.textureScaleYSpin.valueChanged.connect(self.__yScaleChanged)
        self.ui.textureShiftXSpin.valueChanged.connect(self.__xShiftChanged)
        self.ui.textureShiftYSpin.valueChanged.connect(self.__yShiftChanged)
        self.ui.rotationSpin.valueChanged.connect(self.__rotationChanged)
        self.ui.materialFileEdit.returnPressed.connect(self.__materialFileEdited)
        self.ui.btnAlignFace.clicked.connect(self.__alignFace)
        self.ui.btnAlignWorld.clicked.connect(self.__alignWorld)

        base.qtWindow.addDockWindow(self)

        self.hide()

    def __alignWorld(self):
        if self.face:
            self.face.alignTextureToWorld()

    def __alignFace(self):
        if self.face:
            self.face.alignTextureToFace()

    def updateMaterialIcon(self):
        if self.face:
            self.ui.materialIcon.setPixmap(self.face.material.material.pixmap.scaled(128, 128,
                QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.FastTransformation))

    def __materialFileEdited(self):
        filename = self.ui.materialFileEdit.text()
        if self.face:
            self.face.setMaterial(MaterialPool.getMaterial(filename))
            self.updateMaterialIcon()
            self.face.calcTextureCoordinates(True)

    def __xScaleChanged(self, val):
        if self.face:
            self.face.material.scale.x = val
            self.face.calcTextureCoordinates(True)

    def __yScaleChanged(self, val):
        if self.face:
            self.face.material.scale.y = val
            self.face.calcTextureCoordinates(True)

    def __xShiftChanged(self, val):
        if self.face:
            self.face.material.shift.x = val
            self.face.calcTextureCoordinates(True)

    def __yShiftChanged(self, val):
        if self.face:
            self.face.material.shift.y = val
            self.face.calcTextureCoordinates(True)

    def __rotationChanged(self, val):
        if self.face:
            self.face.material.rotation = val
            self.face.calcTextureCoordinates(True)

    def updateForSelection(self):
        self.face = None

        numFaces = base.selectionMgr.getNumSelectedObjects()
        face = base.selectionMgr.selectedObjects[numFaces - 1]

        self.ui.textureScaleXSpin.setValue(face.material.scale.x)
        self.ui.textureScaleYSpin.setValue(face.material.scale.y)

        self.ui.textureShiftXSpin.setValue(face.material.shift.x)
        self.ui.textureShiftYSpin.setValue(face.material.shift.y)

        self.ui.rotationSpin.setValue(face.material.rotation)

        self.ui.materialFileEdit.setText(face.material.material.filename.getFullpath())

        self.face = face
        self.updateMaterialIcon()
