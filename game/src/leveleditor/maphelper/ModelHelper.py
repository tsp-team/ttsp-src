from panda3d.core import ModelNode, NodePath, Vec4, CKeyValues, Vec3

from .MapHelper import MapHelper

class ModelHelper(MapHelper):

    def __init__(self, mapObject):
        MapHelper.__init__(self, mapObject)
        self.modelRoot = NodePath(ModelNode("modelHelper"))

        # Model scale can be specified in entity data
        scale = self.mapObject.entityData.get("scale")
        if scale is not None:
            scale = CKeyValues.to3f(scale)
        else:
            scale = Vec3(1.0)

        self.modelRoot.setScale(scale * 16.0)
        self.modelRoot.reparentTo(self.mapObject.np)

    def generate(self, helperInfo):
        MapHelper.generate(self)

        args = helperInfo['args']
        modelPath = args[0] if len(args) > 0 else None
        if not modelPath:
            # Model wasn't specified in the class definition,
            # check for a property called "model"
            modelPath = self.mapObject.entityData.get("model", None)
        if not modelPath:
            return

        modelNp = base.loader.loadModel(modelPath)

        # Create a representation in each viewport
        for vp in base.viewportMgr.viewports:
            vpRoot = self.modelRoot.attachNewNode("vpRepr")
            vpRoot.hide(~vp.getViewportMask())
            if vp.is2D():
                # Show unlit, untextured, blue wireframe in 2D
                vpRoot.setRenderModeWireframe()
                vpRoot.setLightOff(1)
                vpRoot.setFogOff(1)
                vpRoot.setBSPMaterial("phase_14/materials/unlit.mat", 1)
                vpRoot.setColor(Vec4(0.016, 1, 1, 1), 1)

            vpModel = modelNp.instanceTo(vpRoot)

    def cleanup(self):
        if self.modelRoot:
            self.modelRoot.removeNode()
            self.modelRoot = None
        MapHelper.cleanup(self)
