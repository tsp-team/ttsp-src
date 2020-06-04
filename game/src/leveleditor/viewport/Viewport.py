# Filename: Viewport.py
# Created by:  Brian Lach (June 4, 2020)

from panda3d.core import Camera, BitMask32, WindowProperties, GraphicsPipe, FrameBufferProperties
from panda3d.core import MouseAndKeyboard, ButtonThrower, MouseWatcher, KeyboardButton, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, CollisionTraverser
from panda3d.core import Vec4, ModifierButtons, Point2, Vec3, Point3, Vec2

from direct.showbase.DirectObject import DirectObject

from PyQt5 import QtWidgets

import math

# Base viewport class
class Viewport(DirectObject, QtWidgets.QWidget):

    def __init__(self, vpType, window):
        DirectObject.__init__(self)
        QtWidgets.QWidget.__init__(self, window)

        self.window = parent
        self.type = vpType

        self.lens = None
        self.cam = None
        self.camNp = None
        self.win = None
        self.mouseWatcher = None
        self.buttonThrower = None
        self.clickRay = None
        self.clickNode = None
        self.clickNp = None
        self.clickQueue = None
        self.clickTrav = None
        self.tickTask = None
        self.zoom = 1.0

        self.gridRoot = base.render.attachNewNode("gridRoot")
        self.gridRoot.setLightOff(1)
        self.gridRoot.setFogOff(1)
        self.gridRoot.showThrough(self.getViewportMask())

        self.grid = None

    def makeGrid(self):
        raise NotImplementedError

    def getViewportMask(self):
        return BitMask32.bit(self.type)

    def makeLens(self):
        raise NotImplementedError

    def initialize(self):
        self.lens = self.makeLens()
        self.cam = Camera("viewportCamera")
        self.cam.setLens(self.lens)
        self.cam.setCameraMask(self.getViewportMask())
        self.camNp = base.render.attachNewNode(self.cam)

        winprops = WindowProperties.getDefault()
        winprops.setOrigin(0, 0)
        winprops.setParentWindow(int(self.winId()))
        winprops.setOpen(True)
        winprops.setForeground(True)

        output = base.graphicsEngine.makeOutput(
            base.graphicsPipe, "viewportOutput", 0,
            FrameBufferProperties.getDefault(),
            winprops, (GraphicsPipe.BFFbPropsOptional | GraphicsPipe.BFRequireWindow),
            base.gsg
        )

        assert output is not None, "Unable to create viewport output!"

        output.setClearColorActive(False)
        output.setClearDepthActive(False)

        dr = output.makeDisplayRegion()
        dr.setClearColor(Vec4(0, 0, 0, 1))
        dr.setClearColorActive(True)
        dr.setClearDepthActive(True)
        dr.setCamera(self.camNp)

        self.win = output

        # keep track of the mouse in this viewport
        mak = MouseAndKeyboard(self.win, 0, "mouse")
        mouse = base.dataRoot.attachNewNode(mak)
        self.mouseWatcher = MouseWatcher()
        self.mouseWatcher.setDisplayRegion(dr)
        mw = mouse.attachNewNode(self.mouseWatcher)

        # listen for keyboard and mouse events in this viewport
        bt = ButtonThrower("kbEvents")
        mods = ModifierButtons()
        mods.addButton(KeyboardButton.shift())
        mods.addButton(KeyboardButton.control())
        mods.addButton(KeyboardButton.alt())
        mods.addButton(KeyboardButton.meta())
        bt.setModifierButtons(mods)
        self.buttonThrower = mouse.attachNewNode(bt)

        # collision objects for clicking on objects from this viewport
        self.clickRay = CollisionRay()
        self.clickNode = CollisionNode("viewportClickRay")
        self.clickNode.addSolid(self.clickRay)
        self.clickNp = NodePath(self.clickNode)
        self.clickQueue = CollisionHandlerQueue()
        self.clickTrav = CollisionTraverser("viewportClickTraverser")
        self.clickTrav.addCollider(self.clickNp, self.clickQueue)

        base.viewportMgr.addViewport(self)

        self.makeGrid()

        self.tickTask = base.taskMgr.add(self.__tickTask, "viewportTick")

    def __tickTask(self, task):
        self.tick()
        return task.cont

    def tick(self):
        pass

    def getViewportName(self):
        return "Unknown"

    def getViewportCenterPixels(self):
        return Point2(self.win.getXSize() // 2, self.win.getYSize() // 2)

    def centerCursor(self):
        center = self.getViewportCenterPixels()
        self.win.movePointer(0, center[0], center[1])

    def viewportToWorld(self, viewport):
        front = Point3()
        back = Point3()
        self.lens.extrude(viewport, front, back)
        world = (front + back) / 2

        worldMat = self.camNp.getMat()
        world = worldMat.xformPoint(world)

        return world

    def worldToViewport(self, world):
        # move into local camera space
        invMat = self.camNp.getMat()
        invMat.invertInPlace()

        local = invMat.xformPoint(world)

        point = Point2()
        self.lens.project(local, point)

        return point

    def zeroUnusedCoordinate(self, vec):
        pass

    def click(self, mask):
        if not self.mouseWatcher.hasMouse():
            return None

        self.clickRay.setFromLens(self.cam, self.mouseWatcher.getMouse())
        self.clickNode.setFromCollideMask(mask)
        self.clickNp.reparentTo(self.camNp)
        self.clickQueue.clearEntries()
        self.clickTrav.traverse(base.render)
        self.clickQueue.sortEntries()
        self.clickNp.reparentTo(NodePath())

        return self.clickQueue.getEntries()

    def adjustZoom(self, scrolled = False, delta = 0):
        before = Point3()
        md = self.mouseWatcher.getMouse()

        if scrolled:
            before = self.viewportToWorld(md)
            self.zoom *= math.pow(1.2, float(delta))
            self.zoom = min(256.0, max(0.01, self.zoom))

        if self.lens:
            ratio = self.win.getXSize() / self.win.getYSize()
            zoomFactor = (1.0 / self.zoom) * 100.0
            self.lens.setFilmSize(zoomFactor * ratio, zoomFactor)

        if scrolled:
            after = self.viewportToWorld(md)
            self.camNp.setPos(self.camNp.getPos() - (after - before))

    def resizeEvent(self, event):
        if not self.win:
            return

        newsize = Vec2(event.size().width(), event.size().height())

        props = WindowProperties()
        props.setSize(newsize)
        props.setOrigin(0, 0)

        self.win.requestProperties(props)

        self.adjustZoom()
    