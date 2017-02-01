import time
import random

from isobus.ibsinterface import IBSInterface
from isobus.constants import *

def BuildISOBUSName(**kwargs):
    # Set the default values TODO: Check these values
    settings = dict(  configurable        = 0x0
                    , industryGroup       = 0x2
                    , deviceClassInstance = 0X0
                    , deviceClass         = 0x0
                    , function            = FUNCTION_VT
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

class IBSControlFunction():
    """Generic ISOBUS node"""
    
    # Return True or False on commands based on success

    def __init__(self, interface, channel) :
        self.connection = IBSInterface(interface, channel)
        self.sa = 0xFE
        self.functionInstance = 0x00

    def ClaimAddress(self, sa, ibsName):
        # TODO: Check if SA is not already claimed
        # TODO: Handle configurable address?
        self.connection.SendRequestAddressClaim(sa)
        waittime = 250 + (random.randint(0, 255) * 0.6)
        time.sleep(waittime / 1000.0)
        self.connection.SendAddressClaim(ibsName, sa)
        time.sleep(0.250)

    #TODO: Implement PART 12 here?

