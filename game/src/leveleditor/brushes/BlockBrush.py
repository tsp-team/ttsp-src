from .BaseBrush import BaseBrush

from src.leveleditor import LEUtils
from src.leveleditor.mapobject.Solid import Solid
from src.leveleditor.mapobject.SolidFace import SolidFace
from src.leveleditor.mapobject.SolidVertex import SolidVertex
from src.leveleditor.math.Plane import Plane

class BlockBrush(BaseBrush):
    Name = "Block"

    def create(self, mins, maxs, material, roundDecimals):
        solid = Solid(base.document.getNextID())

        faces = LEUtils.getBoxFaces(mins, maxs)
        for faceVerts in faces:
            face = SolidFace(base.document.getNextFaceID(),
                             Plane.fromVertices(faceVerts[0], faceVerts[1], faceVerts[2]),
                             solid)
            face.setMaterial(material)
            for vert in faceVerts:
                face.vertices.append(SolidVertex(LEUtils.roundVector(vert, roundDecimals), face))
            face.alignTextureToFace()
            solid.faces.append(face)

        solid.generate()
        solid.setToSolidOrigin()
        solid.generateFaces()
        solid.recalcBoundingBox()

        return [solid]
