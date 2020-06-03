from .BaseTool import BaseTool
from src.leveleditor import LEGlobals

class SelectTool(BaseTool):

    Name = "Select"
    ToolTip = "Select Tool [SHIFT+S]"
    Shortcut = "shift+s"

    def enable(self):
        BaseTool.enable(self)
        self.accept('mouse1', self.selectSomething)
        self.selectedObjects = []

    def selectSomething(self):
        entries = base.click(LEGlobals.EntityMask)
        if len(entries) == 0:
            self.deselectAll()
        else:
            for i in range(len(entries)):
                entry = entries[i]
                
                np = entry.getIntoNodePath()
                if np.hasPythonTag("mapobject"):
                    obj = np.getPythonTag("mapobject")
                    if not obj.selected:
                        obj.select()
                    if obj not in self.selectedObjects:
                        base.editEntity(obj)
                        self.selectedObjects.append(obj)
                    break

    def deselectAll(self):
        for obj in self.selectedObjects:
            obj.deselect()
        self.selectedObjects = []

    def disable(self):
        BaseTool.disable(self)
        self.deselectAll()