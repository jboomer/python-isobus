import time
from isobus.vt.interface import IBSVTInterface

def BuildISOBUSName(**kwargs):
    # Set the default values TODO: Check these values
    settings = dict(  configurable        = 0x0
                    , industryGroup       = 0x2
                    , deviceClassInstance = 0X0
                    , deviceClass         = 0x0
                    , function            = 0x3e
                    , functionInstance    = 0x0 
                    , ECUInstance         = 0x0
                    , manufacturerCode    = 0x59
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

    def __init__(self) :
        self.connection = IBSVTInterface()
        self.sa = 0xFE
        self.da = 0xFF
        self.alive = False
        self.functionInstance = 0x00

    def SetSrc(self, sa):
        if sa >= 0 and sa <= 0xFE:
            self.sa = sa

    def ConnectToVT(self, da):
        ret = False
        
        gotStatus, _ = self.connection.WaitForStatusMessage(da)
        ibsName = BuildISOBUSName(functionInstance = self.functionInstance)
        if gotStatus:
            self.connection.ClaimAddress(self.sa, ibsName)
            self.connection.SendWSMaintenance(True, self.sa, da)
            time.sleep(0.5)
            self.connection.StartWSMaintenace(self.sa, da)
            self.alive = True
            self.da = da
            ret = True
        else:
            print("Failed to connect to VT")

        return ret

    def LoadVersion(self, version):
        ret = False
        print("Loading version {0}".format(version))
        if self.alive:
            self.connection.SendLoadVersionCommand(version, self.sa, self.da)
            
            # TODO wait for load version response max 3 status messages w/parsing = 0
            [receivedResponse, error] = self.connection.WaitLoadVersionResponse(self.da, self.sa)
            if receivedResponse and (error == 0):
                print("Loaded version: {0}".format(version))
                ret = True
            else:
                print("Did not load version, error code: {0}".format(error))
        else :
            print("Not connected to a VT")

        return ret

    def StoreVersion(self, version):
        ret = False
        print("Storing version {0}".format(version))
        if self.alive:
            self.connection.SendStoreVersioncommand(version, self.da, self.sa)
            
            # TODO wait for load version response max 3 status messages w/parsing = 0
            [receivedResponse, error] = self.connection.WaitStoreVersionResponse(self.da, self.sa)
            if receivedResponse and (error == 0):
                print("Stored version: {0}".format(version))
                ret = True
            else:
                print("Did not store version, error code: {0}".format(error))
        else :
            print("Not connected to a VT")

        return ret


    def UploadPoolData(self, data, eoop=True):
        ret = False
        if self.alive:

            self.connection.SendGetMemory(len(data), self.da, self.sa)
            [receivedMemResp, version, enoughMemory] = self.connection.WaitForGetMemoryResponse(
                    self.da, self.sa)

            if receivedMemResp and enoughMemory:

                self.connection.SendPoolUpload(self.da, self.sa, data)

                if eoop:
                    self.connection.SendEndOfObjectPool(self.da, self.sa)
                    [received, error] = self.connection.WaitEndOfObjectPoolResponse(self.da, self.sa)
                    if received and error == 0:
                        print("Pool uploaded")
                        ret = True
                    elif received:
                        print("Received error code {0}".format(error))
                    else:
                        print("EoOP Response timed out")
            elif receivedMemResp:
                print('Not enough memory available')
            else:
                print('No Get Memory Response received')

        else :
            print("Not connected to a VT")

        return ret

    def DeleteObjectPool(self):
        ret = False
        if self.alive:

            self.connection.SendDeleteObjectPool(self.da, self.sa)

            # TODO wait for load version response max 3 status messages w/parsing = 0
            [receivedResponse, error] = self.connection.WaitDeleteObjectPoolResponse(
                    self.da, self.sa)
            if receivedResponse and (error == 0):
                print("Deleted objectpool")
                ret = True
            elif receivedResponse:
                print("Got error: {0}".format(error))
            else:
                print("Response timed out")

        else :
            print("Not connected to a VT")

        return ret


    def ChangeActiveMask(self, wsid, maskid):
        ret = False
        if self.alive:
            self.connection.SendChangeActiveMask(wsid, maskid, self.sa, self.da)

            [receivedResponse, newMaskID, error] = (
                    self.connection.WaitForChangeActiveMaskResponse(self.da, self.sa))

            if receivedResponse and (error == 0):
                print("New active mask = 0X{:04X}".format(newMaskID))
                ret = True
            elif receivedResponse:
                print("Error change active mask, error code: {0}".format(error))
            else:
                print("No response received")

        else:
            print("Not connected to a VT")
        return ret

    def ChangeSKMask(self, maskid, skmaskid, alarm=False):
        ret = False
        if self.alive:
            self.connection.SendChangeSKMask(maskid, skmaskid, alarm, self.da, self.sa)

            [receivedResponse, error, newSKMaskID] = (
                    self.connection.WaitForChangeSKMaskResponse(self.da, self.sa))
            if receivedResponse and (error == 0):
                print("New SK mask = 0X{:04X}".format(newSKMaskID))
                ret = True
            elif receivedResponse:
                print("Error change active mask, error code: {0}".format(error))
            else:
                print("No response received")
        else:
            print("Not connected to a VT")

        return ret

    def ChangeAttribute(self, objid, attrid, value):
        ret = False
        if self.alive:
            self.connection.SendChangeAttribute(objid, attrid, value, self.da, self.sa)

            [receivedResponse, error] = (
                    self.connection.WaitChangeAttributeResponse(self.da, self.sa))

            if receivedResponse and (error == 0):
                print("Attribute changed")
                ret = True
            elif receivedResponse:
                print("Error change attribute, error code: {0}".format(error))
            else:
                print("No response received")

        else:
            print("Not connected to a VT")

        return ret

    def ChangeNumericValue(self, objid, value):
        ret = False
        if self.alive:
            self.connection.SendChangeNumericValue(objid, value, vtsa = self.da, ecusa = self.sa)
            [receivedResponse, error] = (
                    self.connection.WaitForChangeNumericValueResponse(self.da, self.sa))

            if receivedResponse and (error == 0):
                print("Numeric value changed")
                ret = True
            elif receivedResponse:
                print("Error change numeric value, error code: {0}".format(error))
            else:
                print("No response received")
        else:
            print("Not connected to a VT")

        return ret


    def ESCInput(self):
        ret = False
        if self.alive:
            self.connection.SendEscCommand(self.da, self.sa)

            [receivedResponse, error, escObject] = (
            self.connection.WaitForESCResponse(self.da, self.sa))
            
            if receivedResponse and (error == 0):
                print("ESC object 0x{:04X}".format(escObject))
                ret = True
            elif receivedResponse and (error == 1):
                print("No input object open")
            elif receivedResponse:
                print("Error code: {0}".format(error))
            else:
                print("No response received")

        else:
            print("Not connected to a VT")

        return ret


    def DisconnectFromVT(self):
        if self.alive:
            self.connection.StopWSMaintenance(self.sa, self.da)
            self.alive = False

    def IdentifyVTs(self):
        self.connection.SendIdentifyVT(self.sa)

