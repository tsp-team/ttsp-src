from panda3d.core import NodePath, CardMaker, Vec4, Quat, Vec3, SamplerState, OmniBoundingVolume, BillboardEffect
from panda3d.core import CollisionBox, CollisionNode, CollisionTraverser, CollisionHandlerQueue, BitMask32, Point3
from panda3d.core import LPlane, LineSegs

from src.leveleditor import LEGlobals
from src.leveleditor import LEUtils
from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK
from src.leveleditor.math.Ray import Ray
from src.leveleditor.actions.EditObjectProperties import EditObjectProperties
from src.leveleditor.selection.SelectionType import SelectionModeTransform

from .SelectTool import SelectTool
from .BoxTool import BoxAction, ResizeHandle

import math

from PyQt5 import QtWidgets, QtCore

# Implementation of move widget:
# Single root move widget node
#  Axis node for X, Y, and Z
#   Instance of each axis to each viewport

Ready = 0
Rollover = 1
Down = 2

Global = 0
Local = 1

class MoveToolOptions(QtWidgets.QDockWidget):

    def __init__(self, tool):
        QtWidgets.QDockWidget.__init__(self)
        self.tool = tool
        self.setWindowTitle("Move Tool")

        group = QtWidgets.QGroupBox("With Respect To", self)
        group.setLayout(QtWidgets.QFormLayout())
        globalBtn = QtWidgets.QRadioButton("Global", group)
        globalBtn.toggled.connect(self.__toggleGlobal)
        group.layout().addWidget(globalBtn)
        localBtn = QtWidgets.QRadioButton("Local", group)
        localBtn.toggled.connect(self.__toggleLocal)
        group.layout().addWidget(localBtn)

        if self.tool.wrtMode == Global:
            globalBtn.setChecked(True)
        elif self.tool.wrtMode == Local:
            localBtn.setChecked(True)

        self.setWidget(group)
        self.hide()
        base.qtWindow.addDockWindow(self)

    def __toggleGlobal(self):
        self.tool.setWrtMode(Global)

    def __toggleLocal(self):
        self.tool.setWrtMode(Local)

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

        self.head = base.loader.loadModel("models/editor/arrow_head.bam")
        self.head.reparentTo(self)
        self.head.setY(0.6)
        self.head.setScale(0.7)

        baseSegs = LineSegs()
        baseSegs.setColor(1, 1, 1, 1)
        baseSegs.setThickness(2.0)
        baseSegs.moveTo(0, 0, 0)
        baseSegs.drawTo(0, 0.6, 0)
        self.base = self.attachNewNode(baseSegs.create())

        box = CollisionBox(Vec3(-0.06, 0.0, -0.06), Vec3(0.06, 0.8, 0.06))
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
        self.boxOriginOffset = Vec3(0, 0, 0)

        # With respect to mode. Gizmo is rotated differently
        # based on this mode.
        self.wrtMode = Global

        self.options = MoveToolOptions(self)

    def setWrtMode(self, mode):
        self.wrtMode = mode
        self.adjustGizmoAngles()

    def adjustGizmoAngles(self):
        if self.wrtMode == Global:
            # Look forward in world space
            self.setGizmoAngles(Vec3(0, 0, 0))

        elif self.wrtMode == Local:
            # Set the gizmo angles to the angles of the most
            # recently selected object.
            if base.selectionMgr.hasSelectedObjects():
                numSelections = base.selectionMgr.getNumSelectedObjects()
                selection = base.selectionMgr.selectedObjects[numSelections - 1]
                self.setGizmoAngles(selection.getAbsAngles())

    def filterHandle(self, handle):
        if base.selectionMgr.hasSelectedObjects():
            return False
        return True

    def setBoxToSelection(self):
        self.state.boxStart = base.selectionMgr.selectionMins
        self.state.boxEnd = base.selectionMgr.selectionMaxs
        # Calculate an offset from the center of the box to the gizmo origin
        # so we can keep the box and gizmo in sync as they move.
        self.boxOriginOffset = self.getGizmoOrigin() - base.selectionMgr.selectionCenter
        self.state.action = BoxAction.Drawn
        self.resizeBoxDone()
        self.showBox()

    def handleSelectedObjectTransformChanged(self, entity):
        # This method unfortunately gets called when we change the transform on
        # the selected objects when finishing the move... changing
        # the widget point while applying the final move position
        # screws it up.
        if not self.isMoving:
            self.calcWidgetPoint()

    def selectionChanged(self):
        if base.selectionMgr.hasSelectedObjects() \
            and base.selectionMgr.isTransformAllowed(SelectionModeTransform.Translate):
            if not self.hasWidgets:
                self.enableWidget()
            else:
                self.calcWidgetPoint()
        elif self.hasWidgets:
            self.disableWidget()
            self.maybeCancel()

    def calcWidgetPoint(self, updateBox = True):
        # Set the gizmo to the average origin of all the selected objects.
        avg = Point3(0)
        for obj in base.selectionMgr.selectedObjects:
            avg += obj.getAbsOrigin()
        avg /= len(base.selectionMgr.selectedObjects)
        self.setGizmoOrigin(avg)
        self.adjustGizmoAngles()
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
                self.moveStart = self.getPointOnGizmo()
            self.preTransformStart = self.getGizmoOrigin()

    def mouseUp(self):
        SelectTool.mouseUp(self)
        if self.widget.activeAxis:
            self.widget.activeAxis.setState(Rollover)

        if self.isMoving:
            # We finished moving some objects, apply the ghost position
            # to the actual position
            for obj, instRoot, inst in self.movingObjects:
                # Set it through the entity property so the change reflects in the
                # object properties panel.
                action = EditObjectProperties(obj, {"origin": inst.getPos(obj.np.getParent())})
                base.actionMgr.performAction(action)
            self.destroyMoveVis()
            base.selectionMgr.updateSelectionBounds()
        self.isMoving = False

    def getGizmoDirection(self, axis):
        quat = self.moveToolRoot.getQuat(NodePath())
        if axis == 0:
            return quat.getRight()
        elif axis == 1:
            return quat.getForward()
        else:
            return quat.getUp()

    def getGizmoOrigin(self):
        return self.moveToolRoot.getPos(NodePath())

    def setGizmoOrigin(self, origin):
        self.moveToolRoot.setPos(NodePath(), origin)

    def setGizmoAngles(self, angles):
        self.moveToolRoot.setHpr(NodePath(), angles)

    def getGizmoRay(self, axis):
        direction = self.getGizmoDirection(axis)
        origin = self.getGizmoOrigin()
        return Ray(origin, direction)

    def getPointOnGizmo(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is3D():
            return

        axis = self.widget.activeAxis.axisIdx
        gray = self.getGizmoRay(axis)
        mray = vp.getMouseRay()
        # Move into world space
        mray.xform(vp.cam.getMat(NodePath()))

        distance = LEUtils.closestDistanceBetweenLines(gray, mray)

        return gray.origin + (gray.direction * -gray.t)

    def resizeBoxDrag(self):
        SelectTool.resizeBoxDrag(self)

        if self.state.action == BoxAction.Resizing and base.selectionMgr.hasSelectedObjects():
            vp = base.viewportMgr.activeViewport
            boxCenter = (self.state.boxStart + self.state.boxEnd) / 2.0
            self.setGizmoOrigin(boxCenter + self.boxOriginOffset)

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
            instRoot.removeNode()
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
            now = self.getPointOnGizmo()
            axis = self.widget.activeAxis.axisIdx
            absolute = base.snapToGrid(self.preTransformStart + now - self.moveStart)
            self.setGizmoOrigin(absolute)
            self.moveBox(absolute - self.boxOriginOffset)
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
        # The transform may have been changed using the object properties panel.
        # Intercept this event to update our gizmo and stuff.
        self.accept('selectedObjectTransformChanged', self.handleSelectedObjectTransformChanged)
        # Same with bounds
        self.accept('selectedObjectBoundsChanged', self.handleSelectedObjectTransformChanged)
        if base.selectionMgr.hasSelectedObjects() \
            and base.selectionMgr.isTransformAllowed(SelectionModeTransform.Translate):
            self.enableWidget()
        self.options.show()

    def disable(self):
        SelectTool.disable(self)
        self.disableWidget()
        if self.isMoving:
            self.destroyMoveVis()
        self.isMoving = False
        self.options.hide()
