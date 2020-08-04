# Purpose: Manages the QActions that are bound to hotkeys

from .KeyBind import KeyBind
from .KeyBinds import KeyBindsByID

from src.leveleditor import LEGlobals

from PyQt5 import QtWidgets, QtGui, QtCore

class EditorAction(QtWidgets.QAction):

    def __init__(self, text, parent, checkable, keyBindID):
        QtWidgets.QAction.__init__(self, text, parent)
        self.keyBindID = keyBindID
        keyBind = KeyBindsByID[keyBindID]
        self.keyBind = keyBind

    def connect(self, func):
        self.triggered.connect(func)

    def disconnect(self, func):
        self.triggered.disconnect(func)

class MenuManager:

    def __init__(self):
        # Key bind ID -> QAction
        self.actions = {}

    def action(self, id):
        return self.actions[id]

    def connect(self, keyBindID, func):
        self.action(keyBindID).connect(func)

    def disconnect(self, keyBindID, func):
        self.action(keyBindID).disconnect(func)

    def enableAction(self, keyBindID):
        action = self.actions.get(keyBindID, None)
        if action:
            action.setEnabled(True)

    def disableAction(self, keyBindID):
        action = self.actions.get(keyBindID, None)
        if action:
            action.setEnabled(False)

    def addAction(self, keyBindID, text, desc, icon = None, toolBar = False, checkable = False, menu = None, enabled = True):
        action = EditorAction(text, base.qtWindow, checkable, keyBindID)
        if icon is not None:
            icon = QtGui.QIcon(icon)
            action.setIcon(icon)
        action.setCheckable(checkable)
        action.setToolTip(desc)
        action.setStatusTip(desc)
        action.setIconVisibleInMenu(False)
        action.setShortcutVisibleInContextMenu(True)
        action.setEnabled(enabled)
        if toolBar:
            if isinstance(toolBar, bool):
                base.topBar.addAction(action)
            else:
                toolBar.addAction(action)
        if menu:
            menu.addAction(action)
        action.setShortcut(action.keyBind.shortcut)
        self.actions[keyBindID] = action
        return action

    def createToolBar(self, name):
        toolBar = base.qtWindow.addToolBar(name)
        label = QtWidgets.QLabel(name)
        label.setAlignment(QtCore.Qt.AlignCenter)
        toolBar.addWidget(label)
        toolBar.addSeparator()
        return toolBar

    def createMenu(self, name):
        menu = QtWidgets.QMenu(name, base.menuBar)
        base.menuBar.addMenu(menu)
        return menu

    def addMenuItems(self):
        selectToolBar = self.createToolBar("Select")
        editToolBar = self.createToolBar("Editing")

        fileMenu = self.createMenu("File")
        self.addAction(KeyBind.FileNew, "New", "Create a new map", menu=fileMenu)
        self.addAction(KeyBind.FileOpen, "Open...", "Open an existing map", menu=fileMenu)
        self.addAction(KeyBind.FileSave, "Save", "Save the map", toolBar=editToolBar, menu=fileMenu, enabled=False)
        self.addAction(KeyBind.FileSaveAs, "Save As...", "Save the map as", menu=fileMenu, enabled=False)
        self.addAction(KeyBind.FileClose, "Close", "Close the map", toolBar=editToolBar, menu=fileMenu, enabled=False)
        fileMenu.addSeparator()
        self.addAction(KeyBind.Exit, "Exit", "Exit %s" % LEGlobals.AppName, menu=fileMenu)

        editMenu = self.createMenu("Edit")
        self.addAction(KeyBind.Undo, "Undo", "Undo the previous action", menu=editMenu, toolBar=editToolBar, enabled=False)
        self.addAction(KeyBind.Redo, "Redo", "Redo the previous action", menu=editMenu, toolBar=editToolBar, enabled=False)
        editMenu.addSeparator()
        self.addAction(KeyBind.Delete, "Delete", "Delete the selected objects", menu=editMenu, enabled=False)
        self.addAction(KeyBind.Copy, "Copy", "Copy the selected objects", menu=editMenu, enabled=False)
        self.addAction(KeyBind.Paste, "Paste", "Paste the copied objects", menu=editMenu, enabled=False)
        editMenu.addSeparator()
        self.addAction(KeyBind.ToggleGridSnap, "Grid Snap", "Toggle snap to grid", menu=editMenu, enabled=False, toolBar=editToolBar, checkable=True)
        self.addAction(KeyBind.IncGridSize, "Increase Grid Size", "Increase grid size", menu=editMenu, enabled=False, toolBar=editToolBar)
        self.addAction(KeyBind.DecGridSize, "Decrease Grid Size", "Decrease grid size", menu=editMenu, enabled=False, toolBar=editToolBar)

        viewMenu = self.createMenu("View")
        self.addAction(KeyBind.Toggle2DGrid, "2D Grid", "Toggle 2D grid", menu=viewMenu, toolBar=editToolBar, enabled=False, checkable=True)
        self.addAction(KeyBind.Toggle3DGrid, "3D Grid", "Toggle 3D grid", menu=viewMenu, toolBar=editToolBar, enabled=False, checkable=True)

        editMenu.addSeparator()
        selectMenu = editMenu.addMenu("Select")
        self.addAction(KeyBind.SelectGroups, "Groups", "Select groups", menu=selectMenu, toolBar=selectToolBar, checkable=True, enabled=False)
        self.addAction(KeyBind.SelectObjects, "Objects", "Select individual objects", menu=selectMenu, toolBar=selectToolBar, checkable=True, enabled=False)
        self.addAction(KeyBind.SelectFaces, "Faces", "Select solid faces", menu=selectMenu, toolBar=selectToolBar, checkable=True, enabled=False)
        self.addAction(KeyBind.SelectVertices, "Vertices", "Select solid vertices", menu=selectMenu, toolBar=selectToolBar, checkable=True, enabled=False)
