import time
from isobus.vt.interface import IBSVTInterface
from isobus.common import IBSException
from isobus.log import log
from isobus.ibsinterface import IBSRxHandler
from isobus.cf import IBSControlFunction
from isobus.cf import BuildISOBUSName

class VTClient(IBSControlFunction):
    """VT Client (implement) simulation"""
    
    # Return True or False on commands based on success

    def __init__(self, interface, channel) :
        self.connection = IBSVTInterface(interface, channel)
        self.sa = 0xFE
        self.da = 0xFF
        self.alive = False
        self.functionInstance = 0x00

    def SetSrc(self, sa):
        if sa >= 0 and sa <= 0xFE:
            self.sa = sa

    def ConnectToVT(self, da):
        gotStatus, _ = self.connection.WaitForStatusMessage(da)
        ibsName = BuildISOBUSName(functionInstance = self.functionInstance)
        if gotStatus:
            self.ClaimAddress(self.sa, ibsName)
            self.connection.SendWSMaintenance(True, self.sa, da)
            time.sleep(0.5)
            self.connection.StartWSMaintenace(self.sa, da)
            self.alive = True
            self.da = da
        else:
            raise IBSException("Failed to connect to VT")

    def LoadVersion(self, version):
        self._CheckAlive()

        self.connection.SendLoadVersionCommand(version, self.sa, self.da)
        log.debug('Loading version {0}...'.format(version))
        
        # TODO wait for load version response max 3 status messages w/parsing = 0
        [receivedResponse, error] = self.connection.WaitLoadVersionResponse(self.da, self.sa)
        if receivedResponse and (error == 0):
            pass
        else:
            raise IBSException("Did not load version, error code: {0}".format(error))

    def StoreVersion(self, version):
        self._CheckAlive()
        log.debug('Storing version {0}'.format(version))

        self.connection.SendStoreVersioncommand(version, self.da, self.sa)
        
        # TODO wait for load version response max 3 status messages w/parsing = 0
        [receivedResponse, error] = self.connection.WaitStoreVersionResponse(self.da, self.sa)
        if receivedResponse and (error == 0):
            pass
        else:
            raise IBSException("Did not store version, error code: {0}".format(error))


    def UploadPoolData(self, data, eoop=True):
        self._CheckAlive()

        self.connection.SendGetMemory(len(data), self.da, self.sa)
        [receivedMemResp, version, enoughMemory] = self.connection.WaitForGetMemoryResponse(
                self.da, self.sa)

        if receivedMemResp and enoughMemory:

            self.connection.SendPoolUpload(self.da, self.sa, data)

            if eoop:
                self.connection.SendEndOfObjectPool(self.da, self.sa)
                [received, error] = self.connection.WaitEndOfObjectPoolResponse(
                        self.da, self.sa)
                if received and error == 0:
                    pass
                elif received:
                    raise IBSException("Received error code {0}".format(error))
                else:
                    raise IBSException("EoOP Response timed out")
        elif receivedMemResp:
            raise IBSException('Not enough memory available')
        else:
            raise IBSException('No Get Memory Response received')



    def DeleteObjectPool(self):
        self._CheckAlive()

        self.connection.SendDeleteObjectPool(self.da, self.sa)

        # TODO wait for load version response max 3 status messages w/parsing = 0
        [receivedResponse, error] = self.connection.WaitDeleteObjectPoolResponse(
                self.da, self.sa)
        if receivedResponse and (error == 0):
            pass
        elif receivedResponse:
            raise IBSException("Got error: {0}".format(error))
        else:
            raise IBSException("Response timed out")



    def ChangeActiveMask(self, wsid, maskid):
        self._CheckAlive()

        self.connection.SendChangeActiveMask(wsid, maskid, self.sa, self.da)

        [receivedResponse, newMaskID, error] = (
                self.connection.WaitForChangeActiveMaskResponse(self.da, self.sa))

        if receivedResponse and (error == 0):
            log.debug("New active mask = 0X{:04X}".format(newMaskID))
            ret = True
        elif receivedResponse:
            raise IBSException("Error change active mask, error code: {0}".format(error))
        else:
            raise IBSException("No response received")


    def ChangeSKMask(self, maskid, skmaskid, alarm=False):
        self._CheckAlive()

        self.connection.SendChangeSKMask(maskid, skmaskid, alarm, self.da, self.sa)

        [receivedResponse, error, newSKMaskID] = (
                self.connection.WaitForChangeSKMaskResponse(self.da, self.sa))
        if receivedResponse and (error == 0):
            return newSKMaskID
        elif receivedResponse:
            raise IBSException("Error change active mask, error code: {0}".format(error))
        else:
            raise IBSException("No response received")


    def ChangeAttribute(self, objid, attrid, value):
        self._CheckAlive()

        self.connection.SendChangeAttribute(objid, attrid, value, self.da, self.sa)

        [receivedResponse, error] = (
                self.connection.WaitChangeAttributeResponse(self.da, self.sa))

        if receivedResponse and (error == 0):
            pass
        elif receivedResponse:
            raise IBSException("Error change attribute, error code: {0}".format(error))
        else:
            raise IBSException("No response received")


    def ChangeNumericValue(self, objid, value):
        self._CheckAlive()

        self.connection.SendChangeNumericValue(objid, value, vtsa = self.da, ecusa = self.sa)
        [receivedResponse, error] = (
                self.connection.WaitForChangeNumericValueResponse(self.da, self.sa))

        if receivedResponse and (error == 0):
            pass
        elif receivedResponse:
            raise IBSException("Error change numeric value, error code: {0}".format(error))
        else:
            raise IBSException("No response received")

    def ChangeStringValue(self, objid, value):
        self._CheckAlive()
    
        self.connection.SendChangeStringValue(objid, value, vtsa = self.da, ecusa = self.sa)
        [receivedResponse, error] = (
                self.connection.WaitForChangeStringValueResponse(self.da, self.sa))

        if receivedResponse and (error == 0):
            pass
        elif receivedResponse:
            raise IBSException("Error change string value, error code: {0}".format(error))
        else:
            raise IBSException("No response received")

    def ChangeListItem(self, objid, index, value):
        self._CheckAlive()

        self.connection.SendChangeListItemCommand(self.da, self.sa, objid, index, value)
        [receivedResponse, error] = (
                self.connection.WaitForChangeListItemResponse(self.da, self.sa))

        if receivedResponse and (error == 0):
            pass
        elif receivedResponse:
            raise IBSException("Error change list item, error code: {0}".format(error))
        else:
            raise IBSException("No response received")



    def ESCInput(self):
        self._CheckAlive()
    
        self.connection.SendEscCommand(self.da, self.sa)

        [receivedResponse, error, escObject] = (
        self.connection.WaitForESCResponse(self.da, self.sa))
        
        if receivedResponse and (error == 0):
            return escObject
        elif receivedResponse and (error == 1):
            raise IBSException("No input object open")
        elif receivedResponse:
            raise IBSException("Error code: {0}".format(error))
        else:
            raise IBSException("No response received")

    def DisconnectFromVT(self):
        if self.alive:
            self.connection.StopWSMaintenance(self.sa, self.da)
            self.alive = False

    def IdentifyVTs(self):
        self.connection.SendIdentifyVT(self.sa)

    def _CheckAlive(self):
        if not self.alive:
            raise IBSException('Not connected to a VT')
