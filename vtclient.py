#! /usr/bin/env python3

import time #sleep
import cmd #shell
import sys #argv
import logging

import isobus
from isobus.vt.vt_client_if import IBSVTInterface

logging.basicConfig(filename='vtclient.log', filemode='w', level=logging.DEBUG)

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

    def __init__(self, conn) :
        self.connection = conn
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

class InputNumber():
    """
    Interpret a number from string, 0x or 0X prefix is hex.
    May throw ValueError
    """
    def __init__(self, fromtext, aliases=None):
        if aliases is not None and fromtext in aliases.keys():
            self.value = aliases[fromtext]
        else:
            if fromtext.startswith('0x') or fromtext.startswith('0X'):
                self.value = int(fromtext, 16)
            else:
                self.value = int(fromtext)
  
class VTClientShell(cmd.Cmd) :
    """
    CLI for the VT Connection
    """
    intro = 'VT Client CLI, type help or ? to list commands'
    prompt = 'vtclient> '
    file = None
    aliases = dict()

    def do_setalias(self, args):
        'Set an alias for an object ID or source address: setalias KEY VALUE'
        arglist = args.split()
        if len(arglist) == 2:
            try:
                self.aliases[arglist[0]] = InputNumber(arglist[1]).value
            except ValueError:
                print('Syntax error')
        else:
            print('{0} arguments expected, {1} given'.format(2, len(arglist)))

    def do_setsrc(self, sa):
        'Sets the source address to use (0x0A is default): setsrc SA'
        if not vtClient.alive:
            try:
                vtClient.SetSrc(InputNumber(sa).value)
            except ValueError:
                print('Please enter a source address such as 0x0A or 38')
        else:
            print('Disconnect before changing source address')

    def do_setfi(self, fi):
        'Sets the function instance to use (0x00 is default): setfi FUNCTIONINSTANCE'
        try:
            vtClient.functionInstance = InputNumber(fi).value
        except ValueError:
            print('Please enter a function instance such as 0x01 or 3')


    def do_loadver(self, version):
        'Load a version of the working set: loadver ABC1234'
        vtClient.LoadVersion(version)

    def do_storever(self, version):
        'Store a version of the working set: storever ABC1234'
        vtClient.StoreVersion(version)

    def do_poolup(self, filename):
        'Upload a complete pool from file: poolup FILENAME.IOP'
        try:
            with open(filename, "rb") as iopfile:
                vtClient.UploadPoolData([byte for byte in iopfile.read()])
        except FileNotFoundError:
            print('File not found')
    
    def do_partpool(self, filename):
        'Upload part of a pool (does not send EoOP): poolpart FILENAME.IOP'
        try:
            with open(filename, "rb") as iopfile:
                vtClient.UploadPoolData([byte for byte in iopfile.read()], False)
        except FileNotFoundError:
            print('File not found')

    def do_delpool(self, arg):
        'Delete object pool from volatile memory'
        vtClient.DeleteObjectPool()

    def do_connect(self, vtsa):
        'Connect to a VT: connect SA '
        try:
            vtClient.ConnectToVT(InputNumber(vtsa).value)
        except ValueError:
            print("Please enter a source address such as 0x0A or 38")

    def do_disconnect(self, arg):
        'Disconnect From a VT: disconnect'
        vtClient.DisconnectFromVT()

    def do_chgmask(self, args):
        'Send a Change Mask command: chgmask WSID MASKID'
        try:
            vtClient.ChangeActiveMask(*self._get_int_args(args))
        except ValueError:
            print('Syntax error')

    def do_chgskmask(self, args):
        'Send a Change SK Mask command: chgskmask MASKID SOFTKEYMASKID'
        try:
            arglist = self._get_int_args(args)
            if len(arglist) == 2:
                vtClient.ChangeSKMask(*arglist, alarm=False)
            else:
                print('Syntax error')
        except ValueError:
            print('Syntax error')

    def do_chgattr(self, args):
        'Send a change attribute command: chgattr OBJID ATTRID VALUE'
        arglist = self._get_int_args(args)
        if len(arglist) == 3:
            try:
                vtClient.ChangeAttribute(*arglist)
            except ValueError:
                print('Syntax error')
        else:
            print('Syntax error')

    def do_chgnumval(self, args):
        'Send a change numeric value command: chgnumval OBJID VALUE'
        try:
            arglist = self._get_int_args(args)
            if len(arglist) == 2:
                vtClient.ChangeNumericValue(*arglist)
            else:
                print('{0} arguments expected, {1} given'.format(2, len(arglist)))
        except ValueError:
            print('Invalid syntax')

    def do_esc(self, arg):
        'Send an ESC command to the VT, to escape user input: esc'
        vtClient.ESCInput()

    def do_identify(self, arg):
        'Send a message to all VTs to display (propietary) identification means'
        vtClient.IdentifyVTs()

    def do_sleep(self, arg):
        'Sleep a few seconds (for scripts): sleep SECONDS(float)'
        try:
            time.sleep(float(arg))
        except ValueError:
           print('Syntax error') 

    def do_exit(self, arg):
        'Exit the CLI: exit'
        print("Exiting...")
        return True
    
    def _get_int_args(self, args):
        return [InputNumber(x, self.aliases).value for x in args.split()]

# Construct global objects, TODO: 'App' class, which has the shell
conn = IBSVTInterface()
vtClient = VTClient(conn)
vtClient.SetSrc(0x0A) # Default source address

def main():
    logging.info('Starting shell')
    shell = VTClientShell()
    if len(sys.argv) == 2:
        with open(sys.argv[1], 'r') as script:
            for line in script.readlines():
                shell.onecmd(line)
        input('Done!')
    else :
        shell.cmdloop()

if __name__ == "__main__":
    main()
