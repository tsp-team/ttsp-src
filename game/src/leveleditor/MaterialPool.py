from panda3d.core import Filename

from .MaterialReference import MaterialReference

MaterialRefs = {}

def getMaterial(filename):
    global MaterialRefs
    filename = Filename(filename)
    fullpath = filename.getFullpath()
    if fullpath in MaterialRefs:
        ref = MaterialRefs[fullpath]
    else:
        ref = MaterialReference(filename)
        MaterialRefs[fullpath] = ref
    return ref
