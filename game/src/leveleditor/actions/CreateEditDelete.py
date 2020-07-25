from .Action import Action

class CreateEditDelete(Action):

    def __init__(self):
        Action.__init__(self)
        self.createObjects = []
        self.deleteObjects = []
        self.editObjects = []

    def create(self, mapObject):
        self.createObjects.append(mapObject)

    def delete(self, mapObject):
        self.deleteObjects.append(mapObject)

    def do(self):
        for delete in self.deleteObjects:
            delete.stash()

        for create in self.createObjects:
            create.unstash()

    def undo(self):
        for create in self.createObjects:
            create.stash()

        for delete in self.deleteObjects:
            delete.unstash()
