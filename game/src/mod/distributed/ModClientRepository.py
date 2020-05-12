from src.mod.distributed.ClientRepository import ClientRepository
from direct.distributed.PyDatagram import PyDatagram

from src.mod.ModMsgTypes import SET_INTEREST_COMPLETE_CMU, CLIENT_HELLO_CMU

class EHandle:
        
    def __init__(self, zoneId):
        self.zoneId = zoneId

class ModClientRepository(ClientRepository):
    
    def __init__(self, *args, **kwargs):
        ClientRepository.__init__(self, *args, **kwargs)
        self.isShowingPlayerIds = False
        
        self.interestInProgress = False
        self.interestEvent = None
        
        if self.__class__ == ModClientRepository:
            from src.coginvasion.attack.AttackManager import AttackManager
            self.attackMgr = AttackManager()
            
    def sendClientHello(self):
        dg = PyDatagram()
        dg.addUint16(CLIENT_HELLO_CMU)
        self.send(dg)
        
    def addInterest(self, parentId, zoneId, desc, event = None):
        if self.interestInProgress:
            print "Warning: ignoring addInterest while another interest operation is in progress"
            return None
            
        self.setInterestZones(self.interestZones + [zoneId])
        self.interestEvent = event
        self.interestInProgress = True
        
        handle = EHandle(zoneId)
        return handle
        
    def removeInterest(self, eHandle, event = None):
        if self.interestInProgress:
            print "Warning: ignoring removeInterest while another interest operation is in progress"
            return
            
        zones = list(self.interestZones)
        zones.remove(eHandle.zoneId)
        self.setInterestZones(zones)
        self.interestEvent = event
        self.interestInProgress = True
        
    def handleMessageType(self, msgType, di):
        if msgType == SET_INTEREST_COMPLETE_CMU:
            if self.interestInProgress:
                if self.interestEvent:
                    messenger.send(self.interestEvent)
                self.interestEvent = None
                self.interestInProgress = False
            else:
                print "Warning: received SET_INTEREST_COMPLETE_CMU when no interest operation is in progress"
