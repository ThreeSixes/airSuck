"""
ssrPrase by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).

Some code in this class was taken from or inspired by code in Malcom Robb's dump1090 fork, and the CRC algorightm comes from Bistromath's gr-air-modes project.
https://github.com/MalcolmRobb/dump1090
https://github.com/bistromath/gr-air-modes
"""

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
    #####################
    # Class constructor #
    #####################
    
    
    def __init__(self):
        """
        ssrParse is a class that provides support for decoding SSR modes A, C, and S.
        
        ssrParse only supports parsing of DF (downlink format) data so far.
        
        the principal method is ssrParse(strData) with strData being a binary string of SSR data.
        """
        
        # Do we set the names of DFs, formats, etc.?
        self.decodeNames = False
        
        # CRC stuff
        self.__crcPoly = 0xfff409
        self.__crc24Mask = 0xffffff
        self.__crcTable = self.buildCrcTable()
        
        # 6-bit ASCII table.
        self.__ascii6Table = ["@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "/", "]", "^", "_", " ", "!", "\"", "#", "$", "%", "&", "\\", "(", ")", "*", "+", ",", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?"]

    ####################
    # Config Functions #
    ####################

    
    def setReturnNames(self, onOff):
        """
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
        Convert a hex string represented in ASCII to a binary string.
        
        Returns a string.
        """
        
        return binascii.unhexlify(asciiHx)
    
    def buildCrcTable(self):
        """
        Create CRC value table for improved CRC computation performance.
        
        Returns the CRC table.
        """
        
        crc = 0
        crcTable = []
        
        for i in range(0, 256):
            crc = i << 16
            
            for j in range(0, 8):
                if int(crc & 0x800000) > 0:
                    crc = ((crc << 1) ^ self.__crcPoly) & self.__crc24Mask
                else:
                    crc = (crc << 1) & self.__crc24Mask
            
            crcTable.append((crc & self.__crc24Mask))
        
        return crcTable
    
    def getCrc(self, data):
        """
        Compute the CRC value of a given frame.
        
        Returns the CRC value as an int.
        """
        
        crc = 0
        
        for i in range(0, len(data)):
            crc = self.__crcTable[((crc >> 16) ^ data[i]) & 0xff] ^ (crc << 8)
        
        return (crc & self.__crc24Mask)
    
    def formatString(self, subject):
        """
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
        Get the ICAO AA as a hex string, given a frame such as DF11 or DF17.
        """
        
        # Hellify our ICAO AA
        retVal = binascii.hexlify(data[1:4])
        
        # Make sure we encode the hexlified string properly.
        retVal = self.formatString(retVal)
        
        return retVal
    
    def getIcaoAAInt(self, data):
        """
        Get the ICAO AA as an int, given a frame such as DF11 or DF17.
        """
        
        return int((data[1] << 16) | (data[2] << 8) | data[3])

    def getCACO(self, data):
        """
        Get the CA/Capability or Control value for a given frame such as DF11, DF17, and DF18.
        """
        
        return (data[0] & 0x07)
    
    def getFlightStatus(self, data):
        """
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
    
    def bin2Gillham(self, data):
        """
        Convert a byestream to a Gillham encoded byte. Retruns an integer for success, and False for a failure.
        
        This function does not ignore the X/M bit.
        """
        
        # Return value
        retVal = False
        
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
        if (data & C1Hex) > 0: retVal = retVal | C1Gil
        if (data & A1Hex) > 0: retVal = retVal | A1Gil
        if (data & C2Hex) > 0: retVal = retVal | C2Gil
        if (data & A2Hex) > 0: retVal = retVal | A2Gil
        if (data & C4Hex) > 0: retVal = retVal | C4Gil
        if (data & A4Hex) > 0: retVal = retVal | A4Gil
        if (data & XMHex) > 0: retVal = retVal | XMGil
        if (data & B1Hex) > 0: retVal = retVal | B1Gil
        if (data & D1Hex) > 0: retVal = retVal | D1Gil
        if (data & B2Hex) > 0: retVal = retVal | B2Gil
        if (data & D2Hex) > 0: retVal = retVal | D2Gil
        if (data & B4Hex) > 0: retVal = retVal | B4Gil
        if (data & D4Hex) > 0: retVal = retVal | D4Gil
        
        return retVal
    
    def modeASquawk2modeCAlt(self, modeAInt):
        """
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
        Decode a given byte as a 6-bit character for aircraft ident data using the AIS char set.
        """
        
        # Set return value.
        retVal = ""
        
        try:
            # Get the 6-bit char.
            retVal = self.__ascii6Table[data]
        
        except:
            # Do nothing - invalid char.
            pass
        
        return retVal
    
    def getIDInfo(self, data):
        """
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
        Check to see if we have an emergency squawk code. Returns false for no emergency nad a string describing the emergency being squawked. Also sets the emergency flag.
        """
        
        retVal = False
        
        # Check for unmanned aicraft with lost comms
        if aSquawk == "7400":
            retVal = "Unmanned aircraft, lost comms"
        
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
            
            # Get the frame's CRC value and compute the CRC value of the frame.
            retVal['frameCrc'] = (binData[-3] << 16) + (binData[-2] << 8) + (binData[-1])
            retVal['cmpCrc'] = self.getCrc(binData[0:-3])
            
            # Short air-to-air ACAS
            if(retVal['df'] == 0):
                if self.decodeNames: retVal['dfName'] = "Short Air-to-air ACAS"
                
                # Get vertical status bits.
                vsBit = (binData[0] & 0x04) >> 2
                retVal['vertStat'] = "air" if vsBit == 0 else "gnd"
                retVal['cc'] = (binData[0] & 0x02) >> 1
                retVal['sl'] = (binData[1] & 0xE0) >> 5
                
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
                
                # If we have a flight status that indicates an emergency...
                if (retVal['fs'] >= 2) and (retVal['fs'] <= 4):
                    retVal['emergency'] = True
                    retVal['fsEmergency'] = True
                else:
                    retVal['fsEmergency'] = False
                
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
                
                # Get the ICAO AA as a hex string and int.
                retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
                retVal['icaoAAInt'] = self.getIcaoAAInt(binData)
            
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
                    
                    # Get the ICAO AA as a hex string and int.
                    retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
                    retVal['icaoAAInt'] = self.getIcaoAAInt(binData)
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
                        # Get the ICAO AA as a hex string and int.
                        retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
                        retVal['icaoAAInt'] = self.getIcaoAAInt(binData)
                    
                    # ADS-B ES/NT w/ other addr
                    elif caCo == 1:
                        # Set address.
                        retVal['addrHx'] = self.getIcaoAAHx(binData)
                        retVal['addrInt'] = self.getIcaoAAInt(binData)
                    
                    # ADS-B rebroadcast using DF17 msg fmt.
                    elif caCo == 6:
                        # Get the ICAO AA as a hex string and int.
                        retVal['icaoAAHx'] = self.getIcaoAAHx(binData)
                        retVal['icaoAAInt'] = self.getIcaoAAInt(binData)
                
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
                        retVal['headingValid'] = headingValid
                        
                        # If we have a valid track, get our track bits
                        if(headingValid == 1):
                            headingRaw = ((binData[5] & 0x07) << 4) | (((binData[6] & 0xF0)) >> 4)
                            
                            # The track data is from 0-360, in 128 steps.
                            headingRaw = headingRaw * 2.8125
                            
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
                        
                        # Get turn bits (reserved for future)
                        #manuBits = binData[5] & 0x03
                        
                        # Set the default not-supersonic
                        retVal['supersonic'] = False
                        
                        # Get Vertical rate data, and the vertical rate sign bit.
                        vertSign = (binData[8] >> 3) & 0x01
                        vertRateRaw = ((binData[8] & 0x07) << 6) | ((binData[9] & 0xfc) >> 2)
                        
                        # If we have vert rate data...
                        if vertRateRaw > 0:
                            # Adjust for vertical rate offset where 1 = 0, 2 = 1, etc.
                            vertRateRaw -= 1
                            
                            # Adjust for vertical rate sign.
                            if vertSign == 1:
                                vertRateRaw = 0 - vertRateRaw
                            
                            # Adjust for 64 ft. scale
                            retVal['vertRate'] = vertRateRaw * 64
                            
                            # Get the geometric height difference sign bit
                            geoSign = (binData[10] >> 7) & 0x01
                            
                            # Get the raw geometric height difference data.
                            geoHeightDiffRaw = binData[10] & 0x7f
                            
                            # If we have valid data...
                            if geoHeightDiffRaw > 0:
                                # Remove offset where 1 = 0, 2 = 1, etc.
                                geoHeightDiffRaw -= 1
                                
                                # If we have a geometric alt below the baro alt, then make the value negative.
                                if geoSign == 1:
                                    geoHeightDiffRaw = 0 - geoHeightDiffRaw
                                
                                # Scale to 25 feet.
                                retVal['altDelta'] = geoHeightDiffRaw * 25
                        
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