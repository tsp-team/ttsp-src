from panda3d.core import Point3, Vec3, ClipPlaneAttrib, NodePath, PlaneNode, \
    LPlane, RenderState, ColorAttrib, Vec4, TransparencyAttrib, CullFaceAttrib

from .BaseTool import BaseTool
from src.leveleditor.geometry.Polygon import Polygon
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.math.Polygon import Polygon as MathPolygon
from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from src.leveleditor.actions.Clip import Clip
from src.leveleditor.math.Plane import Plane

from enum import IntEnum

class ClipState(IntEnum):
    Off = 0
    Drawing = 1
    Drawn = 2
    MovingPoint1 = 3
    MovingPoint2 = 4
    MovingPoint3 = 5

class ClipSide(IntEnum):
    Both = 0
    Front = 1
    Back = 2

PlaneVis3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(0.5, 0.5, 1.0, 0.5)),
    TransparencyAttrib.make(TransparencyAttrib.MAlpha),
    CullFaceAttrib.make(CullFaceAttrib.MCullNone)
)

PlaneVis2DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1)),
    CullFaceAttrib.make(CullFaceAttrib.MCullNone)
)

class ClipTool(BaseTool):

    Name = "Clip"
    Icon = "resources/icons/editor-slice.png"
    Shortcut = "shift+d"
    ToolTip = "Clip Tool [SHIFT+D]"

    def __init__(self):
        # For this node, we will instance the objects we are slicing to this node
        # then apply a ClipPlaneAttrib to the node with the plane that the user
        # defined
        self.visRoot = base.render.attachNewNode("sliceVisRoot")
        self.visRoot.setColor(1, 0, 1, 1, 50)
        self.planeNode = PlaneNode("clipPlaneNode", Plane())
        self.planeNP = base.render.attachNewNode(self.planeNode)
        self.planeVis = Polygon()
        self.planeVis.addView(GeomView.Triangles, VIEWPORT_3D_MASK, state = PlaneVis3DState)
        self.planeVis.addView(GeomView.LineStrips, VIEWPORT_2D_MASK, state = PlaneVis2DState)
        self.planeVis.setVertices([Point3(1), Point3(2), Point3(3), Point3(4)])
        self.reset()

    def reset(self):
        self.point1 = None
        self.point2 = None
        self.point3 = None
        self.drawingPoint = None
        self.controlIsDown = False
        self.prevState = ClipState.Off
        self.state = ClipState.Off
        self.side = ClipSide.Both
        self.clearClipVis()
        self.planeVis.np.reparentTo(NodePath())

    def enable(self):
        BaseTool.enable(self)
        self.accept('mouse1', self.mouseDown)
        self.accept('mouse1-up', self.mouseUp)
        self.accept('mouseMoved', self.mouseMoved)
        self.accept('control', self.controlDown)
        self.accept('enter', self.confirmClip)

    def confirmClip(self):
        if self.point1 is None or self.point2 is None or self.point3 is None:
            self.reset()
            return

        clipPlane = Plane.fromVertices(self.point1, self.point2, self.point3)
        solids = []
        for obj in base.selectionMgr.selectedObjects:
            if obj.ObjectName == "solid":
                solids.append(obj)
        base.actionMgr.performAction(Clip(solids, clipPlane, self.side != ClipSide.Back, self.side != ClipSide.Front))
        self.reset()

    def controlDown(self):
        self.controlIsDown = True

    def controlUp(self):
        self.controlIsDown = False

    def disable(self):
        self.reset()
        BaseTool.disable(self)

    def getStateAtPoint(self, mouse, viewport):
        if self.point1 is None or self.point2 is None or self.point3 is None:
            return ClipState.Off

        p = viewport.viewportToWorld(mouse)
        p1 = viewport.flatten(self.point1)
        p2 = viewport.flatten(self.point2)
        p3 = viewport.flatten(self.point3)

        d = 5 / viewport.zoom

        if (p.x >= p1.x - d and p.x <= p1.x + d and p.y >= p1.y - d and p.y <= p1.y + d):
            return ClipState.MovingPoint1
        if (p.x >= p2.x - d and p.x <= p2.x + d and p.y >= p2.y - d and p.y <= p2.y + d):
            return ClipState.MovingPoint2
        if (p.x >= p3.x - d and p.x <= p3.x + d and p.y >= p3.y - d and p.y <= p3.y + d):
            return ClipState.MovingPoint3

        return ClipState.Off

    def mouseDown(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        self.prevState = self.state
        mouse = vp.getMouse()
        point = base.snapToGrid(vp.expand(vp.viewportToWorld(mouse)))
        st = self.getStateAtPoint(mouse, vp)
        if self.state == ClipState.Off or st == ClipState.Off:
            self.state = ClipState.Drawing
            self.drawingPoint = point
        elif self.state == ClipState.Drawn:
            self.state = st

    def mouseMoved(self, vp):
        if not vp.is2D():
            return

        mouse = vp.getMouse()
        point = base.snapToGrid(vp.viewportToWorld(mouse, False))
        st = self.getStateAtPoint(mouse, vp)
        if self.state == ClipState.Drawing:
            self.state = ClipState.MovingPoint2
            self.point1 = self.drawingPoint
            self.point2 = point
            self.point3 = self.point1 + base.snapToGrid(vp.getUnusedCoordinate(Vec3(128)))
            if self.side != ClipSide.Both:
                self.createClipVis()
            self.updateClipPlane()
        elif self.state == ClipState.MovingPoint1:
            # Move point 1
            cp1 = vp.getUnusedCoordinate(self.point1) + point
            if self.controlIsDown:
                diff = self.point1 - cp1
                self.point2 -= diff
                self.point3 -= diff
            self.point1 = cp1
            self.updateClipPlane()
        elif self.state == ClipState.MovingPoint2:
            # Move point 2
            cp2 = vp.getUnusedCoordinate(self.point2) + point
            if self.controlIsDown:
                diff = self.point2 - cp2
                self.point1 -= diff
                self.point3 -= diff
            self.point2 = cp2
            self.updateClipPlane()
        elif self.state == ClipState.MovingPoint3:
            # Move point 3
            cp3 = vp.getUnusedCoordinate(self.point3) + point
            if self.controlIsDown:
                diff = self.point3 - cp3
                self.point1 -= diff
                self.point2 -= diff
            self.point3 = cp1
            self.updateClipPlane()

    def updateClipPlane(self):
        # Create a ClipPlaneAttrib to quickly represent what the clip will look
        # like. The actual faces are not actually split until we confirm the clip.
        if self.point1 == self.point2 or self.point1 == self.point3 or self.point2 == self.point3:
            self.planeVis.np.reparentTo(NodePath())
            return
        plane = Plane.fromVertices(self.point1, self.point2, self.point3)
        # If we are keeping the back side, flip the plane
        if self.side == ClipSide.Back:
            plane.flip()
        self.planeNode.setPlane(plane)
        self.visRoot.setClipPlane(self.planeNP)

        mpoly = MathPolygon.fromPlaneAndRadius(plane)
        self.planeVis.vertices = mpoly.vertices
        self.planeVis.generateVertices()
        self.planeVis.np.reparentTo(base.render)

    def createClipVis(self):
        for obj in base.selectionMgr.selectedObjects:
            if obj.ObjectName == "solid":
                inst = obj.np.instanceTo(NodePath())
                inst.wrtReparentTo(self.visRoot)

    def clearClipVis(self):
        self.visRoot.node().removeAllChildren()

    def updateClipSide(self, side):
        if side == ClipSide.Both:
            self.clearClipVis()
            self.visRoot.clearClipPlane()
        else:
            if self.side == ClipSide.Both:
                self.createClipVis()
            self.updateClipPlane()
        self.side = side

    def mouseUp(self):
        vp = base.viewportMgr.activeViewport
        if not vp or not vp.is2D():
            return

        point = base.snapToGrid(vp.expand(vp.viewportToWorld(vp.getMouse())))
        if self.state == ClipState.Drawing:
            # Do nothing
            self.state = self.prevState
        else:
            self.state = ClipState.Drawn
