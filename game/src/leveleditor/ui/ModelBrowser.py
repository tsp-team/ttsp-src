from panda3d import core

from .AssetBrowser import AssetBrowser

from PyQt5 import QtGui, QtWidgets, QtCore
from src.coginvasion.globals import CIGlobals

import math
from collections import deque

class ModelBrowser(AssetBrowser):

    FileExtensions = ["bam", "egg", "egg.pz"]

    # Can't preload items because we need to load the model
    # up to make sure it's a valid model first.
    PreloadItems = False

    # Filename -> QIcon
    modelThumbnails = {}

    def __init__(self, parent):
        AssetBrowser.__init__(self, parent)

        self.currentLoadContext = None

        # Set up an offscreen buffer to render the thumbnails of our models.

        props = core.WindowProperties()
        props.setSize(96, 96)
        fbprops = core.FrameBufferProperties()
        fbprops.setSrgbColor(True)
        fbprops.setRgbaBits(8, 8, 8, 0)
        flags = (core.GraphicsPipe.BFRefuseWindow | core.GraphicsPipe.BFSizeSquare)
        self.buffer = base.graphicsEngine.makeOutput(base.pipe, "modelBrowserBuffer", 0,
            fbprops, props, flags, None, None)
        self.buffer.setClearColor(CIGlobals.vec3GammaToLinear(core.Vec4(82 / 255.0, 82 / 255.0, 82 / 255.0, 1.0)))
        self.buffer.setActive(False)

        self.displayRegion = self.buffer.makeDisplayRegion()

        self.render = core.NodePath("modelBrowserRoot")
        self.render.setShaderAuto()

        camNode = core.Camera("modelBrowserRenderCam")
        lens = core.PerspectiveLens()
        lens.setFov(40)
        camNode.setLens(lens)
        self.lens = lens
        self.camera = self.render.attachNewNode(camNode)
        # Isometric camera angle
        self.camera.setHpr(225, -30, 0)

        self.displayRegion.setCamera(self.camera)

        base.graphicsEngine.openWindows()

    def generateAssets(self):
        if self.currentLoadContext:
            self.currentLoadContext.cancel()
        AssetBrowser.generateAssets(self)

    def getThumbnail(self, filename, context):
        pixmap = self.modelThumbnails.get(filename)
        if not pixmap:
            return self.generateThumbnail(filename, context)
        else:
            return pixmap

    def gotModel(self, mdl, filename, context):
        self.currentLoadContext = None

        if not mdl or mdl.isEmpty():
            context.createNextAsset()
            return

        # If there's no geomnode, there is no model!
        if mdl.find("**/+GeomNode").isEmpty():
            context.createNextAsset()
            return

        mdl.reparentTo(self.render)

        # Determine a good offset point to take the thumbnail snapshot
        mins = core.Point3()
        maxs = core.Point3()
        mdl.calcTightBounds(mins, maxs)
        size = maxs - mins
        center = (mins + maxs) / 2.0
        # Choose the longest axis as the radius
        radius = size.length() / 2

        fov = self.lens.getFov()
        distance = (radius / float(math.tan(core.deg2Rad(min(fov[0], fov[1]) / 2.0))))

        # Ensure the far plane is far enough back to see the entire object.
        idealFarPlane = distance + radius * 1.5
        self.lens.setFar(max(self.lens.getDefaultFar(), idealFarPlane))

        # And that the near plane is far enough forward.
        idealNearPlane = distance - radius
        self.lens.setNear(min(self.lens.getDefaultNear(), idealNearPlane))

        self.camera.setPos(center + self.camera.getQuat().xform(core.Vec3.forward() * -distance))

        # Render the model to the back buffer
        self.buffer.setActive(True)
        base.graphicsEngine.renderFrame()
        base.graphicsEngine.renderFrame()

        # Fetch the pixels into a PNMImage
        image = core.PNMImage()
        self.buffer.getScreenshot(image)

        self.buffer.setActive(False)

        mdl.removeNode()

        # Store the pixels in a QPixmap
        qimage = QtGui.QImage(image.getXSize(), image.getYSize(), QtGui.QImage.Format_RGB888)
        for x in range(image.getXSize()):
            for y in range(image.getYSize()):
                col = CIGlobals.vec3LinearToGamma(image.getXelA(x, y))
                qimage.setPixelColor(x, y,
                    QtGui.QColor(int(col[0] * 255), int(col[1] * 255), int(col[2] * 255), int(col[3] * 255)))

        pixmap = QtGui.QPixmap.fromImage(qimage)
        icon = QtGui.QIcon(pixmap)
        self.modelThumbnails[filename] = icon

        context.addAssetItem(icon, filename)

        context.createNextAsset()

    def generateThumbnail(self, filename, context):
        # Load the model up and place it into the scene
        self.currentLoadContext = base.loader.loadModel(filename, callback = self.gotModel,
            extraArgs = [filename, context])
        return None
