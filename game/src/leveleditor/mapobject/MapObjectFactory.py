from .World import World
from .Entity import Entity
from .Solid import Solid

# object name in pmap file to object class
MapObjectsByName = {
    "world": World,
    "entity": Entity,
    "solid": Solid
}
