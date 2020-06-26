from direct.showbase.DirectObject import DirectObject

class ToolManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)

        self.tools = []
        self.currentTool = None
        self.selectTool = None
        self.accept('draw2D', self.__draw2D)
        self.accept('draw3D', self.__draw3D)

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
        from src.leveleditor.tools.EntityTool import EntityTool
        from src.leveleditor.tools.BoxTool import BoxTool
        self.selectTool = SelectTool()
        self.addTool(self.selectTool)
        self.addTool(EntityTool())
        self.addTool(BoxTool())
        self.selectTool.toggle()

        base.qtApp.window.toolBar.addActions(base.qtApp.window.toolGroup.actions())

    def getNumTools(self):
        return len(self.tools)
