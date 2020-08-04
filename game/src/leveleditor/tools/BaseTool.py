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
    KeyBind = None
    WantButton = True
    ToolTip = "Base tool"
    StatusTip = None
    Icon = None
    Usage = ToolUsage.Both

    def __init__(self, mgr):
        DirectObject.__init__(self)
        self.enabled = False
        self.activated = False
        self.mgr = mgr
        self.doc = mgr.doc

    def toolTriggered(self):
        pass

    def enable(self):
        print("Enable", self.Name)
        self.enabled = True
        self.activate()

    def activate(self):
        self.activated = True
        base.taskMgr.add(self.__updateTask, self.Name + "-UpdateTool")

    def __updateTask(self, task):
        self.update()
        return task.cont

    def update(self):
        pass

    def disable(self):
        print("Disable", self.Name)
        self.deactivate()
        self.enabled = False

    def deactivate(self):
        self.activated = False
        base.taskMgr.remove(self.Name + "-UpdateTool")
        self.ignoreAll()
