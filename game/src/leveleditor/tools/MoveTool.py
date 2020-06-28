from panda3d.core import NodePath, CardMaker, Vec4, Quat, Vec3, SamplerState, OmniBoundingVolume, BillboardEffect
from panda3d.core import CollisionBox, CollisionNode, CollisionTraverser, CollisionHandlerQueue, BitMask32, Point3
from panda3d.core import LPlane

from src.leveleditor import LEGlobals

from .SelectTool import SelectTool

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

        box = CollisionBox(Vec3(-0.025, 0.2, -0.025), Vec3(0.025, 1.0, 0.025))
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

class MoveWidgetInstance(NodePath):

    def __init__(self, widget, vp):
        NodePath.__init__(self, "vpInstance")
        self.widget = widget
        self.vp = vp
        self.reparentTo(self.widget)
        self.hide(~vp.getViewportMask())

        self.axisInstances = {}
        for axis in vp.getGizmoAxes():
            inst = self.widget.axes[axis].instanceTo(self)
            self.axisInstances[axis] = inst

    def testAgainstRect(self, point, mins, maxs):
        return point.x >= mins.x and point.x <= maxs.x \
            and point.z >= mins.z and point.z <= maxs.z

    def update(self):
        activeVp = base.viewportMgr.activeViewport

        if self.vp.is3D():
            distance = self.getPos(self.vp.cam).length()
            self.setScale(distance / 4)
        else:
            self.setScale(20 / self.vp.zoom)

        if self.widget.tool.mouseIsDown:
            return

        if activeVp == self.vp:
            self.widget.setActiveAxis(None)

            if self.vp.is2D():
                mouse = self.vp.getMouse()
                worldMouse = self.vp.viewportToWorld(mouse, flatten = True)
                for axis, inst in self.axisInstances.items():
                    mins = Point3()
                    maxs = Point3()
                    inst.calcTightBounds(mins, maxs, base.render)
                    mins = self.vp.flatten(mins)
                    maxs = self.vp.flatten(maxs)
                    if self.testAgainstRect(worldMouse, mins, maxs):
                        self.widget.setActiveAxis(axis)
                        break
            else:
                entries = self.vp.click(LEGlobals.ManipulatorMask, self.widget.widgetQueue,
                                        self.widget.widgetTrav, self)
                if entries and len(entries) > 0:
                    entry = entries[0]
                    axisObj = entry.getIntoNodePath().getPythonTag("widgetAxis")
                    self.widget.setActiveAxis(axisObj.axisIdx)


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
        self.setPos(32, 64, 32)

        #self.setScale(32)

        self.activeAxis = None

        self.axes = {}
        for axis in (0, 1, 2):
            self.axes[axis] = MoveWidgetAxis(self, axis)

        self.vpWidgets = []
        for vp in base.viewportMgr.viewports:
            self.vpWidgets.append(MoveWidgetInstance(self, vp))

    def setActiveAxis(self, axis):
        if self.activeAxis:
            self.activeAxis.setState(Ready)
        if axis is None:
            self.activeAxis = None
        else:
            self.activeAxis = self.axes[axis]
            self.activeAxis.setState(Rollover)

    def update(self):
        for vp in self.vpWidgets:
            vp.update()

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

    def selectionChanged(self):
        if base.selectionMgr.hasSelectedObjects():
            if not self.hasWidgets:
                self.enableWidget()
            else:
                self.calcWidgetPoint()
        elif self.hasWidgets:
            self.disableWidget()

    def calcWidgetPoint(self):
        avg = Point3(0)
        for obj in base.selectionMgr.selectedObjects:
            avg += obj.np.getPos(base.render)
        avg /= len(base.selectionMgr.selectedObjects)
        self.widget.setPos(avg)

    def mouseDown(self):
        SelectTool.mouseDown(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Down)
            vp = base.viewportMgr.activeViewport
            if vp.is2D():
                self.moveStart = vp.viewportToWorld(vp.getMouse(), flatten = False)
            else:
                self.moveStart = self.getPointOnPlane()
            self.preTransformStart = self.widget.getPos()

    def mouseUp(self):
        SelectTool.mouseUp(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Rollover)

    def applyMovementDelta(self, axis, delta):
        for obj in base.selectionMgr.selectedObjects:
            currPos = obj.np.getPos(render)
            currPos[axis] += delta
            obj.np.setPos(render, currPos)
        self.calcWidgetPoint()
        base.selectionMgr.updateSelectionBounds()

    def getPointOnPlane(self):
        vp = base.viewportMgr.activeViewport
        if not vp.is3D():
            return
        axis = self.widget.activeAxis.axisIdx
        worldMouse = vp.viewportToWorld(vp.getMouse())
        vec = Vec3(0)
        vec[self.widget.activeAxis.axisIdx] = 1.0
        vec = vec.cross(Vec3.up())
        offset = self.widget.getPos()[idx]
        movePlane = LPlane(vec[0], vec[1], vec[2], 0)
        pointOnPlane = Point3()
        ret = movePlane.intersectsLine(pointOnPlane, vp.cam.getPos(render), worldMouse)
        assert ret, "Line did not intersect move plane"
        return pointOnPlane

    def mouseMove(self, vp):
        if vp and self.mouseIsDown and self.widget.activeAxis:
            mouse = vp.getMouse()
            if vp.is2D():
                # 2D is easy, just use the mouse coordinates projected into the
                # 2D world as the movement value
                worldMouse = base.snapToGrid(vp.viewportToWorld(mouse, flatten = False))
                axis = self.widget.activeAxis.axisIdx
                currWidget = self.widget.getPos()[axis]
                newPos = worldMouse[axis]
                delta = newPos - currWidget
                self.applyMovementDelta(axis, delta)
            else:
                # 3D is a little more complicated. We need to define a plane parallel to the selected
                # axis, intersect the line from our camera to the 3D mouse position against the plane,
                # and use the intersection point as the movement value.
                axis = self.widget.activeAxis.axisIdx
                now = base.snapToGrid(self.getPointOnPlane())[axis]
                axis = self.widget.activeAxis.axisIdx
                currWidget = self.widget.getPos()[axis]
                newPos = pointOnPlane[axis]
                delta = newPos - currWidget
                self.applyMovementDelta(axis, delta)
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
