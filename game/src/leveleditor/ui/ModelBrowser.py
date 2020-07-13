from panda3d import core

from .AssetBrowser import AssetBrowser

from PyQt5 import QtGui, QtWidgets, QtCore
from src.coginvasion.globals import CIGlobals

import math
from collections import deque

class ModelFolder:

    def __init__(self, filename, parent = None):
        self.filename = filename
        self.absFilename = core.Filename(self.filename)
        self.absFilename.makeAbsolute()
        self.parent = parent
        self.modelFiles = []
        self.children = []
        self.item = None

        if parent:
            self.parentRelativeFilename = core.Filename(self.absFilename)
            self.parentRelativeFilename.makeRelativeTo(parent.absFilename)
        else:
            self.parentRelativeFilename = None

class ModelFolderWidgetItem(QtWidgets.QTreeWidgetItem):
    pass

class ModelBrowser(AssetBrowser):

    FileExtensions = ["bam", "egg", "egg.pz"]

    # Filename -> QIcon
    modelThumbnails = {}

    def __init__(self, parent):
        AssetBrowser.__init__(self, parent)

        self.ui.folderView.itemSelectionChanged.connect(self.__handleFolderSelectionChanged)
        self.ui.folderView.setHeaderLabel("Folder Tree")
        self.ui.fileView.itemDoubleClicked.connect(self.__confirmModel)
        self.ui.fileView.itemSelectionChanged.connect(self.__selectModel)
        self.ui.leFileFilter.textChanged.connect(self.__filterList)

        self.currentFolder = None
        self.currentLoadContext = None
        self.selectedModel = None

        self.queuedUpItems = []
        self.maxQueued = 10

        # Set up an offscreen buffer to render the thumbnails of our models.

        props = core.WindowProperties()
        props.setSize(96, 96)
        fbprops = core.FrameBufferProperties()
        fbprops.setSrgbColor(True)
        flags = (core.GraphicsPipe.BFRefuseWindow | core.GraphicsPipe.BFSizeSquare)
        self.buffer = base.graphicsEngine.makeOutput(base.pipe, "modelBrowserBuffer", 0,
            fbprops, props, flags, base.gsg, None)
        self.buffer.setClearColor(CIGlobals.vec3GammaToLinear(core.Vec4(0.5, 0.5, 0.5, 1.0)))
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

        # Find all of the models in the tree
        self.generateModelTree()
        # Then create a widget for each folder that contains models
        self.generateFolderWidgetTree()

        self.ui.folderView.setCurrentItem(self.rootFolder.item)

    def done(self, ret):
        if self.currentLoadContext:
            self.currentLoadContext.cancel()
            self.currentLoadContext = None
        self.camera.removeNode()
        self.camera = None
        self.lens = None
        self.displayRegion = None
        self.render.removeNode()
        self.render = None
        base.graphicsEngine.removeWindow(self.buffer)
        self.buffer = None
        self.queuedUpItems = None
        self.maxQueued = None
        self.currentFolder = None
        self.rootFolder = None
        self.rootFilename = None
        self.rootFilenameAbs = None
        self.files = None
        AssetBrowser.done(self, ret)

    def __selectModel(self):
        item = self.ui.fileView.selectedItems()[0]
        self.selectedModel = item.filename

    def __confirmModel(self, item):
        # User double clicked a model, confirm selection and close dialog
        self.selectedModel = item.filename
        self.finished.emit(1)
        self.close()

    def __filterList(self, text):
        for i in range(self.ui.fileView.count()):
            self.ui.fileView.setRowHidden(i, False)

        if len(text) == 0:
            return

        for i in range(self.ui.fileView.count()):
            if text not in self.ui.fileView.item(i).text():
                self.ui.fileView.setRowHidden(i, True)

    def filterFileList(self):
        self.__filterList(self.ui.leFileFilter.text())

    def __handleFolderSelectionChanged(self):
        item = self.ui.folderView.selectedItems()[0]
        self.currentFolder = item.modelFolder
        self.generateModels()

    def generateFolderWidgetTree(self):
        self.ui.folderView.clear()

        self.r_generateFolderWidgetTree(self.rootFolder, None)

    def r_generateFolderWidgetTree(self, folder, parent):
        item = ModelFolderWidgetItem()
        item.modelFolder = folder
        folder.item = item
        if folder.parentRelativeFilename:
            item.setText(0, folder.parentRelativeFilename.getFullpath())
        else:
            item.setText(0, folder.filename.getFullpath())
        item.setToolTip(0, item.text(0))
        if parent:
            parent.addChild(item)
        else:
            self.ui.folderView.addTopLevelItem(item)

        for child in folder.children:
            self.r_generateFolderWidgetTree(child, item)

    def r_generateModels(self, dirFilename, parentModelFolder):
        vfs = core.VirtualFileSystem.getGlobalPtr()
        contents = vfs.scanDirectory(dirFilename)
        gotHit = False
        subfolders = []
        modelFiles = []
        for virtualFile in contents.getFiles():
            filename = virtualFile.getFilename()
            if virtualFile.isDirectory():
                subfolders.append(filename)
            elif filename.getExtension() in self.FileExtensions:
                filename.makeRelativeTo(self.rootFilenameAbs)
                modelFiles.append(filename)
                gotHit = True

        thisFolder = ModelFolder(dirFilename, parentModelFolder)
        thisFolder.modelFiles = modelFiles

        gotChildHits = False
        for sub in subfolders:
            _, ret = self.r_generateModels(sub, thisFolder)
            if not gotChildHits:
                gotChildHits = ret

        if parentModelFolder and (gotChildHits or gotHit):
            parentModelFolder.children.append(thisFolder)

        return [thisFolder, gotHit or gotChildHits]

    def addQueuedItems(self):
        for item in self.queuedUpItems:
            self.ui.fileView.addItem(item)
        self.queuedUpItems = []
        self.filterFileList()

    def createNextModel(self):
        if len(self.files) > 0:
            filename = self.files.popleft()
            self.createModelItem(filename)
        else:
            self.addQueuedItems()

    def r_createFilesList(self, folder):
        self.files += folder.modelFiles
        for child in folder.children:
            self.r_createFilesList(child)

    def generateModels(self):
        if self.currentLoadContext:
            self.currentLoadContext.cancel()
        self.ui.fileView.clear()
        self.queuedUpItems = []
        self.files = deque()
        self.r_createFilesList(self.currentFolder)
        self.createNextModel()

    def generateModelTree(self):
        self.rootFilename = core.Filename("resources")
        self.rootFilenameAbs = core.Filename(self.rootFilename)
        self.rootFilenameAbs.makeAbsolute()
        self.rootFolder = self.r_generateModels(self.rootFilename, None)[0]

    def createModelItem(self, filename):
        thumbnail = self.getThumbnail(filename)
        if thumbnail:
            self.addModelItem(thumbnail, filename)
            self.createNextModel()

    def addModelItem(self, thumbnail, filename):
        text = filename.getBasename()
        item = QtWidgets.QListWidgetItem(thumbnail, text)
        item.setToolTip(text)
        item.filename = filename

        self.queuedUpItems.append(item)
        if len(self.queuedUpItems) >= self.maxQueued:
            self.addQueuedItems()

    def getThumbnail(self, filename):
        pixmap = self.modelThumbnails.get(filename)
        if not pixmap:
            return self.generateThumbnail(filename)
        else:
            return pixmap

    def gotModel(self, mdl, filename):
        self.currentLoadContext = None

        if not mdl or mdl.isEmpty():
            self.createNextModel()
            return

        mdl.reparentTo(self.render)
        # If there's no geomnode, there is no model!
        if mdl.find("**/+GeomNode").isEmpty():
            self.createNextModel()
            return

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
                col = CIGlobals.vec3LinearToGamma(image.getXel(x, y))
                qimage.setPixelColor(x, y,
                    QtGui.QColor(int(col[0] * 255), int(col[1] * 255), int(col[2] * 255)))

        pixmap = QtGui.QPixmap.fromImage(qimage)
        icon = QtGui.QIcon(pixmap)
        self.modelThumbnails[filename] = icon

        self.addModelItem(icon, filename)

        self.createNextModel()

    def generateThumbnail(self, filename):
        # Load the model up and place it into the scene
        self.currentLoadContext = base.loader.loadModel(filename, callback = self.gotModel, extraArgs = [filename])
        return None
