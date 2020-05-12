from panda3d.core import *
from panda3d.direct import *
from networksystem import *
from direct.task import Task
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DoInterestManager import DoInterestManager
from direct.distributed.DoCollectionManager import DoCollectionManager
from direct.showbase import GarbageReport
from direct.distributed.PyDatagramIterator import PyDatagramIterator

from .BaseDOManager import BaseDOManager

import inspect
import gc

__all__ = ["ConnectionRepository", "GCTrigger"]

class ConnectionRepository(
        BaseDOManager):
    """
    This is a base class for things that know how to establish a
    connection (and exchange datagrams) with a gameserver.  This
    includes ClientRepository and AIRepository.

    Note: This version uses the networksystem library provided by
    libpandabsp (which internally uses SteamNetworkingSockets).
    """
    notify = directNotify.newCategory("ConnectionRepository")

    taskPriority = -30
    taskChain = None

    gcNotify = directNotify.newCategory("GarbageCollect")

    GarbageCollectTaskName = "allowGarbageCollect"
    GarbageThresholdTaskName = "adjustGarbageCollectThreshold"

    def __init__(self, config, hasOwnerView = False):
        BaseDOManager.__init__(self, hasOwnerView)

        self.netSys = NetworkSystem()
        self.netCallbacks = NetworkCallbacks()
        self.netCallbacks.setCallback(self.__handleNetCallback)
        self.connected = False
        self.connectionHandle = None
        self.connectSuccessCallback = None
        self.connectFailureCallback = None

        self.msgType = 0

        self.config = config

        # Accept this hook so that we can respond to lost-connection
        # events in the main thread, instead of within the network
        # thread (if there is one).
        self.accept(self._getLostConnectionEvent(), self.lostConnection)

        # This DatagramIterator is constructed once, and then re-used
        # each time we read a datagram.
        self.private__di = PyDatagramIterator()

        self._serverAddress = ''

        self.readerPollTaskObj = None

        if self.config.GetBool('gc-save-all', 1):
            # set gc to preserve every object involved in a cycle, even ones that
            # would normally be freed automatically during garbage collect
            # allows us to find and fix these cycles, reducing or eliminating the
            # need to run garbage collects
            # garbage collection CPU usage is O(n), n = number of Python objects
            gc.set_debug(gc.DEBUG_SAVEALL)

        if self.config.GetBool('want-garbage-collect-task', 1):
            # manual garbage-collect task
            taskMgr.add(self._garbageCollect, self.GarbageCollectTaskName, 200)
            # periodically increase gc threshold if there is no garbage
            taskMgr.doMethodLater(self.config.GetFloat('garbage-threshold-adjust-delay', 5 * 60.),
                                  self._adjustGcThreshold, self.GarbageThresholdTaskName)

        self._gcDefaultThreshold = gc.get_threshold()

    def getMsgType(self):
        return self.msgType

    def _getLostConnectionEvent(self):
        return self.uniqueName('lostConnection')

    def _garbageCollect(self, task=None):
        # allow a collect
        # enable automatic garbage collection
        gc.enable()
        # creating an object with gc enabled causes garbage collection to trigger if appropriate
        gct = GCTrigger()
        # disable the automatic garbage collect during the rest of the frame
        gc.disable()
        return Task.cont

    def _adjustGcThreshold(self, task):
        # do an unconditional collect to make sure gc.garbage has a chance to be
        # populated before we start increasing the auto-collect threshold
        # don't distribute the leak check from the client to the AI, they both
        # do these garbage checks independently over time
        numGarbage = GarbageReport.checkForGarbageLeaks()
        if numGarbage == 0:
            self.gcNotify.debug('no garbage found, doubling gc threshold')
            a, b, c = gc.get_threshold()
            gc.set_threshold(min(a * 2, 1 << 30), b, c)

            task.delayTime = task.delayTime * 2
            retVal = Task.again

        else:
            self.gcNotify.warning('garbage found, reverting gc threshold')
            # the process is producing garbage, stick to the default collection threshold
            gc.set_threshold(*self._gcDefaultThreshold)
            retVal = Task.done

        return retVal

    def getServerAddress(self):
        return self._serverAddress

    def tryConnectSteam(self, url):
        urlSpec = URLSpec(url)
        addr = NetAddress()
        addr.setHost(urlSpec.getServer(), urlSpec.getPort())
        self.connectionHandle = self.netSys.connectByIPAddress(addr)
        if not self.connectionHandle:
            return False
        return True

    def connect(self, serverList,
                successCallback = None, successArgs = [],
                failureCallback = None, failureArgs = []):
        """
        Attempts to establish a connection to the server.  May return
        before the connection is established.  The two callbacks
        represent the two functions to call (and their arguments) on
        success or failure, respectively.  The failure callback also
        gets one additional parameter, which will be passed in first:
        the return status code giving reason for failure, if it is
        known.
        """

        self.notify.info("Connecting to gameserver directly (no proxy).")

        self.bootedIndex = None
        self.bootedText = None

        self.connectSuccessCallback = [successCallback, successArgs]
        self.connectFailureCallback = [failureCallback, failureArgs]

        # Try each of the servers in turn.
        for url in serverList:
            self.notify.info("Connecting to %s via Steam interface." % (url))
            if self.tryConnectSteam(url):
                self.startReaderPollTask()
                if successCallback:
                    successCallback(*successArgs)
                return

        # Failed to connect.
        if failureCallback:
            failureCallback(0, '', *failureArgs)

    def startReaderPollTask(self):
        # Stop any tasks we are running now
        self.stopReaderPollTask()
        #self.accept(CConnectionRepository.getOverflowEventName(),
        #            self.handleReaderOverflow)
        self.readerPollTaskObj = taskMgr.add(
            self.readerPollUntilEmpty, self.uniqueName("readerPollTask"),
            priority = self.taskPriority, taskChain = self.taskChain)

    def stopReaderPollTask(self):
        if self.readerPollTaskObj:
            taskMgr.remove(self.readerPollTaskObj)
            self.readerPollTaskObj = None
        #self.ignore(CConnectionRepository.getOverflowEventName())

    def readerPollUntilEmpty(self, task):
        if self.connected:
            while self.readerPollOnce():
                pass
        self.netSys.runCallbacks(self.netCallbacks)
        return Task.cont

    def readerPollOnce(self):
        msg = NetworkMessage()
        if self.netSys.receiveMessageOnConnection(self.connectionHandle, msg):
            self.msgType = msg.getDatagramIterator().getUint16()
            self.handleDatagram(msg.getDatagramIterator())
            return 1

        return 0

    def __handleNetCallback(self, conn, state, oldState):
        # Connection state has changed.

        # We've successfully connected.
        if state == NetworkSystem.NCSConnected:
            self.connected = True
            if self.connectSuccessCallback and self.connectSuccessCallback[0]:
                self.connectSuccessCallback[0](*self.connectSuccessCallback[1])
                self.connectSuccessCallback = None

        # If state was connecting and new state is not connected, we failed!
        elif oldState == NetworkSystem.NCSConnecting:
            self.connected = False
            if self.connectFailureCallback and self.connectFailureCallback[0]:
                self.connectFailureCallback[0](*self.connectFailureCallback[1])
                self.connectFailureCallback = None

        # Lost connection?
        elif state == NetworkSystem.NCSClosedByPeer or \
            state == NetworkSystem.NCSProblemDetectedLocally:

            self.connected = False
            self.stopReaderPollTask()
            messenger.send(self._getLostConnectionEvent(), taskChain = 'default')
            self.lostConnection()

    def lostConnection(self):
        # This should be overrided by a derived class to handle an
        # unexpectedly lost connection to the gameserver.
        self.notify.warning("Lost connection to gameserver.")

    def handleDatagram(self, di):
        # This class is meant to be pure virtual, and any classes that
        # inherit from it need to make their own handleDatagram method
        pass

    def send(self, datagram):
        # Zero-length datagrams might freak out the server.  No point
        # in sending them, anyway.
        if datagram.getLength() > 0:
##             if self.notify.getDebug():
##                 print "ConnectionRepository sending datagram:"
##                 datagram.dumpHex(ostream)

            self.netSys.sendDatagram(self.connectionHandle, datagram, NetworkSystem.NSFReliableNoNagle)

    def isConnected(self):
        return self.connected

    def disconnect(self):
        """
        Closes the previously-established connection.
        """
        self.notify.info("Closing connection to server.")
        self._serverAddress = ''
        if self.connectionHandle:
            self.netSys.closeConnection(self.connectionHandle)
        self.connectionHandle = None
        self.connected = False
        #CConnectionRepository.disconnect(self)
        self.stopReaderPollTask()

    def shutdown(self):
        self.ignoreAll()
        self.disconnect()
        #CConnectionRepository.shutdown(self)

class GCTrigger:
    # used to trigger garbage collection
    pass
