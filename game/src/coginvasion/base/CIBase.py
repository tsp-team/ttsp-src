"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file CIBase.py
@author Brian Lach
@date March 13, 2017

"""

from panda3d.core import loadPrcFile, NodePath, PGTop, TextPropertiesManager, TextProperties, Vec3, MemoryUsage, MemoryUsagePointers, RescaleNormalAttrib
from panda3d.core import CollisionHandlerFloor, CollisionHandlerQueue, CollisionHandlerPusher, loadPrcFileData, TexturePool, ModelPool, RenderState, Vec4, Point3
from panda3d.core import CollisionTraverser, CullBinManager, LightRampAttrib, Camera, OmniBoundingVolume, Texture, GraphicsOutput, PStatCollector, PerspectiveLens, ModelNode, BitMask32, OrthographicLens
from panda3d.core import FrameBufferProperties, WindowProperties
from panda3d.bullet import BulletWorld, BulletDebugNode, BulletRigidBodyNode
from panda3d.bsp import Py_CL_BSPLoader, BSPLoader, BSPRender
from panda3d.bsp import Audio3DManager, DecalModulateSpec

import sys

#from panda3d.recastnavigation import RNNavMeshManager

from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.gui import DirectGuiGlobals
from direct.gui.DirectGui import OnscreenImage

from .BSPBase import BSPBase
from src.coginvasion.manager.UserInputStorage import UserInputStorage
from src.coginvasion.margins.MarginManager import MarginManager
from src.coginvasion.globals import CIGlobals
from src.coginvasion.base.CITransitions import CITransitions
from src.coginvasion.base.CIPostProcess import CIPostProcess
from src.coginvasion.base import ScreenshotHandler
from src.coginvasion.base import MusicCache
from src.coginvasion.hood.SkyUtil import SkyUtil
from src.coginvasion.phys.FPSCamera import FPSCamera
from .Lighting import OutdoorLightingConfig

from .HDR import HDR
from .ShakeCamera import ShakeCamera
from .WaterReflectionManager import WaterReflectionManager
from src.coginvasion.phys import PhysicsUtils

import builtins
import random
import os

LoadSfxCollector = PStatCollector("App:Show Code:Load SFX")

class CIBase(BSPBase):
    notify = directNotify.newCategory("CIBase")

    DebugShaderQualities = False

    def __init__(self):
        self.bspLoader = Py_CL_BSPLoader()
        BSPLoader.setGlobalPtr(self.bspLoader)

        BSPBase.__init__(self)

        self.taskMgr.add(self.updateShadersAndPostProcess, 'CIBase.updateShadersAndPostProcess', 47)

        from direct.distributed.ClockDelta import globalClockDelta
        builtins.globalClockDelta = globalClockDelta

        self.physicsWorld = BulletWorld()
        # Panda units are in feet, so the gravity is 32 feet per second,
        # not 9.8 meters per second.
        self.physicsWorld.setGravity(Vec3(0, 0, -32.1740))

        self.physicsWorld.setGroupCollisionFlag(7, 1, True)
        self.physicsWorld.setGroupCollisionFlag(7, 2, True)
        self.physicsWorld.setGroupCollisionFlag(7, 3, False)
        self.physicsWorld.setGroupCollisionFlag(7, 4, False)
        self.physicsWorld.setGroupCollisionFlag(7, 8, True)

        self.taskMgr.add(self.__physicsUpdate, "physicsUpdate", sort = 30)

        debugNode = BulletDebugNode('Debug')
        self.debugNP = render.attachNewNode(debugNode)
        self.physicsWorld.setDebugNode(self.debugNP.node())

        self.physicsDbgFlag = False
        self.setPhysicsDebug(self.config.GetBool('physics-debug', False))

        #self.shadowCaster = ShadowCaster(Vec3(163, -67, 0))
        #self.shadowCaster.enable()

        self.bspLoader.setGamma(2.2)
        self.bspLoader.setMaterialsFile("phase_14/etc/materials.txt")
        #self.bspLoader.setTextureContentsFile("phase_14/etc/texturecontents.txt")
        self.bspLoader.setWantVisibility(True)
        self.bspLoader.setVisualizeLeafs(False)
        self.bspLoader.setWantLightmaps(True)
        self.bspLoader.setPhysicsWorld(self.physicsWorld)
        #self.bspLoader.setShadowCamPos(Point3(-15, 5, 40))
        #self.bspLoader.setShadowResolution(60 * 2, 1024 * 1)
        self.bspLevel = None
        self.brushCollisionMaterialData = {}
        self.skyBox = None
        self.skyBoxUtil = None

        self.linkClientSideBSPEntities()

        #self.nmMgr = RNNavMeshManager.get_global_ptr()
        #self.nmMgr.set_root_node_path(self.render)
        #self.nmMgr.get_reference_node_path().reparentTo(self.render)
        #self.nmMgr.start_default_update()
        #self.nmMgr.get_reference_node_path_debug().reparentTo(self.render)
        self.navMeshNp = None

        self.precacheList = []

        # Setup 3d audio                                 run before igLoop so 3d positioning doesn't lag behind
        base.audio3d = Audio3DManager(base.sfxManagerList[0], camera, render)
        base.audio3d.setDropOffFactor(0.15)
        base.audio3d.setDopplerFactor(0.15)

        # Setup collision handlers
        base.cTrav = CollisionTraverser()
        base.lifter = CollisionHandlerFloor()
        base.pusher = CollisionHandlerPusher()
        base.queue = CollisionHandlerQueue()

        base.lightingCfg = None

        self.cl_attackMgr = None

        #self.accept('/', self.projectShadows)

        # Let's setup the user input storage system
        uis = UserInputStorage()
        self.inputStore = uis
        self.userInputStorage = uis
        builtins.inputStore = uis
        builtins.userInputStorage = uis

        self.wakeWaterHeight = -30.0

        self.filterList = []

        self.music = None
        self.currSongName = None

        self.avatars = []

        wrm = WaterReflectionManager()
        self.waterReflectionMgr = wrm
        builtins.waterReflectionMgr = wrm

        # Let's setup our margins
        base.marginManager = MarginManager()
        base.margins = aspect2d.attachNewNode(base.marginManager, DirectGuiGlobals.MIDGROUND_SORT_INDEX + 1)
        base.leftCells = [
            base.marginManager.addCell(0.1, -0.6, base.a2dTopLeft),
            base.marginManager.addCell(0.1, -1.0, base.a2dTopLeft),
            base.marginManager.addCell(0.1, -1.4, base.a2dTopLeft)
        ]
        base.bottomCells = [
            base.marginManager.addCell(0.4, 0.1, base.a2dBottomCenter),
            base.marginManager.addCell(-0.4, 0.1, base.a2dBottomCenter),
            base.marginManager.addCell(-1.0, 0.1, base.a2dBottomCenter),
            base.marginManager.addCell(1.0, 0.1, base.a2dBottomCenter)
        ]
        base.rightCells = [
            base.marginManager.addCell(-0.1, -0.6, base.a2dTopRight),
            base.marginManager.addCell(-0.1, -1.0, base.a2dTopRight),
            base.marginManager.addCell(-0.1, -1.4, base.a2dTopRight)
        ]

        base.mouseWatcherNode.setEnterPattern('mouse-enter-%r')
        base.mouseWatcherNode.setLeavePattern('mouse-leave-%r')
        base.mouseWatcherNode.setButtonDownPattern('button-down-%r')
        base.mouseWatcherNode.setButtonUpPattern('button-up-%r')

        base.transitions = CITransitions(loader)
        base.transitions.IrisModelName = "phase_3/models/misc/iris.bam"
        base.transitions.FadeModelName = "phase_3/models/misc/fade.bam"

        self.accept(self.inputStore.TakeScreenshot, ScreenshotHandler.takeScreenshot)

        #self.accept('u', render.setShaderOff)
        #self.accept('i', render.setShaderOff, [1])
        #self.accept('o', render.setShaderOff, [2])

        # Disabled oobe culling
        #self.accept('o', self.oobeCull)
        #self.accept('c', self.reportCam)


        self.taskMgr.add(self.__update3DAudio, 'CIBase.update3DAudio', 48)

    def initialize(self):
        BSPBase.initialize(self)
        self.cam.node().getDisplayRegion(0).setClearDepthActive(1)
        self.camLens.setNearFar(CIGlobals.DefaultCameraNear, CIGlobals.DefaultCameraFar)
        self.win.disableClears()

        render.hide()

        self.bspLoader.setWin(self.win)
        self.bspLoader.setCamera(self.camera)
        self.bspLoader.setRender(self.render)

        self.credits2d = self.render2d.attachNewNode(PGTop("credits2d"))
        self.credits2d.setScale(1.0 / self.getAspectRatio(), 1.0, 1.0)

    def __update3DAudio(self, task):
        self.audio3d.update()
        return task.cont

    def updateShadersAndPostProcess(self, task):
        BSPBase.updateShadersAndPostProcess(self, task)
        if hasattr(self, 'filters'):
            self.filters.update()
        return task.cont

    def linkClientSideBSPEntities(self):
        from src.coginvasion.szboss import FuncWater, Ropes, InfoPlayerRelocate, EnvLightGlow, PointSpotlight, EnvSun, PointDevshotCamera
        self.bspLoader.linkEntityToClass("func_water", FuncWater.FuncWater)
        self.bspLoader.linkEntityToClass("rope_begin", Ropes.RopeBegin)
        self.bspLoader.linkEntityToClass("rope_keyframe", Ropes.RopeKeyframe)
        self.bspLoader.linkEntityToClass("info_player_relocate", InfoPlayerRelocate.InfoPlayerRelocate)
        self.bspLoader.linkEntityToClass("env_lightglow", EnvLightGlow.EnvLightGlow)
        self.bspLoader.linkEntityToClass("point_spotlight", PointSpotlight.PointSpotlight)
        self.bspLoader.linkEntityToClass("env_sun", EnvSun.EnvSun)
        self.bspLoader.linkEntityToClass("point_devshot_camera", PointDevshotCamera.PointDevshotCamera)

    def addPrecacheClass(self, cls):
        self.precacheList.append(cls)

    def hideHood(self):
        base.cr.playGame.hood.loader.geom.hide()

    def reportCam(self):
        #print(self.camera)
        #print(self.camera.getNetTransform())
        self.camera.setScale(render, 1)
        self.camera.setShear(render, 0)

        """
        print('TPM START')
        tpMgr = TextPropertiesManager.getGlobalPtr()
        print('PROPERTIES GET')
        tpRed = TextProperties()
        tpRed.setTextColor(1, 0, 0, 1)
        tpSlant = TextProperties()
        tpSlant.setSlant(0.3)
        print('RED AND SLANT GENERATED')
        tpMgr.setProperties('red', tpRed)
        print('RED SET')
        try:
            tpMgr.setProperties('slant', tpSlant)
        except Exception:
            print('AN EXCEPTION OCCURRED')
        print('SLANT SET')
        print('TPM END')
        """

    def convertHammerAngles(self, angles):
        """
        (pitch, yaw + 90, roll) -> (yaw, pitch, roll)
        """
        temp = angles[0]
        angles[0] = angles[1] - 90
        angles[1] = temp
        return angles

    def planPath(self, startPos, endPos):
        """Uses recast/detour to find a path from the generated nav mesh from the BSP file."""

        if not self.navMeshNp:
            return [startPos, endPos]
        result = []
        valueList = self.navMeshNp.node().path_find_follow(startPos, endPos)
        for i in range(valueList.get_num_values()):
            result.append(valueList.get_value(i))
        return result

    def getBSPLevelLightEnvironmentData(self):
        #    [has data, angles, color]
        data = [0, Vec3(0), Vec4(0)]

        if not self.bspLoader.hasActiveLevel():
            return data

        for i in range(self.bspLoader.getNumEntities()):
            classname = self.bspLoader.getEntityValue(i, "classname")
            if classname == "light_environment":
                data[0] = 1
                data[1] = self.convertHammerAngles(
                    self.bspLoader.getEntityValueVector(i, "angles"))
                data[2] = self.bspLoader.getEntityValueColor(i, "_light")
                break

        return data

    def cleanupSkyBox(self):
        if self.skyBoxUtil:
            self.skyBoxUtil.stopSky()
            self.skyBoxUtil.cleanup()
            self.skyBoxUtil = None
        if self.skyBox:
            self.skyBox.removeNode()
            self.skyBox = None

    def cleanupBSPLevel(self):
        self.cleanupSkyBox()
        #self.cleanupNavMesh()
        if self.bspLevel:
            # Cleanup any physics meshes for the level.
            self.disableAndRemovePhysicsNodes(self.bspLevel)
            self.bspLevel.removeNode()
            self.bspLevel = None
        self.bspLoader.cleanup()
        base.brushCollisionMaterialData = {}

    #def cleanupNavMesh(self):
    #    if self.navMeshNp:
    #        self.navMeshNp.removeNode()
    #        self.navMeshNp = None

    #def setupNavMesh(self, node):
    #    self.cleanupNavMesh()

    #    nmMgr = RNNavMeshManager.get_global_ptr()
    #    self.navMeshNp = nmMgr.create_nav_mesh()
    #    self.navMeshNp.node().set_owner_node_path(node)
    #    self.navMeshNp.node().setup()

    #    if 0:
    #        self.navMeshNp.node().enable_debug_drawing(self.camera)
    #        self.navMeshNp.node().toggle_debug_drawing(True)

    def setupRender(self):
        """
        Creates the render scene graph, the primary scene graph for
        rendering 3-d geometry.
        """
        ## This is the root of the 3-D scene graph.
        ## Make it a BSPRender node to automatically cull
        ## nodes against the BSP leafs if there is a loaded
        ## BSP level.
        self.render = NodePath(BSPRender('render', BSPLoader.getGlobalPtr()))
        self.render.setAttrib(RescaleNormalAttrib.makeDefault())
        self.render.setTwoSided(0)
        self.backfaceCullingEnabled = 1
        self.textureEnabled = 1
        self.wireframeEnabled = 0

    def loadSkyBox(self, skyType):
        if skyType != OutdoorLightingConfig.STNone:
            self.skyBox = loader.loadModel(OutdoorLightingConfig.SkyData[skyType][0])
            self.skyBox.hide(CIGlobals.ShadowCameraBitmask)
            self.skyBox.reparentTo(camera)
            self.skyBox.setCompass()
            self.skyBox.setZ(-350)
            self.skyBoxUtil = SkyUtil()
            self.skyBoxUtil.startSky(self.skyBox)

    def loadBSPLevel(self, mapFile):
        self.cleanupBSPLevel()

        base.bspLoader.read(mapFile)
        base.bspLevel = base.bspLoader.getResult()
        base.bspLoader.doOptimizations()
        #base.brushCollisionMaterialData = PhysicsUtils.makeBulletCollFromGeoms(base.bspLevel.find("**/hull"))
        for prop in base.bspLevel.findAllMatches("**/+BSPProp"):
            base.createAndEnablePhysicsNodes(prop)
        #base.setupNavMesh(base.bspLevel.find("**/model-0"))

        try:
            skyType = self.cr.playGame.hood.olc.skyType
        except:
            try:
                skyType = int(self.bspLoader.getCEntity(0).getEntityValue("skytype"))
            except:
                skyType = 1

        if skyType != OutdoorLightingConfig.STNone:
            skyCubemap = loader.loadCubeMap(OutdoorLightingConfig.SkyData[skyType][2])
            self.shaderGenerator.setIdentityCubemap(skyCubemap)

        CIGlobals.preRenderScene(render)

    def doNextFrame(self, func, extraArgs = []):
        taskMgr.add(self.__doNextFrameTask, "doNextFrame" + str(id(func)), extraArgs = [func, extraArgs], appendTask = True, sort = 100000)

    def __doNextFrameTask(self, func, extraArgs, task):
        func(*extraArgs)
        return task.done

    def loadSfxOnNode(self, sndFile, node):
        """ Loads up a spatialized sound and attaches it to the specified node. """
        LoadSfxCollector.start()
        snd = self.audio3d.loadSfx(sndFile)
        self.audio3d.attachSoundToObject(snd, node)
        LoadSfxCollector.stop()
        return snd

    def loadSfx(self, sndFile):
        LoadSfxCollector.start()
        snd = BSPBase.loadSfx(self, sndFile)
        LoadSfxCollector.stop()
        return snd

    def physicsReport(self):
        print("\nThere are {0} total rigid bodies:".format(base.physicsWorld.getNumRigidBodies()))
        for rb in base.physicsWorld.getRigidBodies():
            print("\t", NodePath(rb))
        print("\n")

    def removeEverything(self):
        for task in self.taskMgr.getTasks():
            if task.getName() not in ['dataLoop', 'igLoop']:
                task.remove()
        camera.reparentTo(render)
        for tex in render.findAllTextures():
            tex.releaseAll()
        for tex in aspect2d.findAllTextures():
            tex.releaseAll()
        for tex in render2d.findAllTextures():
            tex.releaseAll()
        for tex in hidden.findAllTextures():
            tex.releaseAll()
        for node in render.findAllMatches("**;+s"):
            node.removeNode()
        for node in aspect2d.findAllMatches("**;+s"):
            node.removeNode()
        for node in render2d.findAllMatches("**;+s"):
            node.removeNode()
        for node in hidden.findAllMatches("**;+s"):
            node.removeNode()
        TexturePool.garbageCollect()
        ModelPool.garbageCollect()
        RenderState.garbageCollect()
        RenderState.clearCache()
        RenderState.clearMungerCache()

        self.win.getGsg().getPreparedObjects().releaseAll()
        self.graphicsEngine.renderFrame()

    def doMemReport(self):
        MemoryUsage.showCurrentTypes()
        MemoryUsage.showCurrentAges()
        #print(MemoryUsage.getCurrentCppSize())
       # print(MemoryUsage.getExternalSize())
        #print(MemoryUsage.getTotalSize())

    def doPointers(self):
        #print("---------------------------------------------------------------------")
        data = {}
        mup = MemoryUsagePointers()
        MemoryUsage.getPointers(mup)
        for i in range(mup.getNumPointers()):
            ptr = mup.getPythonPointer(i)
            if ptr.__class__.__name__ in data.keys():
                data[ptr.__class__.__name__] += 1
            else:
                data[ptr.__class__.__name__] = 1

        #print("NodeReferenceCount:", data["NodeReferenceCount"])
        #print("CopyOnWriteObject:", data["CopyOnWriteObject"])

        #print("---------------------------------------------------------------------")

    def doCamShake(self, intensity = 1.0, duration = 0.5, loop = False):
        shake = ShakeCamera(intensity, duration)
        shake.start(loop)
        return shake

    def emitShake(self, emitter, magnitude = 1.0, duration = 0.5):
        dist = camera.getDistance(emitter)
        maxDist = 100.0 * magnitude
        maxIntense = 1.4 * magnitude
        if dist <= maxDist:
            self.doCamShake(maxIntense - (maxIntense * (dist / maxDist)), duration)

    def renderFrames(self):
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()

    def prepareScene(self):
        render.prepareScene(self.win.getGsg())

    def setPhysicsDebug(self, flag):
        self.physicsDbgFlag = flag
        debugNode = self.debugNP.node()
        if flag:
            debugNode.showWireframe(True)
            debugNode.showConstraints(True)
            debugNode.showBoundingBoxes(True)
            debugNode.showNormals(False)
            self.debugNP.show()
        else:
            debugNode.showWireframe(False)
            debugNode.showConstraints(False)
            debugNode.showBoundingBoxes(False)
            debugNode.showNormals(False)
            self.debugNP.hide()

    def stopMusic(self):
        if self.music:
            self.music.stop()
            self.music = None
        self.currSongName = None

    def playMusic(self, songName, looping = True, volume = 1.0):
        if isinstance(songName, list):
            # A list of possible songs were passed in, pick a random one.
            songName = random.choice(songName)

        if songName == self.currSongName:
            # Don't replay the same song.
            return self.music

        self.stopMusic()

        self.currSongName = songName

        song = MusicCache.findSong(songName)
        if not song:
            self.notify.warning("Song `{0}` not found in cache.".format(songName))
            return None

        self.music = song
        self.music.setLoop(looping)
        self.music.setVolume(volume)
        self.music.play()

        return self.music

    def fadeOutMusic(self, time = 1.0, music = None):
        if not music:
            music = self.music

        if not music:
            return

        self.fadeAudio(time, music, music.getVolume(), 0.0)

    def fadeAudio(self, time, audio, start, end):
        from direct.interval.IntervalGlobal import LerpFunc

        def __changeMusicVolume(vol):
            audio.setVolume(vol)

        LerpFunc(__changeMusicVolume, time, start, end).start()

    def enablePhysicsNodes(self, rootNode):
        PhysicsUtils.attachBulletNodes(rootNode)

    def disablePhysicsNodes(self, rootNode):
        PhysicsUtils.detachBulletNodes(rootNode)

    def createPhysicsNodes(self, rootNode):
        PhysicsUtils.makeBulletCollFromPandaColl(rootNode)

    def createAndEnablePhysicsNodes(self, rootNode):
        self.createPhysicsNodes(rootNode)
        self.enablePhysicsNodes(rootNode)

    def removePhysicsNodes(self, rootNode):
        PhysicsUtils.removeBulletNodes(rootNode)

    def disableAndRemovePhysicsNodes(self, rootNode):
        PhysicsUtils.detachAndRemoveBulletNodes(rootNode)

    def __physicsUpdate(self, task):
        dt = globalClock.getDt()

        self.physicsWorld.doPhysics(dt, metadata.PHYS_SUBSTEPS, 0.016)

        return task.cont

    def projectShadows(self):
        #self.shadowCaster.projectShadows()
        pass

    def initStuff(self):
        BSPBase.initStuff(self)

        # Any ComputeNodes should be parented to this node, not render.
        # We isolate ComputeNodes to avoid traversing the same ComputeNodes
        # when doing multi-pass rendering.
        self.computeRoot = NodePath('computeRoot')
        self.computeCam = self.makeCamera(base.win)
        self.computeCam.node().setCameraMask(CIGlobals.ComputeCameraBitmask)
        self.computeCam.node().setCullBounds(OmniBoundingVolume())
        self.computeCam.node().setFinal(True)
        self.computeCam.reparentTo(self.computeRoot)

        self.bspLoader.setShaderGenerator(self.shaderGenerator)

        # Precache water bar shader, prevents crash from running out of GPU registers
        loader.loadShader("shaders/progress_bar.sha")

        self.bspLoader.setWantShadows(metadata.USE_REAL_SHADOWS)

        self.waterReflectionMgr.load()

        #self.filters.setDepthOfField(distance = 10.0, range = 175.0, near = 1.0, far = 1000.0 / (1000.0 - 1.0))

        #from src.coginvasion.globals import BSPUtility
        #BSPUtility.applyUnlitOverride(render)

        # We define this here (naming it cl_ to avoid trying to use the old base.attackMgr)
        # in order to precache attacks. The ClientRepository will then take our self.cl_attackMgr
        # and use it as base.cr.attackMgr.
        from src.coginvasion.attack.AttackManager import AttackManager
        self.cl_attackMgr = AttackManager()

        if self.DebugShaderQualities:
            from panda3d.bsp import SHADERQUALITY_HIGH, SHADERQUALITY_MEDIUM, SHADERQUALITY_LOW
            self.accept('1', self.shaderGenerator.setShaderQuality, [SHADERQUALITY_LOW])
            self.accept('2', self.shaderGenerator.setShaderQuality, [SHADERQUALITY_MEDIUM])
            self.accept('3', self.shaderGenerator.setShaderQuality, [SHADERQUALITY_HIGH])

    def makeCamera(self, win, sort = 0, scene = None,
                   displayRegion = (0, 1, 0, 1), stereo = None,
                   aspectRatio = None, clearDepth = 0, clearColor = None,
                   lens = None, camName = 'cam', mask = None,
                   useCamera = None):
        """
        Makes a new 3-d camera associated with the indicated window,
        and creates a display region in the indicated subrectangle.

        If stereo is True, then a stereo camera is created, with a
        pair of DisplayRegions.  If stereo is False, then a standard
        camera is created.  If stereo is None or omitted, a stereo
        camera is created if the window says it can render in stereo.

        If useCamera is not None, it is a NodePath to be used as the
        camera to apply to the window, rather than creating a new
        camera.
        """
        # self.camera is the parent node of all cameras: a node that
        # we can move around to move all cameras as a group.
        if self.camera == None:
            # We make it a ModelNode with the PTLocal flag, so that
            # a wayward flatten operations won't attempt to mangle the
            # camera.
            self.camera = self.render.attachNewNode(ModelNode('camera'))
            self.camera.node().setPreserveTransform(ModelNode.PTLocal)
            builtins.camera = self.camera

            self.mouse2cam.node().setNode(self.camera.node())

        if useCamera:
            # Use the existing camera node.
            cam = useCamera
            camNode = useCamera.node()
            assert(isinstance(camNode, Camera))
            lens = camNode.getLens()
            cam.reparentTo(self.camera)

        else:
            # Make a new Camera node.
            camNode = Camera(camName)
            if lens == None:
                lens = PerspectiveLens()

                if aspectRatio == None:
                    aspectRatio = self.getAspectRatio(win)
                lens.setAspectRatio(aspectRatio)

            cam = self.camera.attachNewNode(camNode)

        if lens != None:
            camNode.setLens(lens)

        if scene != None:
            camNode.setScene(scene)

        if mask != None:
            if (isinstance(mask, int)):
                mask = BitMask32(mask)
            camNode.setCameraMask(mask)

        if self.cam == None:
            self.cam = cam
            self.camNode = camNode
            self.camLens = lens

        self.camList.append(cam)

        # Now, make a DisplayRegion for the camera.
        if stereo is not None:
            if stereo:
                dr = win.makeStereoDisplayRegion(*displayRegion)
            else:
                dr = win.makeMonoDisplayRegion(*displayRegion)
        else:
            dr = win.makeDisplayRegion(*displayRegion)

        dr.setSort(sort)

        dr.disableClears()

        # By default, we do not clear 3-d display regions (the entire
        # window will be cleared, which is normally sufficient).  But
        # we will if clearDepth is specified.
        if clearDepth:
            dr.setClearDepthActive(1)

        if clearColor:
            dr.setClearColorActive(1)
            dr.setClearColor(clearColor)

        dr.setCamera(cam)

        return cam

    def makeCamera2d(self, win, sort = 10,
                     displayRegion = (0, 1, 0, 1), coords = (-1, 1, -1, 1),
                     lens = None, cameraName = None):
        """
        Makes a new camera2d associated with the indicated window, and
        assigns it to render the indicated subrectangle of render2d.
        """
        dr = win.makeMonoDisplayRegion(*displayRegion)
        dr.setSort(sort)
        dr.disableClears()

        # Make any texture reloads on the gui come up immediately.
        dr.setIncompleteRender(False)

        left, right, bottom, top = coords

        # Now make a new Camera node.
        if (cameraName):
            cam2dNode = Camera('cam2d_' + cameraName)
        else:
            cam2dNode = Camera('cam2d')

        if lens == None:
            lens = OrthographicLens()
            lens.setFilmSize(right - left, top - bottom)
            lens.setFilmOffset((right + left) * 0.5, (top + bottom) * 0.5)
            lens.setNearFar(-1000, 1000)
        cam2dNode.setLens(lens)

        # self.camera2d is the analog of self.camera, although it's
        # not as clear how useful it is.
        if self.camera2d == None:
            self.camera2d = self.render2d.attachNewNode('camera2d')

        camera2d = self.camera2d.attachNewNode(cam2dNode)
        dr.setCamera(camera2d)

        if self.cam2d == None:
            self.cam2d = camera2d

        return camera2d

    def precacheStuff(self):
        from src.coginvasion.base.Precache import Precacheable
        for name, dclass in self.cr.dclassesByName.items():
            if hasattr(dclass.getClassDef(), 'precache'):
                print("Precaching dclass", dclass.getClassDef(), name)
                dclass.getClassDef().precache()

        for cls in self.precacheList:
            cls.precache()

        from src.coginvasion.toon import ToonGlobals
        ToonGlobals.precacheToons()

        self.cl_attackMgr.precache()

        from src.coginvasion.gags.LocationSeeker import LocationSeeker
        LocationSeeker.precache()

        from src.coginvasion.cog import SuitBank
        SuitBank.precacheSuits()

        from src.coginvasion.base.Precache import precacheActor, precacheModel, precacheScene, precacheMaterial, precacheTexture, precacheSound, precacheFont
        precacheActor(CIGlobals.getSplat())

        from src.coginvasion.nametag import NametagGlobals
        precacheScene(NametagGlobals.cardModel)
        precacheScene(NametagGlobals.arrowModel)
        precacheScene(NametagGlobals.chatBalloon3dModel)
        precacheScene(NametagGlobals.chatBalloon2dModel)
        precacheScene(NametagGlobals.thoughtBalloonModel)

        precacheModel("phase_3.5/models/props/suit-particles.bam")
        precacheModel("phase_14/models/props/creampie_gib.bam")

        # UI
        precacheTexture("phase_14/maps/crosshair_4.png")
        precacheTexture("phase_14/maps/damage_effect.png")

        # Explosion
        precacheModel("phase_3.5/models/props/explosion.bam")
        precacheTexture("phase_14/maps/water.png")
        precacheTexture("materials/particles/largesmoke.png")

        # Decals
        precacheMaterial("phase_14/materials/pie_splat.mat")
        precacheMaterial("materials/scorch1.mat")
        precacheMaterial("materials/bigshot1.mat")

        # Concrete
        for i in range(1, 5 + 1):
            precacheMaterial("materials/decals/concrete/shot{0}.mat".format(i))
        # Wood
        for i in range(1, 5 + 1):
            precacheMaterial("materials/decals/wood/shot{0}.mat".format(i))
        # Glass
        for i in range(1, 5 + 1):
            precacheMaterial("materials/decals/glass/shot{0}.mat".format(i))
        # Metal
        for i in range(1, 5 + 1):
            precacheMaterial("materials/decals/glass/shot{0}.mat".format(i))

        # Fonts
        precacheFont(CIGlobals.getSuitFont())
        precacheFont(CIGlobals.getToonFont())
        precacheFont(CIGlobals.getMickeyFont())
        precacheFont(CIGlobals.getMinnieFont())

        precacheActor(['phase_14/models/props/tnt.bam', {'chan': 'phase_5/models/props/tnt-chan.bam'}])
        # Cog propeller
        precacheActor(['phase_4/models/props/propeller-mod.bam', {'chan': 'phase_4/models/props/propeller-chan.bam'}])

        from src.coginvasion.base.MuzzleParticle import MuzzleParticle
        MuzzleParticle.precache()

        # Sounds
        ricsFormat = "sound/weapons/ric{0}.wav"
        rics = [1, 5]
        for ric in rics:
            precacheSound(ricsFormat.format(ric))

        from src.coginvasion.phys import Surfaces
        Surfaces.precacheSurfaces()

    def setCellsActive(self, cells, active):
        for cell in cells:
            cell.setActive(active)
        self.marginManager.reorganize()

    def setTimeOfDay(self, time):
        if self.metadata.USE_RENDER_PIPELINE:
            self.pipeline.daytime_mgr.time = time

    def doOldToontownRatio(self):
        BSPBase.adjustWindowAspectRatio(self, 4. / 3.)
        self.credits2d.setScale(1.0 / (4. / 3.), 1.0, 1.0)

    def doRegularRatio(self):
        BSPBase.adjustWindowAspectRatio(self, self.getAspectRatio())

    def adjustWindowAspectRatio(self, aspectRatio):
        if (CIGlobals.getSettingsMgr() is None):
            BSPBase.adjustWindowAspectRatio(self, aspectRatio)
            self.credits2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
            return

        if CIGlobals.getSettingsMgr().getSetting("maspr").getValue():
            # Go ahead and maintain the aspect ratio if the user wants us to.
            BSPBase.adjustWindowAspectRatio(self, aspectRatio)
            self.credits2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
        else:
            # The user wants us to keep a 4:3 ratio no matter what (old toontown feels).
            self.doOldToontownRatio()

    def muteMusic(self):
        self.musicManager.setVolume(0.0)

    def unMuteMusic(self):
        self.musicManager.setVolume(CIGlobals.SettingsMgr.getSetting("musvol").getValue())

    def muteSfx(self):
        self.sfxManagerList[0].setVolume(0.0)

    def unMuteSfx(self):
        self.sfxManagerList[0].setVolume(CIGlobals.SettingsMgr.getSetting("sfxvol").getValue())

    def localAvatarReachable(self):
        # This verifies that the localAvatar hasn't been deleted and isn't none.
        return hasattr(self, 'localAvatar') and self.localAvatar
