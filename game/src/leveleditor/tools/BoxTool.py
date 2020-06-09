from panda3d.core import Point2, Vec3, Vec4, KeyboardButton, NodePath, LineSegs, MeshDrawer, BitMask32, Shader, Vec2
from panda3d.core import Geom, GeomNode, GeomVertexFormat, GeomLines, GeomVertexWriter, GeomVertexData, InternalName, Point3

from .BaseTool import BaseTool, ToolUsage
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.coginvasion.globals import CIGlobals
from src.leveleditor import RenderModes

from enum import IntEnum
import py_linq

from PyQt5 import QtCore

class BoxAction(IntEnum):
    ReadyToDraw = 0
    DownToDraw = 1
    Drawing = 2
    Drawn = 3
    ReadyToResize = 4
    DownToResize = 5
    Resizing = 6

class ResizeHandle(IntEnum):
    TopLeft = 0
    Top = 1
    TopRight = 2

    Left = 3
    Center = 4
    Right = 5

    BottomLeft = 6
    Bottom = 7
    BottomRight = 8

class HandleType(IntEnum):
    Square = 0
    Circle = 1

class BoxState:

    def __init__(self):
        self.activeViewport = None
        self.action = BoxAction.ReadyToDraw
        self.handle = ResizeHandle.Center
        self.boxStart = None
        self.boxEnd = None
        self.moveStart = None
        self.preTransformBoxStart = None
        self.preTransformBoxEnd = None
        self.clickStart = Point2(0, 0)

    def isValidAndApplicable(self, vp):
        return (self.action != BoxAction.DownToDraw and
                self.action != BoxAction.Drawing and
                self.action != BoxAction.DownToResize and
                self.action != BoxAction.Resizing or
                self.activeViewport == vp)

    def fixBoxBounds(self):
        if self.action != BoxAction.Drawing and self.action != BoxAction.Resizing:
            return
        if not isinstance(self.activeViewport, Viewport2D):
            return

        vp = self.activeViewport

        assert len(self.boxStart) == len(self.boxEnd), "This literally should not happen. (BoxTool)"
        for i in range(len(self.boxStart)):
            start = self.boxStart[i]
            end = self.boxEnd[i]
            if start > end:
                tmp = start
                self.boxStart[i] = end
                vec = Vec3(0, 0, 0)
                vec[i] = 1
                flat = vp.flatten(vec)
                # FIXME: There has to be a better way of doing this.
                if flat.x == 1:
                    self.swapHandle("Left", "Right")
                if flat.z == 1:
                    self.swapHandle("Top", "Bottom")

    def swapHandle(self, one, two):
        if one in self.handle.name:
            self.handle = ResizeHandle[self.handle.name.replace(one, two)]
        elif two in self.handle.name:
            self.handle = ResizeHandle[self.handle.name.replace(two, one)]

class BoxTool(BaseTool):

    Name = "Box Tool"
    ToolTip = "Box Tool"
    Usage = ToolUsage.Both

    CursorHandles = {
        ResizeHandle.TopLeft: QtCore.Qt.SizeFDiagCursor,
        ResizeHandle.BottomRight: QtCore.Qt.SizeFDiagCursor,

        ResizeHandle.TopRight: QtCore.Qt.SizeBDiagCursor,
        ResizeHandle.BottomLeft: QtCore.Qt.SizeBDiagCursor,

        ResizeHandle.Top: QtCore.Qt.SizeVerCursor,
        ResizeHandle.Bottom: QtCore.Qt.SizeVerCursor,

        ResizeHandle.Left: QtCore.Qt.SizeHorCursor,
        ResizeHandle.Right: QtCore.Qt.SizeHorCursor,

        ResizeHandle.Center: QtCore.Qt.SizeAllCursor
    }

    DrawActions = [
        BoxAction.Drawing,
        BoxAction.Drawn,
        BoxAction.ReadyToResize,
        BoxAction.DownToResize,
        BoxAction.Resizing
    ]

    @staticmethod
    def getProperBoxCoordinates(start, end):
        newStart = Point3(min(start[0], end[0]), min(start[1], end[1]), min(start[2], end[2]))
        newEnd = Point3(max(start[0], end[0]), max(start[1], end[1]), max(start[2], end[2]))
        return [newStart, newEnd]

    @staticmethod
    def handleHitTestPoint(hitX, hitY, testX, testY, hitbox):
        return (hitX >= testX - hitbox and hitX <= testX + hitbox and
            hitY >= testY - hitbox and hitY <= testY + hitbox)

    @staticmethod
    def getHandle(current, boxStart, boxEnd, hitbox, offset, zoom):
        offset /= zoom
        hitbox /= zoom
        start = Point3(min(boxStart[0], boxEnd[0]) - offset, 0, min(boxStart[2], boxEnd[2]) - offset)
        end = Point3(max(boxStart[0], boxEnd[0]) + offset, 0, max(boxStart[2], boxEnd[2]) + offset)
        center = (end + start) / 2

        if BoxTool.handleHitTestPoint(current[0], current[2], start[0], start[2], hitbox):
            return ResizeHandle.BottomLeft

        if BoxTool.handleHitTestPoint(current[0], current[2], end[0], start[2], hitbox):
            return ResizeHandle.BottomRight

        if BoxTool.handleHitTestPoint(current[0], current[2], start[0], end[2], hitbox):
            return ResizeHandle.TopLeft

        if BoxTool.handleHitTestPoint(current[0], current[2], end[0], end[2], hitbox):
            return ResizeHandle.TopRight

        if BoxTool.handleHitTestPoint(current[0], current[2], center[0], start[2], hitbox):
            return ResizeHandle.Bottom

        if BoxTool.handleHitTestPoint(current[0], current[2], center[0], end[2], hitbox):
            return ResizeHandle.Top

        if BoxTool.handleHitTestPoint(current[0], current[2], start[0], center[2], hitbox):
            return ResizeHandle.Left

        if BoxTool.handleHitTestPoint(current[0], current[2], end[0], center[2], hitbox):
            return ResizeHandle.Right

        # Remove the offset padding for testing if we are inside the box itself
        start[0] += offset
        start[2] += offset
        end[0] -= offset
        end[2] -= offset

        if current[0] > start[0] and current[0] < end[0] \
            and current[2] > start[2] and current[2] < end[2]:
            return ResizeHandle.Center

    def __init__(self):
        BaseTool.__init__(self)
        self.handleWidth = 1
        self.handleOffset = 1.6
        self.handleType = HandleType.Square
        self.boxColor = Vec4(1, 1, 1, 1)
        self.state = BoxState()

    def onBoxChanged(self):
        self.state.fixBoxBounds()
        # TODO: mediator.selectionBoxChanged

    def enable(self):
        BaseTool.enable(self)
        self.accept('mouse1', self.mouseDown)
        self.accept('mouse1-up', self.mouseUp)
        self.accept('mouseMoved', self.mouseMove)
        self.accept('mouseEnter', self.mouseEnter)
        self.accept('mouseExit', self.mouseExit)
        self.accept('enter', self.enterDown)
        self.accept('escape', self.escapeDown)

    def disable(self):
        BaseTool.disable(self)
        self.maybeCancel()

    def mouseDown(self):
        vp = base.viewportMgr.activeViewport
        if vp.is3D():
            self.mouseDown3D()
            return

        self.state.clickStart = Point2(vp.getMouse())

        if self.state.action in [BoxAction.ReadyToDraw, BoxAction.Drawn]:
            self.leftMouseDownToDraw()
        elif self.state.action == BoxAction.ReadyToResize:
            self.leftMouseDownToResize()

    def mouseDown3D(self):
        pass

    def leftMouseDownToDraw(self):
        vp = base.viewportMgr.activeViewport
        mouse = vp.getMouse()
        self.state.activeViewport = vp
        self.state.action = BoxAction.DownToDraw
        toWorld = vp.viewportToWorld(mouse)
        expanded = vp.expand(toWorld)
        self.state.boxStart = base.snapToGrid(expanded)
        self.state.boxEnd = self.state.boxStart
        self.state.handle = ResizeHandle.BottomLeft
        self.onBoxChanged()

    def leftMouseDownToResize(self):
        vp = base.viewportMgr.activeViewport
        self.state.action = BoxAction.DownToResize
        self.state.moveStart = vp.viewportToWorld(vp.getMouse())
        self.state.preTransformBoxStart = self.state.boxStart
        self.state.preTransformBoxEnd = self.state.boxEnd

    def mouseUp(self):
        vp = base.viewportMgr.activeViewport
        if vp.is3D():
            self.mouseUp3D()
            return

        if self.state.action == BoxAction.Drawing:
            self.leftMouseUpDrawing()
        elif self.state.action == BoxAction.Resizing:
            self.leftMouseUpResizing()
        elif self.state.action == BoxAction.DownToDraw:
            self.leftMouseClick()
        elif self.state.action == BoxAction.DownToResize:
            self.leftMouseClickOnResizeHandle()

    def mouseUp3D(self):
        pass

    def resizeBoxDone(self):
        vp = base.viewportMgr.activeViewport
        coords = self.getResizedBoxCoordinates(vp)
        corrected = BoxTool.getProperBoxCoordinates(coords[0], coords[1])
        self.state.activeViewport = None
        self.state.action = BoxAction.Drawn
        self.state.boxStart = corrected[0]
        self.state.boxEnd = corrected[1]
        self.onBoxChanged()

    def leftMouseUpDrawing(self):
        self.resizeBoxDone()

    def leftMouseUpResizing(self):
        self.resizeBoxDone()

    def leftMouseClick(self):
        self.state.activeViewport = None
        self.state.action = BoxAction.ReadyToDraw
        self.state.boxStart = None
        self.state.boxEnd = None
        self.onBoxChanged()

    def leftMouseClickOnResizeHandle(self):
        self.state.action = BoxAction.ReadyToResize

    def mouseMove(self, vp):
        if vp.is3D():
            self.mouseMove3D()
            return
        if not self.state.isValidAndApplicable(vp):
            return

        if self.state.action in [BoxAction.Drawing, BoxAction.DownToDraw]:
            self.mouseDraggingToDraw()
        elif self.state.action in [BoxAction.Drawn, BoxAction.ReadyToResize]:
            self.mouseHoverWhenDrawn()
        elif self.state.action in [BoxAction.DownToResize, BoxAction.Resizing]:
            self.mouseDraggingToResize()

    def mouseMove3D(self):
        pass

    def resizeBoxDrag(self):
        vp = base.viewportMgr.activeViewport
        coords = self.getResizedBoxCoordinates(vp)
        self.state.boxStart = coords[0]
        self.state.boxEnd = coords[1]
        self.onBoxChanged()

    def mouseDraggingToDraw(self):
        self.state.action = BoxAction.Drawing
        self.resizeBoxDrag()

    def mouseDraggingToResize(self):
        self.state.action = BoxAction.Resizing
        self.resizeBoxDrag()

    def cursorForHandle(self, handle):
        return self.CursorHandles.get(handle, QtCore.Qt.ArrowCursor)

    def mouseHoverWhenDrawn(self):
        vp = base.viewportMgr.activeViewport
        now = vp.viewportToWorld(vp.getMouse())
        start = vp.flatten(self.state.boxStart)
        end = vp.flatten(self.state.boxEnd)
        handle = BoxTool.getHandle(now, start, end, self.handleWidth, self.handleOffset, vp.zoom)
        if handle is not None:
            vp.setCursor(self.cursorForHandle(handle))
            self.state.handle = handle
            self.state.action = BoxAction.ReadyToResize
            self.state.activeViewport = vp
        else:
            vp.setCursor(QtCore.Qt.ArrowCursor)
            self.state.action = BoxAction.Drawn
            self.state.activeViewport = None

    def getResizeOrigin(self, vp):
        if self.state.action != BoxAction.Resizing or self.state.handle != ResizeHandle.Center:
            return None
        st = vp.flatten(self.state.preTransformBoxStart)
        ed = vp.flatten(self.state.preTransformBoxEnd)
        points = [st, ed, Point3(st.x, 0, ed.z), Point3(ed.x, 0, st.z)]
        points.sort(key = lambda x: (self.state.moveStart - x).lengthSquared())
        return points[0]

    def getResizeDistance(self, vp):
        origin = self.getResizeOrigin(vp)
        if not origin:
            return None
        before = self.state.moveStart
        after = vp.viewportToWorld(vp.getMouse())
        return base.snapToGrid(origin + after - before) - origin

    def getResizedBoxCoordinates(self, vp):
        if self.state.action != BoxAction.Resizing and self.state.action != BoxAction.Drawing:
            return [self.state.boxStart, self.state.boxEnd]
        now = base.snapToGrid(vp.viewportToWorld(vp.getMouse()))
        cstart = vp.flatten(self.state.boxStart)
        cend = vp.flatten(self.state.boxEnd)

        # Proportional scaling
        ostart = vp.flatten(self.state.preTransformBoxStart if self.state.preTransformBoxStart else Vec3.zero())
        oend = vp.flatten(self.state.preTransformBoxEnd if self.state.preTransformBoxEnd else Vec3.zero())
        owidth = oend.x - ostart.x
        oheight = oend.z - ostart.z
        proportional = vp.mouseWatcher.isButtonDown(KeyboardButton.control()) and \
            self.state.action == BoxAction.Resizing and owidth != 0 and oheight != 0

        if self.state.handle == ResizeHandle.TopLeft:
            cstart.x = now.x
            cend.z = now.z
        elif self.state.handle == ResizeHandle.Top:
            cend.z = now.z
        elif self.state.handle == ResizeHandle.TopRight:
            cend.x = now.x
            cend.z = now.z
        elif self.state.handle == ResizeHandle.Left:
            cstart.x = now.x
        elif self.state.handle == ResizeHandle.Center:
            cdiff = cend - cstart
            distance = self.getResizeDistance(vp)
            if not distance:
                cstart = vp.flatten(self.state.preTransformBoxStart) + now \
                    - base.snapToGrid(self.state.moveStart)
            else:
                cstart = vp.flatten(self.state.preTransformBoxStart) + distance
            cend = cstart + cdiff
        elif self.state.handle == ResizeHandle.Right:
            cend.x = now.x
        elif self.state.handle == ResizeHandle.BottomLeft:
            cstart.x = now.x
            cstart.z = now.z
        elif self.state.handle == ResizeHandle.Bottom:
            cstart.z = now.z
        elif self.state.handle == ResizeHandle.BottomRight:
            cend.x = now.x
            cstart.z = now.z

        if proportional:
            nwidth = cend.x - cstart.x
            nheight = cent.z - cstart.z
            mult = max(nwidth / owidth, nheight / oheight)
            pwidth = owidth * mult
            pheight = oheight * mult
            wdiff = pwidth - nwidth
            hdiff = pheight - nheight
            if self.state.handle == ResizeHandle.TopLeft:
                cstart.x -= wdiff
                cend.z += hdiff
            elif self.state.handle == ResizeHandle.TopRight:
                cend.x += wdiff
                cend.z += hdiff
            elif self.state.handle == ResizeHandle.BottomLeft:
                cstart.x -= wdiff
                cstart.z -= hdiff
            elif self.state.handle == ResizeHandle.BottomRight:
                cend.x += wdiff
                cstart.z -= hdiff

        cstart = vp.expand(cstart) + vp.getUnusedCoordinate(self.state.boxStart)
        cend = vp.expand(cend) + vp.getUnusedCoordinate(self.state.boxEnd)
        return [cstart, cend]

    def maybeCancel(self):
        if self.state.action in [BoxAction.ReadyToDraw, BoxAction.DownToDraw]:
            return False
        if self.state.activeViewport:
            self.state.activeViewport.setCursor(QtCore.Qt.ArrowCursor)
            self.state.activeViewport = None
        self.state.action = BoxAction.ReadyToDraw
        return True

    def enterDown(self):
        if self.maybeCancel():
            self.boxDrawnConfirm()

    def escapeDown(self):
        if self.maybeCancel():
            self.boxDrawnCancel()

    def boxDrawnConfirm(self):
        pass

    def boxDrawnCancel(self):
        pass

    def mouseEnter(self, vp):
        if self.state.activeViewport:
            self.state.activeViewport.setCursor(QtCore.Qt.ArrowCursor)

    def mouseExit(self, vp):
        if self.state.activeViewport:
            self.state.activeViewport.setCursor(QtCore.Qt.ArrowCursor)

    def shouldDrawBox(self):
        return self.state.action in self.DrawActions

    def getHandles(self, start, end, zoom, offset = None):
        if offset is None:
            offset = self.handleOffset

        half = (end - start) / 2
        dist = offset / zoom

        return py_linq.Enumerable([
            (ResizeHandle.TopLeft, start.x - dist, end.z + dist),
            (ResizeHandle.TopRight, end.x + dist, end.z + dist),
            (ResizeHandle.BottomLeft, start.x - dist, start.z - dist),
            (ResizeHandle.BottomRight, end.x + dist, start.z - dist),

            (ResizeHandle.Top, start.x + half.x, end.z + dist),
            (ResizeHandle.Left, start.x - dist, start.z + half.z),
            (ResizeHandle.Right, end.x + dist, start.z + half.z),
            (ResizeHandle.Bottom, start.x + half.x, start.z - dist)
        ])

    def filterHandle(self, handle):
        return True

    def shouldDrawHandles(self):
        return self.state.action in [BoxAction.ReadyToResize, BoxAction.Drawn]

    def drawHandles(self, vp, start, end):
        z = vp.zoom
        handles = self.getHandles(start, end, vp.zoom) \
            .where(lambda x: self.filterHandle(x[0])) \
            .select(lambda x: Point3(x[1], 0, x[2])) \
            .to_list()

        for handle in handles:
            if self.handleType == HandleType.Square:
                vp.renderer.renderState(RenderModes.DoubleSidedNoZ())
                vp.renderer.drawFilledRectRadius(handle, 1, z, True)
            # TODO: circles

    def draw2D(self, vp):
        if self.state.action in [BoxAction.ReadyToDraw, BoxAction.DownToDraw]:
            return
        start = vp.flatten(self.state.boxStart)
        end = vp.flatten(self.state.boxEnd)
        if self.shouldDrawBox():
            vp.renderer.renderState(RenderModes.DashedLineNoZ())
            vp.renderer.color(self.boxColor)
            vp.renderer.drawRect(start, end)
        if self.shouldDrawHandles():
            self.drawHandles(vp, start, end)

    def draw3D(self, vp):
        pass
