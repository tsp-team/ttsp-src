from .Action import Action

class ChangeSelectionMode(Action):

    def __init__(self, mode):
        Action.__init__(self)
        self.oldMode = base.selectionMgr.selectionMode.Type
        self.mode = mode
        self.previousSelections = list(base.selectionMgr.selectedObjects)

    def do(self):
        Action.do(self)
        old = base.qtWindow.selectionModeActions[self.oldMode]
        new = base.qtWindow.selectionModeActions[self.mode]
        old.blockSignals(True)
        new.blockSignals(True)

        base.qtWindow.selectionModeActions[self.oldMode].setChecked(False)
        base.qtWindow.selectionModeActions[self.mode].setChecked(True)
        base.selectionMgr.setSelectionMode(self.mode)
        base.selectionMgr.multiSelect(
            base.selectionMgr.selectionModes[self.mode].getTranslatedSelections(self.oldMode))

        old.blockSignals(False)
        new.blockSignals(False)

    def undo(self):
        old = base.qtWindow.selectionModeActions[self.oldMode]
        new = base.qtWindow.selectionModeActions[self.mode]
        old.blockSignals(True)
        new.blockSignals(True)

        base.qtWindow.selectionModeActions[self.mode].setChecked(False)
        base.qtWindow.selectionModeActions[self.oldMode].setChecked(True)
        base.selectionMgr.setSelectionMode(self.oldMode)
        base.selectionMgr.multiSelect(self.previousSelections)

        old.blockSignals(False)
        new.blockSignals(False)

        Action.undo(self)

    def cleanup(self):
        self.oldMode = None
        self.mode = None
        self.previousSelections = None
        Action.cleanup(self)

    def modifiesState(self):
        return False
