from direct.showbase.DirectObject import DirectObject

# Base class for an undo-able action that can
# be performed on a document (move object, change texture, etc)
class Action(DirectObject):
    Name = "Action"

    NeverPerformed = 0
    Done = 1
    Undone = 2

    def __init__(self):
        self.state = self.NeverPerformed

    def do(self):
        self.state = self.Done

    def undo(self):
        self.state = self.Undone

    def cleanup(self):
        self.state = None
