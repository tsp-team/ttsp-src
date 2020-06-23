from panda3d.core import LineSegs, Vec4, Point3, TextNode

# Widget that shows which direction the camera is looking in the 3D viewport.
class ViewportGizmo:

    def __init__(self, vp):
        self.vp = vp
        axes = self.vp.getGizmoAxes()
        segs = LineSegs()

        self.np = self.vp.a2dBottomLeft.attachNewNode("viewAxisWidget")
        self.np.setScale(0.15)
        self.np.setPos(0.16, 0, 0.16)

        if 0 in axes:
          # X line
          segs.setColor(Vec4(1, 0, 0, 1))
          segs.moveTo(Point3(0))
          segs.drawTo(Point3(1, 0, 0))
          xText = TextNode('yText')
          xText.setTextColor(Vec4(1, 0, 0, 1))
          xText.setText('X')
          xTextNp = self.np.attachNewNode(xText.generate())
          xTextNp.setX(1.05)
          xTextNp.setBillboardPointEye()
          xTextNp.setScale(0.5)

        if 1 in axes:
          # Y line
          segs.setColor(Vec4(0, 1, 0, 1))
          segs.moveTo(Point3(0))
          segs.drawTo(Point3(0, -1, 0))
          yText = TextNode('yText')
          yText.setTextColor(Vec4(0, 1, 0, 1))
          yText.setText('Y')
          yTextNp = self.np.attachNewNode(yText.generate())
          yTextNp.setY(-1.05)
          yTextNp.setBillboardPointEye()
          yTextNp.setScale(0.5)

        if 2 in axes:
          # Z line
          segs.setColor(Vec4(0, 0, 1, 1))
          segs.moveTo(Point3(0))
          segs.drawTo(Point3(0, 0, 1))
          zText = TextNode('zText')
          zText.setTextColor(Vec4(0, 0, 1, 1))
          zText.setText('Z')
          zTextNp = self.np.attachNewNode(zText.generate())
          zTextNp.setZ(1.05)
          zTextNp.setBillboardPointEye()
          zTextNp.setScale(0.5)

        self.np.attachNewNode(segs.create())
