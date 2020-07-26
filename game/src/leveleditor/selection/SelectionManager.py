from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, GeomNode

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.objectproperties.ObjectPropertiesWindow import ObjectPropertiesWindow
from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK
from src.leveleditor import RenderModes
from src.leveleditor import LEGlobals
from .SelectionType import SelectionType
from src.leveleditor.actions.Delete import Delete

from enum import IntEnum

Bounds3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

Bounds2DState = RenderModes.DashedLineNoZ()
Bounds2DState = Bounds2DState.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))

class SelectionManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.selectedObjects = []
        self.selectionMins = Point3()
        self.selectionMaxs = Point3()
        self.selectionCenter = Point3()

        # We'll select groups by default
        self.selectionModes = {}
        self.selectionMode = None

        self.accept('delete', self.deleteSelectedObjects)
        self.accept('objectTransformChanged', self.handleObjectTransformChange)
        self.accept('mapObjectBoundsChanged', self.handleMapObjectBoundsChanged)

        self.addSelectionModes()

        self.setSelectionMode(SelectionType.Groups)

    def getSelectionKey(self):
        return self.selectionMode.Key

    def getSelectionMask(self):
        return self.selectionMode.Mask

    def isTransformAllowed(self, bits):
        return (self.selectionMode.TransformBits & bits) != 0

    def addSelectionMode(self, modeInst):
        self.selectionModes[modeInst.Type] = modeInst

    def addSelectionModes(self):
        from .GroupsMode import GroupsMode
        from .ObjectMode import ObjectMode
        from .FaceMode import FaceMode
        from .VertexMode import VertexMode
        self.addSelectionMode(GroupsMode(self))
        self.addSelectionMode(ObjectMode(self))
        self.faceMode = FaceMode(self)
        self.addSelectionMode(self.faceMode)
        self.addSelectionMode(VertexMode(self))

    def setSelectionMode(self, mode):
        if mode != self.selectionMode and self.selectionMode is not None:
            # Deselect everything from our old mode.
            self.deselectAll()
            self.selectionMode.disable()
        self.selectionMode = self.selectionModes[mode]
        self.selectionMode.enable()

    def handleMapObjectBoundsChanged(self, mapObject):
        if mapObject in self.selectedObjects:
            self.updateSelectionBounds()
            messenger.send('selectedObjectBoundsChanged', [mapObject])

    def handleObjectTransformChange(self, entity):
        if entity in self.selectedObjects:
            self.updateSelectionBounds()
            messenger.send('selectedObjectTransformChanged', [entity])

    def deleteSelectedObjects(self):
        if not self.selectionMode.CanDelete:
            # This mode doesn't allow deleting our selected objects.
            return

        selected = list(self.selectedObjects)
        base.actionMgr.performAction(Delete(selected))
        self.selectedObjects = []
        self.updateSelectionBounds()
        messenger.send('selectionsChanged')

    def hasSelectedObjects(self):
        return len(self.selectedObjects) > 0

    def getNumSelectedObjects(self):
        return len(self.selectedObjects)

    def isSelected(self, obj):
        return obj in self.selectedObjects

    def deselectAll(self, update = True):
        for obj in self.selectedObjects:
            obj.deselect()
        self.selectedObjects = []
        if update:
            self.updateSelectionBounds()
            messenger.send('selectionsChanged')

    def singleSelect(self, obj):
        self.deselectAll(False)
        self.select(obj)

    def multiSelect(self, listOfObjs):
        self.deselectAll(False)
        for obj in listOfObjs:
            self.select(obj, False)
        self.updateSelectionBounds()
        messenger.send('selectionsChanged')

    def deselect(self, obj, updateBounds = True):
        if obj in self.selectedObjects:
            self.selectedObjects.remove(obj)
            obj.deselect()

            if updateBounds:
                self.updateSelectionBounds()
                messenger.send('selectionsChanged')

    def select(self, obj, updateBounds = True):
        if not obj in self.selectedObjects:
            self.selectedObjects.append(obj)
            obj.select()

            if updateBounds:
                self.updateSelectionBounds()
                messenger.send('selectionsChanged')

    def updateSelectionBounds(self):

        if len(self.selectedObjects) == 0:
            base.qtWindow.selectedLabel.setText("No selection.")
            self.selectionMins = Point3()
            self.selectionMaxs = Point3()
            self.selectionCenter = Point3()
            return
        else:
            if len(self.selectedObjects) == 1:
                obj = self.selectedObjects[0]
                base.qtWindow.selectedLabel.setText(obj.getName())
            else:
                base.qtWindow.selectedLabel.setText("Selected %i objects." % len(self.selectedObjects))

        mins = Point3(9999999)
        maxs = Point3(-9999999)

        for obj in self.selectedObjects:
            objMins = Point3()
            objMaxs = Point3()
            obj.np.calcTightBounds(objMins, objMaxs)
            if objMins.x < mins.x:
                mins.x = objMins.x
            if objMins.y < mins.y:
                mins.y = objMins.y
            if objMins.z < mins.z:
                mins.z = objMins.z
            if objMaxs.x > maxs.x:
                maxs.x = objMaxs.x
            if objMaxs.y > maxs.y:
                maxs.y = objMaxs.y
            if objMaxs.z > maxs.z:
                maxs.z = objMaxs.z

        self.selectionMins = mins
        self.selectionMaxs = maxs
        self.selectionCenter = (mins + maxs) / 2.0
