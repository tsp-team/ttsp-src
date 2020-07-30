from panda3d.core import GeomVertexData, GeomEnums, NodePath
from panda3d.core import GeomNode, GeomTriangles, GeomLinestrips, GeomVertexFormat
from panda3d.core import GeomVertexWriter, InternalName, Vec4, Geom
from panda3d.core import ColorAttrib, Vec3, Vec2, deg2Rad, Quat, Point3
from panda3d.core import CullFaceAttrib, AntialiasAttrib, CKeyValues

from .MapWritable import MapWritable
from .SolidVertex import SolidVertex

from src.leveleditor.viewport.ViewportType import VIEWPORT_3D_MASK, VIEWPORT_2D_MASK
from src.leveleditor import LEUtils, LEGlobals
from src.leveleditor.math import PlaneClassification
from src.leveleditor.math.Plane import Plane
from src.leveleditor.Align import Align
from src.leveleditor.IDGenerator import IDGenerator
from src.leveleditor import MaterialPool

class FaceMaterial:

    def __init__(self):
        self.material = None
        self.scale = Vec2(1, 1)
        self.shift = Vec2(0, 0)
        self.uAxis = Vec3(0)
        self.vAxis = Vec3(0)
        self.rotation = 0.0

    def alignTextureToFace(self, face):
        # Set the U and V axes to match the plane's normal
        # Need to start with the world alignment on the V axis so that we don't align backwards.
        # Then we can calculate U based on that, and the real V afterwards.

        norm = face.plane.getNormal()
        direction = face.plane.getClosestAxisToNormal()

        tempV = -Vec3.unitY() if direction == Vec3.unitZ() else -Vec3.unitZ()
        self.uAxis = norm.cross(tempV).normalized()
        self.vAxis = self.uAxis.cross(norm).normalized()

        self.rotation = 0.0

    def alignTextureToWorld(self, face):
        # Set the U and V axes to match the X, Y, or Z axes.
        # How they are calculated depends on which direction the plane is facing.

        direction = face.plane.getClosestAxisToNormal()

        # VHE behavior:
        # U axis: If the closest axis to the normal is the X axis,
        #         the U axis is unit Y. Otherwise, the U axis is unit X.
        # V axis: If the closest axis to the normal is the Z axis,
        #         the V axis is -unit Y. Otherwise, the V axis is -unit z.

        self.uAxis = Vec3.unitY() if direction == Vec3.unitX() else Vec3.unitX()
        self.vAxis = -Vec3.unitY() if direction == Vec3.unitZ() else -Vec3.unitZ()
        self.rotation = 0

    def setTextureRotation(self, angle):
        # Rotate texture around the face normal
        rads = deg2Rad(self.rotation - angle)
        # Rotate around the face normal
        texNorm = self.vAxis.cross(self.uAxis).normalized()
        transform = Quat()
        transform.setFromAxisAngleRad(rads, texNorm)
        self.uAxis = transform.xform(self.uAxis)
        self.vAxis = transform.xform(self.vAxis)
        self.rotation = angle

    def fitTextureToPointCloud(self, cloud, tileX, tileY):
        if self.material is None:
            return
        if tileX <= 0:
            tileX = 1
        if tileY <= 0:
            tileY = 1

        # Scale will change, no need to use it in the calculations
        xvals = []
        yvals = []
        for extent in cloud.extents:
            xvals.append(extent.dot(self.uAxis))
            yvals.append(extent.dot(self.vAxis))

        minU = min(xvals)
        minV = min(yvals)
        maxU = max(xvals)
        maxV = max(yvals)

        self.scale.x = (maxU - minU) / (self.material.size.x * tileX)
        self.scale.y = (maxV - minV) / (self.material.size.y * tileY)
        self.shift.x = -minU / self.scale.x
        self.shift.y = -minV / self.scale.y

    def alignTextureWithPointCloud(self, cloud, mode):
        if self.material is None:
            return

        xvals = []
        yvals = []
        for extent in cloud.extents:
            xvals.append(extent.dot(self.uAxis) / self.scale.x)
            yvals.append(extent.dot(self.vAxis) / self.scale.y)

        minU = min(xvals)
        minV = min(yvals)
        maxU = max(xvals)
        maxV = max(yvals)

        if mode == Align.Left:
            self.shift.x = -minU
        elif mode == Align.Right:
            self.shift.x = -maxU + self.material.size.x
        elif mode == Align.Center:
            avgU = (minU + maxU) / 2
            avgV = (minV + maxV) / 2
            self.shift.x = -avgU + self.material.size.x / 2
            self.shift.y = -avgV + self.material.size.y / 2
        elif mode == Align.Top:
            self.shift.y = -minV
        elif mode == Align.Bottom:
            self.shift.y = -maxV + self.material.size.y

    def writeKeyValues(self, kv):
        kv.setKeyValue("material", self.material.filename.getFullpath())
        kv.setKeyValue("scale", CKeyValues.toString(self.scale))
        kv.setKeyValue("shift", CKeyValues.toString(self.shift))
        kv.setKeyValue("uaxis", CKeyValues.toString(self.uAxis))
        kv.setKeyValue("vaxis", CKeyValues.toString(self.vAxis))
        kv.setKeyValue("rotation", str(self.rotation))

    def readKeyValues(self, kv):
        self.material = MaterialPool.getMaterial(kv.getValue("material"))
        self.scale = CKeyValues.to2f(kv.getValue("scale"))
        self.shift = CKeyValues.to2f(kv.getValue("shift"))
        self.uAxis = CKeyValues.to3f(kv.getValue("uaxis"))
        self.vAxis = CKeyValues.to3f(kv.getValue("vaxis"))
        self.rotation = float(kv.getValue("rotation"))

    def clone(self):
        mat = FaceMaterial()
        mat.material = self.material
        mat.scale = Vec2(self.scale)
        mat.shift = Vec2(self.shift)
        mat.uAxis = Vec3(self.uAxis)
        mat.vAxis = Vec3(self.vAxis)
        mat.rotation = float(self.rotation)
        return mat

class SolidFace(MapWritable):

    ObjectName = "side"

    def __init__(self, id = 0, plane = Plane(0, 0, 1, 0), solid = None):
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
        self.np3DLines = None
        self.solid = solid
        self.hasGeometry = False
        self.vdata = None

    def showClipVisRemove(self):
        if not self.np3D.isStashed():
            self.np3D.stash()
        self.np3DLines.setColor(1, 0, 0, 1)
        self.np2D.setColor(1, 0, 0, 1)

    def showClipVisKeep(self):
        if self.np3D.isStashed():
            self.np3D.unstash()
        self.np3DLines.setColor(1, 1, 0, 1)
        self.np2D.setColor(1, 1, 1, 1)

    def show3DLines(self):
        if self.np3DLines and self.np3DLines.isStashed():
            self.np3DLines.unstash()

    def hide3DLines(self):
        if self.np3DLines and not self.np3DLines.isStashed():
            self.np3DLines.stash()

    def copy(self, generator):
        f = SolidFace(generator.getNextID(), Plane(self.plane), self.solid)
        f.isSelected = self.isSelected
        f.setColor(Vec4(self.color))
        f.setMaterial(self.material.clone())
        for i in range(len(self.vertices)):
            newVert = self.vertices[i].clone()
            newVert.face = f
            f.vertices.append(newVert)
        f.generate()
        return f

    def clone(self):
        f = self.copy(IDGenerator())
        f.id = self.id
        return f

    def paste(self, f):
        self.plane = Plane(f.plane)
        self.setColor(Vec4(f.color))
        self.isSelected = f.isSelected
        self.setMaterial(f.material.clone())
        self.solid = f.solid
        self.vertices = []
        for i in range(len(f.vertices)):
            newVert = f.vertices[i].clone()
            newVert.face = self
            self.vertices.append(newVert)
        self.generate()

    def unclone(self, f):
        self.paste(f)
        self.id = f.id

    def xform(self, mat):
        for vert in self.vertices:
            vert.xform(mat)
        self.plane = Plane.fromVertices(self.vertices[0].pos, self.vertices[1].pos, self.vertices[2].pos)
        self.calcTextureCoordinates(True)
        if self.hasGeometry:
            self.regenerateGeometry()

    def getAbsOrigin(self):
        avg = Point3(0)
        for vert in self.vertices:
            avg += vert.getWorldPos()
        avg /= len(self.vertices)
        return avg

    def getWorldPlane(self):
        plane = Plane(self.plane)
        plane.xform(self.np.getMat(base.render))
        return plane

    def getName(self):
        return "Solid face"

    def select(self):
        self.np3D.setColorScale(1, 0.75, 0.75, 1)
        self.np2D.setColor(1, 0, 0, 1)
        self.np2D.setBin("fixed", LEGlobals.SelectedSort)
        self.np2D.setDepthWrite(False)
        self.np2D.setDepthTest(False)
        self.isSelected = True

    def deselect(self):
        self.np3D.clearColorScale()
        self.np2D.setColor(self.color)
        self.np2D.setDepthWrite(True)
        self.np2D.setDepthTest(True)
        self.np2D.clearBin()
        self.isSelected = False

    def readKeyValues(self, kv):

        self.id = int(self.id)
        base.document.reserveFaceID(self.id)

        self.plane = Plane(CKeyValues.to4f(kv.getValue("plane")))

        for i in range(kv.getNumChildren()):
            child = kv.getChild(i)
            if child.getName() == "material":
                self.material.readKeyValues(child)
            elif child.getName() == "vertex":
                vert = SolidVertex(face = self)
                vert.readKeyValues(child)
                self.vertices.append(vert)

    def writeKeyValues(self, kv):
        kv.setKeyValue("id", str(self.id))
        kv.setKeyValue("plane", CKeyValues.toString(self.plane))

        matKv = CKeyValues("material", kv)
        self.material.writeKeyValues(matKv)

        for vert in self.vertices:
            vertKv = CKeyValues("vertex", kv)
            vert.writeKeyValues(vertKv)

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
        self.np3DLines = self.np.attachNewNode(GeomNode("3dlines"))
        self.np3DLines.hide(~VIEWPORT_3D_MASK)
        self.np3DLines.setColor(1, 1, 0, 1)
        self.np3DLines.setAntialias(AntialiasAttrib.MLine)
        self.hide3DLines()
        if self.material.material:
            self.setMaterial(self.material.material)
        self.np.setCollideMask(GeomNode.getDefaultCollideMask() | LEGlobals.FaceMask)
        self.regenerateGeometry()

    def setMaterial(self, mat):
        self.material.material = mat
        if self.np3D and mat:
            self.np3D.setBSPMaterial(mat.material)
        self.calcTextureCoordinates(True)

    def setColor(self, color):
        if self.np2D:
            self.np2D.setColor(color)
        self.color = color

    def setFaceMaterial(self, faceMat):
        self.material = faceMat
        self.setMaterial(self.material.material)

    def alignTextureToFace(self):
        self.material.alignTextureToFace(self)
        self.calcTextureCoordinates(True)

    def alignTextureToWorld(self):
        self.material.alignTextureToWorld(self)
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

    def classifyAgainstPlane(self, plane):
        front = back = onplane = 0
        count = len(self.vertices)

        for vert in self.vertices:
            test = plane.onPlane(vert.getWorldPos())
            if test <= 0:
                back += 1
            if test >= 0:
                front += 1
            if test == 0:
                onplane += 1

        if onplane == count:
            return PlaneClassification.OnPlane
        if front == count:
            return PlaneClassification.Front
        if back == count:
            return PlaneClassification.Back
        return PlaneClassification.Spanning

    def flip(self):
        self.vertices.reverse()
        self.plane = Plane.fromVertices(self.vertices[0].pos, self.vertices[1].pos, self.vertices[2].pos)
        if self.hasGeometry:
            self.regenerateGeometry()

    def regenerateGeometry(self):
        # Remove existing geometry
        self.np2D.node().removeAllGeoms()
        self.np3DLines.node().removeAllGeoms()
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
            prim3D.addVertices(i + 1, i, 0)
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

        geom3DLines = Geom(vdata)
        geom3DLines.addPrimitive(prim2D)
        self.np3DLines.node().addGeom(geom3DLines)

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
        self.np3DLines.removeNode()
        self.np3DLines = None
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
