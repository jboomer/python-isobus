import time
from isobus.vt.interface import IBSVTInterface
from isobus.common import IBSException
from isobus.log import log
from isobus.ibsinterface import IBSRxHandler


def BuildISOBUSName(**kwargs):
    # Set the default values TODO: Check these values
    settings = dict(  configurable        = 0x0
                    , industryGroup       = 0x2
                    , deviceClassInstance = 0X0
                    , deviceClass         = 0x0
                    , function            = 0x3e
                    , functionInstance    = 0x0 
                    , ECUInstance         = 0x0
                    , manufacturerCode    = 0x00
                    , idNumber            = 0x01FF
                    )
    for setting in settings.keys():
        if setting in kwargs.keys():
            settings[setting] = kwargs[setting]

    ibsName =( (settings['configurable']                  << 63)
             | (settings['industryGroup']                 << 60)
             | (settings['deviceClassInstance']           << 56)
             | (settings['deviceClass']                   << 49)
             | (settings['function']                      << 40)
             | (settings['functionInstance']              << 35)
             | (settings['ECUInstance']                   << 32)
             | (settings['manufacturerCode']              << 21)
             | (settings['idNumber']                      << 0 ))
    return ibsName

class VTClient():
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
            self.connection.ClaimAddress(self.sa, ibsName)
            self.connection.SendWSMaintenance(True, self.sa, da)
            time.sleep(0.5)
            self.connection.StartWSMaintenace(self.sa, da)
            self.alive = True
            self.da = da
        else:
            raise IBSException("Failed to connect to VT")

    def LoadVersion(self, version):
        log.debug('Loading version {0}'.format(version))
        if self.alive:
            self.connection.SendLoadVersionCommand(version, self.sa, self.da)
            
            # TODO wait for load version response max 3 status messages w/parsing = 0
            [receivedResponse, error] = self.connection.WaitLoadVersionResponse(self.da, self.sa)
            if receivedResponse and (error == 0):
                pass
            else:
                raise IBSException("Did not load version, error code: {0}".format(error))
        else :
            raise IBSException("Not connected to a VT")

    def StoreVersion(self, version):
        log.debug('Storing version {0}'.format(version))
        if self.alive:
            self.connection.SendStoreVersioncommand(version, self.da, self.sa)
            
            # TODO wait for load version response max 3 status messages w/parsing = 0
            [receivedResponse, error] = self.connection.WaitStoreVersionResponse(self.da, self.sa)
            if receivedResponse and (error == 0):
                pass
            else:
                raise IBSException("Did not store version, error code: {0}".format(error))
        else :
            raise IBSException("Not connected to a VT")


    def UploadPoolData(self, data, eoop=True):
        if self.alive:

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

        else :
            raise IBSException("Not connected to a VT")


    def DeleteObjectPool(self):
        if self.alive:

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

        else :
            raise IBSException("Not connected to a VT")


    def ChangeActiveMask(self, wsid, maskid):
        if self.alive:
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

        else:
            raise IBSException("Not connected to a VT")

    def ChangeSKMask(self, maskid, skmaskid, alarm=False):
        if self.alive:
            self.connection.SendChangeSKMask(maskid, skmaskid, alarm, self.da, self.sa)

            [receivedResponse, error, newSKMaskID] = (
                    self.connection.WaitForChangeSKMaskResponse(self.da, self.sa))
            if receivedResponse and (error == 0):
                return newSKMaskID
            elif receivedResponse:
                raise IBSException("Error change active mask, error code: {0}".format(error))
            else:
                raise IBSException("No response received")
        else:
            raise IBSException("Not connected to a VT")


    def ChangeAttribute(self, objid, attrid, value):
        if self.alive:
            self.connection.SendChangeAttribute(objid, attrid, value, self.da, self.sa)

            [receivedResponse, error] = (
                    self.connection.WaitChangeAttributeResponse(self.da, self.sa))

            if receivedResponse and (error == 0):
                pass
            elif receivedResponse:
                raise IBSException("Error change attribute, error code: {0}".format(error))
            else:
                raise IBSException("No response received")

        else:
            raise IBSException("Not connected to a VT")

    def ChangeNumericValue(self, objid, value):
        if self.alive:
            self.connection.SendChangeNumericValue(objid, value, vtsa = self.da, ecusa = self.sa)
            [receivedResponse, error] = (
                    self.connection.WaitForChangeNumericValueResponse(self.da, self.sa))

            if receivedResponse and (error == 0):
                pass
            elif receivedResponse:
                raise IBSException("Error change numeric value, error code: {0}".format(error))
            else:
                raise IBSException("No response received")
        else:
            raise IBSException("Not connected to a VT")


    def ChangeListItem(self, objid, index, value):
        if self.alive:
            self.connection.SendChangeListItemCommand(self.da, self.sa, objid, index, value)
            [receivedResponse, error] = (
                    self.connection.WaitForChangeListItemResponse(self.da, self.sa))

            if receivedResponse and (error == 0):
                pass
            elif receivedResponse:
                raise IBSException("Error change list item, error code: {0}".format(error))
            else:
                raise IBSException("No response received")
        else:
            raise IBSException("Not connected to a VT")



    def ESCInput(self):
        if self.alive:
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

        else:
            raise IBSException("Not connected to a VT")


    def DisconnectFromVT(self):
        if self.alive:
            self.connection.StopWSMaintenance(self.sa, self.da)
            self.alive = False

    def IdentifyVTs(self):
        self.connection.SendIdentifyVT(self.sa)

