from panda3d.bsp import BSPMaterial
from panda3d.core import LVector2i

# Reference to a material loaded from disk that can be applied to brush faces.
# Materials with the same filename are unified to the same MaterialReference object.
# Stores the $basetexture Texture and the dimensions of it.
class MaterialReference:

    def __init__(self, filename):
        self.material = BSPMaterial.getFromFile(filename)
        if self.material.hasKeyvalue("$basetexture"):
            baseTexturePath = self.material.getKeyvalue("$basetexture")
            self.texture = base.loader.loadTexture(baseTexturePath)
            self.size = LVector2i(self.texture.getXSize(), self.texture.getYSize())
        else:
            self.texture = None
            self.size = LVector2i(0, 0)
