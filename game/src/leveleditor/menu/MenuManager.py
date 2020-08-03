# Purpose: Manages the QActions that are bound to hotkeys

from .Hotkey import Hotkey, Separator
from .KeyBind import KeyBind
from .KeyBinds import KeyBindsByID

from src.leveleditor import LEGlobals

from PyQt5 import QtWidgets, QtGui

class MenuManager:

    def __init__(self):
        # Key bind ID -> QAction
        self.actions = {}

    def enableAction(self, keyBindID):
        action = self.actions.get(keyBindID, None)
        if action:
            action.setEnabled(True)

    def disableAction(self, keyBindID):
        action = self.actions.get(keyBindID, None)
        if action:
            action.setEnabled(False)

    def addAction(self, keyBindID, text, desc, icon = None, toolBar = False, checkable = False, menu = None):
        if icon is not None:
            icon = QtGui.QIcon(icon)
        action = QtWidgets.QAction(icon, text, base.qtWindow)
        action.setCheckable(checkable)
        action.setToolTip(desc)
        action.setStatusTip(desc)
        action.setIconVisibleInMenu(False)
        action.setShortcutVisibleInContextMenu(True)
        if toolBar:
            base.topBar.addAction(action)
        if menu:
            menu.addAction(action)
        keyBind = KeyBindsByID[keyBindID]
        action.setShortcut(keyBind.shortcut)
        action.keyBind = keyBind
        self.actions[keyBindID] = action
        return action

    def addMenuItems(self):
        fileMenu = QtWidgets.QMenu("File", base.menuBar)
        self.addAction(KeyBind.FileNew, "New", "Create a new map", menu=fileMenu)
        self.addAction(KeyBind.FileOpen, "Open...", "Open an existing map", menu=fileMenu)
        self.addAction(KeyBind.FileSave, "Save", "Save the map", toolBar=True, menu=fileMenu)
        self.addAction(KeyBind.FileSaveAs, "Save As...", "Save the map as", menu=fileMenu)
        self.addAction(KeyBind.FileClose, "Close", "Close the map", toolBar=True, menu=fileMenu)
        fileMenu.addSeparator()
        self.addAction(KeyBind.Exit, "Exit", "Exit %s" % LEGlobals.AppName, menu=fileMenu)

        base.topBar.addSeparator()
