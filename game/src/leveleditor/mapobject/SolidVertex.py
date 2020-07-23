from panda3d.core import LTexCoord, Point3, CKeyValues

from .MapWritable import MapWritable

# Single vertex of a brush face
class SolidVertex(MapWritable):

    def __init__(self, pos, face):
        MapWritable.__init__(self)
        self.uv = LTexCoord(0, 0)
        self.pos = pos
        self.face = face

    def getWorldPos(self):
        if self.face.np is None:
            return self.pos
        else:
            return base.render.getRelativePoint(self.face.np, self.pos)

    def delete(self):
        self.uv = None
        self.pos = None
        self.face = None

    def readKeyValues(self, kv):
        self.pos = CKeyValues.to3f(kv.getValue("origin"))
        self.uv = LTexCoord(CKeyValues.to2f(kv.getValue("texcoord")))

    def writeKeyValues(self, kv):
        kv.setKeyValue("origin", CKeyValues.toString(self.pos))
        kv.setKeyValue("texcoord", CKeyValues.toString(self.uv))

    def clone(self):
        vtx = SolidVertex(self.pos, self.face)
        vtx.uv = self.uv
        return vtx
