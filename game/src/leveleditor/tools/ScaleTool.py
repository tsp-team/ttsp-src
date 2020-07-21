from panda3d.core import LineSegs, Vec3, Point3

from .BaseTransformTool import BaseTransformTool, TransformWidget, TransformWidgetAxis

from src.leveleditor.selection.SelectionType import SelectionModeTransform
from src.leveleditor.actions.EditObjectProperties import EditObjectProperties

class ScaleWidgetAxis(TransformWidgetAxis):

    def __init__(self, widget, axis):
        TransformWidgetAxis.__init__(self, widget, axis)
        self.head = base.loader.loadModel("models/editor/scale_head.bam")
        self.head.reparentTo(self)
        self.head.setY(0.6)
        self.head.setScale(0.7)

        baseSegs = LineSegs()
        baseSegs.setColor(1, 1, 1, 1)
        baseSegs.setThickness(2.0)
        baseSegs.moveTo(0, 0, 0)
        baseSegs.drawTo(0, 0.6, 0)
        self.base = self.attachNewNode(baseSegs.create())

    def getClickBox(self):
        return [Vec3(-0.06, 0.0, -0.06), Vec3(0.06, 0.8, 0.06)]

class ScaleWidget(TransformWidget):

    def createAxis(self, axis):
        return ScaleWidgetAxis(self, axis)

class ScaleTool(BaseTransformTool):

    Name = "Scale"
    ToolTip = "Scale Tool [SHIFT+R]"
    Shortcut = "shift+r"
    Icon = "resources/icons/editor-scale.png"

    def __init__(self):
        BaseTransformTool.__init__(self)
        self.transformType = SelectionModeTransform.Scale
        self.startBoxSize = Vec3(0)
        self.initialBoxStart = Vec3(0)
        self.initialBoxEnd = Vec3(0)
        self.startGizmoDelta = Vec3(0)

    def createWidget(self):
        self.widget = ScaleWidget(self)

    def onFinishTransforming(self):
        for obj, _, inst in self.xformObjects:
            transform = inst.getTransform(obj.np.getParent())
            # Jeez, scaling has the possibility of changing everything.
            # The scale definitely changes. If we use the 2D resize,
            # the origin will also change. And if our object has non-zero
            # angles, the angles will be changed, as well as shear.
            action = EditObjectProperties(obj,
                {"origin": transform.getPos(),
                 "scale": transform.getScale(),
                 "shear": transform.getShear(),
                 "angles": transform.getHpr()})
            base.actionMgr.performAction(action)

        # Reset the scaling on the vis root
        self.toolVisRoot.setScale(1)
        self.setBoxToSelection()
        self.adjustGizmoAngles()

    def mouseDown(self):
        BaseTransformTool.mouseDown(self)
        if base.selectionMgr.hasSelectedObjects():
            self.startBoxSize = self.state.boxEnd - self.state.boxStart
            self.initialBoxStart = self.state.boxStart
            self.initialBoxEnd = self.state.boxEnd
            vp = base.viewportMgr.activeViewport
            if vp.is2D() and self.state.handle is not None:
                # Remove gizmo angles if we're in local mode if using the box.
                self.setGizmoAngles(Vec3(0))

    def onSelectedBoxResize(self):
        newSize = self.state.boxEnd - self.state.boxStart
        scaleX = newSize.x / self.startBoxSize.x
        scaleY = newSize.y / self.startBoxSize.y
        scaleZ = newSize.z / self.startBoxSize.z

        scale = Vec3(scaleX, scaleY, scaleZ)

        scaleOffset = Vec3(self.boxOriginOffset)
        scaleOffset.componentwiseMult(scale)
        boxCenter = (self.state.boxStart + self.state.boxEnd) / 2.0
        self.setGizmoOrigin(boxCenter + scaleOffset)

        localScale = self.toolRoot.getRelativeVector(base.render, scale)

        self.toolVisRoot.setScale(scale)

    def onMouseMoveTransforming3D(self, vp):
        initialGizmoDelta = self.transformStart - self.preTransformStart
        now = self.getPointOnGizmo()
        gizmoDelta = now - self.preTransformStart

        scale = Vec3(1)

        axis = self.widget.activeAxis.axisIdx
        if initialGizmoDelta[axis] != 0:
            scale[axis] = gizmoDelta[axis] / initialGizmoDelta[axis]

        self.toolVisRoot.setScale(scale)

        self.setBoxToVisRoot()
