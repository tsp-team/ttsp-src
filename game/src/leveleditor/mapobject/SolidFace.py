from panda3d.core import LPlane, GeomVertexData, GeomEnums, NodePath
from panda3d.core import GeomNode, GeomTriangles, GeomLinestrips, GeomVertexFormat
from panda3d.core import GeomVertexWriter, InternalName, Vec4
from panda3d.core import ColorAttrib

from .MapWritable import MapWritable

class SolidFace(MapWritable):

    ObjectName = "side"

    def __init__(self):
        MapWritable.__init__(self)
        self.id = 0
        self.material = None
        self.vertices = []
        self.isSelected = False
        self.plane = LPlane()
        self.color = Vec4(1, 1, 1, 1)
        self.solid = None

    def readKeyValues(self, kv):
        pass

    def writeKeyValues(self, kv):
        pass

    def generate(self):
        pass

    def announceGenerate(self):
        pass

    def delete(self):
        pass

    def reparentTo(self, other):
        pass

    def regenerateVertices(self):
        vwriter = GeomVertexWriter(self.vertexBuffer, InternalName.getVertex())
        twriter = GeomVertexWriter(self.vertexBuffer, InternalName.getTexcoord())
        cwriter = GeomVertexWriter(self.vertexBuffer, InternalName.getColor())
        nwriter = GeomVertexWriter(self.vertexBuffer, InternalName.getNormal())

        numVerts = len(self.vertices)

        self.vertexBuffer.setNumRows(numVerts)

        # Fill the vertex data into the vertex buffer
        for i in range(numVerts):
            vtx = self.vertices[i]
            vwriter.addData3f(vtx.pos)
            twriter.addData2f(vtx.uv)
            cwriter.addData4f(self.color)

    def regenerateIndices(self):
        numVerts = len(self.vertices)

        # Generate the triangle indices
        self.prim3D.clearVertices()
        for i in range(1, numVerts - 1):
            self.prim3D.addVertices(0, i, i + 1)
            self.prim3D.closePrimitive()

        # Generate the line strip indices
        self.prim2D.clearVertices()
        for i in range(numVerts):
            self.prim2D.addVertex(i)
        # Close off the line strip with the first vertex
        self.prim2D.addVertex(0)
        self.prim2D.closePrimitive()

    def regenerateGeometry(self):
        self.regenerateVertices()
        self.regenerateIndices()

    def setParent(self, solid):
        self.solid = solid
        self.np.reparentTo(self.solid.np)
