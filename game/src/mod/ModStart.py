if __name__ == "__main__":

    import builtins
    from src.coginvasion.base.Metadata import Metadata
    metadata = Metadata()
    builtins.metadata = metadata

    from panda3d.core import loadPrcFile, loadPrcFileData, ConfigVariableString, ConfigVariableDouble
    loadPrcFile('config/Confauto.prc')
    loadPrcFile('config/config_client.prc')
    loadPrcFileData('', 'model-path ./resources') # Don't require mounting of phases

    if ConfigVariableString("threading-model", "").getValue() == "Cull/Draw":
        metadata.MULTITHREADED_PIPELINE = 1

    from src.coginvasion.settings.SettingsManager import SettingsManager
    from src.coginvasion.settings.Setting import SHOWBASE_PREINIT, SHOWBASE_POSTINIT
    jsonFile = "settings.json"

    sm = SettingsManager()

    from src.coginvasion.globals import CIGlobals
    CIGlobals.SettingsMgr = sm
    sm.loadFile(jsonFile)
    sm.doSunriseFor(sunrise = SHOWBASE_PREINIT)

    from src.mod.ModBase import ModBase
    base = ModBase()

    sm.doSunriseFor(sunrise = SHOWBASE_POSTINIT)

    ConfigVariableDouble('decompressor-step-time').setValue(0.01)
    ConfigVariableDouble('extractor-step-time').setValue(0.01)

    from direct.gui import DirectGuiGlobals
    DirectGuiGlobals.setDefaultFontFunc(CIGlobals.getToonFont)
    DirectGuiGlobals.setDefaultFont(CIGlobals.getToonFont())
    DirectGuiGlobals.setDefaultRolloverSound(loader.loadSfx("phase_3/audio/sfx/GUI_rollover.ogg"))
    DirectGuiGlobals.setDefaultClickSound(loader.loadSfx("phase_3/audio/sfx/GUI_create_toon_fwd.ogg"))
    DirectGuiGlobals.setDefaultDialogGeom(loader.loadModel("phase_3/models/gui/dialog_box_gui.bam"))

    from src.coginvasion.nametag import NametagGlobals
    NametagGlobals.setMe(base.cam)
    NametagGlobals.setCardModel('phase_3/models/props/panel.bam')
    NametagGlobals.setArrowModel('phase_3/models/props/arrow.bam')
    NametagGlobals.setChatBalloon3dModel('phase_3/models/props/chatbox.bam')
    NametagGlobals.setChatBalloon2dModel('phase_3/models/props/chatbox_noarrow.bam')
    NametagGlobals.setThoughtBalloonModel('phase_3/models/props/chatbox_thought_cutout.bam')
    chatButtonGui = loader.loadModel('phase_3/models/gui/chat_button_gui.bam')
    NametagGlobals.setPageButton(chatButtonGui.find('**/Horiz_Arrow_UP'), chatButtonGui.find('**/Horiz_Arrow_DN'),
                                 chatButtonGui.find('**/Horiz_Arrow_Rllvr'), chatButtonGui.find('**/Horiz_Arrow_UP'))
    NametagGlobals.setQuitButton(chatButtonGui.find('**/CloseBtn_UP'), chatButtonGui.find('**/CloseBtn_DN'),
                                 chatButtonGui.find('**/CloseBtn_Rllvr'), chatButtonGui.find('**/CloseBtn_UP'))
    soundRlvr = DirectGuiGlobals.getDefaultRolloverSound()
    NametagGlobals.setRolloverSound(soundRlvr)
    soundClick = DirectGuiGlobals.getDefaultClickSound()
    NametagGlobals.setClickSound(soundClick)

    base.initStuff()

    base.hideMouseCursor()

    from src.coginvasion.base.SplashScreen import SplashScreen
    ss = SplashScreen(base.initStuffMod)

    #base.precacheStuff()

    def maybeDoSomethingWithMusic(condition):
        # 0 = paused
        # 1 = restarted
        base.enableMusic(condition)

    def handleMusicEnabled():
        if not hasattr(base, 'cr'):
            return
        
        if base.music is not None:
            base.music.play()

    base.accept("PandaPaused", maybeDoSomethingWithMusic, [0])
    base.accept("PandaRestarted", maybeDoSomethingWithMusic, [1])
    base.accept('MusicEnabled', handleMusicEnabled)

    #aspect2d.hide()

    base.run()
