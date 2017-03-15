class IBSException(Exception):
    pass

#TODO: This doesn't make sense for negative numbers, should they even be allowed?
class NumericValue():
    """ To store a number which can be read to/from LE or BE """
    def __init__(self, value):
        self.value = value

    @classmethod
    def FromLEBytes(cls, databytes):
        """ Construct from array of bytes in LE order """
        value = sum([(databytes[n] << n*8) for n in range(len(databytes))])
        return cls(value)

    @classmethod
    def FromBEBytes(cls, databytes):
        """ Construct from array of bytes in BE order """
        value = sum([(databytes[n] << n*8) for n in reversed(range(len(databytes)))])
        return cls(value)
    
    def AsLEBytes(self, nBytes = 4):
        """ Returns a list of nBytes bytes in Little-Endian order """
        return [(self.value >> (n * 8) & 0xFF) for n in range(nBytes)]

    def AsBEBytes(self, nBytes = 4):
        """ Returns a list of nBytes bytes in Big-Endian order """
        return [(self.value >> (n * 8) & 0xFF) for n in reversed(range(nBytes))]

    def AsString(self):
        """ Returns the value as a string with hex and decimal representation"""
        return '0x{value1:08X} ({value2})'.format(value1 = self.value, value2 = self.value)

    def Value(self):
        return self.value

class IBSID():
    """ Represents a CAN ID in ISOBUS communication """
    def __init__(self, da, sa, pgn, prio=6):
        self.da = da
        self.sa = sa
        self.pgn = pgn
        self.prio = prio

    def GetCANID(self):
        """ Return the CAN ID as a 29 bit identifier """
        canid = 0
        if ((self.pgn >> 8) & 0xFF) < 0xEF:
            # PDU1
            canid = (((self.prio & 0x7) << 26)
                    | ((self.pgn & 0xFF00) << 8) 
                    | ((self.da & 0xFF) << 8)
                    | (self.sa & 0xFF))
        else :
            # PDU2
            canid = (((self.prio & 0x7) << 26)
                    | ((self.pgn & 0xFFFF) << 8) 
                    | (self.sa & 0xFF))

        return canid
    
    @classmethod
    def FromCANID(cls, canid):
        """ Get values from 29 bit identifier """
        prio = (canid >> 26) & 0x7
        sa = canid & 0xFF

        pgn = 0
        da = 0xFF

        if ((canid >> 16) & 0xFF) <= 0xEF:
            #Destination specific
            pgn = (canid >> 8) & 0xFF00
            da = (canid >> 8) & 0xFF
        else:
            #Broadcast
            pgn = (canid >> 8) & 0xFFFF
            
        return cls(da, sa, pgn, prio)
