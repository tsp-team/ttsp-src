from panda3d.core import Vec3, Point2, WindowProperties

from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

import math

class FlyCam(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)

        self.enabled = False
        self.mouseSensitivity = 0.3
        self.cameraSpeed = 320
        self.cameraRotateSpeed = 75.0
        self.cameraSmooth = 0.7
        self.slideFactor = 0.75
        self.diagonalFactor = math.sqrt(2.0) / 2.0
        self.lastSpeeds = Vec3(0)

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
        self.setEnabled(not self.enabled)

    def centerCursor(self, center = None):
        if not center:
            center = Point2(base.win.getXSize() // 2, base.win.getYSize() // 2)

        base.win.movePointer(0, int(center[0]), int(center[1]))

    def setEnabled(self, flag):
        if flag:
            if not self.enabled:
                props = WindowProperties()
                props.setCursorHidden(True)
                props.setMouseMode(WindowProperties.MConfined)
                base.win.requestProperties(props)
                self.centerCursor()
        else:
            if self.enabled:
                props = WindowProperties()
                props.setCursorHidden(False)
                props.setMouseMode(WindowProperties.MAbsolute)
                base.win.requestProperties(props)

        self.enabled = flag

    def __flyCamTask(self, task):

        dt = globalClock.getDt()
        goalSpeeds = Vec3(0)

        md = base.win.getPointer(0)
        if md.getInWindow():
            if self.enabled:
                center = Point2(base.win.getXSize() // 2, base.win.getYSize() // 2)
                dx = center.getX() - md.getX()
                dy = center.getY() - md.getY()
                base.camera.setH(base.camera, dx * self.mouseSensitivity)
                base.camera.setP(base.camera, dy * self.mouseSensitivity)
                base.win.movePointer(0, int(center[0]), int(center[1]))#self.centerCursor(center)

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
            base.camera.setHpr(base.camera, goalRot * self.cameraRotateSpeed * dt)

            goalSpeeds = goalDir * self.cameraSpeed

        speeds = Vec3(goalSpeeds)
        if not goalSpeeds.almostEqual(self.lastSpeeds, 0.01):
            speeds *= dt
            # dont have float value be affected by direction, always completely up or down
            base.camera.setPos(base.camera.getPos() + base.camera.getQuat().xform(Vec3(speeds[0], speeds[1], 0)))
            base.camera.setZ(base.camera, speeds[2])

        # should never have a roll in the camera
        base.camera.setR(0)

        self.lastSpeeds = speeds

        return task.cont