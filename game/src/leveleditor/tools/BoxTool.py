from panda3d.core import Point2, Vec3, Vec4

from .BaseTool import BaseTool
from src.leveleditor.viewport.Viewport2D import Viewport2D

from enum import IntEnum

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

        if self.boxStart[0] > self.boxEnd[0]:
            temp = self.boxStart[0]
            self.boxStart[0] = self.boxEnd[0]
            self.boxEnd[0] = temp
            flat = vp.flatten(Vec3.right())
            if flat[0] == 1:
                self.swapHandle("Left", "Right")
            if flat[1] == 1:
                self.swapHandle("Top", "Bottom")

        if self.boxStart[1] > self.boxEnd[1]:
            temp = self.boxStart[1]
            self.boxStart[1] = self.boxEnd[1]
            self.boxEnd[1] = temp
            flat = vp.flatten(Vec3.forward())
            if flat[0] == 1:
                self.swapHandle("Left", "Right")
            if flat[1] == 1:
                self.swapHandle("Top", "Bottom")

        if self.boxStart[2] > self.boxEnd[2]:
            temp = self.boxStart[2]
            self.boxStart[2] = self.boxEnd[2]
            self.boxEnd[2] = temp
            flat = vp.flatten(Vec3.up())
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

    @staticmethod
    def getProperBoxCoordinates(start, end):
        newStart = Point3(min(start[0], end[0]), min(start[1], min[1]), min(start[2], end[2]))
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
        self.state = BoxState.ReadyToDraw
