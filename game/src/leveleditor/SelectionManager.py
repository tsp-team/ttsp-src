from panda3d.core import RenderState, ColorAttrib, Vec4, Point3, NodePath, Filename

from PyQt5 import QtWidgets, QtCore, QtGui

from direct.showbase.DirectObject import DirectObject

from src.leveleditor.mapobject.Entity import Entity
from src.leveleditor.geometry.Box import Box
from src.leveleditor.geometry.GeomView import GeomView
from src.leveleditor.viewport.ViewportType import VIEWPORT_2D_MASK, VIEWPORT_3D_MASK
from src.leveleditor import RenderModes
from src.leveleditor.ui.ObjectProperties import Ui_ObjectProperties
from src.leveleditor import LEUtils
from src.leveleditor.mapobject import MetaData

Bounds3DState = RenderState.make(
    ColorAttrib.makeFlat(Vec4(1, 1, 0, 1))
)

Bounds2DState = RenderModes.DashedLineNoZ()
Bounds2DState = Bounds2DState.setAttrib(ColorAttrib.makeFlat(Vec4(1, 1, 0, 1)))

class BaseEditor(QtWidgets.QWidget):

    def __init__(self, parent, item, model):
        QtWidgets.QFrame.__init__(self, parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)
        self.item = item
        self.model = model

    def getItemData(self):
        return self.item.data(QtCore.Qt.EditRole)

    def setEditorData(self, index):
        pass

    def setModelData(self, model, index):
        pass

class ColorEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.lineEdit = QtWidgets.QLineEdit("", self)
        self.lineEdit.returnPressed.connect(self.__confirmColorText)
        self.layout().addWidget(self.lineEdit)
        self.colorLbl = QtWidgets.QLabel("", self)
        self.colorLbl.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.layout().addWidget(self.colorLbl)
        self.editButton = QtWidgets.QPushButton("Pick Color", self)
        self.editButton.clicked.connect(self.__pickColor)
        self.layout().addWidget(self.editButton)
        self.colorDlg = None

        self.adjustToColor(LEUtils.strToQColor(self.getItemData()))

    def __confirmColorText(self):
        self.setModelData(self.model, self.item.index())
        self.adjustToColor(LEUtils.strToQColor(self.lineEdit.text()))

    def __pickColor(self):
        self.origColor = LEUtils.strToQColor(self.getItemData())

        color = LEUtils.strToQColor(self.getItemData())
        colorDlg = QtWidgets.QColorDialog(color, self)
        colorDlg.setOptions(QtWidgets.QColorDialog.DontUseNativeDialog)
        colorDlg.setModal(True)
        colorDlg.currentColorChanged.connect(self.adjustToColorAndSetData)
        colorDlg.finished.connect(self.__colorDlgFinished)
        colorDlg.open()
        colorDlg.blockSignals(True)
        colorDlg.setCurrentColor(color)
        colorDlg.blockSignals(False)
        self.colorDlg = colorDlg

    def __colorDlgFinished(self, ret):
        if ret:
            color = self.colorDlg.currentColor()
            self.adjustToColorAndSetData(color)
        else:
            self.adjustToColorAndSetData(self.origColor)
        self.colorDlg = None

    def adjustToColorAndSetData(self, color):
        if not color.isValid():
            return
        self.adjustToColor(color)
        self.setModelData(self.model, self.item.index())

    def adjustToColor(self, color):
        self.colorLbl.setStyleSheet("border: 1px solid black; background-color: rgb(%i, %i, %i);" % (color.red(), color.green(), color.blue()))
        vals = self.getItemData().split(' ')
        alpha = vals[3]
        self.lineEdit.setText("%i %i %i %s" % (color.red(), color.green(), color.blue(), alpha))

    def setEditorData(self, index):
        self.lineEdit.setText(self.getItemData())

    def setModelData(self, model, index):
        model.setData(index, self.lineEdit.text(), QtCore.Qt.EditRole)

MaxVal = 2147483647
MinVal = -2147483648

# Bruh. Qt has separate classes for the int and double spin boxes.
class BaseScrubSpinBox:

    def __init__(self):
        self.isMoving = False
        self.mouseStartPosY = 0
        self.startValue = 0

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.MiddleButton:
            self.mouseStartPosY = e.pos().y()
            self.startValue = self.value()
            self.isMoving = True
            self.setCursor(QtCore.Qt.SizeVerCursor)

    def mouseMoveEvent(self, e):
        if self.isMoving:
            mult = 0.5
            valueOffset = int((self.mouseStartPosY - e.pos().y()) * mult)
            self.setValue(self.startValue + valueOffset)

    def mouseReleaseEvent(self, e):
        self.isMoving = False
        self.unsetCursor()

class IntScrubSpinBox(QtWidgets.QSpinBox, BaseScrubSpinBox):

    def __init__(self, parent):
        QtWidgets.QSpinBox.__init__(self, parent)
        BaseScrubSpinBox.__init__(self)

    def mousePressEvent(self, e):
        QtWidgets.QSpinBox.mousePressEvent(self, e)
        BaseScrubSpinBox.mousePressEvent(self, e)

    def mouseMoveEvent(self, e):
        QtWidgets.QSpinBox.mouseMoveEvent(self, e)
        BaseScrubSpinBox.mouseMoveEvent(self, e)

    def mouseReleaseEvent(self, e):
        QtWidgets.QSpinBox.mouseReleaseEvent(self, e)
        BaseScrubSpinBox.mouseReleaseEvent(self, e)

class DoubleScrubSpinBox(QtWidgets.QDoubleSpinBox, BaseScrubSpinBox):

    def __init__(self, parent):
        QtWidgets.QDoubleSpinBox.__init__(self, parent)
        BaseScrubSpinBox.__init__(self)

    def mousePressEvent(self, e):
        QtWidgets.QDoubleSpinBox.mousePressEvent(self, e)
        BaseScrubSpinBox.mousePressEvent(self, e)

    def mouseMoveEvent(self, e):
        QtWidgets.QDoubleSpinBox.mouseMoveEvent(self, e)
        BaseScrubSpinBox.mouseMoveEvent(self, e)

    def mouseReleaseEvent(self, e):
        QtWidgets.QDoubleSpinBox.mouseReleaseEvent(self, e)
        BaseScrubSpinBox.mouseReleaseEvent(self, e)

class IntegerEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)

        self.spinBox = IntScrubSpinBox(self)
        self.spinBox.setRange(MinVal, MaxVal)
        self.spinBox.valueChanged.connect(self.__valueChanged)
        self.layout().addWidget(self.spinBox)

    def __valueChanged(self, val):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.spinBox.blockSignals(True)
        self.spinBox.setValue(int(self.getItemData()))
        self.spinBox.blockSignals(False)

    def setModelData(self, model, index):
        model.setData(index, str(self.spinBox.value()), QtCore.Qt.EditRole)

class FloatEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)

        self.spinBox = DoubleScrubSpinBox(self)
        self.spinBox.setRange(MinVal, MaxVal)
        self.spinBox.valueChanged.connect(self.__valueChanged)
        self.layout().addWidget(self.spinBox)

    def __valueChanged(self, val):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.spinBox.blockSignals(True)
        self.spinBox.setValue(int(self.getItemData()))
        self.spinBox.blockSignals(False)

    def setModelData(self, model, index):
        model.setData(index, str(self.spinBox.value()), QtCore.Qt.EditRole)

class StringEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.layout().addWidget(self.lineEdit)

    def setEditorData(self, index):
        self.lineEdit.setText(self.getItemData())

    def setModelData(self, model, index):
        print(self.lineEdit.text())
        model.setData(index, self.lineEdit.text(), QtCore.Qt.EditRole)

class BaseVecEditor(BaseEditor):

    class ComponentSpinBox(DoubleScrubSpinBox):

        def __init__(self, editor, component):
            DoubleScrubSpinBox.__init__(self, editor)
            self.component = component
            self.editor = editor
            self.setRange(MinVal, MaxVal)
            self.valueChanged.connect(self.__valueChanged)
            self.setKeyboardTracking(False)
            self.setAccelerated(True)
            self.editor.layout().addWidget(self)

        def __valueChanged(self, val):
            self.editor.componentChanged()

    def __init__(self, parent, item, model, numComponents):
        BaseEditor.__init__(self, parent, item, model)
        self.components = []
        for i in range(numComponents):
            spinBox = BaseVecEditor.ComponentSpinBox(self, i)
            self.components.append(spinBox)

    def componentChanged(self):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        data = self.getItemData()
        comps = data.split(' ')
        for i in range(len(self.components)):
            self.components[i].blockSignals(True)
            self.components[i].setValue(float(comps[i]))
            self.components[i].blockSignals(False)

    def setModelData(self, model, index):
        data = ""
        for i in range(len(self.components)):
            strVal = str(self.components[i].value())
            if i < len(self.components) - 1:
                data += "%s " % strVal
            else:
                data += strVal
        model.setData(index, data, QtCore.Qt.EditRole)

class Vec2Editor(BaseVecEditor):

    def __init__(self, parent, item, model):
        BaseVecEditor.__init__(self, parent, item, model, 2)

class Vec3Editor(BaseVecEditor):

    def __init__(self, parent, item, model):
        BaseVecEditor.__init__(self, parent, item, model, 3)

class Vec4Editor(BaseVecEditor):

    def __init__(self, parent, item, model):
        BaseVecEditor.__init__(self, parent, item, model, 4)

class ChoicesEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)

        self.combo = QtWidgets.QComboBox(self)
        #self.combo.currentIndexChanged.connect(self.__selectedItem)
        self.layout().addWidget(self.combo)

    def __selectedItem(self, index):
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.combo.blockSignals(True)

        self.combo.clear()
        data = self.getItemData()
        prop = self.item.prop
        for choice in prop.choices:
            self.combo.addItem(choice.display_name)
        self.combo.setCurrentText(data)

        self.combo.blockSignals(False)

    def setModelData(self, model, index):
        model.setData(index, self.combo.currentText(), QtCore.Qt.EditRole)

class StudioEditor(BaseEditor):

    def __init__(self, parent, item, model):
        BaseEditor.__init__(self, parent, item, model)
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.layout().addWidget(self.lineEdit)
        self.browseBtn = QtWidgets.QPushButton("Browse", self)
        self.browseBtn.clicked.connect(self.__browseForModel)
        self.layout().addWidget(self.browseBtn)

    def __browseForModel(self):
        selectedFilename = QtWidgets.QFileDialog.getOpenFileName(self, 'Choose Model',
            filter = 'Panda3D models (*.bam *.egg *.egg.pz)')
        if len(selectedFilename[0]) == 0:
            # Cancelled
            return
        filename = Filename.fromOsSpecific(selectedFilename[0])
        self.lineEdit.setText(filename.getFullpath())
        self.setModelData(self.model, self.item.index())

    def setEditorData(self, index):
        self.lineEdit.setText(self.getItemData())

    def setModelData(self, model, index):
        model.setData(index, self.lineEdit.text(), QtCore.Qt.EditRole)

class ObjectPropertiesDelegate(QtWidgets.QStyledItemDelegate):

    PropTypeEditors = {
        "color255": ColorEditor,
        "integer": IntegerEditor,
        "choices": ChoicesEditor,
        "string": StringEditor,
        "studio": StudioEditor,
        "target_source": StringEditor,
        "target_destination": StringEditor,
        "vec3": Vec3Editor,
        "vec2": Vec2Editor,
        "vec4": Vec4Editor,
        "float": FloatEditor
    }

    def __init__(self, window):
        QtWidgets.QStyledItemDelegate.__init__(self)
        self.window = window

    def getItem(self, idx):
        return self.window.propertiesModel.itemFromIndex(idx)

    def setEditorData(self, editor, index):
        item = self.getItem(index)
        editorCls = self.PropTypeEditors.get(item.propType, None)
        if editorCls:
            editor.setEditorData(index)
            return
        QtWidgets.QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        item = self.getItem(index)
        editorCls = self.PropTypeEditors.get(item.propType, None)
        if editorCls:
            editor.setModelData(model, index)
            return
        QtWidgets.QStyledItemDelegate.setModelData(self, editor, model, index)

    def createEditor(self, parent, option, index):
        item = self.getItem(index)
        editor = self.PropTypeEditors.get(item.propType, None)
        if editor:
            return editor(parent, item, self.window.propertiesModel)
        else:
            return QtWidgets.QStyledItemDelegate.createEditor(self, parent, option, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class ObjectPropertiesItem(QtGui.QStandardItem):

    def __init__(self, win, entity, propName, isKey):
        QtGui.QStandardItem.__init__(self)
        self.win = win
        self.entity = entity
        self.pairing = None
        self.propName = propName
        self.prop = entity.getPropMetaData(propName)
        self.propType = self.prop.value_type
        self.isKey = isKey

        if self.isKey:
            self.setEditable(False)
            self.setText(self.getKeyText())
        else:
            self.setEditable(True)
            self.setText(self.computeValueText())

    def setData(self, strData, role, fromUserEdit = True):
        if fromUserEdit and not self.isKey and role == QtCore.Qt.EditRole:
            # Property value was changed... apply it to all the applicable entities

            if self.prop.value_type == "choices":
                # Find the numerical value for the selected choice name
                data = None
                for choice in self.prop.choices:
                    if choice.display_name == strData:
                        data = choice.value
                        break
                assert data is not None, "Could not match %s to a choice value" % strData
            else:
                data = strData

            self.entity.updateProperties({self.propName: data})

        QtGui.QStandardItem.setData(self, strData, role)

    def getKeyText(self):
        if self.prop.display_name and len(self.prop.display_name) > 0:
            return self.prop.display_name
        else:
            return self.propName

    def computeValueText(self):
        isChoice = self.prop.value_type == "choices"
        entVal = self.entity.getEntityData(self.propName, asString = not isChoice)
        if isChoice:
            entVal = self.prop.choice_by_value(entVal).display_name
        else:
            entVal = str(entVal)
        return entVal

    def data(self, role):
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        return QtGui.QStandardItem.data(self, role)

class ObjectPropertiesModel(QtGui.QStandardItemModel):

    def __init__(self, win):
        QtGui.QStandardItemModel.__init__(self, 0, 2, win.ui.propertiesView)
        self.setColumnCount(2)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Property")
        self.setHeaderData(1, QtCore.Qt.Horizontal, "Value")

class ObjectPropertiesWindow(QtWidgets.QDockWidget, DirectObject):

    def __init__(self, mgr):
        QtWidgets.QDockWidget.__init__(self)
        DirectObject.__init__(self)
        self.mgr = mgr
        self.setWindowTitle("Object Properties")
        w = QtWidgets.QWidget(self)
        self.ui = Ui_ObjectProperties()
        self.ui.setupUi(w)
        self.ui.comboClass.setEditable(True)
        self.setWidget(w)

        self.entity = None

        self.valueItemByPropName = {}

        self.propertiesDelegate = ObjectPropertiesDelegate(self)
        self.propertiesModel = ObjectPropertiesModel(self)
        self.ui.propertiesView.setMouseTracking(True)
        self.ui.propertiesView.setModel(self.propertiesModel)
        self.ui.propertiesView.setItemDelegate(self.propertiesDelegate)
        self.ui.propertiesView.header().setDefaultAlignment(QtCore.Qt.AlignCenter)
        self.ui.propertiesView.clicked.connect(self.__propertyClicked)
        self.ui.lePropertyFilter.textChanged.connect(self.__filterProperties)
        self.ui.comboClass.currentIndexChanged.connect(self.__changeEntityClass)

        self.updateAvailableClasses()

        base.qtWindow.addDockWindow(self)
        self.clearAll()
        self.setEnabled(False)

        self.accept('entityPropertyChanged', self.__handleEntityPropertyChanged)

    def __handleEntityPropertyChanged(self, entity, key, value):
        if entity == self.entity:
            item = self.valueItemByPropName.get(key, None)
            if not item:
                return
            item.setData(item.computeValueText(), QtCore.Qt.EditRole, False)

    def clearAll(self):
        self.ui.lePropertyFilter.clear()
        self.propertiesModel.removeRows(0, self.propertiesModel.rowCount())
        self.ui.lblPropertyDesc.setText("")
        self.ui.lblPropertyName.setText("")
        self.ui.comboClass.setCurrentText("")

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

        self.valueItemByPropName = {}

        if numSelections == 0:
            self.entity = None
            self.clearAll()
            self.setEnabled(False)
            return
        else:
            self.setEnabled(True)

        # Clear our filtering
        self.ui.lePropertyFilter.clear()

        # Only show one entity in the object properties..
        # and choose the most recently selected one if there are multiple selections
        selection = self.mgr.selectedObjects[len(self.mgr.selectedObjects) - 1]
        self.entity = selection

        classname = selection.metaData.name
        if selection.metaData.description:
            desc = selection.metaData.description
        else:
            desc = ""

        if selection.isPointEntity():
            propNames = list(selection.transformProperties.keys())
        else:
            propNames = []
        propNames += list(selection.entityData.keys())

        self.ui.lblPropertyName.setText(classname)
        self.ui.lblPropertyDesc.setText(desc)
        self.ui.comboClass.setCurrentText(classname)

        self.propertiesModel.removeRows(0, self.propertiesModel.rowCount())
        rowIdx = 0
        for prop in propNames:
            propItem = ObjectPropertiesItem(self, selection, prop, True)
            valueItem = ObjectPropertiesItem(self, selection, prop, False)
            valueItem.pairing = propItem
            propItem.pairing = valueItem
            self.propertiesModel.setItem(rowIdx, 0, propItem)
            self.propertiesModel.setItem(rowIdx, 1, valueItem)
            self.ui.propertiesView.openPersistentEditor(valueItem.index())
            self.valueItemByPropName[prop] = valueItem
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
        self.selectionMins = Point3()
        self.selectionMaxs = Point3()
        self.selectionCenter = Point3()

        self.objectProperties = ObjectPropertiesWindow(self)

        self.accept('delete', self.deleteSelectedObjects)
        self.accept('selectionsChanged', self.objectProperties.updateForSelection)
        self.accept('entityTransformChanged', self.handleEntityTransformChange)

    def handleEntityTransformChange(self, entity):
        if entity in self.selectedObjects:
            self.updateSelectionBounds()
            messenger.send('selectedEntityTransformChanged', [entity])

    def deleteSelectedObjects(self):
        selected = list(self.selectedObjects)
        for obj in selected:
            base.document.deleteObject(obj)
        self.selectedObjects = []
        self.updateSelectionBounds()
        messenger.send('selectionsChanged')

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
            messenger.send('selectionsChanged')

    def singleSelect(self, obj):
        self.deselectAll(False)
        self.select(obj)

    def multiSelect(self, listOfObjs):
        self.deselectAll(False)
        for obj in listOfObjs:
            self.select(obj, False)
        self.updateSelectionBounds()
        messenger.send('selectionsChanged')

    def deselect(self, obj, updateBounds = True):
        if obj in self.selectedObjects:
            self.selectedObjects.remove(obj)
            obj.deselect()

            if updateBounds:
                self.updateSelectionBounds()
                messenger.send('selectionsChanged')

    def select(self, obj, updateBounds = True):
        if not obj in self.selectedObjects:
            self.selectedObjects.append(obj)
            obj.select()

            if updateBounds:
                self.updateSelectionBounds()
                messenger.send('selectionsChanged')

    def updateSelectionBounds(self):

        if len(self.selectedObjects) == 0:
            base.qtWindow.selectedLabel.setText("No selection.")
            self.selectionMins = Point3()
            self.selectionMaxs = Point3()
            self.selectionCenter = Point3()
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

        self.selectionMins = mins
        self.selectionMaxs = maxs
        self.selectionCenter = (mins + maxs) / 2.0
