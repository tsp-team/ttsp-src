from panda3d.core import Point3, Vec3, NodePath, CKeyValues

from src.leveleditor.math.Polygon import Polygon
from .MapObject import MapObject
from .SolidFace import SolidFace
from .SolidVertex import SolidVertex

from src.leveleditor import LEUtils
from src.leveleditor.math import PlaneClassification
from src.leveleditor.math.Plane import Plane

from .ObjectProperty import ObjectProperty

class VisOccluder(ObjectProperty):

    def __init__(self, mapObject):
        ObjectProperty.__init__(self, mapObject)
        self.valueType = "boolean"
        self.value = True
        self.defaultValue = True
        self.name = "visoccluder"

    def clone(self, mapObject):
        prop = VisOccluder(mapObject)
        self.copyBase(prop)
        return prop

    def getDescription(self):
        return "Turn this on to make the Solid block visibility of other objects."

    def getDisplayName(self):
        return "Vis Occluder"

# A brush
class Solid(MapObject):

    ObjectName = "solid"

    def __init__(self, id):
        MapObject.__init__(self, id)
        self.faces = []
        self.addProperty(VisOccluder(self))

    def copy(self, generator):
        s = Solid(generator.getNextID())
        s.generate()
        self.copyBase(s, generator)
        for face in self.faces:
            f = face.copy(generator)
            f.solid = s
            s.faces.append(f)
        s.generateFaces()
        return s

    def generateFaces(self):
        for face in self.faces:
            face.generate()

    def writeKeyValues(self, keyvalues):
        MapObject.writeKeyValues(self, keyvalues)

        # Write or faces or "sides"
        for face in self.faces:
            faceKv = CKeyValues("side", keyvalues)
            face.writeKeyValues(faceKv)

    def readKeyValues(self, kv):
        MapObject.readKeyValues(self, kv)

        numChildren = kv.getNumChildren()
        for i in range(numChildren):
            child = kv.getChild(i)
            if child.getName() == "side":
                face = SolidFace(solid = self)
                face.readKeyValues(child)
                face.generate()
                self.faces.append(face)

    def showClipVisRemove(self):
        for face in self.faces:
            face.showClipVisRemove()

    def showClipVisKeep(self):
        for face in self.faces:
            face.showClipVisKeep()

    def showBoundingBox(self):
        for face in self.faces:
            face.show3DLines()

    def hideBoundingBox(self):
        for face in self.faces:
            face.hide3DLines()

    def select(self):
        MapObject.select(self)
        for face in self.faces:
            face.select()

    def deselect(self):
        MapObject.deselect(self)
        for face in self.faces:
            face.deselect()

    def getAbsSolidOrigin(self):
        avg = Point3(0)
        for face in self.faces:
            avg += face.getAbsOrigin()
        avg /= len(self.faces)
        return avg

    def setToSolidOrigin(self):
        # Moves the solid origin to median of all face vertex positions,
        # and transforms all faces to be relative to the median position.
        # Resets angles, scale, and shear.
        origin = self.getAbsSolidOrigin()
        self.setAbsOrigin(origin)
        self.setAbsAngles(Vec3(0))
        self.setAbsScale(Vec3(1))
        self.setAbsShear(Vec3(0))
        mat = self.np.getMat(NodePath())
        mat.invertInPlace()
        for face in self.faces:
            face.xform(mat)

    def getName(self):
        return "Solid"

    def getDescription(self):
        return "Convex solid geometry."

    def delete(self):
        MapObject.delete(self)
        for face in self.faces:
            face.delete()
        self.faces = None

    # Splits this solid into two solids by intersecting against a plane.
    def split(self, plane, generator, temp = False):
        back = front = None

        # Check that this solid actually spans the plane
        classifications = []
        for face in self.faces:
            classify = face.classifyAgainstPlane(plane)
            if classify not in classifications:
                classifications.append(classify)
        if PlaneClassification.Spanning not in classifications:
            if PlaneClassification.Back in classifications:
                back = self
            elif PlaneClassification.Front in classifications:
                front = self
            return [False, back, front]

        backPlanes = [plane]
        flippedFront = Plane(plane)
        flippedFront.flip()
        frontPlanes = [flippedFront]

        for face in self.faces:
            classify = face.classifyAgainstPlane(plane)
            if classify != PlaneClassification.Back:
                frontPlanes.append(face.getWorldPlane())
            if classify != PlaneClassification.Front:
                backPlanes.append(face.getWorldPlane())

        back = Solid.createFromIntersectingPlanes(backPlanes, generator)
        front = Solid.createFromIntersectingPlanes(frontPlanes, generator)
        self.copyBase(back, generator)
        self.copyBase(front, generator)

        unionOfFaces = front.faces + back.faces
        for face in unionOfFaces:
            face.material = self.faces[0].material.clone()
            face.setMaterial(face.material.material)
            face.alignTextureToFace()

        # Restore textures (match the planes up on each face)
        for orig in self.faces:
            for face in back.faces:
                classify = face.classifyAgainstPlane(orig.getWorldPlane())
                if classify != PlaneClassification.OnPlane:
                    continue
                face.material = orig.material.clone()
                face.setMaterial(face.material.material)
                break
            for face in front.faces:
                classify = face.classifyAgainstPlane(orig.getWorldPlane())
                if classify != PlaneClassification.OnPlane:
                    continue
                face.material = orig.material.clone()
                face.setMaterial(face.material.material)
                break

        for face in unionOfFaces:
            face.calcTextureCoordinates(True)

        return [True, back, front]

    @staticmethod
    def createFromIntersectingPlanes(planes, generator):
        solid = Solid(generator.getNextID())
        for i in range(len(planes)):
            # Split the polygon by all the other planes
            poly = Polygon.fromPlaneAndRadius(planes[i])
            for j in range(len(planes)):
                if i != j:
                    poly.splitInPlace(planes[j])

            # The final polygon is the face
            face = SolidFace(generator.getNextFaceID(), planes[i], solid)
            for i in range(len(poly.vertices)):
                # Round vertices a bit for sanity
                face.vertices.append(SolidVertex(LEUtils.roundVector(poly.vertices[i], 2), face))
            face.alignTextureToWorld()
            solid.faces.append(face)

        solid.generate()
        solid.setToSolidOrigin()
        solid.generateFaces()

        # Ensure all faces point outwards
        origin = Point3(0)
        for face in solid.faces:
            # The solid origin should be on or behind the face plane.
            # If the solid origin is in front of the face plane, flip the face.
            if face.plane.distToPlane(origin) > 0:
                face.flip()

        solid.recalcBoundingBox()

        return solid
