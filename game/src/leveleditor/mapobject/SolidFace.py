from panda3d.core import LPlane, GeomVertexData, GeomEnums, NodePath
from panda3d.core import GeomNode, GeomTriangles, GeomLinestrips, GeomVertexFormat
from panda3d.core import GeomVertexWriter, InternalName, Vec4, Geom
from panda3d.core import ColorAttrib, Vec3, Vec2, deg2Rad, Quat

from .MapWritable import MapWritable

from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from src.leveleditor import LEUtils, LEGlobals
from src.leveleditor.Align import Align

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

    def getName(self):
        return "Solid face"

    def select(self):
        self.np.setColorScale(1, 0.75, 0.75, 1)
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

    def alignTextureWithPointCloud(self, cloud, mode):
        if self.material.material is None:
            return

        xvals = []
        yvals = []
        for extent in cloud.extents:
            xvals.append(extent.dot(self.material.uAxis) / self.material.scale.x)
            yvals.append(extent.dot(self.material.vAxis) / self.material.scale.y)

        minU = min(xvals)
        minV = min(yvals)
        maxU = max(xvals)
        maxV = max(yvals)

        if mode == Align.Left:
            self.material.shift.x = -minU
        elif mode == Align.Right:
            self.material.shift.x = -maxU + self.material.material.size.x
        elif mode == Align.Center:
            avgU = (minU + maxU) / 2
            avgV = (minV + maxV) / 2
            self.material.shift.x = -avgU + self.material.material.size.x / 2
            self.material.shift.y = -avgV + self.material.material.size.y / 2
        elif mode == Align.Top:
            self.material.shift.y = -minV
        elif mode == Align.Bottom:
            self.material.shift.y = -maxV + self.material.material.size.y

        self.calcTextureCoordinates(True)

    def fitTextureToPointCloud(self, cloud, tileX, tileY):
        if self.material.material is None:
            return
        if tileX <= 0:
            tileX = 1
        if tileY <= 0:
            tileY = 1

        # Scale will change, no need to use it in the calculations
        xvals = []
        yvals = []
        for extent in cloud.extents:
            xvals.append(extent.dot(self.material.uAxis))
            yvals.append(extent.dot(self.material.vAxis))

        minU = min(xvals)
        minV = min(yvals)
        maxU = max(xvals)
        maxV = max(yvals)

        self.material.scale.x = (maxU - minU) / (self.material.material.size.x * tileX)
        self.material.scale.y = (maxV - minV) / (self.material.material.size.y * tileY)
        self.material.shift.x = -minU / self.material.scale.x
        self.material.shift.y = -minV / self.material.scale.y

        self.calcTextureCoordinates(True)

    def setTextureRotation(self, angle):
        # Rotate texture around the face normal
        rads = deg2Rad(self.material.rotation - angle)
        # Rotate around the face normal
        texNorm = self.material.vAxis.cross(self.material.uAxis).normalized()
        transform = Quat()
        transform.setFromAxisAngleRad(rads, texNorm)
        self.material.uAxis = transform.xform(self.material.uAxis)
        self.material.vAxis = transform.xform(self.material.vAxis)
        self.material.rotation = angle

        self.calcTextureCoordinates(True)

    def alignTextureToWorld(self):
        # Set the U and V axes to match the X, Y, or Z axes.
        # How they are calculated depends on which direction the plane is facing.

        norm = self.plane.getNormal()
        direction = LEUtils.getClosestAxis(norm)

        # VHE behavior:
        # U axis: If the closest axis to the normal is the X axis,
        #         the U axis is unit Y. Otherwise, the U axis is unit X.
        # V axis: If the closest axis to the normal is the Z axis,
        #         the V axis is -unit Y. Otherwise, the V axis is -unit z.

        self.material.uAxis = Vec3.unitY() if direction == Vec3.unitX() else Vec3.unitX()
        self.material.vAxis = -Vec3.unitY() if direction == Vec3.unitZ() else -Vec3.unitZ()
        self.material.rotation = 0

        self.calcTextureCoordinates(True)

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
            vertPos = vert.getWorldPos()
            vert.uv.x = (vertPos.dot(self.material.uAxis) / udiv) + uadd
            vert.uv.y = (vertPos.dot(self.material.vAxis) / vdiv) + vadd

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
