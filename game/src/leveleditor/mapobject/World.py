from .Entity import Entity

# The root entity of each map
class World(Entity):

    ObjectName = "world"

    def __init__(self):
        Entity.__init__(self)
        self.setClassname("worldspawn")
