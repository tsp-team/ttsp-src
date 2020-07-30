from panda3d import core

from .AssetBrowserUI import Ui_AssetBrowser

from PyQt5 import QtWidgets, QtGui, QtCore

class AssetFolder:

    def __init__(self, filename, parent = None):
        self.filename = filename
        self.absFilename = core.Filename(self.filename)
        self.absFilename.makeAbsolute()
        self.parent = parent
        self.assetFiles = []
        self.children = []
        self.item = None

        if parent:
            self.parentRelativeFilename = core.Filename(self.absFilename)
            self.parentRelativeFilename.makeRelativeTo(parent.absFilename)
        else:
            self.parentRelativeFilename = None

class AssetFolderWidgetItem(QtWidgets.QTreeWidgetItem):
    pass

class AssetCreationContext:

    def __init__(self, dlg, files, listView, canFilter, callback = None):
        self.dlg = dlg
        self.files = files
        self.listView = listView
        self.canFilter = canFilter
        self.queuedUpItems = []
        self.maxQueued = 10
        self.createAssetTask = None
        self.callback = callback
        self.isPaused = False
        self.done = False

    def cleanup(self):
        if self.createAssetTask:
            self.createAssetTask.remove()
        self.createAssetTask = None
        self.dlg = None
        self.listView = None
        self.canFilter = None
        self.queuedUpItems = None
        self.maxQueued = None
        self.callback = None

    def pause(self):
        self.isPaused = True

    def resume(self):
        self.isPaused = False
        if not self.done:
            self.createNextAsset()

    def addQueuedItems(self):
        text = self.dlg.ui.leFileFilter.text().lower()

        for item in self.queuedUpItems:
            self.listView.addItem(item)
            if self.canFilter and len(text) > 0 and text not in item.text().lower():
                self.listView.setRowHidden(self.listView.row(item), True)
        self.queuedUpItems = []

    def addAssetItem(self, thumbnail, filename):
        text = filename.getBasename()
        item = QtWidgets.QListWidgetItem(thumbnail, text)
        item.setToolTip(text)
        item.filename = filename

        self.queuedUpItems.append(item)
        if len(self.queuedUpItems) >= self.maxQueued:
            self.addQueuedItems()

    def createNextAsset(self):
        if self.isPaused:
            return

        if len(self.files) > 0:
            filename = core.Filename(self.files.pop(0))
            self.createAssetItem(filename)
        else:
            self.addQueuedItems()
            self.done = True
            if self.callback:
                self.callback()
            self.cleanup()

    def createAssetItem(self, filename):
        self.createAssetTask = base.taskMgr.doMethodLater(0.01, self.__createAssetItemTask, "AssetBrowser.createAssetItem",
            extraArgs = [filename], appendTask = True)

    def __createAssetItemTask(self, filename, task):
        thumbnail = self.dlg.getThumbnail(filename, self)
        if thumbnail:
            self.addAssetItem(thumbnail, filename)
            self.createNextAsset()
        return task.done

# Base class for an asset browser dialog
class AssetBrowser(QtWidgets.QDialog):

    FileExtensions = []

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_AssetBrowser()
        self.ui.setupUi(self)
        self.setModal(True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)

        self.callback = None

        self.firstTime = True

        self.recentlyUsed = []

        self.currentFolder = None
        self.selectedAsset = None
        self.rootFolder = None
        self.rootFilename = None
        self.rootFilenameAbs = None

        self.folderContext = None
        self.recentlyUsedContext = None

        self.ui.folderView.itemSelectionChanged.connect(self.__handleFolderSelectionChanged)
        self.ui.fileView.itemDoubleClicked.connect(self.__confirmAsset)
        self.ui.fileView.itemSelectionChanged.connect(self.__selectAsset)
        self.ui.recentView.itemDoubleClicked.connect(self.__confirmAsset)
        self.ui.recentView.itemSelectionChanged.connect(self.__selectRecentAsset)
        self.ui.leFileFilter.textChanged.connect(self.__filterList)

    def show(self, parent, callback):
        self.callback = callback
        #self.setParent(parent)
        self.setModal(True)
        QtWidgets.QDialog.show(self)
        if self.firstTime:
            self.firstTime = False
            self.initialize()
        else:
            self.generateRecentlyUsedAssets()
            if self.folderContext:
                self.folderContext.resume()

    def initialize(self):
        # Find all of the models in the tree
        self.generateAssetTree()
        # Then create a widget for each folder that contains models
        self.generateFolderWidgetTree()

        # Generate the recently used items
        self.generateRecentlyUsedAssets()
        self.ui.folderView.setCurrentItem(self.rootFolder.item)

    def generateRecentlyUsedAssets(self):
        if self.recentlyUsedContext:
            self.recentlyUsedContext.cleanup()

        self.ui.recentView.clear()

        ctx = AssetCreationContext(self, list(self.recentlyUsed), self.ui.recentView, False)
        ctx.createNextAsset()
        self.recentlyUsedContext = ctx

    def __selectAsset(self):
        items = self.ui.fileView.selectedItems()
        if len(items) > 0:
            item = items[0]
            self.selectedAsset = item.filename
            self.ui.recentView.setCurrentItem(None)

    def __selectRecentAsset(self):
        items = self.ui.recentView.selectedItems()
        if len(items) > 0:
            item = items[0]
            self.selectedAsset = item.filename
            self.ui.fileView.setCurrentItem(None)

    def __confirmAsset(self, item):
        # User double clicked a model, confirm selection and close dialog
        self.selectedAsset = item.filename
        self.hide(1)

    def __filterList(self, text):
        text = text.lower()

        for i in range(self.ui.fileView.count()):
            self.ui.fileView.setRowHidden(i, False)

        if len(text) == 0:
            return

        for i in range(self.ui.fileView.count()):
            if text not in self.ui.fileView.item(i).text().lower():
                self.ui.fileView.setRowHidden(i, True)

    def filterFileList(self):
        self.__filterList(self.ui.leFileFilter.text())

    def __handleFolderSelectionChanged(self):
        item = self.ui.folderView.selectedItems()[0]
        self.currentFolder = item.assetFolder
        self.generateAssets()

    def generateFolderWidgetTree(self):
        self.ui.folderView.clear()

        self.r_generateFolderWidgetTree(self.rootFolder, None)

        self.ui.folderView.expandToDepth(0)

    def r_generateFolderWidgetTree(self, folder, parent):
        item = AssetFolderWidgetItem()
        item.assetFolder = folder
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

    def r_generateAssets(self, dirFilename, parentModelFolder):
        vfs = core.VirtualFileSystem.getGlobalPtr()
        contents = vfs.scanDirectory(dirFilename)
        gotHit = False
        subfolders = []
        assetFiles = []
        for virtualFile in contents.getFiles():
            filename = virtualFile.getFilename()
            if virtualFile.isDirectory():
                subfolders.append(filename)
            elif filename.getExtension() in self.FileExtensions:
                filename.makeRelativeTo(self.rootFilenameAbs)
                assetFiles.append(filename)
                gotHit = True

        thisFolder = AssetFolder(dirFilename, parentModelFolder)
        thisFolder.assetFiles = assetFiles

        gotChildHits = False
        for sub in subfolders:
            _, ret = self.r_generateAssets(sub, thisFolder)
            if not gotChildHits:
                gotChildHits = ret

        if parentModelFolder and (gotChildHits or gotHit):
            parentModelFolder.children.append(thisFolder)

        return [thisFolder, gotHit or gotChildHits]

    def r_createFilesList(self, folder):
        self.files += folder.assetFiles
        for child in folder.children:
            self.r_createFilesList(child)

    def generateAssetTree(self):
        self.rootFilename = core.Filename("resources")
        self.rootFilenameAbs = core.Filename(self.rootFilename)
        self.rootFilenameAbs.makeAbsolute()
        self.rootFolder = self.r_generateAssets(self.rootFilename, None)[0]

    def generateAssets(self):
        if self.folderContext:
            self.folderContext.cleanup()

        self.ui.fileView.clear()
        self.files = []
        self.r_createFilesList(self.currentFolder)
        self.files.sort()

        # Generate the assets thumbnails in the selected folder
        ctx = AssetCreationContext(self, self.files, self.ui.fileView, True)
        ctx.createNextAsset()
        self.folderContext = ctx

    def hide(self, ret):
        self.setParent(None)
        if self.folderContext:
            if not self.folderContext.done:
                self.folderContext.pause()
            else:
                self.folderContext.cleanup()
                self.folderContext = None
        if self.recentlyUsedContext:
            self.recentlyUsedContext.cleanup()
            self.recentlyUsedContext = None
        if ret and self.selectedAsset:
            fullpath = self.selectedAsset.getFullpath()
            if not fullpath in self.recentlyUsed:
                self.recentlyUsed.insert(0, fullpath)
        if self.callback:
            self.callback(ret, self.selectedAsset)
            self.callback = None

        QtWidgets.QDialog.hide(self)

    def done(self, ret):
        self.hide(ret)
