from src.leveleditor.math.Polygon import Polygon
from .MapObject import MapObject
from .SolidFace import SolidFace
from .SolidVertex import SolidVertex

from src.leveleditor import LEUtils

# A brush
class Solid(MapObject):

    ObjectName = "solid"

    def __init__(self):
        MapObject.__init__(self)
        self.faces = []

    @staticmethod
    def createFromIntersectingPlanes(self, planes):
        solid = base.document.createObject(Solid)
        for i in range(len(planes)):
            # Split the polygon by all the other planes
            poly = Polygon.fromPlaneAndRadius(planes[i])
            for j in range(len(planes)):
                if i != j:
                    poly.split(planes[j])

            # The final polygon is the face
            face = SolidFace(base.document.getNextFaceID(), poly.plane, solid)
            for i in range(len(poly.vertices)):
                # Round vertices a bit for sanity
                face.vertices.append(SolidVertex(LEUtils.roundVector(poly.vertices[i], 2), face))
            face.recalcBoundingBox()
            face.alignTextureToWorld()
            solid.faces.append(face)

        # Ensure all faces point outwards
        origin = solid.getOrigin()
        for face in solid.faces:
            if face.plane.distToPlane(origin) >= 0:
                face.flip()

        solid.recalcBoundingBox()
        return solid
