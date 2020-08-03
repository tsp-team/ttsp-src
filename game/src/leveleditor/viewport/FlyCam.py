from panda3d.core import Vec3, Point2, WindowProperties, NodePath, SamplerState

from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState
from direct.gui.DirectGui import OnscreenImage

import math

from PyQt5 import QtWidgets, QtGui, QtCore

class FlyCam(DirectObject):

    def __init__(self, viewport):
        DirectObject.__init__(self)

        self.viewport = viewport

        self.enabled = False
        self.mouseSensitivity = 0.3
        self.cameraSpeed = 500 # 1/16 feet per second
        self.timeToSpeed = 0.5 # seconds
        self.moveStart = 0.0
        self.cameraRotateSpeed = 75.0
        self.cameraSmooth = 0.7
        self.slideFactor = 0.75
        self.maxPitch = 90
        self.minPitch = -90
        self.diagonalFactor = math.sqrt(2.0) / 2.0
        self.lastSpeeds = Vec3(0)
        self.moving = False

        self.cursor = QtGui.QCursor()
        self.cursor.setShape(QtCore.Qt.BlankCursor)

        tex = base.loader.loadTexture('resources/icons/editor-crosshair.png')
        tex.setMinfilter(SamplerState.FTLinear)
        tex.setMagfilter(SamplerState.FTLinear)
        crosshair = OnscreenImage(tex)
        crosshair.setTransparency(True)
        crosshair.setScale(0.04)
        crosshair.reparentTo(NodePath())
        self.crosshair = crosshair

        inputState.watchWithModifiers("forward", "w")
        inputState.watchWithModifiers("reverse", "s")
        inputState.watchWithModifiers("slideLeft", "a")
        inputState.watchWithModifiers("slideRight", "d")
        inputState.watchWithModifiers("floatDown", "q")
        inputState.watchWithModifiers("floatUp", "e")
        inputState.watchWithModifiers("lookUp", "arrow_up")
        inputState.watchWithModifiers("lookDown", "arrow_down")
        inputState.watchWithModifiers("lookRight", "arrow_right")
        inputState.watchWithModifiers("lookLeft", "arrow_left")

        self.accept('z', self.handleZ)

        base.taskMgr.add(self.__flyCamTask, 'flyCam')

    def handleZ(self):
        if self.viewport.mouseWatcher.hasMouse():
            self.setEnabled(not self.enabled)

    def setEnabled(self, flag):
        if flag:
            if not self.enabled:
                self.viewport.setCursor(self.cursor)
                self.viewport.centerCursor(self.cursor)
                self.crosshair.reparentTo(self.viewport.aspect2d)
        else:
            if self.enabled:
                self.crosshair.reparentTo(NodePath())
                self.viewport.unsetCursor()

        self.enabled = flag

    def __flyCamTask(self, task):

        camera = self.viewport.camera
        win = self.viewport.win

        dt = globalClock.getDt()
        goalSpeeds = Vec3(0)

        md = win.getPointer(0)
        if md.getInWindow():
            if self.enabled:
                center = Point2(win.getXSize() // 2, win.getYSize() // 2)
                dx = center.getX() - md.getX()
                dy = center.getY() - md.getY()
                camera.setH(camera.getH() + (dx * self.mouseSensitivity))
                camera.setP(camera.getP() + (dy * self.mouseSensitivity))
                self.viewport.centerCursor(self.cursor)

            # linear movement WASD+QE
            goalDir = Vec3(0)
            if inputState.isSet("forward"):
                goalDir[1] += 1
            if inputState.isSet("reverse"):
                goalDir[1] -= 1
            if inputState.isSet("slideLeft"):
                goalDir[0] -= 1
            if inputState.isSet("slideRight"):
                goalDir[0] += 1
            if inputState.isSet("floatUp"):
                goalDir[2] += 1
            if inputState.isSet("floatDown"):
                goalDir[2] -= 1

            if abs(goalDir[0]) and not abs(goalDir[1]):
                goalDir[0] *= self.slideFactor
            elif abs(goalDir[0]) and abs(goalDir[1]):
                goalDir[0] *= self.diagonalFactor
                goalDir[1] *= self.diagonalFactor

            # rotational movement arrow keys
            goalRot = Vec3(0)
            if inputState.isSet("lookLeft"):
                goalRot[0] += 1
            if inputState.isSet("lookRight"):
                goalRot[0] -= 1
            if inputState.isSet("lookUp"):
                goalRot[1] += 1
            if inputState.isSet("lookDown"):
                goalRot[1] -= 1
            camera.setH(camera.getH() + (goalRot[0] * self.cameraRotateSpeed * dt))
            camera.setP(camera.getP() + (goalRot[1] * self.cameraRotateSpeed * dt))

            # Limit the camera pitch so it doesn't go crazy
            if camera.getP() > self.maxPitch:
                camera.setP(self.maxPitch)
            elif camera.getP() < self.minPitch:
                camera.setP(self.minPitch)

            goalSpeeds = goalDir * self.cameraSpeed

        speeds = Vec3(goalSpeeds)
        if speeds.lengthSquared() > 0.001:
            now = globalClock.getFrameTime()
            if not self.moving:
                self.moving = True
                self.moveStart = now
            speedFactor = min((now - self.moveStart) / self.timeToSpeed, 1.0)
            speeds *= dt * speedFactor
            # dont have float value be affected by direction, always completely up or down
            camera.setPos(camera.getPos() + camera.getQuat().xform(Vec3(speeds[0], speeds[1], 0)))
            camera.setZ(camera, speeds[2])
        else:
            self.moving = False

        # should never have a roll in the camera
        camera.setR(0)

        self.lastSpeeds = speeds

        return task.cont
