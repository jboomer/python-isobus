from isobus import pgn
from isobus.numvalue import NumericValue
from isobus.ibsinterface import IBSInterface


class IBSVTInterface(IBSInterface):
    """ Implements ISOBUS part 6 funcationality (Version 3)
    Extends the ISOBUS general interface
    """

    def WaitForStatusMessage(self, vtsa):
        return self._WaitForIBSMessage(pgn.VT2ECU, vtsa, 0xFF, 0xFE)

    def SendChangeActiveMask(self, wsid, maskid, sa, da):
        candata = ([0xAD] 
        + NumericValue(wsid).AsLEBytes(2) 
        + NumericValue(maskid).AsLEBytes(2)
        + [0xFF, 0xFF, 0xFF])

        self._SendIBSMessage(pgn.ECU2VT, da, sa, candata)

    def WaitForChangeActiveMaskResponse(self, vtsa, ecusa):
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xAD)
        return received, NumericValue.FromLEBytes(data[1:3]).Value(), data[3]

    def SendChangeSKMask(self, maskid, skmaskid, alarm, vtsa, ecusa):
        candata = [0xFF] * 8
        if alarm:
            candata = ([0xAE] 
            + [0x02] 
            + NumericValue(maskid).AsLEBytes(2)
            + NumericValue(skmaskid).AsLEBytes(2)
            + [0xFF, 0xFF])
        else:
            candata = ([0xAE] 
            + [0x01] 
            + NumericValue(maskid).AsLEBytes(2)
            + NumericValue(skmaskid).AsLEBytes(2)
            + [0xFF, 0xFF])

        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, candata)

    def WaitForChangeSKMaskResponse(self, vtsa, ecusa):
        """ Wait for the Change Soft Key Mask response message
        Return True for received, error code, and new SK mask ID
        """
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xAE)
        return received, data[5], NumericValue.FromLEBytes(data[3:5]).Value()


    def SendChangeAttribute(self, objid, attrid, value, vtsa, ecusa):
        candata = ([0xAF]
                + NumericValue(objid).AsLEBytes(2)
                + NumericValue(attrid).AsLEBytes(1)
                + NumericValue(value).AsLEBytes(4))

        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, candata)

    def WaitChangeAttributeResponse(self, vtsa, ecusa):
        """
        Wait for a response for the change attribute command
        Return True for received and Error code
        """
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xAF)
        return received, data[4]

    def SendEscCommand(self, vtsa, ecusa):
        candata = [0x92] + (7 * [0xFF])
        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, candata)

    def WaitForESCResponse(self, vtsa, ecusa):
        """
        Wait for ESC response
        @return True for received, error code and aborted input object ID
        """
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0x92)
        return received, data[3], NumericValue.FromLEBytes(data[1:3]).Value()

    def SendWSMaintenance(self, initiating, sa, da):
        initBit = 0
        if (initiating) :
            initBit = 1

        candata = [0xFF, (initBit & 0x1), 0x3, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self._SendIBSMessage(pgn.ECU2VT, da, sa, candata)

    def StartWSMaintenace(self, sa, da):
        # For socketcan_native, bit 32 (MSb) needs to be set for extended ID
        # Is fixed in latest python-can though!
        canid = 0x98E70000 | ((da & 0xFF) << 8) | (sa & 0xFF)
        candata = [0xFF, 0x00, 0x3, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.AddPeriodicMessage(canid, candata, 1.0)
        
    def StopWSMaintenance(self, sa, da):
        # For socketcan_native, bit 32 (MSb) needs to be set for extended ID
        # Is fixed in latest python-can though!
        canid = 0x98E70000 | ((da & 0xFF) << 8) | (sa & 0xFF)
        self.StopPeriodicMessage(canid)
        
    def SendLoadVersionCommand(self, version, sa, da):
        if len(version) == 7:
            candata = [0xD1] + [ord(x) for x in version]
            self._SendIBSMessage(pgn.ECU2VT, da, sa, candata)
        else :
            print("Version {0} is not 7 characters".format(
                    version))

    def SendStoreVersioncommand(self, version, da, sa):
        if len(version) == 7:
            candata = [0xD0] + [ord(x) for x in version]
            self._SendIBSMessage(pgn.ECU2VT, da, sa, candata)
        else :
            print("Version {0} is not 7 characters".format(
                    version))

    def WaitLoadVersionResponse(self, vtsa, ecusa):
        #TODO: Should wait 3 status messages w/parsing bit=0 i.o. 3 seconds
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xD1)
        return received, data[5]
    
    def WaitStoreVersionResponse(self, vtsa, ecusa):
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xD0)
        return received, data[5]
    
    def SendGetMemory(self, memRequired, vtsa, ecusa):
       candata = (  [0xC0, 0xFF] 
                  + NumericValue(memRequired).AsLEBytes(4)
                  + [0xFF, 0xFF])
       self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, candata)

    def WaitForGetMemoryResponse(self, vtsa, ecusa):
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xC0)
        version = data[1]
        enoughMemory = True
        if data[2] == 0x01:
            enoughMemory = False
        return received, version, enoughMemory

    def SendChangeNumericValue(self, objid, value, vtsa, ecusa):
        candata =([0xA8] 
                + NumericValue(objid).AsLEBytes(2) 
                + [0xFF]
                + NumericValue(value).AsLEBytes(4))
        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, candata)

    def WaitForChangeNumericValueResponse(self, vtsa, ecusa):
        """
        Return true for received, error code
        """
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xA8)
        return received, data[3]
    
    def SendPoolUpload(self, vtsa, ecusa, pooldata):
        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, [0x11] + pooldata)

    def SendEndOfObjectPool(self, vtsa, ecusa):
        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, [0x12] + [0xFF] * 7)

    def WaitEndOfObjectPoolResponse(self, vtsa, ecusa):
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0x12)
        return received, data[1]
        # TODO: Return error codes + faulty objects?

    def SendDeleteObjectPool(self, vtsa, ecusa):
        self._SendIBSMessage(pgn.ECU2VT, vtsa, ecusa, [0xB2] + (7 * [0xFF]))
    
    def WaitDeleteObjectPoolResponse(self, vtsa, ecusa):
        [received, data] = self._WaitForIBSMessage(pgn.VT2ECU, vtsa, ecusa, 0xB2)
        return received, data[1]

    def SendIdentifyVT(self, sa):
        self._SendIBSMessage(pgn.ECU2VT, 0xFF, sa, [0xBB] + (7 * [0xFF]))


