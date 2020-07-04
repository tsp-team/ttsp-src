from panda3d.core import PointLight, Vec4, Vec3, CKeyValues

from .MapHelper import MapHelper

from src.coginvasion.globals import CIGlobals

class LightHelper(MapHelper):

    ChangeWith = [
        "_light",
        "_constant_attn",
        "_linear_attn",
        "_quadratic_attn"
    ]

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.light = None

    def generate(self, helperInfo):
        color = self.mapObject.entityData.get("_light", "255 255 255 200")
        color = CKeyValues.to4f(color)
        color = CIGlobals.colorFromRGBScalar255(color)
        color = CIGlobals.vec3GammaToLinear(color)
        constant = float(self.mapObject.entityData.get("_constant_attn", "0.0"))
        linear = float(self.mapObject.entityData.get("_linear_attn", "0.0"))
        quadratic = float(self.mapObject.entityData.get("_quadratic_attn", "1.0"))

        # Scale intensity for unit 100 distance
        ratio = (constant + 100 * linear + 100 * 100 * quadratic)
        if ratio > 0:
            color *= ratio

        pl = PointLight("lightHelper-light")
        pl.setColor(color)
        pl.setAttenuation(Vec3(constant, linear, quadratic))
        self.light = self.mapObject.np.attachNewNode(pl)
        base.render.setLight(self.light)

    def cleanup(self):
        if self.light:
            base.render.clearLight(self.light)
            self.light.removeNode()
            self.light = None
        MapHelper.cleanup(self)
