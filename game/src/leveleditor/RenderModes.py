from panda3d.core import RenderState, DepthTestAttrib, DepthWriteAttrib, ShaderAttrib, ColorAttrib, Shader, LightAttrib, FogAttrib, CullFaceAttrib
from panda3d.core import LVector2i, Vec4, CullBinAttrib
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
            DepthWriteAttrib.make(DepthWriteAttrib.MOff),
            CullFaceAttrib.make(CullFaceAttrib.MCullNone),
        )
        _DashedLineNoZ = _DashedLineNoZ.setAttrib(CullBinAttrib.make("fixed", 0))
    return _DashedLineNoZ

_DoubleSidedNoZ = None
def DoubleSidedNoZ():
    global _DoubleSidedNoZ
    if not _DoubleSidedNoZ:
        _DoubleSidedNoZ = RenderState.make(
            CullFaceAttrib.make(CullFaceAttrib.MCullNone),
            DepthTestAttrib.make(DepthTestAttrib.MOff),
            DepthWriteAttrib.make(DepthWriteAttrib.MOff),
            CullBinAttrib.make("fixed", 0)
        )
    return _DoubleSidedNoZ
