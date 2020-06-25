from .MapObject import MapObject
from .SolidFace import SolidFace

# A brush
class Solid(MapObject):

    ObjectName = "solid"

    def __init__(self):
        MapObject.__init__(self)
        self.faces = []
