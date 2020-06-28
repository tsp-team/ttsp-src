from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, NodePath

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK
from src.leveleditor import RenderModes

Bounds3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

Bounds2DState = RenderModes.DashedLineNoZ()
Bounds2DState = Bounds2DState.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))

class SelectionManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.selectedObjects = []
        # The box that encompasses all of the selected objects
        self.selectionBounds = Box()
        self.selectionBounds.addView(GeomView.Lines, VIEWPORT_3D_MASK, state = Bounds3DState)
        self.selectionBounds.addView(GeomView.Lines, VIEWPORT_2D_MASK, state = Bounds2DState)
        self.selectionBounds.generateGeometry()
        self.accept('delete', self.deleteSelectedObjects)

    def deleteSelectedObjects(self):
        for obj in self.selectedObjects:
            base.document.deleteObject(obj)
        self.selectedObjects = []
        self.updateSelectionBounds()

    def hasSelectedObjects(self):
        return len(self.selectedObjects) > 0

    def getNumSelectedObject(self):
        return len(self.selectedObjects)

    def isSelected(self, obj):
        return obj in self.selectedObjects

    def deselectAll(self):
        for obj in self.selectedObjects:
            obj.deselect()
        self.selectedObjects = []
        self.updateSelectionBounds()

    def deselect(self, obj):
        if obj in self.selectedObjects:
            self.selectedObjects.remove(obj)
            obj.deselect()

            self.updateSelectionBounds()

    def select(self, obj):
        if not obj in self.selectedObjects:
            self.selectedObjects.append(obj)
            obj.select()

            self.updateSelectionBounds()

    def hideSelectionBounds(self):
        self.selectionBounds.np.reparentTo(NodePath())

    def showSelectionBounds(self):
        self.selectionBounds.np.reparentTo(base.render)

    def updateSelectionBounds(self):
        if len(self.selectedObjects) == 0:
            self.hideSelectionBounds()
            return
        else:
            self.showSelectionBounds()

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

        self.selectionBounds.setMinMax(mins, maxs)
