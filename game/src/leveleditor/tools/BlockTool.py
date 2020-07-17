from .BoxTool import BoxTool

from src.leveleditor import MaterialPool

class BlockTool(BoxTool):

    Name = "Block"
    ToolTip = "Block Tool [SHIFT+S]"
    Shortcut = "shift+s"
    Icon = "resources/icons/editor-block.png"

    def boxDrawnConfirm(self):
        base.brushMgr.brushes[0].create(self.state.boxStart, self.state.boxEnd,
            MaterialPool.getMaterial("materials/dev/dev_measuregeneric01b.mat"), 2)
