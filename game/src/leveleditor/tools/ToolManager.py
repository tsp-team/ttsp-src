class ToolManager:

    def __init__(self):
        self.tools = []
        self.currentTool = None

    def addTool(self, tool):
        if not tool in self.tools:
            tool.createButton()
            self.tools.append(tool)

    def addTools(self):
        from src.leveleditor.tools.SelectTool import SelectTool
        from src.leveleditor.tools.EntityTool import EntityTool
        self.addTool(SelectTool())
        self.addTool(EntityTool())

        base.qtApp.window.toolBar.addActions(base.qtApp.window.toolGroup.actions())

    def getNumTools(self):
        return len(self.tools)