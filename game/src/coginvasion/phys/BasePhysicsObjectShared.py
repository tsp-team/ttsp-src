from panda3d.core import BitMask32, NodePath

class BasePhysicsObjectShared:

    def __init__(self):
        self.bodyNode = None
        self.bodyNP = None
        
        self.bodyNPs = []

        self.shapeGroup = BitMask32.allOn()
        self.underneathSelf = False
        self.worlds = []
        self.__physicsSetup = False
        
        self.surfaceProp = "default"

    def getPhysNP(self, idx = None):
        if idx is None:
            return self.bodyNP
        else:
            return self.bodyNPs[idx]
    
    def getPhysNode(self, idx = None):
        if idx is None:
            return self.bodyNode
        else:
            return self.bodyNPs[idx].node()
        
    def addToPhysicsWorld(self, world):
        if not world:
            return
            
        for bodyNP in self.bodyNPs:
            world.attach(bodyNP.node())
            self.worlds.append(world)

    def removeFromPhysicsWorld(self, world, andRemove = True):
        if not world:
            return
            
        for bodyNP in self.bodyNPs:
            world.remove(bodyNP.node())
            if andRemove and world in self.worlds:
                self.worlds.remove(world)
                
    def arePhysicsSetup(self):
        return self.__physicsSetup

    def cleanupPhysics(self):
        for world in self.worlds:
            self.removeFromPhysicsWorld(world, False)
        self.worlds = []
        
        for bodyNP in self.bodyNPs:
            if self.underneathSelf:
                bodyNP.removeNode()
                
        self.bodyNP = None
        self.bodyNode = None
        self.bodyNPs = []
            
        self.__physicsSetup = False
        
    def attachPhysicsNode(self, bodyNode, parent = None):
        bodyNP = NodePath(bodyNode)
        bodyNP.setSurfaceProp(self.surfaceProp)
        bodyNP.setCollideMask(self.shapeGroup)
        bodyNP.setPythonTag("physicsObject", self)
        if parent:
            bodyNP.reparentTo(parent)
        self.bodyNPs.append(bodyNP)
        return bodyNP

    def setupPhysics(self, bodyNode, underneathSelf = None):
        self.cleanupPhysics()

        if underneathSelf is not None:
            self.underneathSelf = underneathSelf
        else:
            underneathSelf = self.underneathSelf

        self.bodyNode = bodyNode

        assert self.bodyNode is not None

        parent = self.getParent()
        self.bodyNP = self.attachPhysicsNode(bodyNode)
        self.bodyNP.reparentTo(parent)
        if not underneathSelf:
            self.reparentTo(self.bodyNP)
            self.assign(self.bodyNP)
        else:
            self.bodyNP.reparentTo(self)
            
        self.__physicsSetup = True