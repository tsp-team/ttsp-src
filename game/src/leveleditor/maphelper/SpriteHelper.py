from panda3d.core import NodePath, ModelNode, CardMaker
from panda3d.bsp import BSPMaterial

from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK

from .MapHelper import MapHelper

class SpriteHelper(MapHelper):

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.sprite = None

    def generate(self, helperInfo):
        MapHelper.generate(self)

        spritePath = helperInfo['args'][0].replace("\"", "")

        cm = CardMaker("sprite")
        cm.setFrame(-12, 12, -12, 12)
        np = NodePath(cm.generate())
        np.setBSPMaterial(spritePath)
        np.setLightOff(1)
        np.setFogOff(1)
        np.setBillboardPointEye()
        np.setTransparency(True)
        np.hide(~VIEWPORT_3D_MASK)
        np.reparentTo(self.mapObject.np)
        self.sprite = np

        self.mapObject.recalcBoundingBox()

    def cleanup(self):
        if self.sprite:
            self.sprite.removeNode()
            self.sprite = None
        self.mapObject.recalcBoundingBox()
        MapHelper.cleanup(self)
