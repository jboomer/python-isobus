import can
import random #randint
import math # ceil
import time #sleep

from isobus.numvalue import NumericValue
from isobus.ibsid import IBSID
from isobus.constants import *
from isobus.log import log
from isobus.common import IBSException

from can.interfaces.interface import Bus



class IBSInterface():
    """
    Implements general ISOBUS functionality
    """

    def __init__(self, interface, channel):

        can.rc['interface'] = interface
        can.rc['channel'] = channel
        log.info('Opening CAN connection on {0}'.format(
            can.rc['channel']))
        self.bus = Bus()
        self.periodic_tasks = list()

    def __del__(self):
        self.bus.shutdown()

    def AddPeriodicMessage(self, ibsid, contents, period):
        # For socketcan_native, bit 32 (MSb) needs to be set for extended ID
        # Is fixed in latest python-can though!
        msg = can.Message(arbitration_id=(ibsid.GetCANID() | (1 << 31)),
                          data=contents,
                          extended_id=True)
        self.periodic_tasks.append(can.send_periodic(can.rc['channel'], msg, period))

    def StopPeriodicMessage(self, ibsid):
        # For socketcan_native, bit 32 (MSb) needs to be set for extended ID
        # Is fixed in latest python-can though!
        for periodMsg in self.periodic_tasks:
            if periodMsg.can_id == (ibsid.GetCANID() | (1 << 31)):
                self.periodic_tasks.remove(periodMsg)
                periodMsg.stop()
                break

    def ModifyPeriodicMessage(self, ibsid, newContent):
        # For socketcan_native, bit 32 (MSb) needs to be set for extended ID
        # Is fixed in latest python-can though!
        msg = can.Message(arbitration_id=(ibsid.GetCANID() | (1 << 31)),
                          data=newContent,
                          extended_id=True)
        for periodMsg in self.periodic_task:
            if periodMsg.can_id == canid:
                periodMsg.modify_data(self, msg)
                break

    def ClaimAddress(self, sa, ibsName):
        # TODO: Check if SA is not already claimed
        # TODO: Handle configurable address?
        self._SendRequestAddressClaim(sa)
        waittime = 250 + (random.randint(0, 255) * 0.6)
        time.sleep(waittime / 1000.0)
        self._SendAddressClaim(ibsName, sa)
        time.sleep(0.250)


    ## PROTECTED FUNCTIONS
    def _SendRequestAddressClaim(self, sa):
        log.debug('Sending Request Address Claim')
        self._SendRequest(sa, da=SA_GLOBAL, reqPGN=PGN_ADDRCLAIM)

    def _SendAddressClaim(self, ibsName, sa):
        log.debug('Sending Address claim for name {:016X}'.format(
            ibsName))
        candata = NumericValue(ibsName).AsLEBytes(8)
        self._SendIBSMessage(PGN_ADDRCLAIM, SA_GLOBAL, sa, candata)

    def _SendRequest(self, sa, da, reqPGN):
        self._SendIBSMessage(PGN_REQUEST, sa, da, NumericValue(reqPGN).AsLEBytes(3))

    def _SendCANMessage(self, canid, candata):
        if len(candata) <= 8:
            msg = can.Message(arbitration_id=canid,
                              data=candata,
                              extended_id=True)
            try:
                self.bus.send(msg)
            except can.CanError:
                log.warning('Error sending message')

    def _WaitForIBSMessage(self, pgn, fromsa, tosa, muxByte, maxtime=3.0):
        # TODO: Also accept incoming TP session
        # TODO: Can we miss messages because we start listening too late?

        received = False
        data = [RESERVED] * 8 # Dummy data for when nothing is received
        starttime = time.time()
        matchID = IBSID(da = tosa, sa = fromsa, pgn = pgn, prio = 6)
        while not(received):
            mesg = self.bus.recv(0.5)
            if mesg is not None:
                receivedID = IBSID.FromCANID(mesg.arbitration_id)
                if (receivedID.pgn == matchID.pgn
               and receivedID.da  == matchID.da
               and receivedID.sa  == matchID.sa
               and mesg.data[0]   == muxByte):
                    received= True
                    data = mesg.data
                    break
            if (time.time() - starttime) > maxtime:
                break

        return received, data 

    def _SendIBSMessage(self, pgn, da, sa, data, prio=6):
        if len(data) <= 8:
            canid = IBSID(da, sa, pgn, prio).GetCANID()
            self._SendCANMessage(canid, data)
        elif len(data) <= 1785:
            self._SendTPMessage(pgn, da, sa, data)
        elif len(data) <= 117440505:
            self._SendETPMessage(pgn, da, sa, data)
        else:
            log.warning('ERROR : CAN message too large to send')

    def _SendTPMessage(self, pgn, da, sa, data):
        tpcm_id = IBSID(da, sa, pgn=PGN_TP_CM, prio=6)
        tpdt_id = IBSID(da, sa, pgn=PGN_TP_DT, prio=7)

        # Send RTS
        rts_control = 0x10
        nr_of_packets = int(math.ceil(len(data) / 7.0))
        rts_data = ([rts_control] 
                    + NumericValue(len(data)).AsLEBytes(2) 
                    + [nr_of_packets, RESERVED]
                    + NumericValue(pgn).AsLEBytes(3))

        log.debug('Sending RTS for PGN {0} : {1} bytes in {2} packets'.format(
            pgn, len(data), nr_of_packets))
        self._SendCANMessage(tpcm_id.GetCANID(), rts_data)

        # Check the CTS
        [received, ctsdata] = self._WaitForIBSMessage(0xEC00, da, sa, 0x11)
        if received:
            log.debug('Received CTS for max {0} packets, next packet {1}'.format(
                ctsdata[1], ctsdata[2]))

        else:
            return False

        
        # Pack with 0xFF
        if len(data) % 7 > 0:
            data = data + list([RESERVED] * (7 - (len(data) % 7)))


        # Send bytes
        for seqN in range(nr_of_packets):
            startByte = seqN * 7
            self._SendCANMessage(tpdt_id.GetCANID(), [seqN + 1] + data[startByte:startByte + 7])
            # sleep 1 msec, otherwise hardware buffer gets full!
            time.sleep(0.001)


    def _SendETPMessage(self, pgn, da, sa, data):
        etpcm_id = IBSID(da, sa, PGN_ETP_CM, prio=6)
        etpdt_id = IBSID(da, sa, PGN_ETP_DT, prio=7)

        mesg_size = len(data)

        # Send RTS
        rts_control = 0x14
        totalPackets = int(math.ceil(len(data) / 7.0))

        log.debug("ETP : Sending {0} bytes in {1} packets".format(
                len(data), totalPackets))

        rts_data = ([rts_control]
                    + NumericValue(mesg_size).AsLEBytes(4)
                    + NumericValue(pgn).AsLEBytes(3)
                   ) 
        self._SendCANMessage(etpcm_id.GetCANID(), rts_data)
        
        # Pack data with 0xFF to multiple of 7
        if len(data) % 7 > 0:
            data = data + list([RESERVED] * (7 - (len(data) % 7)))

        
        # Setup for the data transfer
        nextPacket = 1
        maxSentPackets = 0
        done = False

        while not(done):
            # TODO: What is the time out for this one?
            [received, ctsdata] = self._WaitForIBSMessage(0xC800, da, sa, 0x15)
            if received:
                nextPacket = NumericValue.FromLEBytes(ctsdata[2:5]).Value()
                maxSentPackets = ctsdata[1]
                log.debug("ETP : Received CTS for max {0} packets, next packet {1}".format(
                    maxSentPackets, nextPacket)
                    )
            else :
                log.warning('ETP : Wait for CTS timed out')
                break
            
            packetOffset = nextPacket - 1
            
            nPackets = min(maxSentPackets, totalPackets - packetOffset)

            log.debug('ETP : Sending {0} packets with packet offset {1}'.format(
                nPackets, packetOffset))
            log.debug('ETP : bytes[{0} - {1}]'.format(
                packetOffset * 7, packetOffset * 7 + nPackets * 7 - 1))

            dpoData = ([0x16]
                       + [nPackets]
                       + NumericValue(packetOffset).AsLEBytes(3)
                       + NumericValue(pgn).AsLEBytes(3))
            self._SendCANMessage(etpcm_id.GetCANID(), dpoData)

            for n in range(nPackets) :
                startByte = (n * 7) + (packetOffset * 7)
                # Send send data[n * 7 + dataoffset: n* 7 +7 + dataoffset]
                self._SendCANMessage(etpdt_id.GetCANID(), [n + 1] + data[startByte:startByte+7])

                 # If it is the last packet, quit the loop
                if (n + nextPacket) >= totalPackets:
                    done = True
                    break

                time.sleep(0.001)

        # TODO: Optionally wait for EOMA
