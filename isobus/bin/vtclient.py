#! /usr/bin/env python3

import time #sleep
import cmd #shell
import sys #argv
import argparse
import os
import glob

import isobus


class InputNumber():
    """ Interpret a number from string, 0x or 0X prefix is hex.
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

def _append_slash_if_dir(p):
    if p and os.path.isdir(p) and p[-1] != os.sep:
        return p + os.sep
    else:
        return p

  
class VTClientShell(cmd.Cmd) :
    """ CLI for the VT Connection """
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
        try:
            vtClient.LoadVersion(version)
        except isobus.IBSException as e:
            print('Error: {reason}'.format(reason=e.args[0]))

    def do_storever(self, version):
        'Store a version of the working set: storever ABC1234'
        if len(version) == 7:
            try:
                vtClient.StoreVersion(version)
            except isobus.IBSException as e:
                print('Error: {reason}'.format(reason=e.args[0]))
        else:
            print('Version string is not 7 characters')

    def do_poolup(self, filename):
        'Upload a complete pool from file: poolup FILENAME.IOP'
        try:
            with open(filename, "rb") as iopfile:
                try:
                    vtClient.UploadPoolData([byte for byte in iopfile.read()])
                except isobus.IBSException as e:
                    print('Error: {reason}'.format(reason=e.args[0]))
        except FileNotFoundError:
            print('File not found')
        except IsADirectoryError:
            print('{fName} is a directory'.format(fName=filename))
    
    def do_partpool(self, filename):
        'Upload part of a pool (does not send EoOP): poolpart FILENAME.IOP'
        try:
            with open(filename, "rb") as iopfile:
                try:
                    vtClient.UploadPoolData([byte for byte in iopfile.read()], False)
                except isobus.IBSException as e:
                    print('Error: {reason}'.format(reason=e.args[0]))
        except FileNotFoundError:
            print('File not found')

    def do_delpool(self, arg):
        'Delete object pool from volatile memory'
        try:
            vtClient.DeleteObjectPool()
        except isobus.IBSException as e:
            print('Error: {reason}'.format(reason=e.args[0]))

    def do_connect(self, vtsa):
        'Connect to a VT: connect SA '
        try:
            vtClient.ConnectToVT(InputNumber(vtsa).value)
            print('Connected to VT with sa {sa}'.format(sa = vtsa))
        except ValueError:
            print("Please enter a source address such as 0x0A or 38")
        except isobus.IBSException:
            print('Failed to connect to VT with sa {sa}'.format(sa=vtsa))

    def do_disconnect(self, arg):
        'Disconnect From a VT: disconnect'
        vtClient.DisconnectFromVT()

    def do_chgmask(self, args):
        'Send a Change Mask command: chgmask WSID MASKID'
        try:
            vtClient.ChangeActiveMask(*self._get_int_args(args))
        except ValueError:
            print('Syntax error')
        except isobus.IBSException as e:
            print('Error: {reason}'.format(reason=e.args[0]))

    def do_chgskmask(self, args):
        'Send a Change SK Mask command: chgskmask MASKID SOFTKEYMASKID'
        try:
            arglist = self._get_int_args(args)
            if len(arglist) == 2:
                try:
                    vtClient.ChangeSKMask(*arglist, alarm=False)
                except isobus.IBSException as e:
                    print('Error: {reason}'.format(reason=e.args[0]))
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
            except isobus.IBSException as e:
                print('Error: {reason}'.format(reason=e.args[0]))
        else:
            print('Syntax error')

    def do_chgnumval(self, args):
        'Send a change numeric value command: chgnumval OBJID VALUE'
        try:
            arglist = self._get_int_args(args)
            if len(arglist) == 2:
                try:
                    vtClient.ChangeNumericValue(*arglist)
                except isobus.IBSException as e:
                    print('Error: {reason}'.format(reason=e.args[0]))
            else:
                print('{0} arguments expected, {1} given'.format(2, len(arglist)))
        except ValueError:
            print('Invalid syntax')

    def do_chgstrval(self, args):
        'Send a change string value command: chgstrval OBJID VALUE'
        arglist = args.split()
        if len(arglist) == 2:
            try:
                objid = InputNumber(arglist[0], self.aliases).value
                try:
                    vtClient.ChangeStringValue(objid, arglist[1])
                except isobus.IBSException as e:
                    print('Error: {reason}'.format(reason=e.args[0]))
            except ValueError:
                print('Invalid syntax')
        else:
            print('Invalid syntax : expects 2 arguments')

    def do_chglistitem(self, args):
        'Send a change list item command: chglistitem OBJID INDEX VALUE'
        try:
            arglist = self._get_int_args(args)
            if len(arglist) == 3:
                try:
                    vtClient.ChangeListItem(*arglist)
                except isobus.IBSException as e:
                    print('Error: {reason}'.format(reason=e.args[0]))
            else:
                print('{0} arguments expected, {1} given'.format(3, len(arglist)))
        except ValueError:
            print('Invalid syntax')

    def do_esc(self, arg):
        'Send an ESC command to the VT, to escape user input: esc'
        try:
            ret = vtClient.ESCInput()
            print('ESC object 0x{objid:04X}'.format(objid=ret))
        except isobus.IBSException as e:
            print('Error: {reason}'.format(reason=e.args[0]))

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

    def complete_poolup(self, text, line, begidx, endidx):
        return self._tab_complete_filepath(text, line, begidx, endidx)

    def complete_partpool(self, text, line, begidx, endidx):
        return self._tab_complete_filepath(text, line, begidx, endidx)

    def _tab_complete_filepath(self, text, line, begidx, endidx):
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return # arg not found

        fixed = line[before_arg+1:begidx]  # fixed portion of the arg
        arg = line[before_arg+1:endidx]
        pattern = arg + '*'

        completions = []
        for path in glob.glob(pattern):
            path = _append_slash_if_dir(path)
            completions.append(path.replace(fixed, "", 1))
        return completions    
    
    
    def _get_int_args(self, args):
        return [InputNumber(x, self.aliases).value for x in args.split()]

# Parse command line arguments
parser = argparse.ArgumentParser(description = 'CLI for a VT Client')
parser.add_argument('-s', '--script'
                    , help='Run a script instead of the interactive CL')
parser.add_argument('-i', '--interface' 
                    , default='socketcan_native' 
                    , choices=['pcan', 'socketcan_native', 'socketcan_ctypes']
                    , help='Interface, default=socketcan_native(only in Python3!)')
parser.add_argument('-c', '--channel'
                    , default='vcan0'
                    , help='Channel/bus name, default=vcan0')
args = parser.parse_args()

# Construct global objects
vtClient = isobus.VTClient(interface = args.interface, channel = args.channel)
vtClient.SetSrc(0x0A) # Default source address

def main():
    shell = VTClientShell()
    if args.script is not None:
        with open(args.script, 'r') as script:
            for line in script.readlines():
                shell.onecmd(line)
        input('Done!')
    else :
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print('Exiting...')

if __name__ == "__main__":
    main()
