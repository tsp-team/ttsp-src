from .Action import Action

class ChangeSelectionMode(Action):

    def __init__(self, mode):
        Action.__init__(self)
        self.oldMode = base.selectionMgr.selectionMode.Type
        self.mode = mode
        self.previousSelections = list(base.selectionMgr.selectedObjects)

    def do(self):
        Action.do(self)

        oldAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.oldMode].KeyBind)
        oldAction.setChecked(False)
        newAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.mode].KeyBind)
        newAction.setChecked(True)

        base.selectionMgr.setSelectionMode(self.mode)
        base.selectionMgr.multiSelect(
            base.selectionMgr.selectionModes[self.mode].getTranslatedSelections(self.oldMode))

    def undo(self):
        oldAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.oldMode].KeyBind)
        oldAction.setChecked(True)
        newAction = base.menuMgr.action(base.selectionMgr.selectionModes[self.mode].KeyBind)
        newAction.setChecked(False)

        base.selectionMgr.setSelectionMode(self.oldMode)
        base.selectionMgr.multiSelect(self.previousSelections)

        Action.undo(self)

    def cleanup(self):
        self.oldMode = None
        self.mode = None
        self.previousSelections = None
        Action.cleanup(self)

    def modifiesState(self):
        return False
