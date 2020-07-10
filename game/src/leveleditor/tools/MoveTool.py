from panda3d.core import NodePath, CardMaker, Vec4, Quat, Vec3, SamplerState, OmniBoundingVolume, BillboardEffect
from panda3d.core import CollisionBox, CollisionNode, CollisionTraverser, CollisionHandlerQueue, BitMask32, Point3
from panda3d.core import LPlane, LineSegs

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
        self.reparentTo(self.tool.moveToolRoot)

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
        self.moveToolRoot = base.render.attachNewNode("moveToolRoot")
        self.moveVisRoot = self.moveToolRoot.attachNewNode("moveVisRoot")
        self.moveVisRoot.setTransparency(True, 1)
        self.moveVisRoot.setColorScale(1, 1, 1, 0.5, 1)
        self.moveAxis3DLine = None
        self.isMoving = False
        self.movingObjects = []

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
        self.moveToolRoot.setPos(avg)
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
            self.preTransformStart = self.moveToolRoot.getPos()

    def mouseUp(self):
        SelectTool.mouseUp(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Rollover)

        if self.isMoving:
            # We finished moving some objects, apply the ghost position
            # to the actual position
            for obj, instRoot, inst in self.movingObjects:
                obj.np.setPos(render, inst.getPos(render))
            self.destroyMoveVis()
            base.selectionMgr.updateSelectionBounds()
        self.isMoving = False

    def applyPosition(self, axis, absolute, updateBox = False):
        currPos = self.moveToolRoot.getPos()
        currPos[axis] = absolute[axis]
        self.moveToolRoot.setPos(currPos)

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

    def createMoveVis(self):
        # Instance each selected map object to the vis root
        for obj in base.selectionMgr.selectedObjects:
            instRoot = NodePath("instRoot")
            inst = obj.np.instanceTo(instRoot)
            instRoot.wrtReparentTo(self.moveVisRoot)
            self.movingObjects.append((obj, instRoot, inst))

        # Show an infinite line along the axis we are moving the object
        # if we are using the 3D view
        if self.widget.activeAxis:
            axis = self.widget.activeAxis.axisIdx
            segs = LineSegs()
            col = Vec4(0, 0, 0, 1)
            col[axis] = 1.0
            segs.setColor(col)
            p = Point3(0)
            p[axis] = -1000000
            segs.moveTo(p)
            p[axis] = 1000000
            segs.drawTo(p)
            self.moveAxis3DLine = self.moveToolRoot.attachNewNode(segs.create())
            self.moveAxis3DLine.setLightOff(1)
            self.moveAxis3DLine.setFogOff(1)

        self.widget.stash()

    def destroyMoveVis(self):
        for obj, instRoot, inst in self.movingObjects:
            inst.removeNode()
        self.movingObjects = []
        if self.moveAxis3DLine:
            self.moveAxis3DLine.removeNode()
            self.moveAxis3DLine = None
        self.widget.unstash()

    def mouseMove(self, vp):

        if vp and vp.is3D() and self.mouseIsDown and self.widget.activeAxis:
            if not self.isMoving:
                self.createMoveVis()
                self.isMoving = True
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
                    self.moveBox(absolute, axis = axis)
                    self.hideBox()
                    self.showText()
        else:
            if not self.isMoving and self.state.action in [BoxAction.DownToResize, BoxAction.Resizing]:
                self.createMoveVis()
                self.isMoving = True
            SelectTool.mouseMove(self, vp)

    def update(self):
        SelectTool.update(self)
        if self.hasWidgets:
            self.widget.update()
            if self.widget.activeAxis or self.state.action in [BoxAction.ReadyToResize, BoxAction.DownToResize]:
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
        if self.isMoving:
            self.destroyMoveVis()
        self.isMoving = False
