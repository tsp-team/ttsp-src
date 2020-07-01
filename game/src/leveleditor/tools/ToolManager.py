from direct.showbase.DirectObject import DirectObject

from PyQt5 import QtWidgets

class ToolManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)

        self.tools = []
        self.currentTool = None
        self.selectTool = None
        self.accept('draw2D', self.__draw2D)
        self.accept('draw3D', self.__draw3D)

        self.toolGroup = None

    def __draw2D(self, vp):
        if self.currentTool:
            self.currentTool.draw2D(vp)

    def __draw3D(self, vp):
        if self.currentTool:
            self.currentTool.draw3D(vp)

    def addTool(self, tool):
        if not tool in self.tools:
            tool.createButton()
            self.tools.append(tool)

    def addTools(self):
        from src.leveleditor.tools.SelectTool import SelectTool
        from src.leveleditor.tools.MoveTool import MoveTool
        from src.leveleditor.tools.RotateTool import RotateTool
        from src.leveleditor.tools.ScaleTool import ScaleTool
        from src.leveleditor.tools.EntityTool import EntityTool
        from src.leveleditor.tools.BlockTool import BlockTool

        self.selectTool = SelectTool()
        self.addTool(self.selectTool)
        self.addTool(MoveTool())
        self.addTool(RotateTool())
        self.addTool(ScaleTool())

        base.toolBar.addSeparator()

        self.addTool(EntityTool())
        self.addTool(BlockTool())

        # Now group all of our tools so we can only have one tool
        # selected at a time.
        self.toolGroup = QtWidgets.QActionGroup(base.toolBar)
        for tool in self.tools:
            if tool.button:
                self.toolGroup.addAction(tool.button)

        # Selection tool by default
        self.selectTool.toggle()

    def getNumTools(self):
        return len(self.tools)
