from direct.showbase.DirectObject import DirectObject

class BrushManager(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        self.brushes = []

    def addBrush(self, brush):
        self.brushes.append(brush)

    def addBrushes(self):
        from .BlockBrush import BlockBrush
        self.addBrush(BlockBrush())
