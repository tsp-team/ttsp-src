from PyQt5 import QtWidgets, QtGui

#from src.leveleditor.ui.ObjectProperties import Ui_Dialog

class EntityEdit(QtWidgets.QDialog):

    def __init__(self, entity):
        QtWidgets.QGroupBox.__init__(self, base.qtApp.window)
        #self.ui = Ui_Dialog()
        #self.ui.setupUi(self)
        #self.setWindowTitle("Object Properties: %s" % entity.classname)
        self.show()
