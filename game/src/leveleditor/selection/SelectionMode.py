from direct.showbase.DirectObject import DirectObject
from .SelectionType import SelectionType, SelectionModeTransform

class SelectionMode(DirectObject):

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
        DirectObject.__init__(self)
        self.mgr = mgr

    def enable(self):
        self.accept('selectionsChanged', self.onSelectionsChanged)

    def disable(self):
        self.ignoreAll()

    def onSelectionsChanged(self):
        raise NotImplementedError
