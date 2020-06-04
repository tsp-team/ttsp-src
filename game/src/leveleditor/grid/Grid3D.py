from .Grid import Grid

from src.coginvasion.globals import CIGlobals

class Grid3D(Grid):

    def calcZoom(self):
        z = max(int(abs(self.viewport.camNp.getZ() * 16)), 0.001)
        return CIGlobals.clamp(10000 / z, 0.001, 256)