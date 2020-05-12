from src.coginvasion.szboss.DistributedEntityAI import DistributedEntityAI
import random

class KeypadAI(DistributedEntityAI):
    
    CodeEntry = 0
    CodeResponse = 1

    def __init__(self, air, dispatch):
        DistributedEntityAI.__init__(self, air, dispatch)
        self.numbers = []
        self.code = []
        self.setModel("models/keypad.bam")
        self.entityState = self.CodeEntry
        self.codeWasCorrect = False
        
    def b_setNumbers(self, nums):
        self.numbers = nums
        self.sendUpdate('setNumbers', [nums])
        
    def getNumbers(self):
        return self.numbers
        
    def loadEntityValues(self):
        DistributedEntityAI.loadEntityValues(self)
        #codeStr = self.getEntityValue("code")
        #for numStr in codeStr:
        #    self.code.append(int(numStr))
        
        for i in range(4):
            self.code.append(random.randint(0, 9))
            
    def think(self):
        DistributedEntityAI.think(self)
        
        state = self.getEntityState()
        elapsed = self.getEntityStateElapsed()
        if state == self.CodeResponse and elapsed >= 0.5:
            if self.codeWasCorrect:
                self.dispatchOutput("OnCodeCorrect")
                self.dispatch.codeUsed()
            else:
                self.dispatchOutput("OnCodeIncorrect")
            self.b_setNumbers([])
            self.setEntityState(self.CodeEntry)
            self.codeWasCorrect = False
        
    def pressButton(self, num):
        if self.getEntityState() != self.CodeEntry:
            return
            
        self.numbers.append(num)
        self.b_setNumbers(self.numbers)
        
        if len(self.numbers) == len(self.code):
            if self.numbers == self.code:
                self.d_playSound("access")
                self.codeWasCorrect = True
            else:
                self.d_playSound("denied")
                self.codeWasCorrect = False
            self.setEntityState(self.CodeResponse)
            return
            
        self.d_playSound("press")
        
