from .BaseBrush import BaseBrush

from src.leveleditor import LEUtils
from src.leveleditor.mapobject.Solid import Solid
from src.leveleditor.mapobject.SolidFace import SolidFace
from src.leveleditor.mapobject.SolidVertex import SolidVertex
from src.leveleditor.math.Plane import Plane

class BlockBrush(BaseBrush):
    Name = "Block"

    def create(self, generator, mins, maxs, material, roundDecimals):
        faces = LEUtils.getBoxFaces(mins, maxs, roundDecimals)
        return [self.makeSolid(generator, faces, material)]
