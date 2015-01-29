############
# Imports. #
############

import binascii
import math
import sys

##################
# ssrParse class #
##################

class ssrParse:
    """
    ssrParse is a class that provides support for decoding SSR modes A, C, and S.
    
    ssrParse only supports parsing of DF (downlink format) data so far.
    
    the principal method is ssrParse(strData) with strData being a binary string of SSR data.
    
    Some code in this class was taken from or inspired by code in Malcom Robb's dump1090 fork.
    https://github.com/MalcolmRobb/dump1090
    """
    
    ###################
    # Class-wide vars #
    ###################
    
    # Do we set the names of DFs, formats, etc.?
    decodeNames = False
    
    ####################
    # Config Functions #
    ####################

    
    def setReturnNames(self, onOff):
        """
        setReturnNames(onOff)
        
        Turns decoding of DF names, formats, and other data on or off. onOff is a boolean value where True = decode names, and False = don't decode names. This can be changed during runtime.
        
        Returns True for success, False for failure.
        """
        
        # Did it work or not?
        retVal = False
        
        # Toggle onOff given a correct parameter
        if onOff == True:
            self.decodeNames = True
            retVal = True
        elif onOff == False:
            self.decodeNames = False
            retVal = True
            
        return retVal

    #####################
    # Parsing functions #
    #####################
    
    
    def asciiHx2Str(self, asciiHx):
        """
        asciiHx2Str(asciiHx)
        
        Convert a hex string represented in ASCII to a binary string.
        
        Returns a string.
        """
        
        return binascii.unhexlify(asciiHx)
    
    def crcChk(self, data):
        """
        crcChk(data)
        24-Bit CRC check against DF11 and DF17, since other data types seem to have the ICAO  XOR'd with the sender's address.
        This method is based on the dump1090's modesChecksum() in mode_s.c
        
        I AM BROKEN
        """
        
        # CRC sum table from dump1090's mode_s.c
        ckSumTable = [
        0x3935ea, 0x1c9af5, 0xf1b77e, 0x78dbbf, 0xc397db, 0x9e31e9, 0xb0e2f0, 0x587178,
        0x2c38bc, 0x161c5e, 0x0b0e2f, 0xfa7d13, 0x82c48d, 0xbe9842, 0x5f4c21, 0xd05c14,
        0x682e0a, 0x341705, 0xe5f186, 0x72f8c3, 0xc68665, 0x9cb936, 0x4e5c9b, 0xd8d449,
        0x939020, 0x49c810, 0x24e408, 0x127204, 0x093902, 0x049c81, 0xfdb444, 0x7eda22,
        0x3f6d11, 0xe04c8c, 0x702646, 0x381323, 0xe3f395, 0x8e03ce, 0x4701e7, 0xdc7af7,
        0x91c77f, 0xb719bb, 0xa476d9, 0xadc168, 0x56e0b4, 0x2b705a, 0x15b82d, 0xf52612,
        0x7a9309, 0xc2b380, 0x6159c0, 0x30ace0, 0x185670, 0x0c2b38, 0x06159c, 0x030ace,
        0x018567, 0xff38b7, 0x80665f, 0xbfc92b, 0xa01e91, 0xaff54c, 0x57faa6, 0x2bfd53,
        0xea04ad, 0x8af852, 0x457c29, 0xdd4410, 0x6ea208, 0x375104, 0x1ba882, 0x0dd441,
        0xf91024, 0x7c8812, 0x3e4409, 0xe0d800, 0x706c00, 0x383600, 0x1c1b00, 0x0e0d80,
        0x0706c0, 0x038360, 0x01c1b0, 0x00e0d8, 0x00706c, 0x003836, 0x001c1b, 0xfff409,
        0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000,
        0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000,
        0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000, 0x000000]
        
        # Hold our return value.
        retVal = False
        
        # Hold our remainder and CRC values.
        crc = 0
        
        # Get the length in bytes of our data in bytes.
        dataLen = len(data)
        
        # Get the last three bytes of CRC (24 bits)
        specCrc = (data[dataLen - 3] << 16) | (data[dataLen - 2] << 8) | data[dataLen - 1]
        
        # Get the ICAO address as an int.
        icaoAAInt = self.getIcaoAAInt(data)
        
        # Convert our length in bytes to bits.
        dataLen *= 8
        
        # Figoure out where in the checksum table we need to start.
        tableOffset = 122 - dataLen
        
        # Remove the last 24 bits (3 bytes) from the length of the data.
        dataLen -= 24
        
        # Load the first byte.
        byteCtr = 0
        thisByte = data[byteCtr]
        
        # Compute the CRC, bit by bit.
        for i in range(0, (dataLen - 1)):
            # If we're at an 8th bit...
            if((i & 7) == 0):
                # increment the byte counter
                byteCtr += 1
                # Get the new byte.
                thisByte = data[byteCtr]
            
            # Check for a bit set
            if ((thisByte & 0x80) > 0):
                crc ^= ckSumTable[tableOffset + i]
            
            # Slide one bit left.
            thisByte = thisByte << 1
            
        # Compute final CRC value.
        retVal = (crc ^ icaoAAInt) & 0xffffff
        
        print("Debug computed CRC " + str(retVal))
        print("Debug provided CRC " + str(specCrc))
        
        return retVal
    
    def formatString(self, subject):
        """
        formatString(subject)
        
        Properly format a string as either ASCII for Python versions < 3, and as UTF-8 for Python version >= 3.
        This should be used for any data that has been "hexlified".
        Returns either a unicode or ASCII string.
        """
        
        # Decode input value as UTF-8.
        retVal = subject.decode('utf8')
        
        # Version check and convert to ASCII if version > 3. We do this to stay consistent with our other
        # string ouptput encodings, given a python version.
        if sys.version_info[0] < 3:
            # Encode ouptut for Python versions < 3 as ASCII
            retVal = retVal.encode('ascii')
        
        return retVal
    
    def getIcaoAAHx(self, data):
        """
        getIcaoAAHx(data)
        
        Get the ICAO AA as a hex string, given a frame such as DF11 or DF17.
        """
        
        # Hellify our ICAO AA
        retVal = binascii.hexlify(data[1:4])
        
        # Make sure we encode the hexlified string properly.
        retVal = self.formatString(retVal)
        
        return retVal
    
    def getIcaoAAInt(self, data):
        """
        getIcaoAAInt(data)
        
        Get the ICAO AA as an int, given a frame such as DF11 or DF17.
        """
        
        return int((data[1] << 16) | (data[2] << 8) | data[3])

    def getCACO(self, data):
        """
        getCACO(data)
        
        Get the CA/Capability or Control value for a given frame such as DF11, DF17, and DF18.
        """
        
        return (data[0] & 0x07)
    
    def getFlightStatus(self, data):
        """
        getFlightStatus(data)
        
        Get the flight status field from DF4, DF5, DF20, and DF21 as an array [0] containing the extracted numeric data and [1] containing descriptive text.
        """
        
        # FS bit table
        fsText = ["Nrml, Air", "Nrml, Gnd", "Alert, Air", "Alert, Gnd", "Alert + SPI", "SPI", "Reserved", "Unknown"]
        
        # Get FS bits
        fsBits = data[0] & 0x07
        
        # Return flight status data, based on the 3 FS bits.
        return [fsBits, fsText[fsBits]]
    
    def getEmergencyState(self, data):
        """
        getEmergencyState(data)
        
        Get the emergency state of an aircraft given a frame such as DF28 an array [0] containing the extracted numeric data and [1] containing descriptive text. Also sets the emergency flag.
        """
        
        # Emergency state text
        esText = ["No emergency",
        "General emergency (sqwk 7700)",
        "Lifeguard/Medical",
        "Minimum Fuel",
        "No comms (sqwk 7600)",
        "Unlawful interference (sqwk 7500)",
        "Downed aircraft",
        "Reserved"]
        
        # Get ES bits
        esBits = (data[5] & 0xe0) >> 5
        
        return [esBits, esText[esBits]]
    
    def get13BitAlt(self, data):
        """
        get13BitAlt(data)
        
        Get the 13-bit altitude data from DF0, DF4, DF16, and DF20.
        """
        
        # Set up return value and set as an error.
        alt = False
        
        # Get the altitude bits.
        altBits = ((data[2] << 8) | data[3]) & 0x1fff
        
        # If the altitude bits are non-zero
        if altBits > 0:
            # Attempt to decode altitude data
            alt = self.decode13BitAlt(altBits)
        
        return alt
    
    def getModeAStr(self, modeAGil):
        """
        getModeAStr(modeAGil)
        
        Get a formatted mode A Squawk code. Returns a squawk string. 
        """
        
        # Decode our Gillham enocded mode A squawk code into an integer.
        retVal = self.gillham2Bin(modeAGil)
        
        # Convert the hexidecimal representation of that integer to a string.
        retVal = str(hex(retVal))
        
        # Drop the 0x from the front of the string, and make sure we have 4 digits by zero-filling the left.
        retVal = retVal.replace('0x', '')
        retVal = retVal.rjust(4, '0')
        
        return retVal
    
    def gillham2Bin(self, grayCode):
        """
        gillham2Bin(gray)
        
        Convert Gillham gray code used in 13-bit altitude and mode A/C data to an int.
        
        This function ignores the X/M bit.
        """
        
        # Return value
        retVal = 0x0000
        
        # Bit positions for Gillham each bit
        C1Gil = 0x1000
        A1Gil = 0x0800
        C2Gil = 0x0400
        A2Gil = 0x0200
        C4Gil = 0x0100
        A4Gil = 0x0080
        XMGil = 0x0040 # The X/M bit.
        B1Gil = 0x0020
        D1Gil = 0x0010 # The Q bit.
        B2Gil = 0x0008
        D2Gil = 0x0004
        B4Gil = 0x0002
        D4Gil = 0x0001
        
        # Bit positions for Hex number.
        C1Hex = 0x0010
        A1Hex = 0x1000
        C2Hex = 0x0020
        A2Hex = 0x2000
        C4Hex = 0x0040
        A4Hex = 0x4000
        XMHex = 0x0800 # The X/M bit.
        B1Hex = 0x0100
        D1Hex = 0x0001 # The Q bit.
        B2Hex = 0x0200
        D2Hex = 0x0002
        B4Hex = 0x0400
        D4Hex = 0x0004
        
        # Convert Gillham code to hex.
        if (grayCode & C1Gil) > 0: retVal = retVal | C1Hex
        if (grayCode & A1Gil) > 0: retVal = retVal | A1Hex
        if (grayCode & C2Gil) > 0: retVal = retVal | C2Hex
        if (grayCode & A2Gil) > 0: retVal = retVal | A2Hex
        if (grayCode & C4Gil) > 0: retVal = retVal | C4Hex
        if (grayCode & A4Gil) > 0: retVal = retVal | A4Hex
        #if (grayCode & XMGil) > 0: retVal = retVal | XMHex
        if (grayCode & B1Gil) > 0: retVal = retVal | B1Hex
        if (grayCode & D1Gil) > 0: retVal = retVal | D1Hex
        if (grayCode & B2Gil) > 0: retVal = retVal | B2Hex
        if (grayCode & D2Gil) > 0: retVal = retVal | D2Hex
        if (grayCode & B4Gil) > 0: retVal = retVal | B4Hex
        if (grayCode & D4Gil) > 0: retVal = retVal | D4Hex
        
        return retVal
    
    def bin2Gillham(self, modeAHx):
        """
        hex2Gillham(modeAHx)
        
        Convert a decoded mode A squawk code expressed as a 2-byte number to Gillham code. Note that we ignore the X bit since it's not really used.
        
        returns a 12-bit Gillham-encoded squawk code as an integer.
        """
        
        # Default return value.
        retVal = 0x00
        
        # Hex bits for gillham encoding
        A1 = 0x1000
        A2 = 0x2000
        A4 = 0x4000
        B1 = 0x0100
        B2 = 0x0200
        B4 = 0x0400
        C1 = 0x0010
        C2 = 0x0020
        C4 = 0x0040
        D1 = 0x0001
        D2 = 0x0002
        D4 = 0x0004
        
        # Filter out illegal values (Clear the bits in the "8" position for each nibble).
        maskedData = modeAHx & 0x7777
        
        # Shift bits around to get 12-bit Gillham encoded values, excluding the X bit.
        # Note: Gillham encoded values are big-endian.
        retVal = (A1 & maskedData) >> 2
        retVal = retVal | (A2 & maskedData) >> 5
        retVal = retVal | (A4 & maskedData) >> 8
        retVal = retVal | (B1 & maskedData) >> 3
        retVal = retVal | (B2 & maskedData) >> 6
        retVal = retVal | (B4 & maskedData) >> 9
        retVal = retVal | (C1 & maskedData) << 7
        retVal = retVal | (C2 & maskedData) << 4
        retVal = retVal | (C4 & maskedData) << 1
        retVal = retVal | (D1 & maskedData) << 4
        retVal = retVal | (D2 & maskedData) << 1
        retVal = retVal | (D4 & maskedData) >> 2
        
        return retVal
    
    def modeASquawk2modeCAlt(self, modeAInt):
        """
        modeASquawk2modeCAlt(modeAInt)
        
        Attempt to convert a mode A squawk code to a mode C altitude. It accepts a 2-byte number containing a hex representation of the squawk code. Squawk 0040 = 0x0040.
        
        If the altitude can be decoded it returns an integer. If the altitude violates mode C constraints it returns False. Mode C altitudes have 100ft resolution.
        """
        
        # Set a dummy return value
        retVal = False
        
        # Check to make sure the mode C altitude doesn't violate constraints.
        # First, check for illegal bits. The 8 bit in each nibble shouldn't be set, and D1,2 are illegal. At least one C1-4 bit should be set.
        if ((modeAInt & 0x888b) == 0) and ((modeAInt & 0x00f0) > 0):
            # Get the int value for mode A to C conversion.
            retVal = self.modeA2C(modeAInt)
            
            # If we got a useful value from moeA2C
            if (retVal != False) and (retVal >= -12):
                # Our mode C altitude values are 100-ft resolution, so adjust for that fact.
                retVal = retVal * 100
        
        return retVal
    
    def modeA2C(self, modeAData):
        """
        ModeA2ModeC(modeAData)
        
        Convert mode A data into mode C data.
        """
        # I have no idea how this algrithm was devised since I'm not sure how the encoding works for altitude. Cheers.
        # From dump1090's mode_ac.c
        
        # Set a sentinel value.
        retVal = False
        
        # How many 100s or 500s should we have?
        hunds = 0
        fiveHunds = 0
        
        # Detect illegal values - D1 can't be set, and D2 set is an unlikely condition, also C1-4 can't be set to zero.
        if((modeAData & 0x888b) == 0) and ((modeAData & 0x00f0) > 0):
            # C1-4 bits represnet hundreds.
            if(modeAData & 0x0010):
                hunds ^= 0x007
            if(modeAData & 0x0020):
                hunds ^= 0x003
            if(modeAData & 0x0040):
                hunds ^= 0x001
            
            # Remove sevens from hunds
            if((hunds & 0x05) == 5):
                hunds ^= 2
            
            # Work on our 500s, D2, 4 bits first
            if((modeAData & 0x0002) > 0):
                fiveHunds ^= 0x0ff
            if((modeAData & 0x0004) > 0):
                fiveHunds ^= 0x07f
                
            # Continue on our 500s, A1-4 next
            if((modeAData & 0x1000) > 0):
                fiveHunds ^= 0x03f
            if((modeAData & 0x2000) > 0):
                fiveHunds ^= 0x01f
            if((modeAData & 0x4000) > 0):
                fiveHunds ^= 0x00f
                
            # Finish 500s, B1-4
            if((modeAData & 0x0100) > 0):
                fiveHunds ^= 0x007
            if((modeAData & 0x0200) > 0):
                fiveHunds ^= 0x003
            if((modeAData & 0x0400) > 0):
                fiveHunds ^= 0x001
            
            # Correct order of hundreds
            if ((fiveHunds & 1) > 0):
                hunds = 6 - hunds
            
            # Final return value.
            retVal = ((fiveHunds * 5) + hunds - 13)
            
        return retVal
    
    def decode12BitAlt(self, data):
        """
        decod12BitAlt(data)
        
        Decode 12-bit Altitude (in DF9, DF17, etc.)
        """
        
        # If we don't have valid altitude data
        if(data == 0):
            alt = False
        else:
            # Check for a "Q" bit. If yes, then we have 25ft resolution
            if((data & 0x0010) > 0):
                alt = ((data & 0x0fe0) >> 1) | (data & 0x000f)
                alt = ((alt * 25) - 1000)
            else:
                # We have a gray-coded altitude value mode A/C style at 100ft resolution
                
                # Set M=0 (bit 6)
                alt = (((data & 0x0fc0) << 1) | (data & 0x003f))
                
                # Convert to mode C data.
                alt = self.modeA2C(self.gillham2Bin(alt))
                
                # If we got a valid altitude back...
                if alt != False:
                    if(alt < -12): alt = 0
                    alt *= 100
        
        return alt
    
    def decode13BitAlt(self, data):
        """
        decode13BitAlt(data)
        
        Decode 13-bit Altitude (in DF0, DF4, DF15, DF20, and DF23)
        """
        
        # Altitude sentinel value.
        alt = False
        
        # Get M and Q bits.
        mBit = (data & 0x0040) >> 6
        qBit = (data & 0x0010) >> 4
        
        # If we're not dealing in meters.. (I don't know what the algorithm looks like for meters...)
        if mBit == 0:
            
            # Check our altitude format via Q bit.
            if qBit == 1:
                # Get rid of the M and Q bits.
                alt = ((data & 0x1f80) >> 2) | ((data & 0x0020) >> 1) | (data & 0x000f)
                
                # Get our 25-foot resolution altitude relative to +1000 ft.
                alt = (alt * 25) - 1000
            
            # We have a mode C 100-foot resolution altitude.    
            else:
                # Try to get an altitude value.
                alt = self.modeA2C(self.gillham2Bin(data))
                
                # Make sure we got something.
                if alt != False:
                    
                    # See if we aren't < 1200 ft. if we are, then zero out.
                    if alt < -12:
                        alt = 0
                    
                    # Since we have 100-foot increments, multiply by 100.
                    alt *= 100
        
        return alt
    
    def decode6BitChr(self, data):
        """
        decode6Bit(data):
        
        Decode a given byte as a 6-bit character for aircraft ident data.
        
        From bistomath's gr-air-modes code:
           https://github.com/bistromath/gr-air-modes/blob/master/python/parse.py
        """
        
        # Decode from A-Z
        if (data == 0):
            # Null chracter.
            None
        if (data > 0 and data < 27):
            retVal = chr(ord("A") + data - 1)
        # 32 is a space.
        elif data == 32:
            retVal = " "   
        # Decode from 0 - 9.
        elif (data > 47 and data < 58):
            retVal = chr(ord("0") + data - 48)
        else:
            # Unknown chracter represented as ?
            retVal = "?"
        
        return retVal
    
    def getIDInfo(self, data):
        """
        getIDInfo(data)
        
        Get the 8 character flight ID data from data as a string converted to an int.
        """
        
        # Set up our retun variable.
        retVal = ""
        
        # For each char...
        # From bistromath's gr-air-modes code: https://github.com/bistromath/gr-air-modes/blob/master/python/parse.py
        for i in range(0, 8):
            retVal += self.decode6BitChr(data >> (42-6*i) & 0x3F)
            
        # Retrun the flight ID data
        return retVal.strip()
    
    def checkSquawk(self, aSquawk):
        """
        checkSquawk(aSquawk)
        
        Check to see if we have an emergency squawk code. Returns false for no emergency nad a string describing the emergency being squawked. Also sets the emergency flag.
        """
        
        retVal = False
        
        # Check for hijack
        if aSquawk == "7500":
            retVal = "Hijack"
            
        # And loss of radio
        elif aSquawk == "7600":
            retVal = "Lost Comms/Radio"
        
        # And general emergency conditions
        elif aSquawk == "7700":
            retVal = "General Emergency"
        
        return retVal
    
    def getDwnlnkReq(self, data):
        """
        decodeDwnlnkField(data)
        
        Decode Downlink request field from DF4, 5, 20, and 21. Returns an array where [0] is the numeric downlink request value and [1] is the name.
        """
        
        # Named values for DRs
        drTable = ["No downlink req",
                   "Comm-B msg req",
                   "Reserved ACAS",
                   "Reserved ACAS",
                   "Comm-B bcast msg 1",
                   "Comm-B bcast msg 2",
                   "Reserved ACAS",
                   "Reserved ACAS",
                   "Not assigned",
                   "Not assigned",
                   "Not assigned",
                   "Not assigned",
                   "Not assigned",
                   "Not assigned",
                   "Not assigned",
                   "Not assigned",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM",
                   "ELM"]
        
        # Dummy return array
        retVal = [False, False]
        
        # Get downlink request bits
        drBits = (data[1] & 0xF8) >> 3
        
        # Set return values
        retVal[0] = drBits
        retVal[1] = drTable[drBits]
        
        return retVal
    
    def getUtilityMsg(self, data):
        """
        getUtilityMsg(data)
        
        Get the utility message field data from DF4, 5, 20, and 21. Returns an array with the IIS field in [0], the IDS in [1], and the IDS name in [2].
        """
        
        # IDS description table
        idsTable = ["No data", "COMM-B", "COMM-C", "COMM-D"]
        
        # Set dummy return values.
        retVal = [False, False, False]
        
        # Get IDS bits
        idsBits = (data[2] & 0x60) >> 5
        
        # Get and set IIS bits.
        retVal[0] = ((data[1] & 0x07) << 1) | ((data[2] & 0x80) >> 7)
        
        # Set IDS bits and name.
        retVal[1] = idsBits
        retVal[2] = idsTable[idsBits]
        
        return retVal
    
    def ssrParse(self, binData):
        """
        ssrParse(binData)
        
        Parse SSR data.
        
        Parse SSR data, looking for fields, etc. from binary data in the string binData.
        Mode A/C data is only supported for dump1090-style messages which are already decoded into 2-byte hex representations of a mode A squawk code where squawk 1200 = 0x1200.
        
        Please note that when decoding Mode A/C replies, we don't actually know if we're working with a mode A ident reply or mode C altitude reply because we don't know the RADAR pulse spacing from the interrogation. We do our best to see if a squawk could be a mode C reply and decode it both as mode A and C.
        
        This method returns a dictionary of all decode fields.
        
        http://www.lll.lu/~edward/edward/adsb/DecodingADSBposition.html
        http://www.radartutorial.eu/13.ssr/sr25.en.html
        """
        
        # This dict will hold all the information we're able to decode from frames
        retVal = {}
                
        # Get length in bytes.
        retVal['len'] = len(binData)
        
        # If we seem to have mode S based on length
        # 7 bytes = 56 bits, 14 bytes = 112 bits
        if (retVal['len'] == 7) or (retVal['len'] == 14):
            
            #Set our type to mode-s
            retVal['mode'] = "s"
            
            # Get our DF (downlink format)
            retVal['df'] = binData[0] >> 3
            
            # Short air-to-air ACAS
            if(retVal['df'] == 0):
                if self.decodeNames: retVal['dfName'] = "Short Air-to-air ACAS"
                
                # Get vertical status bits.
                vsBit = (binData[5] & 0x04) >> 2
                retVal['vertStat'] = "air" if vsBit == 0 else "gnd"
                retVal['cc'] = (binData[5] & 0x02) >> 1
                retVal['sl'] = (binData[6] & 0xE0) >> 2
                
                # Grab our altitude.
                alt = self.get13BitAlt(binData)
                
                # If we got good data
                if alt != False:
                    #Set our altitude data.
                    retVal['alt'] = alt
                
            # Roll cal (alt)   
            elif(retVal['df'] == 4):
                if self.decodeNames: retVal['dfName'] = "Roll call reply (alt)"
                
                # Get our flight status info
                fsData = self.getFlightStatus(binData)
                
                # Set flight status data.
                retVal['fs'] = fsData[0]
                if self.decodeNames: retVal['fsName'] = fsData[1]
                
                # Downlink request data
                dfData = self.getDwnlnkReq(binData)
                
                # Set the downlink request values
                retVal['dr'] = dfData[0]
                if self.decodeNames: retVal['drName'] = dfData[1]
                
                # Get our utility message data
                umData = self.getUtilityMsg(binData)
                
                # Set the utilit message fields
                retVal['iis'] = umData[0]
                retVal['ids'] = umData[1]
                
                # If we're decoding names set the IDS name
                if self.decodeNames: retVal['idsName'] = umData[2]
                
                # Grab our altitude.
                alt = self.get13BitAlt(binData)
                
                # If we got good data
                if alt != False:
                    #Set our altitude data.
                    retVal['alt'] = alt
            
            # Roll call (ident)
            elif(retVal['df'] == 5):
                if self.decodeNames: retVal['dfName'] = "Roll call reply (ident)"
                
                # Get our flight status info
                fsData = self.getFlightStatus(binData)
                
                # Set flight status data.
                retVal['fs'] = fsData[0]
                if self.decodeNames: retVal['fsName'] = fsData[1]
                
                # Downlink request data
                dfData = self.getDwnlnkReq(binData)
                
                # Set the downlink request values
                retVal['dr'] = dfData[0]
                if self.decodeNames: retVal['drName'] = dfData[1]
                
                # Get our utility message data
                umData = self.getUtilityMsg(binData)
                
                # Set the utilit message fields
                retVal['iis'] = umData[0]
                retVal['ids'] = umData[1]
                
                # If we're decoding names set the IDS name
                if self.decodeNames: retVal['idsName'] = umData[2]
                
                # Get our mode A squawk bytes.
                sqkBytes = ((binData[2] << 8) | binData[3]) & 0x1fff
                
                retVal['aSquawk'] = self.getModeAStr(sqkBytes)
                
                # Check for emergency squawk codes.
                sqwkEmergency = self.checkSquawk(retVal['aSquawk'])
                
                # Check to see if we have some emergency condition
                if sqwkEmergency != False:
                    retVal['aSquawkEmergency'] = sqwkEmergency
                    # Set the emergency flag
                    retVal['emergency'] = True
            
            # All call
            elif(retVal['df'] == 11):
                if self.decodeNames: retVal['dfName'] = "All call reply"
                
                # Get the CA/Capability value
                retVal['ca'] = self.getCACO(binData)
                
                # Get the ICAO AA as a hex string.
                retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
            
            # Long air-to-air ACAS
            elif(retVal['df'] == 16):
                if self.decodeNames: retVal['dfName'] = "Long Air-to-air ACAS"
                
                # Grab our altitude.
                alt = self.get13BitAlt(binData)
                
                # If we got good data
                if alt != False:
                    #Set our altitude data.
                    retVal['alt'] = alt
                    #retVal['altUnit'] = "ft"
            
            # Extended squitter / TIS-B
            elif(retVal['df'] == 17) or (retVal['df'] == 18):
                
                # Get the CA/Capability value
                caCo = self.getCACO(binData)
                
                # Get our format bytes.
                retVal['fmt'] = binData[4] >> 3
                
                # Do some work on our DFs
                if retVal['df'] == 17:
                    if self.decodeNames: retVal['dfName'] = "Extended squitter"
                    
                    # Set our CA
                    retVal['ca'] = caCo
                    
                    # Get the aircraft address for DF 17
                    aa = self.getIcaoAAHx(binData)
                    
                    # Get the ICAO AA as a hex string.
                    retVal['icaoAAHx'] = aa
                else:
                    if self.decodeNames: retVal['dfName'] = "TIS-B"
                     # Control field description
                    ctrlText = ["ADS-B ES/NT w/ ICAO AA",
                    "ADS-B ES/NT w/ other addr",
                    "Fine fmt TIS-B",
                    "Coarse fmt TIS-B",
                    "TIS-B mgmt msg",
                    "TIS-B relay of ADS-B msg w/other addr",
                    "ADS-B rebroadcast using DF17 msg fmt",
                    "Reserved"]
                    
                    # Set the control value
                    retVal['ctrl'] = caCo
                    # Set the control name
                    if self.decodeNames: retVal['ctrlName'] = ctrlText[caCo]
                    
                    # ADSB ES/NT w/ICAO AA
                    if caCo == 0:
                        # Set address.
                        retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
                
                    # ADS-B ES/NT w/ other addr
                    elif caCo == 1:
                        # Set address.
                        retVal['addrHx'] = self.getIcaoAAHx(binData)
                    
                    # ADS-B rebroadcast using DF17 msg fmt.
                    elif caCo == 6:
                        # Set address.
                        retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
                
                #Only proceed if we have DF17 or DF18 + CO0/1/6
                if(retVal['df'] == 17) or ((retVal['df'] == 18) and ((caCo <= 1) or (caCo == 6))):
                
                    # No pos data
                    if(retVal['fmt'] == 0):
                        if self.decodeNames: retVal['fmtName'] = "No position info"
                        retVal['nxc'] = 0
                    
                    # ID and category
                    if (retVal['fmt'] >= 1) and (retVal['fmt'] <= 4):
                        # AC ID and aircraft category
                        if self.decodeNames: retVal['fmtName'] = "ID and category"
                        
                        # Get the category item #.
                        catItem = binData[4] & 0x07
                        
                        # Set the aircraft category information.
                        retVal['category'] = chr(0x45 - retVal['fmt']) + str(catItem)
                        
                        # Convert our flight ID data to a big number so we can do binary operations on it. 
                        bigNumber = (binData[5] << 40) | (binData[6] << 32) | (binData[7] << 24) | (binData[8] << 16) | (binData[9] << 8) | binData[10]
                        
                        # Try to interpret bigNumber as ID data.
                        idData = self.getIDInfo(bigNumber)
                    
                        # See if we have legit data.
                        if idData != "":
                            # Set the idInfo field.
                            retVal['idInfo'] = idData
                    
                    # Surface position
                    elif (retVal['fmt'] >= 5) and (retVal['fmt'] <= 8):
                        if self.decodeNames: retVal['fmtName'] = "Surface pos"
                        # Calculate our nav. uncertainty category, V0 is NUC and V1 is NIC
                        retVal['nxc'] = 14 - retVal['fmt']
                        
                        # Get subformat bits
                        subFmt = binData[4] >> 3
                        
                        # Get movment bits
                        movementRaw = ((binData[4] & 0x07) << 4) | (binData[5] >> 4)
                        
                        # Get our track validity bit
                        headingValid = (binData[5] & 0x08) >> 3
                        retVal['headingValid'] = trackValid
                        
                        # If we have a valid track, get our track bits
                        if(headingValid == 1):
                            headingRaw = ((binData[5] & 0x07) << 4) | (((binData[6] & 0xF0)) >> 4)
                            
                            # The track data is from 0-360, in 128 steps.
                            headingRaw = trackRaw * 2.8125
                            
                            # Round to 1 decimal place
                            headingRaw = round(headingRaw, 1)
                            
                            # Set the track value
                            retVal['heading'] = headingRaw
                            
                        # Get UTC sync and even/odd format bit.
                        utcSync = (binData[6] & 0x08) >> 3
                        evenOdd = (binData[6] & 0x04) >> 2
                        
                        # Set UTC sync and evenOdd
                        retVal['utcSync'] = utcSync
                        retVal['evenOdd'] = evenOdd
                        
                        # Get 17 bit CPR latitude
                        rawLat = ((binData[6] & 0x03) << 15) | (binData[7] << 7) | ((binData[8] & 0xfe) >> 1)
                        
                        # Get 17 bit CRP longitude
                        rawLon = ((binData[8] & 0x01) << 16) | (binData[9] << 8) | binData[10]
                        
                        # Set raw lat and lon
                        retVal['rawLat'] = rawLat
                        retVal['rawLon'] = rawLon
                        
                    # Airborne position
                    elif (retVal['fmt'] >= 9) and (retVal['fmt'] <= 18) or ((retVal['fmt'] >= 20) and (retVal['fmt'] <= 22)):
                        if self.decodeNames: retVal['fmtName'] = "Airborne pos"
                        
                        #Caclulate our NUC
                        if (retVal['fmt'] <= 18):
                            retVal['nxc'] = 18 - retVal['fmt']
                        elif(retVal <= 21):
                            retVal['nxc'] = 29 - retVal['fmt']
                        
                        # Get the single-antenna flag.
                        retVal['singleAnt'] = binData[4] & 0x01
                        
                        # Get surveillance status bytes.
                        ss = (binData[4] & 0x06) >> 1
                        
                        # Surveillance status table
                        ssTable = ["No alert", "Permanent alert", "Code change", "SPI"]
                        
                        retVal['ss'] = ss
                        if self.decodeNames: retVal['ssName'] = ssTable[ss]
                        
                        # If we have a "permanent alert"
                        if ss == 1:
                            retVal['emergency'] = True
                        
                        # Get the altitude type
                        if (retVal['fmt'] >= 9) and (retVal['fmt'] <= 18):
                            retVal['altType'] = "Baro"
                        else:
                            retVal['altType'] = "GNSS"
                        
                        # Attempt to decode the altitude data.
                        altitudeBytes = (binData[5] << 8) | binData[6]
                        altProcessed = self.decode12BitAlt(altitudeBytes >> 4)
                        
                        # Verify altitude and see if we have an odd format bit.
                        if (altProcessed != False): 
                            retVal['alt'] = altProcessed
                        
                        # If we have format types 9, 10, 20, or 21 get the UTC sync flag
                        if((retVal['fmt'] <= 10) or (retVal['fmt'] >= 20)):
                            retVal['utcSync'] = (binData[6] & 0x08) >> 3
                        
                        # Pull position format flag, even/odd
                        retVal['evenOdd'] = (binData[6] & 0x04) >> 2
                        
                        # Grab lat bits.
                        rawLat = ((binData[6] & 0x03) << 15) | (binData[7] << 7) | ((binData[8] & 0xfe) >> 1)
                        retVal['rawLat'] = rawLat
                        
                        # Grab lon bits.
                        rawLon = ((binData[8] & 0x01) << 16) | (binData[9] << 8) | binData[10]
                        retVal['rawLon'] = rawLon
                    
                    # Airborne velocity
                    elif retVal['fmt'] == 19:
                        if self.decodeNames: retVal['fmtName'] = "Airborne velo"
                        
                        # Get subtype.
                        subType = binData[4] & 0x07
                        
                        # Set the subtype
                        retVal['subType'] = subType
                        
                        # Get source bit.
                        srcFlag = (binData[8] >> 4) & 0x01
                        retVal['srcFlag'] = srcFlag
                        
                        # Get the intent bit.
                        retVal['intentFlag'] = binData[5] >> 7
                        
                        # Get the high-level ADS-B (IFR) support bit
                        retVal['ifrCap'] = (binData[5] & 0x40) >> 6
                        
                        # Get the NUC/NAC
                        retVal['nxc'] = (binData[5] & 0x38) >> 3
                        
                        # Get the GNSS vs. Baro delta flag, where 0 = GNSS > Baro, 1 = Baro > GNSS
                        altDeltaSign = binData[6] >> 7
                        
                        # Get the difference in altitude between GNSS and Baro instruments.
                        altDeltaBytes = binData[6] & 0x7f
                        
                        # See if we have the necessary instuments to set the value (!=0)
                        if altDeltaBytes == 1:
                            # A value of 1 means there's no difference between readings
                            retVal['altDeltaBytes'] = 0
                        
                        # We have a value.
                        elif altDeltaBytes >= 2:
                            # Scale to 25 ft.
                            retVal['altDelta'] = altDeltaBytes * 25
                            retVal['altDeltaSign'] = altDeltaSign
                        
                        # Get turn bits (reserved for future)
                        #manuBits = binData[5] & 0x03
                        
                        # Set the default not-supersonic
                        retVal['supersonic'] = False
                        
                        # Get Vertical rate data, and the vertical rate sign bit.
                        vertSign = (binData[8] >> 3) & 0x01
                        vertRateRaw = ((binData[8] & 0x07) << 6) | ((binData[8] & 0xfc) >> 2)
                        
                        # If we have vert rate data...
                        if vertRateRaw > 0:
                            vertRateRaw -= 1
                            
                            # Adjust fo vertical sign.
                            if vertSign == 1:
                                vertRateRaw = 0 - vertRateRaw
                            
                            # Adjust for scale
                            retVal['vertRate'] = vertRateRaw * 64
                            
                            # Get Geometric height diff
                            geoSign = (binData[9] >> 7) & 0x01
                            
                            # Get the raw height data value.
                            getHeightDiffRaw = binData[9] & 0xef
                        
                        # Do we have a supersonic aircraft?
                        if (subType == 2) or (subType == 4):
                            
                            # Also, set the supersonic flag.
                            retVal['supersonic'] = True
                        
                        # Are we using a cartesian or polar coordinate system?
                        if (subType == 1) or (subType == 2):
                        # We are cartesian!                        
                            retVal['dataFmt'] = "crt"
                            
                            # Get the E/W and N/S bit for the direction
                            ewDirFlag = (binData[5] >> 2) & 0x01
                            nsDirFlag = (binData[7] >> 7) & 0x01
                            
                            # Get E/W and N/S velocity data
                            ewVeloRaw = ((binData[5] & 0x03) << 8) | binData[6]
                            # Adjust offset
                            ewVeloRaw -= 1
                            
                            nsVeloRaw = ((binData[7] & 0x7f) << 3) | (binData[8] >> 5)
                            # Adjust offset
                            nsVeloRaw -= 1
                            
                            # Do we have data?
                            if (ewVeloRaw >= 0) or (nsVeloRaw >= 0):
                            
                                # Are we suspersonic
                                if retVal['supersonic']:
                                    # If so, LSB is now 4.
                                    ewVeloRaw = ewVeloRaw << 2
                                    nsVeloRaw = nsVeloRaw << 2
                                
                                # Get our velocity (knots)
                                velo = math.sqrt((ewVeloRaw ** 2) + (nsVeloRaw ** 2))
                                
                                # Round our velocity to 1 decimal place.
                                velo = round(velo, 1)
                                
                                # Set our ground speed.
                                retVal['gndspeed'] = velo
                                    
                                # Account for E/W and N/S direction flags
                                if(ewDirFlag == 1):
                                    ewVeloRaw = 0 - ewVeloRaw
                                
                                if(nsDirFlag == 1):
                                    nsVeloRaw = 0 - nsVeloRaw
                                
                                # Get our heading in degrees.
                                heading = math.atan2(ewVeloRaw, nsVeloRaw) * 180 / math.pi
                                
                                # Make sure we have a heading that's > 0 flip it to the other side of the grid.
                                if (heading < 0):
                                    heading = heading + 360
                              
                                # Reduce to 1 decimal place of accuracy.
                                heading = round(heading, 1)
                              
                                # Set our heading
                                retVal['heading'] = heading
                        
                        # We have polar coordinates.
                        elif (subType == 3) or (subType == 4):
                            retVal['dataFmt'] = "plr"
                            
                            # Get heading status flag
                            headingStat = (binData[5] & 0x04) >> 2
                            
                            # Set value
                            retVal['headingAvail'] = headingStat
                            
                            # If we have heading data...
                            if (headingStat == 1):
                                
                                # 1024 bit heading... LSB = 1024/360 = 0.3515625
                                headingRaw = ((binData[5] & 0x03) << 8) | binData[6]
                                
                                # Convert the heading to an angle moving clockwise from north.
                                heading = headingRaw * 0.3515625
                                
                                # Set the heading, rounded to one decimal point
                                retVal['heading'] = round(heading, 1)
                            
                            # Get airspeed type bit
                            airspeedType = binData[7] >> 7
                            
                            # Get airspeed bits
                            rawAirspeed = ((binData[7] & 0x7f) << 3) | (binData[8] >> 5)
                            
                            # If we have airspeed data (data = 0)
                            if rawAirspeed > 0:
                                # Are we supersonic?
                                if retVal['supersonic']:
                                    rawAirspeed = rawAirspeed << 2
                                
                                retVal['airspeed'] = rawAirspeed
                            
                            # If we have a 0, we have true airspeed, if we have a 1 it's indicated airspeed
                            retVal['airspeedRef'] = 'true' if airspeedType == 1 else 'indicated'
                    
                    # Reserved for testing
                    elif(retVal['fmt'] == 23):
                        if self.decodeNames: retVal['fmtName'] = "Testing"
                        
                        # Get subtype
                        subType = binData[4] & 0x07
                        retVal['subType'] = subType
                        
                        # If we have a subType of 7...
                        if subType == 7:
                            # Get the test squawk code bits
                            modeABits = (((binData[5] << 8) | binData[6]) & 0xfff1) >> 3
                            
                            # Set the mode A squawk code data.
                            retVal['aSquawk'] = self.getModeAStr(modeABits)
                                
                            # Check for emergency squawk codes.
                            sqwkEmergency = self.checkSquawk(retVal['aSquawk'])
                            
                            # Check to see if we have some emergency condition
                            if sqwkEmergency != False:
                                retVal['aSquawkEmergency'] = sqwkEmergency
                                # Set the emergency flag
                                retVal['emergency'] = True
                        
                    # Reserved for system status
                    elif(retVal['fmt'] == 24):
                        if self.decodeNames: retVal['fmtName'] = "System status"
                    
                    # Reserved
                    elif((retVal['fmt'] >= 25) and (retVal['fmt'] <= 27)):
                        if self.decodeNames: retVal['fmtName'] = "Reserved"
                    
                    # Extended squitter aircraft status
                    elif(retVal['fmt'] == 28):
                        if self.decodeNames: retVal['fmtName'] = "ES Aircraft Status"
                        
                        # Get subtype
                        subType = binData[4] & 0x07
                        retVal['subType'] = subType
                        
                        # If we have a subType of 1...
                        if subType == 1:
                            
                            # Get ES data
                            esData = self.getEmergencyState(binData)
                            
                            # Set ES output.
                            retVal['es'] = esData[0]
                            if self.decodeNames: retVal['esName'] = esData[1]
                            
                            # If we have ES > 0 there's an emergency.
                            if esData[0] > 0:
                                # Set emergency flag
                                retVal['emergency'] = True
                            
                            # Get the test squawk code bits
                            modeABits = ((binData[5] << 8) | binData[6]) & 0x1fff
                            
                            # Set the mode A squawk code data.
                            retVal['aSquawk'] = self.getModeAStr(modeABits)
                            
                            # Check for emergency squawk codes.
                            sqwkEmergency = self.checkSquawk(retVal['aSquawk'])
                            
                            # Check to see if we have some emergency condition
                            if sqwkEmergency != False:
                                retVal['aSquawkEmergency'] = sqwkEmergency
                                # Set the emergency flag
                                retVal['emergency'] = True
                    
                    # Fluid - depends on version
                    elif(retVal['fmt'] == 29):
                        if self.decodeNames: retVal['fmtName'] = "Next trajectory change point / Target state and status"
                    
                    # Aircraft operational coordination, not used in V1
                    elif(retVal['fmt'] == 30):
                        if self.decodeNames: retVal['fmtName'] = "Aircraft operational coordination"
                    
                    # Aircraft operational status
                    elif(retVal['fmt'] == 31):
                        if self.decodeNames: retVal['fmtName'] = "Aircraft operational status"
                    
                    # Unknown/invalid
                    else:
                        if self.decodeNames: retVal['fmtName'] = "Invalid"
            
            # Military extended squitter
            elif(retVal['df'] == 19):
                if self.decodeNames: retVal['dfName'] = "Extended squitter (Military)"
            
            # Comm B altitude data.
            elif(retVal['df'] == 20):
                if self.decodeNames: retVal['dfName'] = "Comm B alt"
                
                # Grab our altitude.
                alt = self.get13BitAlt(binData)
                
                # If we got good data
                if alt != False:
                    #Set our altitude data.
                    retVal['alt'] = alt
                    #retVal['altUnit'] = "ft"
                
                # Get our flight status info
                fsData = self.getFlightStatus(binData)
                
                # Set flight status data.
                retVal['fs'] = fsData[0]
                if self.decodeNames: retVal['fsName'] = fsData[1]
                
                # Downlink request data
                dfData = self.getDwnlnkReq(binData)
                
                # Set the downlink request values
                retVal['dr'] = dfData[0]
                if self.decodeNames: retVal['drName'] = dfData[1]
                
                # Get our utility message data
                umData = self.getUtilityMsg(binData)
                
                # Set the utilit message fields
                retVal['iis'] = umData[0]
                retVal['ids'] = umData[1]
                
                # If we're decoding names set the IDS name
                if self.decodeNames: retVal['idsName'] = umData[2]
                
                # See if we have flight ID data.
                if binData[4] == 0x20:
                    # Convert our flight ID data to a big number so we can do binary operations on it. 
                    bigNumber = (binData[5] << 40) | (binData[6] << 32) | (binData[7] << 24) | (binData[8] << 16) | (binData[9] << 8) | binData[10]
                    
                    # Try to interpret bigNumber as ID data.
                    idData = self.getIDInfo(bigNumber)
                    
                    # See if we have legit data.
                    if idData != "":
                        # Set the idInfo field.
                        retVal['idInfo'] = idData
                
            # Comm B identification data.
            elif(retVal['df'] == 21):
                if self.decodeNames: retVal['dfName'] = "Comm B ident"
                
                # Get our flight status info
                fsData = self.getFlightStatus(binData)
                
                # Set flight status data.
                retVal['fs'] = fsData[0]
                if self.decodeNames: retVal['fsName'] = fsData[1]
                
                # Downlink request data
                dfData = self.getDwnlnkReq(binData)
                
                # Set the downlink request values
                retVal['dr'] = dfData[0]
                if self.decodeNames: retVal['drName'] = dfData[1]
                
                # Get our utility message data
                umData = self.getUtilityMsg(binData)
                
                # Set the utilit message fields
                retVal['iis'] = umData[0]
                retVal['ids'] = umData[1]
                
                # If we're decoding names set the IDS name
                if self.decodeNames: retVal['idsName'] = umData[2]
                
                # See if we have flight ID data.
                if binData[4] == 0x20:
                    # Convert our flight ID data to a big number so we can do binary operations on it. 
                    bigNumber = (binData[5] << 40) | (binData[6] << 32) | (binData[7] << 24) | (binData[8] << 16) | (binData[9] << 8) | binData[10]
                    
                    # Try to interpret bigNumber as ID data.
                    idData = self.getIDInfo(bigNumber)
                    
                    # See if we have legit data.
                    if idData != "":
                        # Set the idInfo field.
                        retVal['idInfo'] = idData
                
                # Get our altitude bytes.
                aSquawkBytes = ((binData[2] << 8) | binData[3]) & 0x1fff
                
                retVal['aSquawk'] = self.getModeAStr(aSquawkBytes)
                   
                # Check for emergency squawk codes.
                sqwkEmergency = self.checkSquawk(retVal['aSquawk'])
                    
                # Check to see if we have some emergency condition
                if sqwkEmergency != False:
                    retVal['aSquawkEmergency'] = sqwkEmergency
                    # Set the emergency flag
                    retVal['emergency'] = True
            
            # Military use only
            elif(retVal['df'] == 22):
                if self.decodeNames: retVal['dfName'] = "Military"
            
            # Comm D extended length message
            elif(retVal['df'] == 24):
                if self.decodeNames: retVal['dfName'] = "Comm D ELM"
            
            # Unknown/unsupported/error
            else:
                if self.decodeNames: retVal['dfName'] = "Unknown"
            
        # Mode A/C data
        elif (retVal['len'] == 2):
            retVal['mode'] = "ac"
            
            # Set our mode a squawk code... this is only supported for dump1090 data right now.
            retVal['aSquawk'] = self.formatString(binascii.hexlify(binData)).rjust(4, '0')
            
            # Check for emergency squawk codes.
            sqwkEmergency = self.checkSquawk(retVal['aSquawk'])
            
            # Check to see if we have some emergency condition
            if sqwkEmergency != False:
                retVal['aSquawkEmergency'] = sqwkEmergency
                # Set the emergency flag
                retVal['emergency'] = True
            
            # Get the mode A squawk as an integer.
            aHx = (binData[0] << 8) | binData[1]
            
            # Attempt to decode the mode A squawk as a mode C altitude.
            cAlt = self.modeASquawk2modeCAlt(aHx)
            
            # If it worked, set our possible altitude value.
            if cAlt != False:
                retVal['cAlt'] = cAlt
            
        # Looks like the data is not Mode A/C/S based on invalid length.
        else:
            retVal['mode'] = "invalid"
        
        # Return our dictionary full of new information from parsed frames.
        return retVal