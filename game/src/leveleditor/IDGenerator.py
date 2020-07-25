from panda3d.core import UniqueIdAllocator

class IDGenerator:

    def __init__(self):
        self.alloc = UniqueIdAllocator(0, 0xFFFF)
        self.faceAlloc = UniqueIdAllocator(0, 0xFFFF)

    def getNextFaceID(self):
        return self.faceAlloc.allocate()

    def freeFaceID(self, id):
        self.faceAlloc.free(id)

    def reserveFaceID(self, id):
        self.faceAlloc.initialReserveId(id)

    def getNextID(self):
        return self.alloc.allocate()

    def freeID(self, id):
        self.alloc.free(id)

    def reserveID(self, id):
        self.alloc.initialReserveId(id)
