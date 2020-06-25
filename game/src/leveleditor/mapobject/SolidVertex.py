from panda3d.core import LTexCoord, Point3, CKeyValues

from .MapWritable import MapWritable

# Single vertex of a brush face
class SolidVertex(MapWritable):

    def __init__(self, pos, face):
        MapWritable.__init__(self)
        self.uv = LTexCoord(0, 0)
        self.pos = pos
        self.face = face

    def readKeyValues(self, kv):
        self.pos = CKeyValues.to3f(kv.getValue("location"))
        self.uv = LTexCoord(float(kv.getValue("textureu")), float(kv.getValue("texturev")))

    def writeKeyValues(self, kv):
        kv.setKeyValue("location", CKeyValues.toString(self.pos))
        kv.setKeyValue("textureu", str(self.uv.getX()))
        kv.setKeyValue("texturev", str(self.uv.getY()))

    def clone(self):
        vtx = SolidVertex(self.pos, self.face)
        vtx.uv = self.uv
        return vtx
