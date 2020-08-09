from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, NodePath, CollisionBox, CollisionNode, CollisionTraverser, BitMask32
from panda3d.core import CollisionHandlerQueue, GeomNode

from .BoxTool import BoxTool, ResizeHandle, BoxAction
from src.leveleditor import LEGlobals
from src.leveleditor import LEUtils
from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from src.leveleditor.actions.Select import Select, Deselect
from src.leveleditor.menu.KeyBind import KeyBind

from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView

class SelectTool(BoxTool):

    Name = "Select"
    ToolTip = "Select Tool"
    KeyBind = KeyBind.SelectTool
    Icon = "resources/icons/editor-select.png"
    Draw3DBox = False

    def __init__(self, mgr):
        BoxTool.__init__(self, mgr)
        self.box.setColor(Vec4(1, 1, 0, 1))
        self.suppressSelect = False

    def cleanup(self):
        self.suppressSelect = None
        BoxTool.cleanup(self)

    def activate(self):
        BoxTool.activate(self)

        # Update tool properties with the properties of our selection mode.
        props = base.selectionMgr.selectionMode.getProperties()
        if props:
            self.mgr.toolProperties.addGroup(props)

        self.accept('shift-mouse1', self.mouseDown)
        self.accept('shift-mouse1-up', self.mouseUp)
        self.accept('wheel_up', self.wheelUp)
        self.accept('wheel_down', self.wheelDown)
        self.accept('shift', self.shiftDown)
        self.accept('shift-up', self.shiftUp)
        self.accept('escape', self.deselectAll)
        self.accept('selectionsChanged', self.selectionChanged)
        self.accept('selectionModeChanged', self.selectionModeChanged)

    def selectionModeChanged(self, old, mode):
        if old:
            # Remove the old mode properties
            oldProps = old.getProperties()
            if oldProps:
                self.mgr.toolProperties.removeGroup(oldProps)

        # Add the new mode properties
        newProps = mode.getProperties()
        if newProps:
            self.mgr.toolProperties.addGroup(newProps)

    def enable(self):
        BoxTool.enable(self)
        self.lastEntries = None
        self.entryIdx = 0

        self.multiSelect = False
        self.mouseIsDown = False

    def shiftDown(self):
        self.multiSelect = True

    def shiftUp(self):
        self.multiSelect = False

    def __toggleSelect(self, obj):
        if not self.multiSelect:
            if not base.selectionMgr.isSelected(obj) or base.selectionMgr.getNumSelectedObjects() > 1:
                base.actionMgr.performAction("Select %s" % obj.getName(), Select([obj], True))
        else:
            # In multi-select (shift held), if the object we clicked on has
            # already been selected, deselect it.
            if base.selectionMgr.isSelected(obj):
                base.actionMgr.performAction("Deselect %s" % obj.getName(), Deselect([obj]))
            else:
                base.actionMgr.performAction("Append select %s" % obj.getName(), Select([obj], False))

    def selectionChanged(self):
        pass

    def mouseDown(self):
        vp = base.viewportMgr.activeViewport
        if not vp:
            return

        self.mouseIsDown = True

        BoxTool.mouseDown(self)

        if self.suppressSelect:
            return

        entries = vp.click(base.selectionMgr.getSelectionMask())
        if not entries:
            if (not self.multiSelect) and (self.state.action != BoxAction.ReadyToResize):
                # Deselect all if not doing multi-select and no hits
                self.deselectAll()
            return

        key = base.selectionMgr.getSelectionKey()

        for i in range(len(entries)):
            # Our entries have been sorted by distance, so use the first (closest) one.
            entry = entries[i]
            np = entry.getIntoNodePath().findNetPythonTag(key)
            if not np.isEmpty():
                # Don't backface cull if there is a billboard effect on or above this node
                if not LEUtils.hasNetBillboard(entry.getIntoNodePath()):
                    surfNorm = entry.getSurfaceNormal(vp.cam).normalized()
                    rayDir = entry.getFrom().getDirection().normalized()
                    if surfNorm.dot(rayDir) >= 0:
                        # Backface cull
                        continue
                obj = np.getPythonTag(key)
                self.__toggleSelect(obj)
                break

        self.entryIdx = 0
        self.lastEntries = entries

    def mouseUp(self):
        self.mouseIsDown = False
        vp = base.viewportMgr.activeViewport
        if not vp:
            return
        if vp.is2D():
            BoxTool.mouseUp(self)

    def boxDrawnConfirm(self):
        invalid, mins, maxs = self.getSelectionBox()
        if invalid:
            return

        selection = []

        # Create a one-off collision box, traverser, and queue to test against all MapObjects
        box = CollisionBox(mins, maxs)
        node = CollisionNode("selectToolCollBox")
        node.addSolid(box)
        node.setFromCollideMask(base.selectionMgr.getSelectionMask())
        node.setIntoCollideMask(BitMask32.allOff())
        boxNp = self.doc.render.attachNewNode(node)
        queue = CollisionHandlerQueue()
        base.clickTraverse(boxNp, queue)
        queue.sortEntries()
        key = base.selectionMgr.getSelectionKey()
        entries = queue.getEntries()
        # Select every MapObject our box intersected with
        for entry in entries:
            np = entry.getIntoNodePath().findNetPythonTag(key)
            if not np.isEmpty():
                obj = np.getPythonTag(key)
                if not obj in selection:
                    selection.append(obj)
        boxNp.removeNode()

        if len(selection) > 0:
            base.actionMgr.performAction("Select %i objects" % len(selection), Select(selection, True))

    def wheelUp(self):
        if not self.mouseIsDown:
            return

    def wheelDown(self):
        if not self.mouseIsDown:
            return

    def deselectAll(self):
        self.lastEntries = None
        self.entryIdx = 0

        if base.selectionMgr.hasSelectedObjects():
            base.actionMgr.performAction("Deselect all", Deselect(all = True))

    def disable(self):
        BoxTool.disable(self)
        self.multiSelect = False
        self.mouseIsDown = False
