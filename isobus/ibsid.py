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

        if ((canid >> 16) & 0xFF) > 0xEF:
            #Destination specific
            pgn = (canid >> 8) & 0xFF00
            da = (canid >> 8) & 0xFF
        else:
            #Broadcast
            pgn = (canid >> 8) & 0xFFFF
            
        return cls(da, sa, pgn, prio)
