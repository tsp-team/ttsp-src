
# Represents the current map that we are working on.
class Document:

    def __init__(self):
        self.filename = None
        self.unsaved = True

    def save(self, filename = None):
        # if filename is not none, this is a save-as
        if not filename:
            filename = self.filename

    def close(self):
        pass

    def open(self, filename = None):
        # if filename is none, this is a new document/map
        pass

    def isUnsaved(self):
        return self.unsaved

    def getMapName(self):
        if not self.filename:
            return "Unsaved map"
        return self.filename.getBasename()