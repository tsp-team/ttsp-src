from panda3d.core import NodePath, CardMaker, Vec4, Quat, Vec3, SamplerState, OmniBoundingVolume, BillboardEffect
from panda3d.core import CollisionBox, CollisionNode, CollisionTraverser, CollisionHandlerQueue, BitMask32, Point3
from panda3d.core import LPlane

from src.leveleditor import LEGlobals
from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK

from .SelectTool import SelectTool
from .BoxTool import BoxAction, ResizeHandle

import math

# Implementation of move widget:
# Single root move widget node
#  Axis node for X, Y, and Z
#   Instance of each axis to each viewport

Ready = 0
Rollover = 1
Down = 2

class MoveWidgetAxis(NodePath):

    def __init__(self, widget, axis):
        NodePath.__init__(self, "moveWidgetAxis")
        self.reparentTo(widget)
        self.widget = widget
        vec = Vec3(0)
        vec[axis] = 1.0
        self.defaultColor = Vec4(vec[0], vec[1], vec[2], 1.0)
        self.rolloverColor = Vec4(vec + 0.5, 1.0)
        self.downColor = Vec4(vec - 0.5, 1.0)
        self.lookAt(vec)

        self.axisIdx = axis

        self.axis = base.loader.loadModel("models/editor/arrow.bam")
        self.axis.reparentTo(self)

        box = CollisionBox(Vec3(-0.035, 0.2, -0.035), Vec3(0.035, 1.0, 0.035))
        cnode = CollisionNode("pickBox")
        cnode.addSolid(box)
        cnode.setIntoCollideMask(LEGlobals.ManipulatorMask)
        cnode.setFromCollideMask(BitMask32.allOff())
        self.pickNp = self.attachNewNode(cnode)
        self.pickNp.setPythonTag("widgetAxis", self)

        self.setState(Ready)

    def setState(self, state):
        self.state = state
        if state == Ready:
            self.setColorScale(self.defaultColor)
        elif state == Rollover:
            self.setColorScale(self.rolloverColor)
        elif state == Down:
            self.setColorScale(self.downColor)

class MoveWidget(NodePath):

    def __init__(self, tool):
        self.tool = tool
        NodePath.__init__(self, "moveWidget")
        self.widgetQueue = CollisionHandlerQueue()
        self.widgetTrav = CollisionTraverser()
        self.setLightOff(1)
        self.setFogOff(1)
        self.setDepthWrite(False, 1)
        self.setDepthTest(False, 1)
        self.setBin("unsorted", 60)
        self.hide(~VIEWPORT_3D_MASK)

        self.vp = None
        for vp in base.viewportMgr.viewports:
            if vp.is3D():
                self.vp = vp
                break

        self.activeAxis = None

        self.axes = {}
        for axis in (0, 1, 2):
            self.axes[axis] = MoveWidgetAxis(self, axis)

    def setActiveAxis(self, axis):
        if self.activeAxis:
            self.activeAxis.setState(Ready)
        if axis is None:
            self.activeAxis = None
        else:
            self.activeAxis = self.axes[axis]
            self.activeAxis.setState(Rollover)

    def update(self):
        distance = self.getPos(self.vp.cam).length()
        self.setScale(distance / 4)

        if self.tool.mouseIsDown or base.viewportMgr.activeViewport != self.vp:
            return

        self.setActiveAxis(None)
        entries = self.vp.click(LEGlobals.ManipulatorMask, self.widgetQueue,
                                self.widgetTrav, self)
        if entries and len(entries) > 0:
            entry = entries[0]
            axisObj = entry.getIntoNodePath().getPythonTag("widgetAxis")
            self.setActiveAxis(axisObj.axisIdx)

    def enable(self):
        self.reparentTo(base.render)

    def disable(self):
        self.reparentTo(NodePath())

class MoveTool(SelectTool):

    Name = "Move"
    ToolTip = "Move Tool [SHIFT+W]"
    Shortcut = "shift+w"
    Icon = "resources/icons/editor-move.png"

    def __init__(self):
        SelectTool.__init__(self)
        self.hasWidgets = False
        self.widget = MoveWidget(self)
        self.moveStart = Point3(0)
        self.preTransformStart = Point3(0)

    def filterHandle(self, handle):
        if base.selectionMgr.hasSelectedObjects():
            return False
        return True

    def setBoxToSelection(self):
        self.state.boxStart = base.selectionMgr.selectionMins
        self.state.boxEnd = base.selectionMgr.selectionMaxs
        self.state.action = BoxAction.Drawn
        self.resizeBoxDone()
        self.hideBox()
        self.showText()

    def selectionChanged(self):
        if base.selectionMgr.hasSelectedObjects():
            if not self.hasWidgets:
                self.enableWidget()
            else:
                self.calcWidgetPoint()
        elif self.hasWidgets:
            self.disableWidget()
            self.maybeCancel()

    def calcWidgetPoint(self, updateBox = True):
        avg = Point3(0)
        for obj in base.selectionMgr.selectedObjects:
            avg += obj.np.getPos(base.render)
        avg /= len(base.selectionMgr.selectedObjects)
        self.widget.setPos(avg)
        if updateBox:
            self.setBoxToSelection()

    def mouseDown(self):
        SelectTool.mouseDown(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Down)
            vp = base.viewportMgr.activeViewport
            if vp.is2D():
                self.moveStart = vp.viewportToWorld(vp.getMouse(), flatten = False)
            else:
                self.moveStart = self.getPointOnPlane()[0]
            self.preTransformStart = self.widget.getPos()

    def mouseUp(self):
        SelectTool.mouseUp(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Rollover)

    def applyPosition(self, axis, absolute, updateBox = False):
        for obj in base.selectionMgr.selectedObjects:
            offset = obj.np.getPos(self.widget)
            currPos = obj.np.getPos(self.widget.getParent())
            currPos[axis] = absolute[axis] + offset[axis]
            obj.np.setPos(self.widget.getParent(), currPos)

        self.calcWidgetPoint(updateBox)
        base.selectionMgr.updateSelectionBounds()

    def getPointOnPlane(self):
        vp = base.viewportMgr.activeViewport
        if not vp.is3D():
            return
        axis = self.widget.activeAxis.axisIdx
        worldMouse = vp.viewportToWorld(vp.getMouse())
        vecAxis = Vec3(0)
        vecAxis[axis] = 1.0
        planeTangent = vecAxis.cross(worldMouse - vp.cam.getPos(base.render)).normalized()
        planeNormal = vecAxis.cross(planeTangent).normalized()
        movePlane = LPlane(planeNormal, self.widget.getPos())
        pointOnPlane = Point3()
        ret = movePlane.intersectsLine(pointOnPlane, vp.cam.getPos(base.render), worldMouse)
        assert ret, "Line did not intersect move plane"
        return [pointOnPlane, planeNormal]

    def resizeBoxDrag(self):
        SelectTool.resizeBoxDrag(self)

        if self.state.action == BoxAction.Resizing and base.selectionMgr.hasSelectedObjects():
            vp = base.viewportMgr.activeViewport
            absolute = (self.state.boxStart + self.state.boxEnd) / 2.0
            for axis in vp.spec.flattenIndices:
                self.applyPosition(axis, absolute)

    def mouseMove(self, vp):
        if vp and vp.is3D() and self.mouseIsDown and self.widget.activeAxis:
            mouse = vp.getMouse()
            # 3D is a little more complicated. We need to define a plane parallel to the selected
            # axis, intersect the line from our camera to the 3D mouse position against the plane,
            # and use the intersection point as the movement value.
            axis = self.widget.activeAxis.axisIdx
            pointOnPlane, planeNormal = self.getPointOnPlane()
            worldMouse = vp.viewportToWorld(mouse)
            camPos = vp.cam.getPos(render)
            toMouse = (pointOnPlane - camPos).normalized()
            denom = toMouse.dot(planeNormal)
            if denom != 0:
                t = (pointOnPlane - camPos).dot(planeNormal) / denom
                if t >= 0:
                    now = base.snapToGrid(pointOnPlane)
                    absolute = base.snapToGrid(self.preTransformStart + now - self.moveStart)
                    self.applyPosition(axis, absolute, True)
        else:
            SelectTool.mouseMove(self, vp)

    def update(self):
        SelectTool.update(self)
        if self.hasWidgets:
            self.widget.update()
            if self.widget.activeAxis:
                self.suppressSelect = True
            else:
                self.suppressSelect = False
        else:
            self.suppressSelect = False

    def enableWidget(self):
        self.calcWidgetPoint()
        self.widget.enable()
        self.hasWidgets = True

    def disableWidget(self):
        self.widget.disable()
        self.hasWidgets = False

    def enable(self):
        SelectTool.enable(self)
        if base.selectionMgr.hasSelectedObjects():
            self.enableWidget()

    def disable(self):
        SelectTool.disable(self)
        self.disableWidget()
