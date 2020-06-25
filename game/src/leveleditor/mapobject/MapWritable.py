from direct.showbase.DirectObject import DirectObject

# Base class for serializable map data
class MapWritable(DirectObject):

    ObjectName = "writable"

    def __init__(self):
        DirectObject.__init__(self)

    def writeKeyValues(self, keyvalues):
        raise NotImplementedError

    def readKeyValues(self, keyvalues):
        raise NotImplementedError
