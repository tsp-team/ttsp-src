from panda3d.core import BitMask32, CullBinManager

EntityMask = BitMask32.bit(0)
ManipulatorMask = BitMask32.bit(1)

# Solid selection masks
FaceMask = BitMask32.bit(2)
VertexMask = BitMask32.bit(3)

SelectedSort = 1
BoxSort = 2
WidgetSort = 3

AppName = "Foundry"
