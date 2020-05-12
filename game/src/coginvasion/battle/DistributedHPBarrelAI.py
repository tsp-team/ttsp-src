"""
COG INVASION ONLINE
Copyright (c) CIO Team. All rights reserved.

@file DistributedHPBarrelAI.py
@author Maverick Liberty
@date March 27, 2018

It seriously took me 2 years to add in toon-up barrels. SMH

"""

from src.coginvasion.globals import CIGlobals
from DistributedRestockBarrelAI import DistributedRestockBarrelAI

class DistributedHPBarrelAI(DistributedRestockBarrelAI):
    
    def __init__(self, air, dispatch):
        DistributedRestockBarrelAI.__init__(self, air, dispatch)
            
        self.hp = 10
        
    def loadEntityValues(self):
        self.hp = self.getEntityValueInt("healamt")
        
    def announceGenerate(self):
        DistributedRestockBarrelAI.announceGenerate(self)
        self.sendUpdate('setLabel', [0])
        
    def delete(self):
        DistributedRestockBarrelAI.delete(self)
        #del self.hoodId
        del self.hp
    
    def d_setGrab(self, avId):
        DistributedRestockBarrelAI.d_setGrab(self, avId)
        avatar = self.air.doId2do.get(avId, None)
        
        if avatar is not None:
            healAmt = self.hp
            
            if healAmt == -1:
                healAmt = 100
                    
            if (avatar.getHealth() + healAmt > avatar.getMaxHealth()):
                healAmt = avatar.getMaxHealth() - avatar.getHealth()
            
            if healAmt > 0:
                # Let's toon up the avatar that wants to grab health and announce it.
                avatar.toonUp(healAmt, announce = 1, sound = 0)
