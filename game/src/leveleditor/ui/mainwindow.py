# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LevelEditor(object):
    def setupUi(self, LevelEditor):
        LevelEditor.setObjectName("LevelEditor")
        LevelEditor.resize(1083, 818)
        LevelEditor.setMinimumSize(QtCore.QSize(640, 480))
        LevelEditor.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        LevelEditor.setDocumentMode(False)
        LevelEditor.setTabShape(QtWidgets.QTabWidget.Rounded)
        LevelEditor.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QtWidgets.QWidget(LevelEditor)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.gameViewArea = QtWidgets.QMdiArea(self.centralwidget)
        self.gameViewArea.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.gameViewArea.setObjectName("gameViewArea")
        self.gridLayout.addWidget(self.gameViewArea, 0, 0, 1, 1)
        LevelEditor.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(LevelEditor)
        self.statusbar.setObjectName("statusbar")
        LevelEditor.setStatusBar(self.statusbar)
        self.menubar = QtWidgets.QMenuBar(LevelEditor)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1083, 22))
        self.menubar.setObjectName("menubar")
        self.menuHello = QtWidgets.QMenu(self.menubar)
        self.menuHello.setObjectName("menuHello")
        LevelEditor.setMenuBar(self.menubar)
        self.toolsDock = QtWidgets.QDockWidget(LevelEditor)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolsDock.sizePolicy().hasHeightForWidth())
        self.toolsDock.setSizePolicy(sizePolicy)
        self.toolsDock.setFloating(False)
        self.toolsDock.setObjectName("toolsDock")
        self.dockWidgetContents_3 = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dockWidgetContents_3.sizePolicy().hasHeightForWidth())
        self.dockWidgetContents_3.setSizePolicy(sizePolicy)
        self.dockWidgetContents_3.setObjectName("dockWidgetContents_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.dockWidgetContents_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.toolButton = QtWidgets.QToolButton(self.dockWidgetContents_3)
        self.toolButton.setObjectName("toolButton")
        self.verticalLayout.addWidget(self.toolButton)
        self.toolButton_2 = QtWidgets.QToolButton(self.dockWidgetContents_3)
        self.toolButton_2.setObjectName("toolButton_2")
        self.verticalLayout.addWidget(self.toolButton_2)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.toolsDock.setWidget(self.dockWidgetContents_3)
        LevelEditor.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.toolsDock)
        self.menubar.addAction(self.menuHello.menuAction())

        self.retranslateUi(LevelEditor)
        QtCore.QMetaObject.connectSlotsByName(LevelEditor)

    def retranslateUi(self, LevelEditor):
        _translate = QtCore.QCoreApplication.translate
        LevelEditor.setWindowTitle(_translate("LevelEditor", "TTSP Editor"))
        self.menuHello.setTitle(_translate("LevelEditor", "Hello"))
        self.toolsDock.setWindowTitle(_translate("LevelEditor", "Tools"))
        self.toolButton.setText(_translate("LevelEditor", "Select"))
        self.toolButton_2.setText(_translate("LevelEditor", "Entity"))

