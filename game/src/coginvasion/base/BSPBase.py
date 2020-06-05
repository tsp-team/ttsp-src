from panda3d.core import CullBinManager, NodePath, OmniBoundingVolume, WindowProperties, LightRampAttrib
from panda3d.bsp import BSPShaderGenerator, VertexLitGenericSpec, LightmappedGenericSpec, UnlitGenericSpec, UnlitNoMatSpec, CSMRenderSpec, SkyBoxSpec, DecalModulateSpec

from direct.showbase.ShowBase import ShowBase
from direct.directnotify.DirectNotifyGlobal import directNotify

from src.coginvasion.base.CogInvasionLoader import CogInvasionLoader
from src.coginvasion.globals import CIGlobals
from src.coginvasion.base.CIPostProcess import CIPostProcess

import builtins

class BSPBase(ShowBase):
    notify = directNotify.newCategory("BSPBase")

    def __init__(self):
        ShowBase.__init__(self)
        self.loader.destroy()
        self.loader = CogInvasionLoader(self)
        builtins.loader = self.loader
        self.graphicsEngine.setDefaultLoader(self.loader.loader)
        
        self.makeAllPipes()

        from panda3d.core import RenderAttribRegistry
        from panda3d.core import ShaderAttrib, TransparencyAttrib
        from panda3d.bsp import BSPMaterialAttrib
        attribRegistry = RenderAttribRegistry.getGlobalPtr()
        attribRegistry.setSlotSort(BSPMaterialAttrib.getClassSlot(), 0)
        attribRegistry.setSlotSort(ShaderAttrib.getClassSlot(), 1)
        attribRegistry.setSlotSort(TransparencyAttrib.getClassSlot(), 2)

        self.taskMgr.add(self.updateShadersAndPostProcess, 'CIBase.updateShadersAndPostProcess', 47)

        self.bloomToggle = False
        self.hdrToggle = False
        self.fxaaToggle = CIGlobals.getSettingsMgr().getSetting("aa").getValue() == "FXAA"
        self.aoToggle = False

        # Initialized in initStuff()
        self.shaderGenerator = None

        self.initialize()

    def setAmbientOcclusion(self, toggle):
        self.aoToggle = toggle

    def setFXAA(self, toggle):
        self.fxaaToggle = toggle

    def setHDR(self, toggle):
        self.hdrToggle = toggle

        if toggle:
            # Don't clamp lighting calculations with hdr.
            render.setAttrib(LightRampAttrib.makeIdentity())
        else:
            render.setAttrib(LightRampAttrib.makeDefault())

    def setBloom(self, flag):
        self.bloomToggle = flag

    def initStuff(self):
        self.shaderGenerator = BSPShaderGenerator(self.win, self.win.getGsg(), self.camera, self.render)
        self.win.getGsg().setShaderGenerator(self.shaderGenerator)
        vlg = VertexLitGenericSpec()    # models
        ulg = UnlitGenericSpec()        # ui elements, particles, etc
        lmg = LightmappedGenericSpec()  # brushes, displacements
        unm = UnlitNoMatSpec()          # when there's no material
        csm = CSMRenderSpec()           # renders the shadow scene for CSM
        skb = SkyBoxSpec()              # renders the skybox onto faces
        dcm = DecalModulateSpec()       # blends decals
        self.shaderGenerator.addShader(vlg)
        self.shaderGenerator.addShader(ulg)
        self.shaderGenerator.addShader(unm)
        self.shaderGenerator.addShader(lmg)
        self.shaderGenerator.addShader(csm)
        self.shaderGenerator.addShader(skb)
        self.shaderGenerator.addShader(dcm)

        self.shaderGenerator.setShaderQuality(CIGlobals.getSettingsMgr().getSetting("shaderquality").getValue())
        
        self.filters = CIPostProcess()
        self.filters.startup(self.win)
        self.filters.addCamera(self.cam)
        self.filters.setup()

        self.setHDR(self.hdrToggle)
        self.setBloom(self.bloomToggle)
        self.setFXAA(self.fxaaToggle)
        self.setAmbientOcclusion(self.aoToggle)

    def hideMouseCursor(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)

    def showMouseCursor(self):
        props = WindowProperties()
        props.setCursorHidden(False)
        self.win.requestProperties(props)

    def updateShadersAndPostProcess(self, task):
        if self.shaderGenerator:
            self.shaderGenerator.update()
        if hasattr(self, 'filters'):
            self.filters.windowEvent()
        return task.cont

    def initialize(self):
        gsg = self.win.getGsg()

        # Let's print out the Graphics information.
        self.notify.info('Graphics Information:\n\tVendor: {0}\n\tRenderer: {1}\n\tVersion: {2}\n\tSupports Cube Maps: {3}\n\tSupports 3D Textures: {4}\n\tSupports Compute Shaders: {5}'
                         .format(gsg.getDriverVendor(),
                                 gsg.getDriverRenderer(),
                                 gsg.getDriverVersion(),
                                 str(gsg.getSupportsCubeMap()),
                                 str(gsg.getSupports3dTexture()),
                                 str(gsg.getSupportsComputeShaders())))

        # Enable shader generation on all of the main scenes
        if gsg.getSupportsBasicShaders() and gsg.getSupportsGlsl():
            render.setShaderAuto()
            render2d.setShaderAuto()
            render2dp.setShaderAuto()
        else:
            # I don't know how this could be possible
            self.notify.error("GLSL shaders unsupported by graphics driver.")
            return

        # FIXME: is this still needed?
        # Let's disable fog on Intel graphics
        if gsg.getDriverVendor() == "Intel":
            metadata.NO_FOG = 1
            self.notify.info('Applied Intel-specific graphical fix.')

        self.camNode.setCameraMask(CIGlobals.MainCameraBitmask)

        render.show(CIGlobals.ShadowCameraBitmask)

        cbm = CullBinManager.getGlobalPtr()
        cbm.addBin('ground', CullBinManager.BTUnsorted, 18)
        # The portal uses the shadow bin by default,
        # but we still want to see it with real shadows.
        cbm.addBin('portal', CullBinManager.BTBackToFront, 19)
        if not metadata.USE_REAL_SHADOWS:
            cbm.addBin('shadow', CullBinManager.BTBackToFront, 19)
        else:
            cbm.addBin('shadow', CullBinManager.BTFixed, -100)
        cbm.addBin('gui-popup', CullBinManager.BTUnsorted, 60)
        cbm.addBin('gsg-popup', CullBinManager.BTFixed, 70)

        self.setBackgroundColor(CIGlobals.DefaultBackgroundColor)
        self.disableMouse()
        self.enableParticles()
