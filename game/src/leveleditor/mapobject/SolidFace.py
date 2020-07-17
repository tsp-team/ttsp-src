from panda3d.core import LPlane, GeomVertexData, GeomEnums, NodePath
from panda3d.core import GeomNode, GeomTriangles, GeomLinestrips, GeomVertexFormat
from panda3d.core import GeomVertexWriter, InternalName, Vec4, Geom
from panda3d.core import ColorAttrib, Vec3, Vec2

from .MapWritable import MapWritable

from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from src.leveleditor import LEUtils, LEGlobals

class FaceMaterial:

    def __init__(self):
        self.material = None
        self.scale = Vec2(1, 1)
        self.shift = Vec2(0, 0)
        self.uAxis = Vec3(0)
        self.vAxis = Vec3(0)
        self.rotation = 0.0

class SolidFace(MapWritable):

    ObjectName = "side"

    def __init__(self, id = 0, plane = LPlane(), solid = None):
        MapWritable.__init__(self)
        self.id = id
        self.material = FaceMaterial()
        self.vertices = []
        self.isSelected = False
        self.plane = plane
        self.color = Vec4(0.5, 0.5, 1, 1)
        self.np = None
        # 2D renders this
        self.np2D = None
        # 3D renders this
        self.np3D = None
        self.solid = solid
        self.hasGeometry = False
        self.vdata = None

    def select(self):
        self.np.setColorScale(1, 0.5, 0.5, 1)
        self.isSelected = True

    def deselect(self):
        self.np.setColorScale(1, 1, 1, 1)
        self.isSelected = False

    def readKeyValues(self, kv):
        pass

    def writeKeyValues(self, kv):
        pass

    def generate(self):
        self.np = NodePath("solidface.%i" % self.id)
        # This is selectable in object/group mode and face mode
        self.np.setPythonTag("solidface", self)
        if self.solid:
            self.np.reparentTo(self.solid.np)
        self.np2D = self.np.attachNewNode(GeomNode("2d"))
        self.np2D.hide(~VIEWPORT_2D_MASK)
        if self.color:
            self.setColor(self.color)
        self.np3D = self.np.attachNewNode(GeomNode("3d"))
        self.np3D.hide(~VIEWPORT_3D_MASK)
        if self.material.material:
            self.setMaterial(self.material.material)
        self.np.setCollideMask(GeomNode.getDefaultCollideMask() | LEGlobals.FaceMask)
        self.regenerateGeometry()

    def setMaterial(self, mat):
        self.material.material = mat
        if self.np3D and mat:
            self.np3D.setBSPMaterial(mat.material)

    def setColor(self, color):
        if self.np2D:
            self.np2D.setColor(color)
        self.color = color

    def alignTextureToFace(self):
        # Set the U and V axes to match the plane's normal
        # Need to start with the world alignment on the V axis so that we don't align backwards.
        # Then we can calculate U based on that, and the real V afterwards.

        norm = self.plane.getNormal()
        direction = LEUtils.getClosestAxis(norm)

        tempV = -Vec3.unitY() if direction == Vec3.unitZ() else -Vec3.unitZ()
        self.material.uAxis = norm.cross(tempV).normalized()
        self.material.vAxis = self.material.uAxis.cross(norm).normalized()

        self.material.rotation = 0.0

        self.calcTextureCoordinates(True)

    def calcTextureCoordinates(self, minimizeShiftValues):
        if minimizeShiftValues:
            self.minimizeTextureShiftValues()

        for vert in self.vertices:
            vert.uv.set(0, 0)

        if self.material.material is None:
            return
        if self.material.material.size.x == 0 or self.material.material.size.y == 0:
            return
        if self.material.scale.x == 0 or self.material.scale.y == 0:
            return

        udiv = self.material.material.size.x * self.material.scale.x
        uadd = self.material.shift.x / self.material.material.size.x
        vdiv = self.material.material.size.y * self.material.scale.y
        vadd = self.material.shift.y / self.material.material.size.y

        for vert in self.vertices:
            vert.uv.x = (vert.pos.dot(self.material.uAxis) / udiv) + uadd
            vert.uv.y = (vert.pos.dot(self.material.vAxis) / vdiv) + vadd

        if self.hasGeometry:
            self.modifyGeometryUVs()

    def modifyGeometryUVs(self):
        # Modifies the geometry vertex UVs in-place
        twriter = GeomVertexWriter(self.vdata, InternalName.getTexcoord())

        for i in range(len(self.vertices)):
            twriter.setData2f(self.vertices[i].uv)

    def minimizeTextureShiftValues(self):
        if self.material.material is None:
            return

        # Keep the shift values to a minimum
        self.material.shift.x %= self.material.material.size.x
        self.material.shift.y %= self.material.material.size.y

        if self.material.shift.x < -self.material.material.size.x / 2:
            self.material.shift.x += self.material.material.size.x
        if self.material.shift.y < -self.material.material.size.y / 2:
            self.material.shift.y += self.material.material.size.y

    def regenerateGeometry(self):
        # Remove existing geometry
        self.np2D.node().removeAllGeoms()
        self.np3D.node().removeAllGeoms()

        #
        # Generate vertex data
        #

        numVerts = len(self.vertices)

        vdata = GeomVertexData("SolidFace", GeomVertexFormat.getV3n3t2(), GeomEnums.UHStatic)
        vdata.setNumRows(len(self.vertices))

        vwriter = GeomVertexWriter(vdata, InternalName.getVertex())
        twriter = GeomVertexWriter(vdata, InternalName.getTexcoord())
        nwriter = GeomVertexWriter(vdata, InternalName.getNormal())

        for i in range(len(self.vertices)):
            vert = self.vertices[i]
            vwriter.addData3f(vert.pos)
            twriter.addData2f(vert.uv)
            nwriter.addData3f(self.plane.getNormal())

        #
        # Generate indices
        #

        # Triangles in 3D view
        prim3D = GeomTriangles(GeomEnums.UHStatic)
        for i in range(1, numVerts - 1):
            prim3D.addVertices(0, i, i + 1)
            prim3D.closePrimitive()

        # Line loop in 2D view.. using line strips
        prim2D = GeomLinestrips(GeomEnums.UHStatic)
        for i in range(numVerts):
            prim2D.addVertex(i)
        # Close off the line strip with the first vertex.. creating a line loop
        prim2D.addVertex(0)
        prim2D.closePrimitive()

        #
        # Generate mesh objects
        #

        geom3D = Geom(vdata)
        geom3D.addPrimitive(prim3D)
        self.np3D.node().addGeom(geom3D)

        geom2D = Geom(vdata)
        geom2D.addPrimitive(prim2D)
        self.np2D.node().addGeom(geom2D)

        self.vdata = vdata

        self.hasGeometry = True

    def delete(self):
        for vert in self.vertices:
            vert.delete()
        self.vertices = None
        self.id = None
        self.material = None
        self.color = None
        self.np3D.removeNode()
        self.np3D = None
        self.np2D.removeNode()
        self.np2D = None
        self.np.removeNode()
        self.np = None
        self.solid = None
        self.isSelected = None
        self.plane = None
        self.vdata = None
        self.hasGeometry = None
