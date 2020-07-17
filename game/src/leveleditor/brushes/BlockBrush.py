from panda3d.core import LPlane

from .BaseBrush import BaseBrush

from src.leveleditor import LEUtils
from src.leveleditor.mapobject.Solid import Solid
from src.leveleditor.mapobject.SolidFace import SolidFace
from src.leveleditor.mapobject.SolidVertex import SolidVertex

class BlockBrush(BaseBrush):
    Name = "Block"

    def create(self, mins, maxs, material, roundDecimals):
        solid = base.document.createObject(Solid)
        faces = LEUtils.getBoxFaces(mins, maxs)
        for faceVerts in faces:
            face = SolidFace(base.document.getNextFaceID(),
                             LPlane(faceVerts[0], faceVerts[1], faceVerts[2]),
                             solid)
            face.setMaterial(material)
            for vert in faceVerts:
                face.vertices.append(SolidVertex(LEUtils.roundVector(vert, roundDecimals), face))
            face.alignTextureToFace()
            face.generate()
            solid.faces.append(face)
        solid.recalcBoundingBox()
        return [solid]
