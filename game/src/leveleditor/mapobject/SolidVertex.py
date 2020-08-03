from panda3d.core import LTexCoord, Point3, CKeyValues, NodePath

from .MapWritable import MapWritable

# Single vertex of a brush face
class SolidVertex(MapWritable):

    def __init__(self, pos = Point3(0), face = None):
        MapWritable.__init__(self)
        self.uv = LTexCoord(0, 0)
        self.pos = pos
        self.face = face

    def xform(self, mat):
        self.pos = mat.xformPoint(self.pos)

    def getWorldPos(self):
        if self.face is None:
            return self.pos
        else:
            mat = self.face.np.getMat(NodePath())
            return mat.xformPoint(self.pos)

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
        vtx = SolidVertex(Point3(self.pos), self.face)
        vtx.uv = LTexCoord(self.uv)
        return vtx
