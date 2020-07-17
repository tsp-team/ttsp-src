from panda3d.core import BitMask32

EntityMask = BitMask32.bit(0)
ManipulatorMask = BitMask32.bit(1)

# Solid selection masks
FaceMask = BitMask32.bit(2)
VertexMask = BitMask32.bit(3)
