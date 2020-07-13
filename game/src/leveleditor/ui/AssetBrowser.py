from .AssetBrowserUI import Ui_AssetBrowser

from PyQt5 import QtWidgets, QtGui, QtCore

class AssetBrowser(QtWidgets.QDialog):

    FileExtensions = []

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_AssetBrowser()
        self.ui.setupUi(self)
