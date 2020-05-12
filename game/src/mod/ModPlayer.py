from src.coginvasion.toon.DistributedToon import DistributedToon
from src.coginvasion.globals import CIGlobals

from direct.gui.DirectGui import OnscreenText

class ModPlayer(DistributedToon):
    
    def __init__(self, cr):
        DistributedToon.__init__(self, cr)
        self.money = 0
        
    def setMoney(self, money):
        self.money = money
        
    def getMoney(self):
        return self.money
        
    def disable(self):
        self.money = None
        DistributedToon.disable(self)
