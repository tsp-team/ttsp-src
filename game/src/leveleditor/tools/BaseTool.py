from PyQt5 import QtGui, QtWidgets

from direct.showbase.DirectObject import DirectObject

class BaseTool(DirectObject):

    Name = "Tool"
    Shortcut = None
    WantButton = True
    ToolTip = "Base tool"

    def __init__(self):
        DirectObject.__init__(self)
        self.enabled = False
        self.button = None

    def createButton(self):
        if self.WantButton:
            self.button = QtWidgets.QAction(base.qtApp.window.toolGroup)
            self.button.setText(self.Name)
            self.button.setToolTip(self.ToolTip)
            self.button.setCheckable(True)
            if self.Shortcut:
                self.button.setShortcut(QtGui.QKeySequence.fromString(self.Shortcut))
            self.button.toggled.connect(self.__handleToggle)

    def __handleToggle(self, toggled):
        if toggled:
            self.enable()
        else:
            self.disable()

    def enable(self):
        print("Enable", self.Name)
        self.enabled = True
        base.toolMgr.currentTool = self

    def disable(self):
        print("Disable", self.Name)
        self.ignoreAll()
        self.enabled = False
        base.toolMgr.currentTool = None
