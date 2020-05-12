from src.coginvasion.phys.BaseLocalControls import BaseLocalControls
from src.coginvasion.globals import CIGlobals

class ModLocalControls(BaseLocalControls):

    BattleNormalSpeed = 400 / 16.0
    BattleRunSpeed = 400 / 16.0
    BattleWalkSpeed = 190 / 16.0

    def getFootstepIval(self, speed):
        return CIGlobals.remapVal(speed, self.BattleWalkSpeed, self.BattleNormalSpeed, 0.4, 0.3)

    def getFootstepVolume(self, speed):
        return CIGlobals.remapVal(speed, self.BattleWalkSpeed, self.BattleNormalSpeed, 0.2, 0.5)

    def getFootstepSoundsDir(self):
        return "sound/player/footsteps_hl2/"

    def getCorrectedFootstepSound(self, surface):
        if surface == "metalfloor":
            return "metal"
        elif surface == "default":
            return "concrete"
        
        return surface

    def footstepSoundCompare(self, surface, basename):
        return surface == basename[:len(basename)-1]
    
    """
    def enableControls(self, wantMouse = 0):
        if self.controlsEnabled:
            return
            
        BaseLocalControls.enableControls(self, wantMouse)
        
        self.currDebugAnim = None
        taskMgr.add(self.__debugAnimTask, 'mlc-debuganimtask')
    
    def disableControls(self, chat = False):
        if not self.controlsEnabled:
            return
            
        BaseLocalControls.disableControls(self, chat)
        
        taskMgr.remove('mlc-debuganimtask')
        
    def __debugAnimTask(self, task):
        from src.coginvasion.phys import PhysicsUtils
        from panda3d.core import NodePath
        hit = PhysicsUtils.rayTestClosestNotMe(base.localAvatar, camera.getPos(render), camera.getPos(render) + (camera.getQuat(render).getForward() * 10000))
        if hit:
            np = NodePath(hit.getNode())
            avNP = np.getPythonTag("avatar")
            onScreenDebug.clear()
            if avNP and hasattr(avNP, 'osdAnimBlends'):
                avNP.osdAnimBlends()
                self.currDebugAnim = avNP
        return task.cont
    """
