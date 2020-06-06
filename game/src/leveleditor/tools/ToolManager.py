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
        from src.leveleditor.tools.BoxTool import BoxTool
        self.addTool(SelectTool())
        self.addTool(EntityTool())
        self.addTool(BoxTool())

        base.qtApp.window.toolBar.addActions(base.qtApp.window.toolGroup.actions())

    def getNumTools(self):
        return len(self.tools)