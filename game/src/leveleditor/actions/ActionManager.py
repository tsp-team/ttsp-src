from direct.showbase.DirectObject import DirectObject

class ActionManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.historyIndex = -1
        self.savedIndex = -1
        self.stateChangeIndex = -1
        self.history = []

    def getCurrentStateChangeIndex(self):
        if self.historyIndex == -1:
            return -1

        # Search back from the current history index to find the most recent state.
        for i in range(self.historyIndex + 1):
            idx = self.historyIndex - i
            action = self.history[idx]
            if action.ModifiesState:
                return idx

        return -1

    def documentSaved(self):
        self.savedIndex = self.stateChangeIndex

    def updateSaveStatus(self):
        if self.stateChangeIndex != self.savedIndex:
            base.document.markUnsaved()
        else:
            base.document.markSaved()

    def undo(self):
        # Anything to undo?
        if len(self.history) == 0 or self.historyIndex < 0:
            # Nope.
            return

        # Get at the current action and undo it
        action = self.history[self.historyIndex]
        action.undo()
        # Move the history index back
        self.historyIndex -= 1

        if action.ModifiesState:
            self.stateChangeIndex = self.getCurrentStateChangeIndex()
            self.updateSaveStatus()

        base.statusBar.showMessage("Undo %s" % action.Name)

    def redo(self):
        # Anything to redo?
        numActions = len(self.history)
        if numActions == 0 or self.historyIndex >= numActions - 1:
            return

        # Redo the next action
        self.historyIndex += 1
        action = self.history[self.historyIndex]
        action.do()

        if action.ModifiesState:
            self.stateChangeIndex = self.getCurrentStateChangeIndex()
            self.updateSaveStatus()

        base.statusBar.showMessage("Redo %s" % action.Name)

    def performAction(self, action):
        # We are overriding everything after the current history index.
        # If the history index is not at the end of the list,
        # shave off everything from the current index to the end of the list.

        if self.historyIndex < len(self.history) - 1:
            first = self.historyIndex + 1
            last = len(self.history) - 1
            for i in range(first, last):
                other = self.history[i]
                other.cleanup()
            del self.history[first:]

            if self.savedIndex > self.historyIndex:
                # If the saved index is ahead of the history index, the
                # saved index is now invalid since those actions have
                # been deleted.
                self.savedIndex = -1

        action.do()
        self.history.append(action)
        self.historyIndex += 1

        if action.ModifiesState:
            self.stateChangeIndex = self.getCurrentStateChangeIndex()
            self.updateSaveStatus()

        base.statusBar.showMessage(action.Name)
