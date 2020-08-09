from src.leveleditor.DocObject import DocObject
from .SelectionType import SelectionType, SelectionModeTransform

class SelectionMode(DocObject):

    Type = SelectionType.Nothing
    # Collision mask used for the mouse click ray
    Mask = 0
    # The key to locate the object from what we clicked on
    Key = None
    # Can we delete the selected objects?
    CanDelete = True
    # Can we clone/duplicate the selected objects?
    CanDuplicate = True
    # What kinds of transform can we apply?
    TransformBits = SelectionModeTransform.All

    def __init__(self, mgr):
        DocObject.__init__(self, mgr.doc)
        self.mgr = mgr
        self.enabled = False
        self.activated = False
        self.properties = None

    def cleanup(self):
        self.mgr = None
        self.enabled = None
        self.activatated = None
        self.properties = None
        DocObject.cleanup(self)

    def enable(self):
        self.enabled = True
        self.activate()

    def activate(self):
        self.activated = True
        self.accept('selectionsChanged', self.onSelectionsChanged)

    def disable(self):
        self.enabled = False
        self.deactivate()

    def deactivate(self):
        self.activated = False
        self.ignoreAll()

    def onSelectionsChanged(self):
        if self.properties:
            self.properties.updateForSelection()

    def getProperties(self):
        return self.properties

    # Returns a list of objects that will be selected
    # when switching to this mode from prevMode.
    def getTranslatedSelections(self, prevMode):
        return []
