from direct.showbase.DirectObject import DirectObject

from PyQt5 import QtWidgets

from src.leveleditor.tools.SelectTool import SelectTool
from src.leveleditor.tools.MoveTool import MoveTool
from src.leveleditor.tools.RotateTool import RotateTool
from src.leveleditor.tools.ScaleTool import ScaleTool
from src.leveleditor.tools.EntityTool import EntityTool
from src.leveleditor.tools.BlockTool import BlockTool
from src.leveleditor.tools.ClipTool import ClipTool

from functools import partial

Separator = -1

class ToolManager(DirectObject):

    Tools = [
        SelectTool,
        MoveTool,
        RotateTool,
        ScaleTool,

        Separator,

        EntityTool,
        BlockTool,
        ClipTool
    ]

    def __init__(self, doc):
        DirectObject.__init__(self)

        self.doc = doc
        self.tools = []
        self.currentTool = None
        self.selectTool = None

        self.toolGroup = None

        self.accept('documentActivated', self.__onDocActivated)
        self.accept('documentDeactivated', self.__onDocDeactivated)

    def __onDocActivated(self, doc):
        if doc != self.doc:
            return

        if self.currentTool and not self.currentTool.activated:
            self.currentTool.activate()

        for tool in self.tools:
            base.menuMgr.enableAction(tool.KeyBind)
            base.menuMgr.connect(tool.KeyBind, partial(self.switchToTool, tool))

    def __onDocDeactivated(self, doc):
        if doc != self.doc:
            return

        if self.currentTool and self.currentTool.activated:
            self.currentTool.deactivate()

        for tool in self.tools:
            base.menuMgr.disableAction(tool.KeyBind)
            base.menuMgr.disconnect(tool.KeyBind, partial(self.switchToTool, tool))

    def switchToTool(self, tool):
        if tool == self.currentTool:
            tool.toolTriggered()
            return

        if self.currentTool:
            self.currentTool.disable()

        self.currentTool = tool
        self.currentTool.enable()

    @staticmethod
    def addToolActions():
        toolMenu = base.menuMgr.createMenu("Tools")

        toolBar = base.toolBar
        toolGroup = QtWidgets.QActionGroup(toolBar)
        for tool in ToolManager.Tools:
            if tool == Separator:
                toolBar.addSeparator()
                toolMenu.addSeparator()
            else:
                action = base.menuMgr.addAction(tool.KeyBind, tool.Name, tool.ToolTip,
                    menu=toolMenu, toolBar=toolBar, checkable=True, enabled=False,
                    icon=tool.Icon)
                toolGroup.addAction(action)

    def addTool(self, tool):
        if not tool in self.tools:
            self.tools.append(tool)

    def addTools(self):
        for tool in self.Tools:
            if tool == Separator:
                continue

            self.addTool(tool(self))

    def getNumTools(self):
        return len(self.tools)
