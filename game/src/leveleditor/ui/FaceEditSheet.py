from panda3d.core import Filename

from .Ui_FaceEditSheet import Ui_FaceEditSheet
from src.leveleditor import MaterialPool
from src.leveleditor.math.PointCloud import PointCloud
from src.leveleditor.Align import Align

from PyQt5 import QtWidgets, QtCore

class FaceEditSheet(QtWidgets.QDockWidget):

    def __init__(self, faceMode):
        QtWidgets.QDockWidget.__init__(self)
        self.faceMode = faceMode
        self.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
        self.setWindowTitle("Face Edit Sheet")
        sheet = QtWidgets.QWidget()
        ui = Ui_FaceEditSheet()
        ui.setupUi(sheet)
        self.setWidget(sheet)
        self.ui = ui

        self.faces = []
        self.face = None
        self.treatAsOne = False

        self.ui.textureScaleXSpin.valueChanged.connect(self.__xScaleChanged)
        self.ui.textureScaleYSpin.valueChanged.connect(self.__yScaleChanged)
        self.ui.textureShiftXSpin.valueChanged.connect(self.__xShiftChanged)
        self.ui.textureShiftYSpin.valueChanged.connect(self.__yShiftChanged)
        self.ui.rotationSpin.valueChanged.connect(self.__rotationChanged)
        self.ui.materialFileEdit.returnPressed.connect(self.__materialFileEdited)
        self.ui.btnBrowse.clicked.connect(self.__browseForMaterial)
        self.ui.btnAlignFace.clicked.connect(self.__alignFace)
        self.ui.btnAlignWorld.clicked.connect(self.__alignWorld)
        self.ui.btnFit.clicked.connect(self.__fitTexture)
        self.ui.btnJustifyBottom.clicked.connect(self.__justifyBottom)
        self.ui.btnJustifyCenter.clicked.connect(self.__justifyCenter)
        self.ui.btnJustifyLeft.clicked.connect(self.__justifyLeft)
        self.ui.btnJustifyRight.clicked.connect(self.__justifyRight)
        self.ui.btnJustifyTop.clicked.connect(self.__justifyTop)
        self.ui.chkTreatAsOne.toggled.connect(self.__toggleTreatAsOne)

        base.qtWindow.addDockWindow(self)

        self.hide()

    def __browseForMaterial(self):
        base.materialBrowser.show(self, self.__materialBrowserDone)

    def __materialBrowserDone(self, status, asset):
        if status:
            path = asset.getFullpath()
            self.ui.materialFileEdit.setText(path)
            self.__changeMaterial(path)

    def __getPointCloud(self, faces):
        points = []
        for face in faces:
            for vertex in face.vertices:
                points.append(vertex.getWorldPos())
        return PointCloud(points)

    def __fitTexture(self):
        if self.treatAsOne:
            cloud = self.__getPointCloud(self.faces)
            for face in self.faces:
                face.fitTextureToPointCloud(cloud, 1, 1)
        else:
            for face in self.faces:
                cloud = self.__getPointCloud([face])
                face.fitTextureToPointCloud(cloud, 1, 1)

    def __doAlign(self, mode):
        if self.treatAsOne:
            cloud = self.__getPointCloud(self.faces)
            for face in self.faces:
                face.alignTextureWithPointCloud(cloud, mode)
        else:
            for face in self.faces:
                cloud = self.__getPointCloud([face])
                face.alignTextureWithPointCloud(cloud, mode)

    def __justifyBottom(self):
        self.__doAlign(Align.Bottom)

    def __justifyCenter(self):
        self.__doAlign(Align.Center)

    def __justifyLeft(self):
        self.__doAlign(Align.Left)

    def __justifyRight(self):
        self.__doAlign(Align.Right)

    def __justifyTop(self):
        self.__doAlign(Align.Top)

    def __toggleTreatAsOne(self, checkState):
        self.treatAsOne = checkState

    def __alignWorld(self):
        for face in self.faces:
            face.alignTextureToWorld()
        self.updateForSelection()

    def __alignFace(self):
        for face in self.faces:
            face.alignTextureToFace()
        self.updateForSelection()

    def updateMaterialIcon(self):
        if self.face:
            self.ui.materialIcon.setPixmap(self.face.material.material.pixmap.scaled(128, 128,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def __materialFileEdited(self):
        filename = self.ui.materialFileEdit.text()
        self.__changeMaterial(filename)

    def __changeMaterial(self, filename):
        mat = MaterialPool.getMaterial(filename)
        self.faceMode.activeMaterial = mat
        for face in self.faces:
            face.setMaterial(mat)

        self.updateMaterialIcon()

    def __xScaleChanged(self, val):
        for face in self.faces:
            face.material.scale.x = val
            face.calcTextureCoordinates(True)

    def __yScaleChanged(self, val):
        for face in self.faces:
            face.material.scale.y = val
            face.calcTextureCoordinates(True)

    def __xShiftChanged(self, val):
        for face in self.faces:
            face.material.shift.x = val
            face.calcTextureCoordinates(True)

    def __yShiftChanged(self, val):
        for face in self.faces:
            face.material.shift.y = val
            face.calcTextureCoordinates(True)

    def __rotationChanged(self, val):
        for face in self.faces:
            face.setTextureRotation(val)

    def updateForSelection(self):
        self.faces = []

        faces = list(base.selectionMgr.selectedObjects)
        numFaces = len(faces)
        face = faces[numFaces - 1]

        self.ui.textureScaleXSpin.setValue(face.material.scale.x)
        self.ui.textureScaleYSpin.setValue(face.material.scale.y)

        self.ui.textureShiftXSpin.setValue(face.material.shift.x)
        self.ui.textureShiftYSpin.setValue(face.material.shift.y)

        self.ui.rotationSpin.setValue(face.material.rotation)

        self.ui.materialFileEdit.setText(face.material.material.filename.getFullpath())

        self.face = face
        self.faces = faces

        self.faceMode.activeMaterial = self.face.material.material

        self.updateMaterialIcon()
