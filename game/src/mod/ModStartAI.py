import builtins
import sys
sys.dont_write_bytecode = True

from src.coginvasion.base.Metadata import Metadata
metadata = Metadata()
builtins.metadata = metadata
metadata.PROCESS = 'server'
metadata.DEDICATED_SERVER = True

from panda3d.core import loadPrcFile, loadPrcFileData, ConfigVariableString, ConfigVariableDouble, VirtualFileSystem, Filename, PStatClient
loadPrcFile('config/Confauto.prc')
loadPrcFile('config/config_server.prc')
loadPrcFileData('', 'model-path ./resources') # Don't require mounting of phases

#PStatClient.connect()

vfs = VirtualFileSystem.getGlobalPtr()
vfs.mount(Filename("resources/phase_0.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_3.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_3.5.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_4.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_5.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_5.5.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_6.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_7.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_8.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_9.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_10.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_11.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_12.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_13.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/phase_14.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/mod.mf"), ".", VirtualFileSystem.MFReadOnly)
vfs.mount(Filename("resources/museum.mf"), ".", VirtualFileSystem.MFReadOnly)

loadPrcFileData('', 'window-type none')
loadPrcFileData('', 'audio-library-name none')

from direct.showbase.ShowBase import ShowBase
base = ShowBase()

from panda3d.recastnavigation import RNNavMeshManager

nmMgr = RNNavMeshManager.get_global_ptr()
nmMgr.set_root_node_path(render)
nmMgr.get_reference_node_path().reparentTo(render)
nmMgr.start_default_update()
nmMgr.get_reference_node_path_debug().reparentTo(render)
base.nmMgr = nmMgr

from direct.distributed.ClockDelta import globalClockDelta
builtins.globalClockDelta = globalClockDelta

ConfigVariableDouble('decompressor-step-time').setValue(0.01)
ConfigVariableDouble('extractor-step-time').setValue(0.01)

from src.mod import ModGlobals

from src.mod.distributed.ModServerRepository import ModServerRepository
base.sr = ModServerRepository(7032, dcFileNames = ModGlobals.DCFileNames)

def __handleAIReady():
    print("AI ready")
    base.air.setInterestZones([ModGlobals.UberZoneId, ModGlobals.BattleZoneId])
    from direct.distributed.TimeManagerAI import TimeManagerAI
    tm = TimeManagerAI(base.air)
    tm.generateWithRequiredAndId(ModGlobals.TimeManagerID, 0, ModGlobals.UberZoneId)

    def makeBattle():
        from src.mod.ModBattleZoneAI import ModBattleZoneAI
        bZone = ModBattleZoneAI(base.air)
        bZone.generateWithRequiredAndId(ModGlobals.BattleZoneDoID, 0, ModGlobals.BattleZoneId)
        print(base.air.doId2do)
        bZone.setAvatars([ModGlobals.LocalAvatarID])
        plyr = base.air.doId2do.get(ModGlobals.LocalAvatarID)
        plyr.bspLoader = bZone.bspLoader
        plyr.bspLoader.addDynamicEntity(plyr)
        if ModGlobals.IsMuseum:
            bZone.b_setMap("museum_history")
        else:
            bZone.b_setMap("facility")

    def __aiWaitForPlayer(task):
        if ModGlobals.LocalAvatarID in base.air.doId2do.keys():
            print("Player generated on server")
            makeBattle()
            return task.done
        return task.cont

    taskMgr.add(__aiWaitForPlayer, "aiWaitForPlayer")

def __handleAIConnected():
    base.air.sendAIHello()
    base.acceptOnce('createReady', __handleAIReady)

from src.mod.distributed.ModAIRepository import ModAIRepository
base.air = ModAIRepository(ModGlobals.DCFileNames, 'AI')
base.air.connect(['http://127.0.0.1:7032'], __handleAIConnected)

# =================================================================================

import time
sv_min_frametime = ConfigVariableDouble("sv_min_frametime", 1 / 120.0).getValue()

while True:
    try:
        #frameStart = globalClock.getRealTime()
        base.taskMgr.step()
        #frameEnd = globalClock.getRealTime()
        #secElapsed = (frameEnd - frameStart)

        # How many seconds do we have to sleep?
        #sleepTime = sv_min_frametime - secElapsed
        #if sleepTime > 0:
        #    time.sleep(sleepTime)
    except:
        break
