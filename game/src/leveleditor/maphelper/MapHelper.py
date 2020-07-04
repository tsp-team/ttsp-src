from direct.showbase.DirectObject import DirectObject

class MapHelper(DirectObject):

    # Update this helper if any of the specified properties
    # change.
    ChangeWith = []

    # Update this helper if any properties with the specified
    # type change.
    ChangeWithType = []

    def __init__(self, mapObject):
        DirectObject.__init__(self)
        self.mapObject = mapObject

    def generate(self):
        pass

    def select(self):
        pass

    def deselect(self):
        pass

    def cleanup(self):
        self.mapObject = None
