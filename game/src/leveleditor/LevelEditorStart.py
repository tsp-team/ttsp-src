import sys

try:
    import PyQt5
except ImportError:
    print("ERROR: You need to pull in PyQt5 via pip to use the level editor")
    sys.exit(1)

try:
    import fgdtools
except ImportError:
    print("ERROR: You need to pull in fgdtools via pip to use the level editor")
    sys.exit(1)

import builtins
from src.coginvasion.base.Metadata import Metadata
metadata = Metadata()
builtins.metadata = metadata

from panda3d.core import loadPrcFile, loadPrcFileData, ConfigVariableString, ConfigVariableDouble
loadPrcFile('config/Confauto.prc')
loadPrcFile('config/config_client.prc')
loadPrcFileData('', 'model-path ./resources') # Don't require mounting of phases

from src.coginvasion.settings.SettingsManager import SettingsManager
sm = SettingsManager()

from src.coginvasion.globals import CIGlobals
CIGlobals.SettingsMgr = sm

from src.leveleditor.LevelEditor import LevelEditor
base = LevelEditor()

ConfigVariableDouble('decompressor-step-time').setValue(0.01)
ConfigVariableDouble('extractor-step-time').setValue(0.01)

base.initStuff()

base.run()