from PyQt5 import QtGui, QtWidgets

from direct.showbase.DirectObject import DirectObject

from enum import IntEnum

# What viewport type can a tool be used in?
class ToolUsage(IntEnum):
    View2D = 0
    View3D = 1
    Both = 2

class BaseTool(DirectObject):

    Name = "Tool"
    Shortcut = None
    WantButton = True
    ToolTip = "Base tool"
    Usage = ToolUsage.Both

    def __init__(self):
        DirectObject.__init__(self)
        self.enabled = False
        self.button = None

    def toggle(self):
        if self.button:
            self.button.toggle()

    def draw2D(self, vp):
        pass

    def draw3D(self, vp):
        pass

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
        base.taskMgr.add(self.__updateTask, self.Name + "-UpdateTool")

    def __updateTask(self, task):
        self.update()
        return task.cont

    def update(self):
        pass

    def disable(self):
        print("Disable", self.Name)
        base.taskMgr.remove(self.Name + "-UpdateTool")
        self.ignoreAll()
        self.enabled = False
        base.toolMgr.currentTool = None
