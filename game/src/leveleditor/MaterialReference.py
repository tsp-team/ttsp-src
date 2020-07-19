from panda3d.bsp import BSPMaterial
from panda3d.core import LVector2i, PNMImage, VirtualFileSystem

from PyQt5 import QtGui, QtCore

# Reference to a material loaded from disk that can be applied to brush faces.
# Materials with the same filename are unified to the same MaterialReference object.
# Stores the $basetexture Texture and the dimensions of it.
class MaterialReference:

    def __init__(self, filename):
        self.material = BSPMaterial.getFromFile(filename)
        self.filename = filename
        if self.material.hasKeyvalue("$basetexture"):
            baseTexturePath = self.material.getKeyvalue("$basetexture")
            imageData = bytes(VirtualFileSystem.getGlobalPtr().readFile(baseTexturePath, True))
            byteArray = QtCore.QByteArray.fromRawData(imageData)
            image = QtGui.QImage.fromData(byteArray)
            self.pixmap = QtGui.QPixmap.fromImage(image)
            self.icon = QtGui.QIcon(self.pixmap)
            self.size = LVector2i(image.width(), image.height())
        else:
            self.texture = None
            self.size = LVector2i(0, 0)
            self.icon = None
            self.pixmap = None
