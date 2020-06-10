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
        self.pos = CKeyValues.to3f(kv["Location"])
        self.uv = LTexCoord(float(kv["TextureU"]), float(kv["TextureV"]))

    def writeKeyValues(self, kv):
        kv["Location"] = CKeyValues.toString(self.pos)
        kv["TextureU"] = str(self.uv.getX())
        kv["TextureV"] = str(self.uv.getY())

    def clone(self):
        vtx = SolidVertex(self.pos, self.face)
        vtx.uv = self.uv
        return vtx
