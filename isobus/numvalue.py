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

