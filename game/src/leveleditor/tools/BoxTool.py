from panda3d.core import Point2, Vec3, Vec4, KeyboardButton, NodePath, LineSegs, MeshDrawer, BitMask32, Shader, Vec2
from panda3d.core import Geom, GeomNode, GeomVertexFormat, GeomLines, GeomVertexWriter, GeomVertexData, InternalName, Point3

from .BaseTool import BaseTool, ToolUsage
from src.leveleditor.viewport.Viewport2D import Viewport2D
from src.coginvasion.globals import CIGlobals

from enum import IntEnum

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

        assert len(self.boxStart) != len(self.boxEnd), "This literally should not happen. (BoxTool)"
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
            if flat[0] == 1:
                self.swapHandle("Left", "Right")
            if flat[1] == 1:
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
    def handleHitTestLine(hitX, hitY, test1X, test1Y, test2X, test2Y, hitbox):
        if test1X != test2X and test1Y != test2Y:
            return # only works on straight lines
        sx = min(test1X, test2X)
        sy = min(test1Y, test2Y)
        ex = max(test1X, test2X)
        ey = max(test1Y, test2Y)
        hoz = test1Y == test2Y
        if hoz:
            return hitX >= sx and hitX <= ex and hitY >= sy - hitbox and hitY <= sy + hitbox
        else:
            return hitY >= sy and hitY <= ey and hitX >= sx - hitbox and hitX <= sx + hitbox

    @staticmethod
    def getHandle(current, boxStart, boxEnd, hitbox):
        start = Point3(min(boxStart[0], boxEnd[0]), min(boxStart[1], boxEnd[1]), 0)
        end = Point3(max(boxStart[0], boxEnd[0]), max(boxStart[1], boxEnd[1]), 0)

        if BoxTool.handleHitTestPoint(current[0], current[1], start[0], start[1], hitbox):
            return ResizeHandle.BottomLeft

        if BoxTool.handleHitTestPoint(current[0], current[1], end[0], start[1], hitbox):
            return ResizeHandle.BottomRight

        if BoxTool.handleHitTestPoint(current[0], current[1], start[0], end[1], hitbox):
            return ResizeHandle.TopLeft

        if BoxTool.handleHitTestPoint(current[0], current[1], end[0], end[1], hitbox):
            return ResizeHandle.TopRight

        if BoxTool.handleHitTestLine(current[0], current[1], start[0], start[1], end[0], start[1], hitbox):
            return ResizeHandle.Bottom

        if BoxTool.handleHitTestLine(current[0], current[1], start[0], end[1], end[0], end[1], hitbox):
            return ResizeHandle.Top

        if BoxTool.handleHitTestLine(current[0], current[1], start[0], start[1], start[0], end[1], hitbox):
            return ResizeHandle.Left

        if BoxTool.handleHitTestLine(current[0], current[1], end[0], start[1], end[0], end[1], hitbox):
            return ResizeHandle.Right

        if current[0] > start[0] and current[0] < end[0] and current[1] > start[1] and current[1] < end[1]:
            return ResizeHandle.Center

    def __init__(self):
        BaseTool.__init__(self)
        self.handleWidth = 12
        self.boxColor = Vec4(1)
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
        self.state.boxStart = base.snapToGrid(vp.expand(vp.viewportToWorld(mouse)))
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

        mouse = vp.getMouse()

        # FIXME
        #print(abs(mouse.x - self.state.clickStart.x), abs(mouse.y - self.state.clickStart.y))

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
        handle = BoxTool.getHandle(now, start, end, self.handleWidth / vp.zoom)
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
        points = [st, ed, Point3(st.x, ed.y, 0), Point3(ed.x, st.y, 0)]
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

        self.x = 0

        # Proportional scaling
        ostart = vp.flatten(self.state.preTransformBoxStart if self.state.preTransformBoxStart else Vec3.zero())
        oend = vp.flatten(self.state.preTransformBoxEnd if self.state.preTransformBoxEnd else Vec3.zero())
        owidth = oend.x - ostart.x
        oheight = oend.y - ostart.y
        proportional = vp.mouseWatcher.isButtonDown(KeyboardButton.control()) and \
            self.state.action == BoxAction.Resizing and owidth != 0 and oheight != 0

        if self.state.handle == ResizeHandle.TopLeft:
            cstart.x = now.x
            cend.y = now.y
        elif self.state.handle == ResizeHandle.Top:
            cend.y = now.y
        elif self.state.handle == ResizeHandle.TopRight:
            cend.x = now.x
            cend.y = now.y
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
            cstart.y = now.y
        elif self.state.handle == ResizeHandle.Bottom:
            cstart.y = now.y
        elif self.state.handle == ResizeHandle.BottomRight:
            cend.x = now.x
            cstart.y = now.y

        if proportional:
            nwidth = cend.x - cstart.x
            nheight = cent.y - cstart.y
            mult = max(nwidth / owidth, nheight / oheight)
            pwidth = owidth * mult
            pheight = oheight * mult
            wdiff = pwidth - nwidth
            hdiff = pheight - nheight
            if self.state.handle == ResizeHandle.TopLeft:
                cstart.x -= wdiff
                cend.y += hdiff
            elif self.state.handle == ResizeHandle.TopRight:
                cend.x += wdiff
                cend.y += hdiff
            elif self.state.handle == ResizeHandle.BottomLeft:
                cstart.x -= wdiff
                cstart.y -= hdiff
            elif self.state.handle == ResizeHandle.BottomRight:
                cend.x += wdiff
                cstart.y -= hdiff

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

    def draw2D(self, vp):
        if self.state.action in [BoxAction.ReadyToDraw, BoxAction.DownToDraw]:
            return
        start = vp.flatten(self.state.boxStart)
        end = vp.flatten(self.state.boxEnd)
        if self.shouldDrawBox():
            vp.renderer.drawRect(start, end)

    def draw3D(self, vp):
        pass
