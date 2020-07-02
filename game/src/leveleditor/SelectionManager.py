from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, NodePath

from PyQt5 import QtWidgets, QtCore, QtGui

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.mapobject.Entity import Entity
from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK
from src.leveleditor import RenderModes
from src.leveleditor.ui.ObjectProperties import Ui_ObjectProperties

Bounds3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

Bounds2DState = RenderModes.DashedLineNoZ()
Bounds2DState = Bounds2DState.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))

MultipleValues = "<multiple values>"
MultipleEntities = "<multiple entities>"

class ObjectPropertiesItem(QtGui.QStandardItem):

    def __init__(self, win, entities, propName, isKey):
        QtGui.QStandardItem.__init__(self)
        self.win = win
        self.entities = entities
        self.pairing = None
        self.propName = propName
        self.prop = entities[0].metaData.property_by_name(propName)
        self.isKey = isKey

        if self.isKey:
            self.setEditable(False)
            if self.prop.display_name and len(self.prop.display_name) > 0:
                self.setText(self.prop.display_name)
            else:
                self.setText(self.propName)
        else:
            self.setEditable(True)
            self.computeValueText()

    def computeValueText(self):
        value = None
        for ent in self.entities:
            entVal = str(ent.entityData[self.propName])
            if value is not None and entVal != value:
                # There are different values across entities for this property.
                value = MultipleValues
                break
            elif value is None:
                value = entVal
        self.setText(value)

    def data(self, role):
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft
        return QtGui.QStandardItem.data(self, role)

class ObjectPropertiesModel(QtGui.QStandardItemModel):

    def __init__(self, win):
        QtGui.QStandardItemModel.__init__(self, 0, 2, win.ui.propertiesView)
        self.setColumnCount(2)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Property")
        self.setHeaderData(1, QtCore.Qt.Horizontal, "Value")

class ObjectPropertiesWindow(QtWidgets.QDockWidget):

    def __init__(self, mgr):
        QtWidgets.QDockWidget.__init__(self)
        self.mgr = mgr
        self.setWindowTitle("Object Properties")
        w = QtWidgets.QWidget(self)
        self.ui = Ui_ObjectProperties()
        self.ui.setupUi(w)
        self.ui.comboClass.setEditable(True)
        self.setWidget(w)

        self.propertiesModel = ObjectPropertiesModel(self)
        self.ui.propertiesView.setMouseTracking(True)
        self.ui.propertiesView.setModel(self.propertiesModel)
        self.ui.propertiesView.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.ui.propertiesView.clicked.connect(self.__propertyClicked)
        self.ui.lePropertyFilter.textChanged.connect(self.__filterProperties)
        self.ui.comboClass.currentIndexChanged.connect(self.__changeEntityClass)

        self.updateAvailableClasses()

        base.qtWindow.addDockWindow(self)
        self.hide()

    def __changeEntityClass(self, idx):
        classname = self.ui.comboClass.currentText()
        for ent in self.mgr.selectedObjects:
            ent.setClassname(classname)
        self.updateForSelection()
        self.mgr.updateSelectionBounds()

    def __propertyClicked(self, idx):
        item = self.propertiesModel.itemFromIndex(idx)
        self.updatePropertyDetailText(item.prop)

    def updatePropertyDetailText(self, prop):
        if prop.display_name and len(prop.display_name) > 0:
            self.ui.lblPropertyName.setText(prop.display_name)
        else:
            self.ui.lblPropertyName.setText(prop.name)

        if prop.description and len(prop.description) > 0:
            self.ui.lblPropertyDesc.setText(prop.description)
        else:
            self.ui.lblPropertyDesc.setText("")

    def __filterProperties(self, text):
        if len(text) == 0:
            # Empty filter, show everything
            for i in range(self.propertiesModel.rowCount()):
                self.ui.propertiesView.setRowHidden(i, QtCore.QModelIndex(), False)
            return

        # First hide all rows...
        for i in range(self.propertiesModel.rowCount()):
            self.ui.propertiesView.setRowHidden(i, QtCore.QModelIndex(), True)

        # ...then show all rows containing the filter string
        items = self.propertiesModel.findItems(text, QtCore.Qt.MatchContains)
        for item in items:
            self.ui.propertiesView.setRowHidden(item.row(), QtCore.QModelIndex(), False)

    def updateForSelection(self):
        numSelections = self.mgr.getNumSelectedObjects()

        if numSelections == 0:
            self.hide()
            return
        else:
            self.show()

        # Clear our filtering
        self.ui.lePropertyFilter.clear()

        hasMultipleClassnames = False
        classname = None
        desc = ""
        propName2entities = {}

        # Determine the classname to display based on our selections
        for i in range(numSelections):
            selection = self.mgr.selectedObjects[i]
            entClassname = selection.metaData.name
            if classname is not None and entClassname != classname and not hasMultipleClassnames:
                # Multiple entity classnames
                classname = MultipleEntities
                desc = ""
                hasMultipleClassnames = True
            elif not hasMultipleClassnames:
                classname = entClassname
                if selection.metaData.description:
                    desc = selection.metaData.description

            for prop in selection.entityData.keys():
                if not prop in propName2entities:
                    propName2entities[prop] = [selection]
                else:
                    propName2entities[prop].append(selection)

        self.ui.lblPropertyName.setText(classname)
        self.ui.lblPropertyDesc.setText(desc)
        self.ui.comboClass.setCurrentText(classname)

        self.propertiesModel.removeRows(0, self.propertiesModel.rowCount())
        rowIdx = 0
        for prop, entityList in propName2entities.items():
            propItem = ObjectPropertiesItem(self, entityList, prop, True)
            valueItem = ObjectPropertiesItem(self, entityList, prop, False)
            valueItem.pairing = propItem
            propItem.pairing = valueItem
            self.propertiesModel.setItem(rowIdx, 0, propItem)
            self.propertiesModel.setItem(rowIdx, 1, valueItem)
            rowIdx += 1

    def updateAvailableClasses(self):
        self.ui.comboClass.clear()
        names = []
        for ent in base.fgd.entities:
            if ent.class_type in ['PointClass', 'SolidClass']:
                names.append(ent.name)
        names.sort()
        completer = QtWidgets.QCompleter(names)
        completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.ui.comboClass.setCompleter(completer)
        self.ui.comboClass.addItems(names)

class SelectionManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.selectedObjects = []
        # The box that encompasses all of the selected objects
        self.selectionBounds = Box()
        self.selectionBounds.addView(GeomView.Lines, VIEWPORT_3D_MASK, state = Bounds3DState)
        self.selectionBounds.addView(GeomView.Lines, VIEWPORT_2D_MASK, state = Bounds2DState)
        self.selectionBounds.generateGeometry()
        self.accept('delete', self.deleteSelectedObjects)
        self.objectProperties = ObjectPropertiesWindow(self)

    def deleteSelectedObjects(self):
        selected = list(self.selectedObjects)
        for obj in selected:
            base.document.deleteObject(obj)
        self.selectedObjects = []
        self.updateSelectionBounds()

    def hasSelectedObjects(self):
        return len(self.selectedObjects) > 0

    def getNumSelectedObjects(self):
        return len(self.selectedObjects)

    def isSelected(self, obj):
        return obj in self.selectedObjects

    def deselectAll(self, update = True):
        for obj in self.selectedObjects:
            obj.deselect()
        self.selectedObjects = []
        if update:
            self.updateSelectionBounds()

    def singleSelect(self, obj):
        self.deselectAll(False)
        self.select(obj)

    def multiSelect(self, listOfObjs):
        self.deselectAll(False)
        for obj in listOfObjs:
            self.select(obj, False)
        self.updateSelectionBounds()

    def deselect(self, obj, updateBounds = True):
        if obj in self.selectedObjects:
            self.selectedObjects.remove(obj)
            obj.deselect()

            if updateBounds:
                self.updateSelectionBounds()

    def select(self, obj, updateBounds = True):
        if not obj in self.selectedObjects:
            self.selectedObjects.append(obj)
            obj.select()

            if updateBounds:
                self.updateSelectionBounds()

    def hideSelectionBounds(self):
        self.selectionBounds.np.reparentTo(NodePath())

    def showSelectionBounds(self):
        self.selectionBounds.np.reparentTo(base.render)

    def updateSelectionBounds(self):
        messenger.send('selectionsChanged')

        self.objectProperties.updateForSelection()

        if len(self.selectedObjects) == 0:
            base.qtWindow.selectedLabel.setText("No selection.")
            self.hideSelectionBounds()
            return
        else:
            if len(self.selectedObjects) == 1:
                obj = self.selectedObjects[0]
                if isinstance(obj, Entity):
                    text = obj.classname
                    if "targetname" in obj.entityData and obj.entityData["targetname"] is not None:
                        text += " - " + obj.entityData["targetname"]
                    base.qtWindow.selectedLabel.setText(text)
            else:
                base.qtWindow.selectedLabel.setText("Selected %i objects." % len(self.selectedObjects))
            self.showSelectionBounds()

        mins = Point3(9999999)
        maxs = Point3(-9999999)

        for obj in self.selectedObjects:
            objMins = Point3()
            objMaxs = Point3()
            obj.np.calcTightBounds(objMins, objMaxs)
            if objMins.x < mins.x:
                mins.x = objMins.x
            if objMins.y < mins.y:
                mins.y = objMins.y
            if objMins.z < mins.z:
                mins.z = objMins.z
            if objMaxs.x > maxs.x:
                maxs.x = objMaxs.x
            if objMaxs.y > maxs.y:
                maxs.y = objMaxs.y
            if objMaxs.z > maxs.z:
                maxs.z = objMaxs.z

        self.selectionBounds.setMinMax(mins, maxs)
