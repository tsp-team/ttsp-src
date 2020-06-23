# Filename: Viewport.py
# Created by:  Brian Lach (June 4, 2020)

from panda3d.core import Camera, BitMask32, WindowProperties, GraphicsPipe, FrameBufferProperties
from panda3d.core import MouseAndKeyboard, ButtonThrower, MouseWatcher, KeyboardButton, NodePath
from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, CollisionTraverser, Mat4
from panda3d.core import Vec4, ModifierButtons, Point2, Vec3, Point3, Vec2, ModelNode, LVector2i, LPoint2i
from panda3d.core import OmniBoundingVolume, OrthographicLens

from src.coginvasion.globals import CIGlobals

from .ViewportType import *
from .ViewportGizmo import ViewportGizmo

from direct.showbase.DirectObject import DirectObject

from PyQt5 import QtWidgets, QtGui

# Base viewport class
class Viewport(DirectObject, QtWidgets.QWidget):

    ClearColor = CIGlobals.vec3GammaToLinear(Vec4(0.361, 0.361, 0.361, 1.0))

    def __init__(self, vpType, window):
        DirectObject.__init__(self)
        QtWidgets.QWidget.__init__(self, window)

        self.qtWindow = None

        self.window = window
        self.type = vpType

        self.spec = VIEWPORT_SPECS[self.type]

        self.lens = None
        self.camNode = None
        self.camera = None
        self.cam = None
        self.win = None
        self.displayRegion = None
        self.mouseWatcher = None
        self.buttonThrower = None
        self.clickRay = None
        self.clickNode = None
        self.clickNp = None
        self.clickQueue = None
        self.clickTrav = None
        self.tickTask = None
        self.zoom = 1.0
        self.gizmo = None

        # 2D stuff copied from ShowBase :(
        self.camera2d = None
        self.cam2d = None
        self.render2d = None
        self.aspect2d = None
        self.a2dBackground = None
        self.a2dTop = None
        self.a2dBottom = None
        self.a2dLeft = None
        self.a2dRight = None
        self.a2dTopCenter = None
        self.a2dTopCenterNs = None
        self.a2dBottomCenter = None
        self.a2dBottomCenterNs = None
        self.a2dRightCenter = None
        self.a2dRightCenterNs = None
        self.a2dTopLeft = None
        self.a2dTopLeftNs = None
        self.a2dTopRight = None
        self.a2dTopRightNs = None
        self.a2dBottomLeft = None
        self.a2dBottomLeftNs = None
        self.a2dBottomRight = None
        self.a2dBottomRightNs = None
        self.__oldAspectRatio = None

        self.gridRoot = base.render.attachNewNode("gridRoot")
        self.gridRoot.setLightOff(1)
        self.gridRoot.setBSPMaterial("resources/phase_14/materials/unlit.mat")
        self.gridRoot.setDepthWrite(False, 1)
        self.gridRoot.setBin("background", 0)
        self.gridRoot.hide(BitMask32.allOn())
        self.gridRoot.showThrough(self.getViewportMask())

        self.grid = None

    def getGizmoAxes(self):
        raise NotImplementedError

    def getMouse(self):
        return self.mouseWatcher.getMouse()

    def is3D(self):
        return self.type == VIEWPORT_3D

    def is2D(self):
        return self.type != VIEWPORT_3D

    def makeGrid(self):
        raise NotImplementedError

    def getViewportMask(self):
        return BitMask32.bit(self.type)

    def makeLens(self):
        raise NotImplementedError

    def getGridAxes(self):
        raise NotImplementedError

    def expand(self, point):
        return point

    def initialize(self):
        self.lens = self.makeLens()
        self.camera = base.render.attachNewNode(ModelNode("viewportCameraParent"))
        self.camNode = Camera("viewportCamera")
        self.camNode.setLens(self.lens)
        self.camNode.setCameraMask(self.getViewportMask())
        self.cam = self.camera.attachNewNode(self.camNode)

        winprops = WindowProperties.getDefault()
        winprops.setOrigin(0, 0)
        winprops.setParentWindow(int(self.winId()))
        winprops.setOpen(True)
        winprops.setForeground(False)
        winprops.setUndecorated(True)

        output = base.graphicsEngine.makeOutput(
            base.pipe, "viewportOutput", 0,
            FrameBufferProperties.getDefault(),
            winprops, (GraphicsPipe.BFFbPropsOptional | GraphicsPipe.BFRequireWindow),
            base.gsg
        )

        assert output is not None, "Unable to create viewport output!"

        self.qtWindow = QtGui.QWindow.fromWinId(output.getWindowHandle().getIntHandle())
        print(self.qtWindow)

        output.setClearColorActive(False)
        output.setClearDepthActive(False)

        dr = output.makeDisplayRegion()
        dr.setClearColor(self.ClearColor)
        dr.setClearColorActive(True)
        dr.setClearDepthActive(True)
        dr.setCamera(self.cam)
        self.displayRegion = dr

        self.win = output

        # keep track of the mouse in this viewport
        mak = MouseAndKeyboard(self.win, 0, "mouse")
        mouse = base.dataRoot.attachNewNode(mak)
        self.mouseWatcher = MouseWatcher()
        self.mouseWatcher.setDisplayRegion(self.displayRegion)
        mw = mouse.attachNewNode(self.mouseWatcher)

        # listen for keyboard and mouse events in this viewport
        bt = ButtonThrower("kbEvents")
        bt.setPrefix("vp%i-" % self.spec.type)
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

        self.setupRender2d()
        self.setupCamera2d()

        self.gizmo = ViewportGizmo(self)

        base.viewportMgr.addViewport(self)

        self.makeGrid()

    def getAspectRatio(self):
        return self.win.getXSize() / self.win.getYSize()

    def setupRender2d(self):
        ## This is the root of the 2-D scene graph.
        self.render2d = NodePath("viewport-render2d")

        # Set up some overrides to turn off certain properties which
        # we probably won't need for 2-d objects.

        # It's probably important to turn off the depth test, since
        # many 2-d objects will be drawn over each other without
        # regard to depth position.

        # We used to avoid clearing the depth buffer before drawing
        # render2d, but nowadays we clear it anyway, since we
        # occasionally want to put 3-d geometry under render2d, and
        # it's simplest (and seems to be easier on graphics drivers)
        # if the 2-d scene has been cleared first.

        self.render2d.setDepthTest(0)
        self.render2d.setDepthWrite(0)
        self.render2d.setMaterialOff(1)
        self.render2d.setTwoSided(1)

        self.aspect2d = self.render2d.attachNewNode("viewport-aspect2d")

        aspectRatio = self.getAspectRatio()
        self.aspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)

        self.a2dBackground = self.aspect2d.attachNewNode("a2dBackground")

        ## The Z position of the top border of the aspect2d screen.
        self.a2dTop = 1.0
        ## The Z position of the bottom border of the aspect2d screen.
        self.a2dBottom = -1.0
        ## The X position of the left border of the aspect2d screen.
        self.a2dLeft = -aspectRatio
        ## The X position of the right border of the aspect2d screen.
        self.a2dRight = aspectRatio

        self.a2dTopCenter = self.aspect2d.attachNewNode("a2dTopCenter")
        self.a2dTopCenterNs = self.aspect2d.attachNewNode("a2dTopCenterNS")
        self.a2dBottomCenter = self.aspect2d.attachNewNode("a2dBottomCenter")
        self.a2dBottomCenterNs = self.aspect2d.attachNewNode("a2dBottomCenterNS")
        self.a2dLeftCenter = self.aspect2d.attachNewNode("a2dLeftCenter")
        self.a2dLeftCenterNs = self.aspect2d.attachNewNode("a2dLeftCenterNS")
        self.a2dRightCenter = self.aspect2d.attachNewNode("a2dRightCenter")
        self.a2dRightCenterNs = self.aspect2d.attachNewNode("a2dRightCenterNS")

        self.a2dTopLeft = self.aspect2d.attachNewNode("a2dTopLeft")
        self.a2dTopLeftNs = self.aspect2d.attachNewNode("a2dTopLeftNS")
        self.a2dTopRight = self.aspect2d.attachNewNode("a2dTopRight")
        self.a2dTopRightNs = self.aspect2d.attachNewNode("a2dTopRightNS")
        self.a2dBottomLeft = self.aspect2d.attachNewNode("a2dBottomLeft")
        self.a2dBottomLeftNs = self.aspect2d.attachNewNode("a2dBottomLeftNS")
        self.a2dBottomRight = self.aspect2d.attachNewNode("a2dBottomRight")
        self.a2dBottomRightNs = self.aspect2d.attachNewNode("a2dBottomRightNS")

        # Put the nodes in their places
        self.a2dTopCenter.setPos(0, 0, self.a2dTop)
        self.a2dTopCenterNs.setPos(0, 0, self.a2dTop)
        self.a2dBottomCenter.setPos(0, 0, self.a2dBottom)
        self.a2dBottomCenterNs.setPos(0, 0, self.a2dBottom)
        self.a2dLeftCenter.setPos(self.a2dLeft, 0, 0)
        self.a2dLeftCenterNs.setPos(self.a2dLeft, 0, 0)
        self.a2dRightCenter.setPos(self.a2dRight, 0, 0)
        self.a2dRightCenterNs.setPos(self.a2dRight, 0, 0)

        self.a2dTopLeft.setPos(self.a2dLeft, 0, self.a2dTop)
        self.a2dTopLeftNs.setPos(self.a2dLeft, 0, self.a2dTop)
        self.a2dTopRight.setPos(self.a2dRight, 0, self.a2dTop)
        self.a2dTopRightNs.setPos(self.a2dRight, 0, self.a2dTop)
        self.a2dBottomLeft.setPos(self.a2dLeft, 0, self.a2dBottom)
        self.a2dBottomLeftNs.setPos(self.a2dLeft, 0, self.a2dBottom)
        self.a2dBottomRight.setPos(self.a2dRight, 0, self.a2dBottom)
        self.a2dBottomRightNs.setPos(self.a2dRight, 0, self.a2dBottom)

    def setupCamera2d(self, sort = 10, displayRegion = (0, 1, 0, 1),
                      coords = (-1, 1, -1, 1)):
        dr = self.win.makeMonoDisplayRegion(*displayRegion)
        dr.setSort(10)

        # Enable clearing of the depth buffer on this new display
        # region (see the comment in setupRender2d, above).
        dr.setClearDepthActive(1)

        # Make any texture reloads on the gui come up immediately.
        dr.setIncompleteRender(False)

        left, right, bottom, top = coords

        # Now make a new Camera node.
        cam2dNode = Camera('cam2d')

        lens = OrthographicLens()
        lens.setFilmSize(right - left, top - bottom)
        lens.setFilmOffset((right + left) * 0.5, (top + bottom) * 0.5)
        lens.setNearFar(-1000, 1000)
        cam2dNode.setLens(lens)

        # self.camera2d is the analog of self.camera, although it's
        # not as clear how useful it is.
        self.camera2d = self.render2d.attachNewNode('camera2d')

        camera2d = self.camera2d.attachNewNode(cam2dNode)
        dr.setCamera(camera2d)

        self.cam2d = camera2d

        return camera2d

    def mouse1Up(self):
        pass

    def mouse1Down(self):
        pass

    def mouse2Up(self):
        pass

    def mouse2Down(self):
        pass

    def mouse3Up(self):
        pass

    def mouse3Down(self):
        pass

    def mouseEnter(self):
        pass

    def mouseExit(self):
        pass

    def mouseMove(self):
        pass

    def wheelUp(self):
        pass

    def wheelDown(self):
        pass

    def tick(self):
        pass

    def getViewportName(self):
        return self.spec.name

    def getViewportCenterPixels(self):
        return LPoint2i(self.win.getXSize() // 2, self.win.getYSize() // 2)

    def centerCursor(self):
        center = self.getViewportCenterPixels()
        self.win.movePointer(0, center[0], center[1])

    def viewportToWorld(self, viewport, vec = False):
        front = Point3()
        back = Point3()
        self.lens.extrude(viewport, front, back)
        world = (front + back) / 2

        worldMat = self.cam.getMat(render)
        if vec:
            world = worldMat.xformVec(world)
        else:
            world = worldMat.xformPoint(world)

        return world

    def worldToViewport(self, world):
        # move into local camera space
        invMat = Mat4(self.cam.getMat(render))
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

        self.clickRay.setFromLens(self.camNode, self.mouseWatcher.getMouse())
        self.clickNode.setFromCollideMask(mask)
        self.clickNp.reparentTo(self.cam)
        self.clickQueue.clearEntries()
        self.clickTrav.traverse(base.render)
        self.clickQueue.sortEntries()
        self.clickNp.reparentTo(NodePath())

        return self.clickQueue.getEntries()

    def fixRatio(self, size = None):
        if not self.lens:
            return

        if size is None:
            aspectRatio = self.win.getXSize() / self.win.getYSize()
        else:
            aspectRatio = size.x / size.y
        zoomFactor = (1.0 / self.zoom) * 100.0
        self.lens.setFilmSize(zoomFactor * aspectRatio, zoomFactor)

        if aspectRatio != self.__oldAspectRatio:
            self.__oldAspectRatio = aspectRatio
            # Fix up some anything that depends on the aspectRatio
            if aspectRatio < 1:
                # If the window is TALL, lets expand the top and bottom
                self.aspect2d.setScale(1.0, aspectRatio, aspectRatio)
                self.a2dTop = 1.0 / aspectRatio
                self.a2dBottom = - 1.0 / aspectRatio
                self.a2dLeft = -1
                self.a2dRight = 1.0
            else:
                # If the window is WIDE, lets expand the left and right
                self.aspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
                self.a2dTop = 1.0
                self.a2dBottom = -1.0
                self.a2dLeft = -aspectRatio
                self.a2dRight = aspectRatio

            # Reposition the aspect2d marker nodes
            self.a2dTopCenter.setPos(0, 0, self.a2dTop)
            self.a2dTopCenterNs.setPos(0, 0, self.a2dTop)
            self.a2dBottomCenter.setPos(0, 0, self.a2dBottom)
            self.a2dBottomCenterNs.setPos(0, 0, self.a2dBottom)
            self.a2dLeftCenter.setPos(self.a2dLeft, 0, 0)
            self.a2dLeftCenterNs.setPos(self.a2dLeft, 0, 0)
            self.a2dRightCenter.setPos(self.a2dRight, 0, 0)
            self.a2dRightCenterNs.setPos(self.a2dRight, 0, 0)

            self.a2dTopLeft.setPos(self.a2dLeft, 0, self.a2dTop)
            self.a2dTopLeftNs.setPos(self.a2dLeft, 0, self.a2dTop)
            self.a2dTopRight.setPos(self.a2dRight, 0, self.a2dTop)
            self.a2dTopRightNs.setPos(self.a2dRight, 0, self.a2dTop)
            self.a2dBottomLeft.setPos(self.a2dLeft, 0, self.a2dBottom)
            self.a2dBottomLeftNs.setPos(self.a2dLeft, 0, self.a2dBottom)
            self.a2dBottomRight.setPos(self.a2dRight, 0, self.a2dBottom)
            self.a2dBottomRightNs.setPos(self.a2dRight, 0, self.a2dBottom)

    def resizeEvent(self, event):
        if not self.win:
            return

        newsize = LVector2i(event.size().width(), event.size().height())

        props = WindowProperties()
        props.setSize(newsize)
        props.setOrigin(0, 0)

        self.win.requestProperties(props)

        self.fixRatio(newsize)

    def draw(self):
        pass
