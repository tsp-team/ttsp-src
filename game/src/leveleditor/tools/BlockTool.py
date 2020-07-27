from panda3d.core import Point3

from .BoxTool import BoxTool
from src.leveleditor.actions.Create import MultiCreate
from src.leveleditor.grid.GridSettings import GridSettings

from src.leveleditor import MaterialPool

class BlockTool(BoxTool):

    Name = "Block"
    ToolTip = "Block Tool [SHIFT+S]"
    Shortcut = "shift+s"
    Icon = "resources/icons/editor-block.png"

    def __init__(self):
        BoxTool.__init__(self)
        self.lastBox = None

    def leftMouseDownToDraw(self):
        BoxTool.leftMouseDownToDraw(self)

        vp = base.viewportMgr.activeViewport
        if self.lastBox is not None:
            self.state.boxStart += vp.getUnusedCoordinate(self.lastBox[0])
            self.state.boxEnd += vp.getUnusedCoordinate(self.lastBox[1])
        else:
            self.state.boxEnd += vp.getUnusedCoordinate(Point3(GridSettings.DefaultStep))

        self.onBoxChanged()

    def boxDrawnConfirm(self):
        box = [self.state.boxStart, self.state.boxEnd]
        if box[0].x != box[1].x and box[0].y != box[1].y and box[0].z != box[1].z:
            solids = base.brushMgr.brushes[0].create(self.state.boxStart, self.state.boxEnd,
                MaterialPool.getMaterial("materials/dev/dev_measuregeneric01b.mat"), 2)

            creations = []
            for solid in solids:
                creations.append((base.document.world.id, solid))
            base.actionMgr.performAction("Create %i solid(s)" % len(creations), MultiCreate(creations))

            self.lastBox = box

    def boxDrawnCancel(self):
        self.lastBox = [self.state.boxStart, self.state.boxEnd]
