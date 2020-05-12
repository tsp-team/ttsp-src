from src.mod.distributed.ServerRepository import ServerRepository
from direct.distributed.MsgTypesCMU import *
from direct.distributed.PyDatagram import PyDatagram
from panda3d.core import DatagramIterator, PointerToConnection, NetAddress

from src.mod.ModMsgTypes import *

class ModServerRepository(ServerRepository):

    class ClientSnapshotObject:

        def __init__(self, doId):
            self.doId = doId
            self.dg = PyDatagram()
            self.numUpdates = 0

        def addUpdate(self, dg):
            self.dg.appendData(dg.getData(), dg.getLength())
            self.numUpdates += 1

    class ClientSnapshot:

        def __init__(self, client):
            self.client = client
            self.objects = {}        
    
    def __init__(self, *args, **kwargs):
        ServerRepository.__init__(self, *args, **kwargs)
        self.aiClients = []
        
        self.queuedClients = []
        self.clientsSignedOn = []

        # Per client snapshots we are working on this tick
        self.clientSnapshots = {}

    def sendClientSnapshots(self):
        for client, snapshot in self.clientSnapshots.items():
            
            dg = PyDatagram()
            dg.addUint16(AI_SNAPSHOT_CMU)
            numObjects = len(snapshot.objects)
            dg.addUint16(numObjects)
            for doId, obj in snapshot.objects.items():
                dg.addUint32(doId)
                dg.addUint16(obj.numUpdates)
                dg.appendData(obj.dg.getData(), obj.dg.getLength())
    
    def handleMessageType(self, client, type, dgi):
        if type == AI_HELLO_CMU:
            self.handleAIHello(client)
        elif type == CLIENT_HELLO_CMU:
            self.handleClientHello(client)
        else:
            self.notify.warning("Received unknown message type: " + str(type))
    
    def handleClientSetInterest(self, client, dgi):
        ServerRepository.handleClientSetInterest(self, client, dgi)
        
        # Tell the client we've completed the interest operation
        # This message should arrive after all new objects generate.
        dg = PyDatagram()
        dg.addUint16(SET_INTEREST_COMPLETE_CMU)
        self.sendDatagram(dg, client.connection)
        
    def handleAIHello(self, client):
        if client in self.aiClients:
            return
            
        print "Adding new AI client", client
        self.aiClients.append(client)
        self.__assignClientDoIdRange(client)
        
    def handleClientHello(self, client):
        print "Client hello", client.connection
        if (client not in self.queuedClients) and (client not in self.clientsSignedOn):
            self.queuedClients.append(client)
            self.clientsSignedOn.append(client)
        
    def __assignClientDoIdRange(self, client):
        #  Add clients information to dictionary
        id = self.idAllocator.allocate()
        doIdBase = id * self.doIdRange + 1
        print "Assigning id %s to client %s" % (doIdBase, client.netAddress)
        client.doIdBase = doIdBase
        self.clientsByDoIdBase[client.doIdBase] = client
        self.sendDoIdRange(client)
        
    def __processClientQueue(self):
        if len(self.aiClients) == 0:
            # Can't do it yet, still awaiting an AI.
            if len(self.queuedClients) > 0:
                print "Awaiting AI to process new clients..."
            return
        
        for client in self.queuedClients:
            self.__assignClientDoIdRange(client)
        self.queuedClients = []
        
    # listens for new clients

    def _handleNewConnection(self, newConnection, info):
        self.notify.info(
            "Got client from %s" % (info.netAddress))

        self.lastConnection = newConnection
        client = self.Client(newConnection, info.netAddress, 0)
        self.clientsByConnection[client.connection] = client

    def readerPollUntilEmpty(self, task):
        self.__processClientQueue()

        return ServerRepository.readerPollUntilEmpty(self, task)
    
    def handleClientObjectUpdateField(self, client, datagram, dgi, targeted = False):
        """ Received an update request from a client. """
        if targeted:
            targetId = dgi.getUint32()
        doId = dgi.getUint32()
        fieldId = dgi.getUint16()

        doIdBase = self.getDoIdBase(doId)
        owner = self.clientsByDoIdBase.get(doIdBase)
        object = owner and owner.objectsByDoId.get(doId)
        if not object:
            self.notify.warning(
                "Ignoring update for unknown object %s from client %s" % (
                doId, client.doIdBase))
            return

        dcfield = object.dclass.getFieldByIndex(fieldId)
        if dcfield == None:
            self.notify.warning(
                "Ignoring update for field %s on object %s from client %s; no such field for class %s." % (
                fieldId, doId, client.doIdBase, object.dclass.getName()))

        if client != owner and not client in self.aiClients:
            # This message was not sent by the object's owner.
            if not dcfield.hasKeyword('clsend') and not dcfield.hasKeyword('p2p') and not dcfield.hasKeyword('ownsend'):
                self.notify.warning(
                    "Ignoring update for %s.%s on object %s from client %s: not owner" % (
                    object.dclass.getName(), dcfield.getName(), doId, client.doIdBase))
                return

        # We reformat the message slightly to insert the sender's
        # doIdBase.
        dg = PyDatagram()
        dg.addUint16(OBJECT_UPDATE_FIELD_CMU)
        dg.addUint32(client.doIdBase)
        dg.addUint32(doId)
        dg.addUint16(fieldId)
        dg.appendData(dgi.getRemainingBytes())

        if targeted:
            # A targeted update: only to the indicated client.
            target = self.clientsByDoIdBase.get(targetId)
            if not target:
                self.notify.warning(
                    "Ignoring targeted update to %s for %s.%s on object %s from client %s: target not known" % (
                    targetId,
                    dclass.getName(), dcfield.getName(), doId, client.doIdBase))
                return
            self.sendDatagram(dg, target.connection)

        elif dcfield.hasKeyword('broadcast'):
            # Broadcast: to everyone except orig sender
            self.sendToZoneExcept(object.zoneId, dg, [client])

        elif dcfield.hasKeyword('reflect'):
            # Reflect: broadcast to everyone including orig sender
            self.sendToZoneExcept(object.zoneId, dg, [])
            
        elif dcfield.hasKeyword('airecv'):
            # AI should receive this message
            ai = self.aiClients[0]
            self.sendDatagram(dg, ai.connection)
            
        elif client != owner or dcfield.hasKeyword('ownrecv'):
            # to object owner only
            self.sendDatagram(dg, owner.connection)
            
    def handleDatagram(self, msg):
        """ switching station for messages """

        datagram = msg.getDatagram()
        connection = msg.getConnection()
        client = self.clientsByConnection.get(msg.getConnection())

        if not client:
            # This shouldn't be possible, though it appears to happen
            # sometimes?
            self.notify.warning(
                "Ignoring datagram from unknown connection %s" % (msg.getConnection()))
            return

        if self.notify.getDebug():
            self.notify.debug(
                "ServerRepository received datagram from %s:" % (client.doIdBase))
            #datagram.dumpHex(ostream)

        dgi = DatagramIterator(datagram)

        type = dgi.getUint16()

        if type == CLIENT_DISCONNECT_CMU:
            self.handleClientDisconnect(client)
        elif type == CLIENT_SET_INTEREST_CMU:
            self.handleClientSetInterest(client, dgi)
        elif type == CLIENT_OBJECT_GENERATE_CMU:
            self.handleClientCreateObject(client, datagram, dgi)
        elif type == CLIENT_OBJECT_UPDATE_FIELD:
            self.handleClientObjectUpdateField(client, datagram, dgi)
        elif type == CLIENT_OBJECT_UPDATE_FIELD_TARGETED_CMU:
            self.handleClientObjectUpdateField(client, datagram, dgi, targeted = True)
        elif type == OBJECT_DELETE_CMU:
            self.handleClientDeleteObject(client, datagram, dgi.getUint32())
        elif type == OBJECT_SET_ZONE_CMU:
            self.handleClientObjectSetZone(client, datagram, dgi)
        else:
            self.handleMessageType(client, type, dgi)
