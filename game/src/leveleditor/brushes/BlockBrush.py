from .BaseBrush import BaseBrush

from src.leveleditor import LEUtils
from src.leveleditor.mapobject.Solid import Solid
from src.leveleditor.mapobject.SolidFace import SolidFace
from src.leveleditor.mapobject.SolidVertex import SolidVertex
from src.leveleditor.math.Plane import Plane

class BlockBrush(BaseBrush):
    Name = "Block"

    def create(self, mins, maxs, material, roundDecimals):
        solid = base.document.createObject(Solid)
        center = (maxs + mins) / 2.0
        solid.np.setPos(center)
        faces = LEUtils.getBoxFaces(mins, maxs)
        for faceVerts in faces:
            face = SolidFace(base.document.getNextFaceID(),
                             Plane.fromVertices(faceVerts[0] - center, faceVerts[1] - center, faceVerts[2] - center),
                             solid)
            face.setMaterial(material)
            for vert in faceVerts:
                vert = vert - center
                face.vertices.append(SolidVertex(LEUtils.roundVector(vert, roundDecimals), face))
            face.alignTextureToFace()
            face.generate()
            solid.faces.append(face)
        solid.recalcBoundingBox()
        return [solid]
