from direct.showbase.DirectObject import DirectObject

# Base class for an undo-able action that can
# be performed on a document (move object, change texture, etc)
class Action(DirectObject):
    Name = "Action"

    def do(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError
