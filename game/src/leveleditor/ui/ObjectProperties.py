# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'designer/objectproperties.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ObjectProperties(object):
    def setupUi(self, ObjectProperties):
        ObjectProperties.setObjectName("ObjectProperties")
        ObjectProperties.resize(800, 600)
        self.gridLayout = QtWidgets.QGridLayout(ObjectProperties)
        self.gridLayout.setObjectName("gridLayout")
        self.objectPropertiesTabs = QtWidgets.QTabWidget(ObjectProperties)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.objectPropertiesTabs.sizePolicy().hasHeightForWidth())
        self.objectPropertiesTabs.setSizePolicy(sizePolicy)
        self.objectPropertiesTabs.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.objectPropertiesTabs.setObjectName("objectPropertiesTabs")
        self.tabProperties = QtWidgets.QWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabProperties.sizePolicy().hasHeightForWidth())
        self.tabProperties.setSizePolicy(sizePolicy)
        self.tabProperties.setObjectName("tabProperties")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tabProperties)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.labelClass = QtWidgets.QLabel(self.tabProperties)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.labelClass.setFont(font)
        self.labelClass.setObjectName("labelClass")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.labelClass)
        self.comboClass = QtWidgets.QComboBox(self.tabProperties)
        self.comboClass.setObjectName("comboClass")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.comboClass)
        self.gridLayout_2.addLayout(self.formLayout, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnAddKey = QtWidgets.QPushButton(self.tabProperties)
        self.btnAddKey.setObjectName("btnAddKey")
        self.horizontalLayout.addWidget(self.btnAddKey)
        self.btnCopyKey = QtWidgets.QPushButton(self.tabProperties)
        self.btnCopyKey.setObjectName("btnCopyKey")
        self.horizontalLayout.addWidget(self.btnCopyKey)
        self.btnPasteKey = QtWidgets.QPushButton(self.tabProperties)
        self.btnPasteKey.setObjectName("btnPasteKey")
        self.horizontalLayout.addWidget(self.btnPasteKey)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.lePropertyFilter = QtWidgets.QLineEdit(self.tabProperties)
        self.lePropertyFilter.setObjectName("lePropertyFilter")
        self.gridLayout_2.addWidget(self.lePropertyFilter, 2, 0, 1, 1)
        self.splitter = QtWidgets.QSplitter(self.tabProperties)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.propertiesView = QtWidgets.QTreeView(self.splitter)
        self.propertiesView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        self.propertiesView.setAlternatingRowColors(True)
        self.propertiesView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.propertiesView.setIndentation(8)
        self.propertiesView.setUniformRowHeights(True)
        self.propertiesView.setAnimated(True)
        self.propertiesView.setObjectName("propertiesView")
        self.propertiesView.header().setVisible(True)
        self.propertiesView.header().setCascadingSectionResizes(False)
        self.scrollArea_2 = QtWidgets.QScrollArea(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea_2.sizePolicy().hasHeightForWidth())
        self.scrollArea_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setKerning(True)
        self.scrollArea_2.setFont(font)
        self.scrollArea_2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.scrollArea_2.setAutoFillBackground(False)
        self.scrollArea_2.setFrameShape(QtWidgets.QFrame.Panel)
        self.scrollArea_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 758, 195))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblPropertyName = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.lblPropertyName.setFont(font)
        self.lblPropertyName.setWordWrap(True)
        self.lblPropertyName.setObjectName("lblPropertyName")
        self.verticalLayout.addWidget(self.lblPropertyName)
        self.lblPropertyDesc = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
        self.lblPropertyDesc.setWordWrap(True)
        self.lblPropertyDesc.setObjectName("lblPropertyDesc")
        self.verticalLayout.addWidget(self.lblPropertyDesc)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.gridLayout_2.addWidget(self.splitter, 3, 0, 1, 1)
        self.objectPropertiesTabs.addTab(self.tabProperties, "")
        self.tabOutputs = QtWidgets.QWidget()
        self.tabOutputs.setObjectName("tabOutputs")
        self.objectPropertiesTabs.addTab(self.tabOutputs, "")
        self.tabInputs = QtWidgets.QWidget()
        self.tabInputs.setObjectName("tabInputs")
        self.objectPropertiesTabs.addTab(self.tabInputs, "")
        self.gridLayout.addWidget(self.objectPropertiesTabs, 0, 0, 1, 1)

        self.retranslateUi(ObjectProperties)
        self.objectPropertiesTabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(ObjectProperties)

    def retranslateUi(self, ObjectProperties):
        _translate = QtCore.QCoreApplication.translate
        ObjectProperties.setWindowTitle(_translate("ObjectProperties", "Form"))
        self.labelClass.setText(_translate("ObjectProperties", "Class:"))
        self.btnAddKey.setText(_translate("ObjectProperties", "Add Key"))
        self.btnCopyKey.setText(_translate("ObjectProperties", "Copy Keys"))
        self.btnPasteKey.setText(_translate("ObjectProperties", "Paste Keys"))
        self.lePropertyFilter.setPlaceholderText(_translate("ObjectProperties", "(Property Name Filter)"))
        self.lblPropertyName.setText(_translate("ObjectProperties", "This is the Property Name"))
        self.lblPropertyDesc.setText(_translate("ObjectProperties", "This is a more elaborate description of the entity property. You can describe in detail what the property does, how different values affect it, etc. Now I am typing random words to fill up space. I don\'t know what else I can say to describe this text."))
        self.objectPropertiesTabs.setTabText(self.objectPropertiesTabs.indexOf(self.tabProperties), _translate("ObjectProperties", "Properties"))
        self.objectPropertiesTabs.setTabText(self.objectPropertiesTabs.indexOf(self.tabOutputs), _translate("ObjectProperties", "Outputs"))
        self.objectPropertiesTabs.setTabText(self.objectPropertiesTabs.indexOf(self.tabInputs), _translate("ObjectProperties", "Inputs"))
