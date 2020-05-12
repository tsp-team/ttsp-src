from panda3d.core import Vec3, Quat

from src.coginvasion.toon.DistributedToonAI import DistributedToonAI

import random

class ModPlayerAI(DistributedToonAI):

    def __init__(self, air):
        DistributedToonAI.__init__(self, air)
        self.money = 0
        self.viewOrigin = Vec3()
        self.viewAngles = Vec3()
        self.viewAngleVectors = []
        self.numbers = []
        
    def addCodeNumber(self, num):
        self.numbers.append(num)
        self.sendUpdate('setCodeNumbers', [self.numbers])
        
    def getCodeNumbers(self):
        return self.numbers
        
    def clearCodeNumbers(self):
        self.numbers = []
        self.sendUpdate('setCodeNumbers', [self.numbers])
        
    def setView(self, x, y, z, h, p, r):
        self.viewOrigin = Vec3(x, y, z)
        self.viewAngles = Vec3(h, p, r)
        quat = Quat()
        quat.setHpr(self.viewAngles)
        self.viewAngleVectors = [
            quat.getRight(), quat.getForward(), quat.getUp()
        ]
        
    def getViewAngleVectors(self):
        return self.viewAngleVectors
        
    def getViewVector(self, n):
        return self.viewAngleVectors[n]
        
    def getViewAngles(self):
        return self.viewAngles
        
    def getViewOrigin(self):
        return self.viewOrigin
        
    def setMoney(self, money):
        self.money = money
        
    def b_setMoney(self, money):
        self.sendUpdate('setMoney', [money])
        self.setMoney(money)
        
    def getMoney(self):
        return self.money
        
    def takeDamage(self, damageInfo):
        DistributedToonAI.takeDamage(self, damageInfo)
        bz = self.air.battleZones[self.zoneId]
        bz.playerTakeDamage(damageInfo.damageAmount, self.doId)
        
    def announceGenerate(self):
        DistributedToonAI.announceGenerate(self)
        taskMgr.add(self.__hpRegenTask, self.taskName("hpRegen"))
        
    def __hpRegenTask(self, task):
        if self.isDead():
            return task.done
            
        task.delayTime = random.uniform(7, 10)
        
        if self.health >= self.maxHealth:
            return task.again
        
        regenAmount = min(2, self.maxHealth - self.health)
        self.b_setHealth(self.getHealth() + regenAmount)
        
        return task.again
        
    def delete(self):
        taskMgr.remove(self.taskName("hpRegen"))
        self.money = None
        self.viewOrigin = None
        self.viewAngles = None
        self.viewAngleVectors = None
        DistributedToonAI.delete(self)
        
