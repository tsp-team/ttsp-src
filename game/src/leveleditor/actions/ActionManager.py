from direct.showbase.DirectObject import DirectObject

class ActionManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.historyIndex = -1
        self.history = []

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

        base.statusBar.showMessage("Redo %s" % action.Name)

    def performAction(self, action):
        # We are overriding everything after the current history index.
        # If the history index is not at the end of the list,
        # shave off everything from the current index to the end of the list.

        if self.historyIndex < len(self.history) - 1:
            first = self.historyIndex + 1
            last = len(self.history) - 1
            for i in range(first, last):
                action = self.history[i]
                action.cleanup()
            del self.history[first:]

        action.do()
        self.history.append(action)
        self.historyIndex += 1

        base.statusBar.showMessage(action.Name)
