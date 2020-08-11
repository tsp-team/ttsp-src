from panda3d.core import CollisionBox, CollisionNode, BitMask32, CollisionHandlerQueue

from src.leveleditor.DocObject import DocObject
from .SelectionType import SelectionType, SelectionModeTransform

from src.leveleditor.menu.KeyBind import KeyBind
from src.leveleditor.actions.Select import Select, Deselect
from src.leveleditor import LEUtils

class SelectionMode(DocObject):

    Type = SelectionType.Nothing
    # Collision mask used for the mouse click ray
    Mask = 0
    # The key to locate the object from what we clicked on
    Key = None
    # Can we delete the selected objects?
    CanDelete = True
    # Can we clone/duplicate the selected objects?
    CanDuplicate = True
    # What kinds of transform can we apply?
    TransformBits = SelectionModeTransform.All
    ToolOnly = True

    def __init__(self, mgr):
        DocObject.__init__(self, mgr.doc)
        self.mgr = mgr
        self.enabled = False
        self.activated = False
        self.properties = None
        self.entryIdx = 0
        self.lastEntries = None

    def toggleSelect(self, obj, appendSelect):
        if not appendSelect:
            if not self.mgr.isSelected(obj) or self.mgr.getNumSelectedObjects() > 1:
                base.actionMgr.performAction("Select %s" % obj.getName(), Select([obj], True))
        else:
            # In multi-select (shift held), if the object we clicked on has
            # already been selected, deselect it.
            if self.mgr.isSelected(obj):
                base.actionMgr.performAction("Deselect %s" % obj.getName(), Deselect([obj]))
            else:
                base.actionMgr.performAction("Append select %s" % obj.getName(), Select([obj], False))

    def getObjectUnderMouse(self, index = 0):
        vp = base.viewportMgr.activeViewport
        if not vp:
            return None

        entries = vp.click(self.Mask)
        if not entries or len(entries) == 0:
            return None

        objIndex = 0
        key = self.Key
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
                if index == objIndex:
                    return [obj, entries]
                else:
                    objIndex += 1

        return None

    def selectObjectUnderMouse(self, appendSelect = False):
        ret = self.getObjectUnderMouse()

        if ret:
            self.toggleSelect(ret[0], appendSelect)
            return ret[0]

        return None

    def selectObjectsInBox(self, mins, maxs):
        selection = []

        # Create a one-off collision box, traverser, and queue to test against all MapObjects
        box = CollisionBox(mins, maxs)
        node = CollisionNode("selectToolCollBox")
        node.addSolid(box)
        node.setFromCollideMask(self.Mask)
        node.setIntoCollideMask(BitMask32.allOff())
        boxNp = self.doc.render.attachNewNode(node)
        queue = CollisionHandlerQueue()
        base.clickTraverse(boxNp, queue)
        queue.sortEntries()
        key = self.Key
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

    def deselectAll(self):
        self.lastEntries = None
        self.entryIdx = 0

        if base.selectionMgr.hasSelectedObjects():
            base.actionMgr.performAction("Deselect all", Deselect(all = True))

    def deleteSelectedObjects(self):
        base.selectionMgr.deleteSelectedObjects()

    def cleanup(self):
        self.mgr = None
        self.enabled = None
        self.activatated = None
        self.properties = None
        self.lastEntries = None
        self.entryIdx = None
        DocObject.cleanup(self)

    def enable(self):
        self.enabled = True
        self.activate()

    def activate(self):
        self.activated = True
        if not self.ToolOnly:
            self.__activate()

    def disable(self):
        self.enabled = False
        self.toolDeactivate()
        self.deactivate()

    def deactivate(self, docChange = False):
        if not self.ToolOnly:
            self.__deactivate()

    def toolActivate(self):
        if self.ToolOnly:
            self.__activate()

    def toolDeactivate(self):
        if self.ToolOnly:
            self.__deactivate()

    def __activate(self):
        if self.CanDelete:
            base.menuMgr.connect(KeyBind.Delete, self.deleteSelectedObjects)

        self.updateModeActions()

        if self.properties and self.doc.toolMgr:
            base.toolMgr.toolProperties.addGroup(self.properties)
            self.properties.updateForSelection()
        self.accept('selectionsChanged', self.onSelectionsChanged)

    def __deactivate(self):
        if self.CanDelete:
            base.menuMgr.disconnect(KeyBind.Delete, self.deleteSelectedObjects)
        self.activated = False
        self.lastEntries = None
        self.entryIdx = 0
        if self.properties and self.doc.toolMgr:
            base.toolMgr.toolProperties.removeGroup(self.properties)
        self.ignoreAll()

    def updateModeActions(self):
        if self.CanDelete:
            if len(self.mgr.selectedObjects) == 0:
                base.menuMgr.disableAction(KeyBind.Delete)
            else:
                base.menuMgr.enableAction(KeyBind.Delete)

    def onSelectionsChanged(self):
        self.updateModeActions()
        if self.properties:
            self.properties.updateForSelection()

    def getProperties(self):
        return self.properties

    # Returns a list of objects that will be selected
    # when switching to this mode from prevMode.
    def getTranslatedSelections(self, prevMode):
        return []
