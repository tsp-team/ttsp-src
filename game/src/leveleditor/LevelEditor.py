from panda3d.core import WindowProperties, NativeWindowHandle

from src.coginvasion.base.BSPBase import BSPBase

from PyQt5 import QtWidgets, QtCore, QtGui

class LevelEditorSubWind(QtWidgets.QWidget):

    def __init__(self, area):
        QtWidgets.QWidget.__init__(self)
        area.addSubWindow(self)
        layout = QtWidgets.QGridLayout(self)
        self.setLayout(layout)
        self.setWindowTitle("3D View")
        self.resize(640, 480)
        self.show()
        
    def resizeEvent(self, event):
        if not hasattr(base, 'win'):
            return

        props = WindowProperties()
        props.setSize(event.size().width(), event.size().height())
        base.win.requestProperties(props)

class LevelEditorWindow(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        from src.leveleditor.ui.mainwindow import Ui_LevelEditor
        self.ui = Ui_LevelEditor()
        self.ui.setupUi(self)

        self.gameViewWind = LevelEditorSubWind(self.ui.gameViewArea)

class LevelEditorApp(QtWidgets.QApplication):

    def __init__(self):
        QtWidgets.QApplication.__init__(self, [])

        self.setStyle("Fusion")


        dark_palette = QtGui.QPalette()

        dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        dark_palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

        self.setPalette(dark_palette)

        self.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

        self.window = LevelEditorWindow()
        self.window.show()

class LevelEditor(BSPBase):

    def __init__(self):
        self.qtApp = LevelEditorApp()

        BSPBase.__init__(self)
        self.loader.mountMultifiles()
        self.loader.mountMultifile("resources/mod.mf")

        toon = loader.loadModel("phase_4/models/neighborhoods/toontown_central_beta.bam")
        toon.reparentTo(render)
        #toon.setY(10)

        base.enableMouse()

        from panda3d.core import DirectionalLight, AmbientLight
        dlight = DirectionalLight('dlight')
        dlight.setColor((2.2, 2.2, 2.2, 1))
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        render.setLight(dlnp)
        self.dlnp = dlnp
        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = render.attachNewNode(alight)
        render.setLight(alnp)

        # Timer to run the panda mainloop
        self.mainloopTimer = QtCore.QTimer()
        self.mainloopTimer.timeout.connect(self.taskMgr.step)
        self.mainloopTimer.setSingleShot(False)

        base.setBackgroundColor(0, 0, 0)

    def initStuff(self):
        BSPBase.initStuff(self)
        self.camLens.setMinFov(70.0 / (4./3.))

    def openDefaultWindow(self, *args, **kwargs):
        props = WindowProperties.getDefault()
        props.setParentWindow(int(self.qtApp.window.gameViewWind.winId()))
        props.setOpen(True)
        props.setForeground(True)
        props.setOrigin(0, 0)
        kwargs['props'] = props
        BSPBase.openDefaultWindow(self, *args, **kwargs)

    def run(self):
        self.mainloopTimer.start(0)
        self.qtApp.exec_()