from panda3d.core import UniqueIdAllocator

from direct.distributed.PyDatagram import PyDatagram
from direct.distributed.NetMessenger import NetMessenger

from src.mod.ModMsgTypes import AI_HELLO_CMU
from ModClientRepository import ModClientRepository
from src.mod import ModGlobals

from src.coginvasion.ai.AIZoneData import AIZoneDataStore, DynamicZonesBegin, DynamicZonesEnd

class ModAIRepository(ModClientRepository):

    def __init__(self, *args, **kwargs):
        ModClientRepository.__init__(self, *args, **kwargs)

        # Anything that is a DistributedAvatarAI (Toons, Suits, etc).
        # This is a per-zone list of avatars.
        self.avatars = {}
        self.numAvatars = 0

        self.battleZones = {}

        self.districtId = 0

        self.zoneDataStore = AIZoneDataStore()

        self.zoneAllocator = UniqueIdAllocator(DynamicZonesBegin,
                                               DynamicZonesEnd)

        self.netMessenger = NetMessenger(self)

        # We deal with attacks on the server side as well
        from src.coginvasion.attack.AttackManagerAI import AttackManagerAI
        self.attackMgr = AttackManagerAI()

    def sendUpdate(self, distObj, fieldName, args):
        """ Sends a normal update for a single field. """
        dg = distObj.dclass.clientFormatUpdate(
            fieldName, distObj.doId, args)
        self.send(dg)

    def createObjectByName(self, dcClassName, initArgs = []):
        dclass = self.dclassesByName.get(dcClassName, None)
        if not dclass:
            return None
        classDef = dclass.getClassDef()
        if not self in initArgs:
            initArgs.insert(0, self)
        obj = classDef(*initArgs)
        return obj

    def generateObjectByName(self, dcClassName, initArgs = [], zoneId = ModGlobals.BattleZoneId):
        obj = self.createObjectByName(dcClassName, initArgs)
        if not obj:
            return None
        obj.generateWithRequired(zoneId)
        return obj

    def shutdown(self):
        for doId, do in self.doId2do.items():
            self.deleteObject(doId)
        self.sendDisconnect()

    def getZoneDataStore(self):
        return self.zoneDataStore

    def sendAIHello(self):
        dg = PyDatagram()
        dg.addUint16(AI_HELLO_CMU)
        self.send(dg)

    def getBattleZone(self, zoneId):
        return self.battleZones.get(zoneId, None)

    def getPhysicsWorld(self, zoneId):
        bz = self.getBattleZone(zoneId)
        if bz:
            return bz.physicsWorld
        return None

    def requestDelete(self, do):
        self.sendDeleteMsg(do.doId)

    def deallocateChannel(self, channel):
        pass

    def addAvatar(self, avatar, zoneId = None):
        if zoneId is None:
            if hasattr(avatar, 'getZoneId'):
                zoneId = avatar.getZoneId()
            else:
                zoneId = avatar.zoneId

        if not zoneId in self.avatars:
            self.avatars[zoneId] = []

        if not avatar in self.avatars[zoneId]:
            self.avatars[zoneId].append(avatar)
            self.numAvatars += 1

            if zoneId in self.battleZones:
                print("Adding avatar to battle zone at {0}".format(zoneId))
                avatar.battleZone = self.battleZones[zoneId]
                avatar.addToPhysicsWorld(avatar.battleZone.physicsWorld)

    def removeAvatar(self, avatar):
        removed = False

        zoneOfAv = 0

        for zoneId in self.avatars.keys():
            if avatar in self.avatars[zoneId]:
                self.avatars[zoneId].remove(avatar)
                zoneOfAv = zoneId
                removed = True
                break

        if removed:
            self.numAvatars -= 1

        if avatar.battleZone:
            print("Removing avatar from battle zone at {0}".format(zoneOfAv))
            avatar.removeFromPhysicsWorld(avatar.battleZone.physicsWorld)
            avatar.battleZone = None

    def handleCrash(self, e):
        raise e

    def allocateZone(self):
        return self.zoneAllocator.allocate()

    def deallocateZone(self, zone):
        self.zoneAllocator.free(zone)

    def generateWithRequired(self, do, parentId, zoneId, optionalFields = None):
        self.createDistributedObject(distObj = do, zoneId = zoneId, optionalFields = optionalFields, indirect = True)

    def generateWithRequiredAndId(self, do, doId, parentId, zoneId, optionalFields = None):
        self.createDistributedObject(distObj = do, zoneId = zoneId, optionalFields = optionalFields, doId = doId, reserveDoId = True, indirect = True)

    def createDistributedObject(self, className = None, distObj = None,
                                zoneId = 0, optionalFields = None,
                                doId = None, reserveDoId = False, indirect = False):

        if not className:
            if not distObj:
                self.notify.error("Must specify either a className or a distObj.")
            className = distObj.__class__.__name__

        if doId is None:
            doId = self.allocateDoId()
        elif reserveDoId:
            self.reserveDoId(doId)

        dclass = self.dclassesByName.get(className)
        if not dclass:
            self.notify.error("Unknown distributed class: %s" % (distObj.__class__))
        classDef = dclass.getClassDef()
        if classDef == None:
            self.notify.error("Could not create an undefined %s object." % (
                dclass.getName()))

        if not distObj:
            distObj = classDef(self)
        if not isinstance(distObj, classDef):
            self.notify.error("Object %s is not an instance of %s" % (distObj.__class__.__name__, classDef.__name__))

        distObj.dclass = dclass
        distObj.doId = doId
        self.doId2do[doId] = distObj
        distObj.generateInit()
        distObj._retrieveCachedData()
        if not indirect:
            distObj.generate()
        distObj.setLocation(0, zoneId)
        if not indirect:
            distObj.announceGenerate()
        datagram = self.formatGenerate(distObj, optionalFields)
        self.send(datagram)
        return distObj
