import can
import random #randint
import math # ceil
import time #sleep

from isobus.numvalue import NumericValue

INTERFACE = 'socketcan_native'
CHANNEL = 'vcan0'

can.rc['interface'] = INTERFACE
can.rc['channel'] = CHANNEL

from can.interfaces.interface import Bus

class IBSInterface():
    """
    Implements general ISOBUS functionality
    """

    def __init__(self):
        print("Opening CAN connection on {0}".format(
            can.rc['channel']))
        self.bus = Bus()
        self.periodic_tasks = list()

    def __del__(self):
        print("Closing CAN connection on {0}".format(
            can.rc['channel']))
        self.bus.shutdown()

    # TODO: Have pgn,sa and da arguments instead for periodic message functions
    def AddPeriodicMessage(self, canid, contents, period):
        msg = can.Message(arbitration_id=canid,
                          data=contents,
                          extended_id=True)
        self.periodic_tasks.append(can.send_periodic(CHANNEL, msg, period))

    def StopPeriodicMessage(self, canid):
        for periodMsg in self.periodic_tasks:
            if periodMsg.can_id == canid:
                self.periodic_tasks.remove(periodMsg)
                periodMsg.stop()
                break

    def ModifyPeriodicMessage(self, canid, newContent):
        msg = can.Message(arbitration_id=canid,
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
        print("Sending Request Address Claim")
        self._SendRequest(sa, da=0xFF, reqPGN=0xEE00)

    def _SendAddressClaim(self, ibsName, sa):
        print("Sending Address claim for name {:016X}".format(
            ibsName))
        candata = NumericValue(ibsName).AsLEBytes(8)
        self._SendIBSMessage(0xEE00, 0xFF, sa, candata)

    def _SendRequest(self, sa, da, reqPGN):
        self._SendIBSMessage(0xEA00, sa, da, NumericValue(reqPGN).AsLEBytes(3))

    def _SendCANMessage(self, canid, candata):
        if len(candata) <= 8:
            msg = can.Message(arbitration_id=canid,
                              data=candata,
                              extended_id=True)
            try:
                self.bus.send(msg)
            except can.CanError:
                print("Error sending message")

    def _WaitForIBSMessage(self, pgn, fromsa, tosa, muxByte, maxtime=3.0):
        # TODO: Also accept incoming TP session
        # TODO: Can we miss messages because we start listening too late?

        received = False
        data = [0xFF] * 8 # Dummy data for when nothing is received
        starttime = time.time()
        while not(received):
            mesg = self.bus.recv(0.5)
            if mesg is not None:
                if (((mesg.arbitration_id >> 8) & 0xFFFF) == (pgn | (tosa & 0xFF))
                        and (mesg.arbitration_id & 0xFF) == fromsa
                        and mesg.data[0] == muxByte):
                    received= True
                    data = mesg.data
                    break
            if (time.time() - starttime) > maxtime:
                break

        return received, data 

    def _SendIBSMessage(self, pgn, da, sa, data, prio=6):
        if len(data) <= 8:
            canid = 0
            if ((pgn >> 8) & 0xFF) < 0xEF:
                # PDU1
                canid = (((prio & 0x7) << 26)
                        | ((pgn & 0xFF00) << 8) 
                        | ((da & 0xFF) << 8)
                        | (sa & 0xFF))
            else :
                # PDU2
                canid = (((prio & 0x7) << 26)
                        | ((pgn & 0xFFFF) << 8) 
                        | (sa & 0xFF))

            self._SendCANMessage(canid, data)
        elif len(data) <= 1785:
            self._SendTPMessage(pgn, da, sa, data)
        elif len(data) <= 117440505:
            self._SendETPMessage(pgn, da, sa, data)
        else:
            print("ERROR : CAN message too large to send")

    def _SendTPMessage(self, pgn, da, sa, data):
        tpcm_id = 0x18EC0000 | ((da & 0xFF) << 8) | (sa & 0xFF)
        tpdt_id = 0x18EB0000 | ((da & 0xFF) << 8) | (sa & 0xFF)

        # Send RTS
        rts_control = 0x10
        nr_of_packets = int(math.ceil(len(data) / 7.0))
        rts_data = ([rts_control] 
                    + NumericValue(len(data)).AsLEBytes(2) 
                    + [nr_of_packets, 0xFF]
                    + NumericValue(pgn).AsLEBytes(3))

        print("Sending RTS for PGN {0} : {1} bytes in {2} packets".format(
            pgn, len(data), nr_of_packets))
        self._SendCANMessage(tpcm_id, rts_data)

        # Check the CTS
        [received, ctsdata] = self._WaitForIBSMessage(0xEC00, da, sa, 0x11)
        if received:
            print("Received CTS for max {0} packets, next packet {1}".format(
                ctsdata[1], ctsdata[2]))

        else:
            return False

        
        # Pack with 0xFF
        if len(data) % 7 > 0:
            data = data + list([0xFF] * (7 - (len(data) % 7)))


        # Send bytes
        for seqN in range(nr_of_packets):
            self._SendCANMessage(tpdt_id, [seqN + 1] + data[seqN * 7:seqN * 7 + 7])
            # sleep 1 msec, otherwise hardware buffer gets full!
            time.sleep(0.001)


    def _SendETPMessage(self, pgn, da, sa, data):
        etpcm_id = 0x18C80000 | ((da & 0xFF) << 8) | (sa & 0xFF)
        etpdt_id = 0x18C70000 | ((da & 0xFF) << 8) | (sa & 0xFF)

        mesg_size = len(data)

        # Send RTS
        rts_control = 0x14
        totalPackets = int(math.ceil(len(data) / 7.0))

        print("ETP : Sending {0} bytes in {1} packets".format(
                len(data), totalPackets))

        rts_data = ([rts_control]
                    + NumericValue(mesg_size).AsLEBytes(4)
                    + NumericValue(pgn).AsLEBytes(3)
                   ) 
        self._SendCANMessage(etpcm_id, rts_data)
        
        # Pack data with 0xFF to multiple of 7
        if len(data) % 7 > 0:
            data = data + list([0xFF] * (7 - (len(data) % 7)))

        
        # Setup for the data transfer
        nextPacket = 1
        maxSentPackets = 0
        done = False

        while not(done):
            # TODO: What is the time out for this one?
            [received, ctsdata] = self._WaitForIBSMessage(0xC800, da, sa, 0x15)
            if received:
              #  nextPacket = (ctsdata[4] << 16) | (ctsdata[3] << 8) | (ctsdata[2])
                nextPacket = NumericValue.FromLEBytes(ctsdata[2:5]).Value()
                maxSentPackets = ctsdata[1]
                print("ETP : Received CTS for max {0} packets, next packet {1}".format(
                    maxSentPackets, nextPacket)
                    )
            else :
                print("ETP : Wait for CTS timed out")
                break
            
            packetOffset = nextPacket - 1
            
            nPackets = min(maxSentPackets, totalPackets - packetOffset)

            print("ETP : Sending {0} packets with packet offset {1}".format(
                nPackets, packetOffset))
            print("ETP : bytes[{0} - {1}]".format(
                packetOffset * 7, packetOffset * 7 + nPackets * 7 - 1))

            dpoData = ([0x16]
                       + [nPackets]
                       + NumericValue(packetOffset).AsLEBytes(3)
                       + NumericValue(pgn).AsLEBytes(3))
            self._SendCANMessage(etpcm_id, dpoData)

            for n in range(nPackets) :
                startByte = (n * 7) + (packetOffset * 7)
                # Send send data[n * 7 + dataoffset: n* 7 +7 + dataoffset]
                self._SendCANMessage(etpdt_id, [n + 1] + data[startByte:startByte+7])

                 # If it is the last packet, quit the loop
                if (n + nextPacket) >= totalPackets:
                    done = True
                    break

                time.sleep(0.001)

        # TODO: Optionally wait for EOMA
