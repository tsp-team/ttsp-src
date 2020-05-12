def makeVPPhysics(multipart = False):
    from panda3d.core import TransformState
    from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode
    
    carriage = BulletBoxShape((4.40625, 7.125, 2.75))
    tread = BulletBoxShape((1.9, 10.34, 2.75))
    legs = BulletBoxShape((3.375, 3.375, 2.1875))
    gear = BulletBoxShape((6.72, 6.72, 1.1))
    torso = BulletBoxShape((4.44, 3.625, 4.125))
    head = BulletBoxShape((2, 2, 2.22))
    torsoTrans = TransformState.makePos((0, 0, 13.93))
    headTrans = TransformState.makePos((0, 0, 20.28))
    
    bodyNode = BulletRigidBodyNode("VPPhysics")
    bodyNode.addShape(carriage, TransformState.makePos((0, 0, 2.75)))
    bodyNode.addShape(tread, TransformState.makePos((6.3, 0, 2.75)))
    bodyNode.addShape(tread, TransformState.makePos((-6.3, 0, 2.75)))
    bodyNode.addShape(legs, TransformState.makePos((0, 0, 7.75)))
    bodyNode.addShape(gear, TransformState.makePos((0, 0, 10.94)))
    if not multipart:
        bodyNode.addShape(torso, torsoTrans)
        bodyNode.addShape(head, headTrans)
    bodyNode.setKinematic(True)
    bodyNode.setMass(0.0)
    
    if multipart:
        upperNode = BulletRigidBodyNode("VPPhysics-upper")
        upperNode.addShape(torso, torsoTrans)
        upperNode.addShape(head, headTrans)
        upperNode.setKinematic(True)
        upperNode.setMass(0.0)
    
    if multipart:
        return [bodyNode, upperNode]
    return bodyNode
