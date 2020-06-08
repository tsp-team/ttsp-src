from panda3d.core import RenderState, DepthTestAttrib, DepthWriteAttrib, ShaderAttrib, ColorAttrib, Shader, LightAttrib, FogAttrib
from panda3d.core import LVector2i, Vec4
from panda3d.bsp import BSPMaterial, BSPMaterialAttrib

_DashedLineNoZ = None
def DashedLineNoZ():
    global _DashedLineNoZ
    if not _DashedLineNoZ:
        shattr = ShaderAttrib.make(Shader.load(Shader.SLGLSL, "resources/shaders/editor/lineStipple.vert.glsl",
            "resources/shaders/editor/lineStipple.frag.glsl"))
        shattr = shattr.setShaderInput("stippleParams", LVector2i(0xAAAA, 10))
        _DashedLineNoZ = RenderState.make(
            shattr,
            DepthTestAttrib.make(DepthTestAttrib.MOff),
            DepthWriteAttrib.make(DepthWriteAttrib.MOff)
        )
    return _DashedLineNoZ