from .Entity import Entity

# The root entity of each map
class World(Entity):

    ObjectName = "world"

    def __init__(self, id):
        Entity.__init__(self, id)
        self.setClassname("worldspawn")
        self.np.node().setFinal(False)

    def isWorld(self):
        return True
