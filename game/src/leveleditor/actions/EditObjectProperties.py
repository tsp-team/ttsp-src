from .Action import Action

class EditObjectProperties(Action):

    Name = "Edit Object Properties"
    ModifiesState = True

    def __init__(self, ent, newProperties):
        self.obj = ent
        self.newProperties = newProperties

        # Copy the current values based on the new property keys
        self.oldProperties = {}
        for key, value in newProperties.items():
            self.oldProperties[key] = ent.getPropertyValue(key)

    def do(self):
        self.obj.updateProperties(self.newProperties)

    def undo(self):
        self.obj.updateProperties(self.oldProperties)

    def cleanup(self):
        self.obj = None
        self.newProperties = None
        self.oldProperties = None
