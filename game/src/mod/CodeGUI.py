from panda3d.core import NodePath

from direct.gui.DirectGui import OnscreenText

class CodeGUI(NodePath):

    def __init__(self):
        NodePath.__init__(self, 'codeGUI')
        self.reparentTo(base.a2dBottomLeft)
        self.setPos(0.4, 0, 0.1)

        self.lbl = OnscreenText(fg = (175 / 255.0, 226 / 255.0, 255 / 255.0, 1.0), text = "_ _ _ _", parent = self)
        self.numbers = []

    def addNumber(self, num):
        self.numbers.append(num)
        self.updateText()

    def clearNumbers(self):
        self.numbers = []
        self.updateText()

    def updateText(self):
        self.lbl['text'] = ""
        for i in range(4):
            print(i)
            if i <= len(self.numbers) - 1:
                self.lbl['text'] += str(self.numbers[i])
            else:
                self.lbl['text'] += "_"
            if i + 1 < 4:
                self.lbl['text'] += " "
