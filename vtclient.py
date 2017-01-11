#! /usr/bin/env python3

import time #sleep
import cmd #shell
import sys #argv
import logging

import isobus

logging.basicConfig(filename='vtclient.log', filemode='w', level=logging.DEBUG)


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
vtClient = isobus.VTClient()
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
