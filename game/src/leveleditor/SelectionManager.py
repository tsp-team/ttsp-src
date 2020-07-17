from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, GeomNode

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.objectproperties.ObjectPropertiesWindow import ObjectPropertiesWindow
from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK
from src.leveleditor import RenderModes
from src.leveleditor import LEGlobals

from enum import IntEnum

Bounds3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

Bounds2DState = RenderModes.DashedLineNoZ()
Bounds2DState = Bounds2DState.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))

class SelectionMode(IntEnum):
    # Select individual MapObjects: entities, solids, etc
    Objects = 0
    # Select groups of MapObjects, i.e. when you click on one MapObject
    # it will select that and everything that it is grouped to.
    Groups = 1
    # Select faces of Solids. This pops up the face edit sheet
    Faces = 2
    # Select vertices of Solids
    Vertices = 3

SelectionModeData = {
    SelectionMode.Objects: ["mapobject", GeomNode.getDefaultCollideMask() | LEGlobals.EntityMask],
    SelectionMode.Groups: ["mapobject", GeomNode.getDefaultCollideMask() | LEGlobals.EntityMask],
    SelectionMode.Faces: ["solidface", LEGlobals.FaceMask],
    SelectionMode.Vertices: ["solidvertex", LEGlobals.VertexMask]
}

class SelectionManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.selectedObjects = []
        self.selectionMins = Point3()
        self.selectionMaxs = Point3()
        self.selectionCenter = Point3()

        # We'll select groups by default
        self.selectionMode = SelectionMode.Groups
        self.calcSelectionMask()

        self.objectProperties = ObjectPropertiesWindow(self)

        self.accept('delete', self.deleteSelectedObjects)
        self.accept('selectionsChanged', self.objectProperties.updateForSelection)
        self.accept('objectTransformChanged', self.handleObjectTransformChange)
        self.accept('mapObjectBoundsChanged', self.handleMapObjectBoundsChanged)

    def setSelectionMode(self, mode):
        if mode != self.selectionMode:
            # Deselect everything from our old mode.
            self.deselectAll()
        self.selectionMode = mode
        self.calcSelectionMask()

    def calcSelectionMask(self):
        self.selectionKey = SelectionModeData[self.selectionMode][0]
        self.selectionMask = SelectionModeData[self.selectionMode][1]

    def handleMapObjectBoundsChanged(self, mapObject):
        if mapObject in self.selectedObjects:
            self.updateSelectionBounds()
            messenger.send('selectedObjectBoundsChanged', [mapObject])

    def handleObjectTransformChange(self, entity):
        if entity in self.selectedObjects:
            self.updateSelectionBounds()
            messenger.send('selectedObjectTransformChanged', [entity])

    def deleteSelectedObjects(self):
        selected = list(self.selectedObjects)
        for obj in selected:
            base.document.deleteObject(obj)
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
