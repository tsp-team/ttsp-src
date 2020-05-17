from panda3d.core import loadPrcFileData, FilterProperties

from src.coginvasion.base.CIBase import CIBase

from src.mod import ModGlobals
from src.mod.VOX import VOX
from src.mod.ModMainMenu import ModMainMenu

import subprocess

class ModBase(CIBase):
    
    def __init__(self):
        CIBase.__init__(self)
        
        self.isMuseum = ModGlobals.IsMuseum
        
        from p3recastnavigation import RNNavMeshManager

        nmMgr = RNNavMeshManager.get_global_ptr()
        nmMgr.set_root_node_path(render)
        nmMgr.get_reference_node_path().reparentTo(render)
        nmMgr.start_default_update()
        nmMgr.get_reference_node_path_debug().reparentTo(render)
        self.nmMgr = nmMgr

        from direct.distributed.ClockDelta import globalClockDelta
        __builtins__['globalClockDelta'] = globalClockDelta
        
        self.loader.mountMultifile("resources/mod.mf")
        self.loader.mountMultifile("resources/museum.mf")
        
        self.vox = VOX()
        self.mainMenu = ModMainMenu()
        
        self.lost = False

        self.accept('7', self.audio3d.printAudioDigest)
        self.accept('t', self.printTaskMgr)

        #self.setPhysicsDebug(True)

        #self.bspLoader.setWireframe(True)
        
        #self.setPhysicsDebug(True)
        
        #fprops = FilterProperties()
        #fprops.add_echo(0.0, 1.0, 3.0, 0.2)
        #fprops.addSfxreverb(0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0)
        #fprops.addLowpass(1000, 1.0)
        #fprops.addSfxreverb(0, 0, 0, 0, 0.5, 1000, 0.15, 0.0, 0.1, 100, 0, 20, 0, 20)
        #self.sfxManagerList[0].configureFilters(fprops)
        
    def printTaskMgr(self):
        print(self.taskMgr)
        
    def buildCubemaps(self):
        # Don't render any existing/default cubemaps when building
        loadPrcFileData("", "mat_envmaps 0")
        self.win.getGsg().getShaderGenerator().rehashGeneratedShaders()

        self.bspLoader.buildCubemaps()
        
    def loadBSPLevel(self, mapFile):
        CIBase.loadBSPLevel(self, mapFile)
        
        if self.isMuseum:
            museumCubemap = loader.loadCubeMap("resources/museum/materials/sky/sky#.png")
            self.shaderGenerator.setIdentityCubemap(museumCubemap)
        
        #skyCubemap = loader.loadCubeMap("phase_14/maps/TT_sky/TT_sky_#.jpg")
        #self.shaderGenerator.setIdentityCubemap(skyCubemap)
        
    def initStuff(self):
        CIBase.initStuff(self)
        from src.coginvasion.base import MusicCache
        MusicCache.precacheMusic()
        MusicCache.precacheMusicDir("sound/music")
        
    def initStuffMod(self):
        
        self.vox.load("sound/vox", "wav")
        if not self.isMuseum:
            self.accept('y', self.vox.say, ["buzwarn buzwarn Attention , forbidden personnel detected in this area . All cogs apprehend immediately"])
        self.mainMenu.create()
        
    def playGame(self):
        base.transitions.fadeScreen(1.0)
        self.mainMenu.shutdown()
        
        #if not self.isMuseum:
            #self.precacheStuff()
            
        # TODO: Production case
        import os
        enginePath = os.environ["CIOENGINE"]
        subprocess.Popen([enginePath + "\\python\\ppython", "-B", "-m", "src.mod.ModStartAI"])
        
        print("Starting client repo")
        from src.mod.distributed.ModClientRepository import ModClientRepository
        self.cr = ModClientRepository(ModGlobals.DCFileNames)
        
        from src.coginvasion.distributed.DistributedSmoothNode import globalActivateSmoothing
        globalActivateSmoothing(True, False)
        
        self.establishConnections()
        
        from src.mod.NPC_VP import NPC_VP
        from src.coginvasion.szboss.goon.NPC_Goon import NPC_Goon
        self.addPrecacheClass(NPC_VP)
        self.addPrecacheClass(NPC_Goon)

        #self.setSceneGraphAnalyzerMeter(True)
        
        #base.sfxManagerList[0].setActive(False)
        
        #self.filters.setSSR()
        #self.bufferViewer.enable(1)
        
    def leaveGame(self):
        self.localAvatar.battleZone.d_shutdown()
        
        for doId, do in self.cr.doId2do.items():
            if doId != self.localAvatarId:
                self.cr.deleteObject(doId)
                
        self.cr.sendDeleteMsg(self.localAvatarId)
        self.cr.deleteObject(self.localAvatarId)
        self.cr.sendDisconnect()
        
    def lose(self, wait = 5.0, duration = 2.0):
        if self.lost:
            return
        
        def adjustMusicVol(vol):
            self.musicManager.setVolume(vol)
        
        def adjustSfxVol(vol):
            self.sfxManagerList[0].setVolume(vol)
        
        from direct.gui.DirectGui import OnscreenText, DGG
        from direct.interval.IntervalGlobal import Parallel, Sequence, Wait, LerpFunc, Func
        fadeIval = base.transitions.getFadeOutIval(duration)
        diedText = OnscreenText(text = "You failed to save Flippy!\nYou lose!", fg = (1, 1, 1, 1))
        diedText.reparentTo(aspect2d, DGG.FADE_SORT_INDEX + 1)
        diedText.setAlphaScale(0)
        textFadeIval = diedText.colorScaleInterval(duration, (1, 1, 1, 1), (1, 1, 1, 0))
        Sequence(Wait(wait), Parallel(fadeIval, textFadeIval,
                                      LerpFunc(adjustMusicVol, duration,
                                               self.musicManager.getVolume(), 0.0),
                                      LerpFunc(adjustSfxVol, duration,
                                      self.sfxManagerList[0].getVolume(), 0.0)), Func(self.leaveGame)).start()
                                      
        self.lost = True
        
    def establishConnections(self):
        print("Now connecting")
        self.cr.connect(['http://127.0.0.1:7032'], self.__onClientConnect)
        
    def __onClientConnect(self):
        print("Sending client hello")
        self.cr.sendClientHello()
        self.acceptOnce('createReady', self.__handleClientReady)
        
    def __handleClientReady(self):
        print("Client ready")
        self.start()
        
    def makePlayer(self):
        from src.mod.ModLocalAvatar import ModLocalAvatar
        localAvatar = ModLocalAvatar(self.cr)
        base.localAvatar = localAvatar
        localAvatar.setDNAStrand("00/01/05/19/01/19/01/19/137/59/27/27/00") # beta Flippy!
        localAvatar.setPosHpr(0, 0, 0, 0, 0, 0)
        self.cr.createDistributedObject('ModPlayer', localAvatar, zoneId = ModGlobals.BattleZoneId,
                                        doId = ModGlobals.LocalAvatarID, reserveDoId = True)
        base.localAvatarId = localAvatar.doId
        base.localAvId = localAvatar.doId

        self.accept('l', render.ls)
        self.accept('b', self.buildCubemaps)
        
    def beginGame(self):
        from src.coginvasion.base.Precache import precacheScene
        precacheScene(render)
        
        if not self.isMuseum:
            base.localAvatar.startPlay(True, True)
        else:
            base.localAvatar.startPlay(True, True)#False, False)
        
        self.transitions.irisIn()
        
    def start(self):
        # First, wait for time sync
        self.cr.setInterestZones([ModGlobals.UberZoneId])
        self.acceptOnce('gotTimeSync', self.__handleTimeSync)
        
    def __handleTimeSync(self):
        print("Time is synchronized with server")
        self.cr.setInterestZones([ModGlobals.UberZoneId, ModGlobals.BattleZoneId])
        self.makePlayer()
        self.transitions.fadeScreen(1.0)
        #self.beginGame()
        
        
