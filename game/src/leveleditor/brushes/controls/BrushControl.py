from PyQt5 import QtWidgets

class BrushControl:

    def __init__(self, label, callback = None):
        self.label = None
        self.control = None
        self.callback = callback

    def valueChanged(self, newVal):
        if self.callback:
            self.callback(newVal)

    def enable(self):
        self.control.setEnabled(True)

    def disable(self):
        self.control.setEnabled(False)

    def getValue(self):
        return 0

    def isEnabled(self):
        return self.control.enabled()
