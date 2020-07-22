from panda3d.core import LPlane

from src.leveleditor.math.Polygon import Polygon
from .MapObject import MapObject
from .SolidFace import SolidFace
from .SolidVertex import SolidVertex

from src.leveleditor import LEUtils
from src.leveleditor.math import PlaneClassification

from .ObjectProperty import ObjectProperty

class VisOccluder(ObjectProperty):

    def __init__(self, mapObject):
        ObjectProperty.__init__(self, mapObject)
        self.valueType = "boolean"
        self.value = True
        self.defaultValue = True
        self.name = "visoccluder"

    def getDescription(self):
        return "Turn this on to make the Solid block visibility of other objects."

    def getDisplayName(self):
        return "Vis Occluder"

# A brush
class Solid(MapObject):

    ObjectName = "solid"

    def __init__(self):
        MapObject.__init__(self)
        self.faces = []
        self.addProperty(VisOccluder(self))

    def select(self):
        MapObject.select(self)
        for face in self.faces:
            face.select()

    def deselect(self):
        MapObject.deselect(self)
        for face in self.faces:
            face.deselect()

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
    def split(self, plane, temp = False):
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
            return [False, front, back]

        backPlanes = [plane]
        frontPlanes = [LPlane(-plane[0], -plane[1], -plane[2], -plane[3])]

        for face in self.faces:
            classify = face.classifyAgainstPlane(plane)
            if classify != PlaneClassification.Back:
                frontPlanes.append(face.getWorldPlane())
            if classify != PlaneClassification.Front:
                backPlanes.append(face.getWorldPlane())

        back = SolidFace.createFromIntersectingPlanes(backPlanes, temp)
        front = SolidFace.createFromIntersectingPlanes(frontPlanes, temp)

    @staticmethod
    def createFromIntersectingPlanes(planes, temp = False):
        solid = base.document.createObject(Solid, id = -1 if temp else None)
        for i in range(len(planes)):
            # Split the polygon by all the other planes
            poly = Polygon.fromPlaneAndRadius(planes[i])
            for j in range(len(planes)):
                if i != j:
                    poly.split(planes[j])

            # The final polygon is the face
            face = SolidFace(-1 if temp else base.document.getNextFaceID(), poly.plane, solid)
            for i in range(len(poly.vertices)):
                # Round vertices a bit for sanity
                face.vertices.append(SolidVertex(LEUtils.roundVector(poly.vertices[i], 2), face))
            face.alignTextureToWorld()
            solid.faces.append(face)

        # Ensure all faces point outwards
        origin = solid.getOrigin()
        for face in solid.faces:
            if face.plane.distToPlane(origin) >= 0:
                face.flip()

        solid.recalcBoundingBox()
        return solid
