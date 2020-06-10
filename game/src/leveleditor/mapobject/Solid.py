from .MapObject import MapObject
from .Face import Face

# A brush
class Solid(MapObject):

    def __init__(self, id = 0):
        MapObject.__init__(self, id)
        self.faces = []