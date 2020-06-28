from direct.showbase.DirectObject import DirectObject

class MapHelper(DirectObject):

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
