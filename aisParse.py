"""
aisPrase by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSuck).
"""

############
# Imports. #
############

import binascii
import math
import sys
from pprint import pprint

##################
# aisParse class #
##################

class aisParse:
    """
    aisParse is a class that provides support for decoding AIS NMEA sentences.
    
    the principal method is aisParse(sentence).
    """
    
    #####################
    # Class constructor #
    #####################
    
    
    def __init__(self):
        # Do we set the names of NMEA sentences?
        self.decodeNames = False
        
        # 6-bit ASCII -> ASCII table.
        self.__ascii6Table = ["@", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "/", "]", "^", "_", " ", "!", "\"", "#", "$", "%", "&", "\\", "(", ")", "*", "+", ",", "-", ".", "/", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?"]
    


    ####################
    # Config Functions #
    ####################

    
    def setReturnNames(self, onOff):
        """
        setReturnNames(onOff)
        
        Turns decoding of AIS sentences, and other data on or off. onOff is a boolean value where True = decode names, and False = don't decode names. This can be changed during runtime.
        
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
    
    def __getSigned(self, unsignedNum, bits):
        """
        __getSigned(unsignedNum, bits)
        
        Converts an unsiged integer to a two's complement signed integer, given a bit length of the number.
        
        Returns a signed integer.
        """
        
        # Set up a variable to hold our signed number.
        signedNum = 0
        
        # Get our MSB
        msb = 1 << (bits - 1)
        
        # If our MSB is a 1, then we know we're a negative number.
        if (unsignedNum & msb) > 0:
            # Get the binary number with all ones set.
            maxVal = (2 ** bits) - 1
            
            # Make the number negative.
            signedNum = unsignedNum - maxVal
        else:
            # We're not negative.
            signedNum = unsignedNum
        
        # Return the signed int.
        return signedNum
    
    def __validateSentence(self, sentence):
        """
        __validateSentence(sentence)
        
        Attempt to verify the provided AIS NMEA sentence is likely a valid sentnece for processing.
        
        Returns True or False.
        """
        # Set up return value, and assume we have a bad frame.
        retVal = False
        
        return retVal
    
    def __getFields(self, sentence):
        """
        __getFields(sentence)
        
        Attempt to break the AIS sentence up into chunks delimited by commas.
        
        Returns an array of fields.
        """
        
        # Create an empty array for returning data.
        retVal = []
        
        # Try to split the sentence up into an array.
        try:
            retVal = sentence.split(',')
        
        except:
            print("Unable to split AIS sentence into fields.")
        
        return retVal
    
    def __vector2Bin(self, vector):
        """
        __vector2ASCII(vector)
        
        Convert bit vectors for AIVDM and AIVDO to ASCII characters.
        
        Returns a char.
        """
        
        retVal = ""
        
        #vector = ord(vector)
        
        # Make sure the data we're trying to handle is in range.
        #if (vector >= 64) and (vector <= 87):
        
        # Attempt to get the ASCII value from the vector.
        vector = vector - 48
        
        # If the final value is over 40 subtract another 8 from it to get the second block.
        if vector > 40:
            vector = vector - 8
        
        # Send a unicode char.
        retVal = vector
        
        return retVal
    
    def __decodeAIVDMO(self, field):
        """
        __decodeAIVDMO(field)
        
        Convert a string of bit vectors for AIVDM and AIVDO to ASCII data.
        
        Returns a string.
        """
        
        # Create necessary values.
        retVal = ""
        storeInt = 0
        
        datLen = len(field)
        
        # Decode each bit vector
        for i in range(0, len(field)):
            #
            if i > 0:
                storeInt = (storeInt << 6) | (self.__vector2Bin(field[i]) & 0x3f)
            else:
                storeInt = self.__vector2Bin(field[i])
            
            # Figure out how far off we are from being alined on 8-bit boundaries.
            spareBits = len(field) % 8
            
            # Shift them to the left on the 8-bit boundary in order to make life easy.
            storeInt = storeInt << spareBits
            
        # Now create a string...
        for i in range(0, datLen):
            retVal = retVal + chr((storeInt >> (i * 8)) & 0xff)
        
        return retVal
    
    def __getNMEAChecksum(self, data):
        """
        __getNMEAChecksum(data)
        
        Get the checksum from a given NMEA sentnece.
        
        Returns the chcecksum as an ASCII-encoded hex value.
        """
        
        ckSum = 0
        
        # Excluding the first char attempt to compute the XOR-based checksum of the AIS data.
        for i in range(1, len(data)):
            ckSum = None
        
        return ckSum
    
    def __computeTurn(self, turnRt):
        """
        __computeTurn(self, turnRt)
        
        Compute rate of turn. Return value yet to be determined.
        """
        
        retVal = ""
        
        return retVal
    
    def __getLocMeta(self, locType):
        """
        __getLocMeta(type)
        
        Given a type of request as an int get the location type.
        
        Returns a string.
        """
        
        locMetaStr = ["Class A",
            "Class A scheduled",
            "Class A interrogation response"]
        
        return locMetaStr[locType]
    
    def __getRepeatIndicator(self, frame):
        """
        __getRepeatIndicator(frame)
        
        Accepts a byte array with the frame.
        
        Returns a dict contianing representing the repeat indicator.
        """
        # Get the repeat indicator.
        repeatInidicator = self.__vector2Bin(frame[1]) >> 6
        
        # Return the repeat indicator.
        return {'repeatIndicator': repeatInidicator}
    
    def __getMMSI(self, frame):
        """
        __getMMSI(frame)
        
        Accepts a byte array with the frame.
        
        Returns a dict contianing representing the MMSI.
        """
        
        # Get the vessel's MMSI.
        mmsi = ((self.__vector2Bin(frame[1]) & 0x0f) << 26) | ((self.__vector2Bin(frame[2]) & 0x3f) << 20) | ((self.__vector2Bin(frame[3]) & 0x3f) << 14) | ((self.__vector2Bin(frame[4]) & 0x3f) << 8) | ((self.__vector2Bin(frame[5]) & 0x3f) << 2) | ((self.__vector2Bin(frame[6]) & 0xc0) >> 4)
        
        # Set the MMSI.
        return {'mmsi': mmsi}
    
    def __getRadioStatus(self, desc, frame):
        """
        __getRadioStatus(desc, frame)
        
        Get radio status data given a description and the frame. The description sets the key in the returned dict.
        
        Returns a dict with the radio status with desc as the key for the data.
        """
        # Get radio status
        radioStatus = ((self.__vector2Bin(frame[24]) & 0x01) << 18) | ((self.__vector2Bin(frame[25]) & 0x3f) << 12) | ((self.__vector2Bin(frame[26]) & 0x3f) << 6) | (self.__vector2Bin(frame[27]) & 0x3f)
        
        # Set radio status.
        return {desc: radioStatus}
    
    def __getEPFDMeta(self, epfd):
        """
        __getPEFDMeta(epfd)
        
        Get EPFD metadata given an EPFD value.
        
        Returns a string.
        """
        
        # EPFD descriptions
        epfdDesc = ["Undefined",
            "GPS",
            "GLONASS",
            "Combined GPS/GLONASS",
            "Loran-C",
            "Chayka",
            "Integrated navigation system",
            "Surveyed",
            "Galileo"]
        
        # Return the string.
        return epfdDesc[epfd]
    
    def __getLocation(self, lat, lon):
        """
        __getLocation(lat, lon)
        
        Given two raw integers representing a raw AIS latitude and longitude compute the proper latitude and longitude values.
        
        Returns a dict containing two floats containing a lat and lon.
        """
        
        # Create a return value that's false by default.
        retVal = False
        
        # Run our ints through two's complement.
        lat = self.__getSigned(lat, 27)
        lon = self.__getSigned(lon, 28)
        
        # Now scale the lat and lon properly and set accuracy to 4 places.
        lat = round(lat / 600000.0, 4)
        lon = round(lon / 600000.0, 4)
        
        # If we have a valid latitude and longitude.
        if (lat < 91) and (lon < 181):
            # Set position accuracy flag
            retVal = {'lat': lat, 'lon': lon}
        
        return retVal
    
    def aisParse(self, sentence):
        """
        aisParse(sentence)
        
        Parse AIS sentences.
        
        This method returns a dictionary of all decode fields.
        """
        
        # This dict will hold all the information we're able to decode from frames
        retVal = {}
        
        # Break the sentence apart.
        sentenceParts = self.__getFields(sentence)
        
        # Get the sentence type
        if '!' in sentenceParts[0]:
            retVal.update({'sentenceType': sentenceParts[0].replace('!', '')})
        else:
            retVal.update({'sentenceType': sentenceParts[0]})
        
        try:
            # Get the fragment count
            retVal.update({'fragmentCount': int(sentenceParts[1])})
            
            # Get the fragment number
            retVal.update({'fragmentNumber': int(sentenceParts[2])})
                
            # Get the message ID number, and if we have a value update our data with it.
            msgID = sentenceParts[3]
            
            if msgID != "":
                retVal.update({'messageID': int(msgID)})
            
            # Figoure out the channel if it's 1 or 2.
            channelStr = sentenceParts[4]
            
            # Convert 1 or 2 to A or B if they are specified that way.
            if channelStr == "1":
                channelStr = "A"
            elif channelStr == "2":
                channelStr = "B"
            
            # Get the message ID number
            retVal.update({'channel': channelStr})
            
            # Get the payload
            retVal.update({'payload': sentenceParts[5]})
            
            # Get the last two fields by splitting field 6 by an *.
            endParts = sentenceParts[6]
            
            # Get the stray bits and checksum.
            endFields = endParts.split('*')
            
            # If we don't have exactly two fields something went wrong.
            if len(endFields) != 2:
                raise ValueError
            
            # Number of padding bits included in the sentence
            retVal.update({'padBits': int(endFields[0])})
            
            # We should have exactly two characters as the length of the 
            if len(endFields[1]) == 2:
                # Number of padding bits included in the sentence
                retVal.update({'frameSum': int(ord(binascii.unhexlify(endFields[1])))})
            else:
                print("Punt at frame sum length.")
                raise ValueError
        
        except:
            print("Failed to process standard AIS fields.")
        
        # Category A psotion.
        if (retVal['sentenceType'] == "AIVDM") or (retVal['sentenceType'] == "AIVDO"):
            
            # Create a binary version of the payload data for parsing.
            payloadBin = bytearray(sentenceParts[5])
            
            if retVal['fragmentNumber'] == 1:
                # Get the payload type.
                payloadType = self.__vector2Bin(payloadBin[0])
                
                # Get the payload type data.
                retVal.update({'payloadType': payloadType})
                
                # If we have a position type A report
                if (payloadType >= 1) and (payloadType <= 3):
                    
                    # Set the repeat indicator.
                    retVal.update(self.__getRepeatIndicator(payloadBin))
                    
                    # Set the MMSI.
                    retVal.update(self.__getMMSI(payloadBin))
                    
                    # Get navigation status
                    navStat = self.__vector2Bin(payloadBin[6]) & 0x0f
                    
                    # If we have a non-default navigation status number...
                    if navStat < 15:
                        # Set that navigation status
                        retVal.update({'navStat': navStat})
                    
                    # Get rate of turn
                    turnRt = ((self.__vector2Bin(payloadBin[7]) & 0x3f) << 2) | ((self.__vector2Bin(payloadBin[8]) & 0xc0) >> 4)
                    
                    # If the turn rate isn't 128 set it.
                    if turnRt != 128:
                        # Set rate of turn
                        retVal.update({'turnRt': turnRt})
                    
                    #### TODO: CREATE METHOD TO HANDLE TURN RATE DATA #####
                    
                    # Speed over ground
                    gndSpd = ((self.__vector2Bin(payloadBin[8]) & 0x0f) << 6) | (self.__vector2Bin(payloadBin[9]) & 0x3f)
                    
                    # Unsigned int with LSB = 0.1
                    gndSpd = gndSpd / 10.0
                    
                    # Set velocity and velocity type
                    retVal.update({'velo': gndSpd, 'veloType': 'gnd'})
                    
                    # Position accuracy flag
                    posAcc = self.__vector2Bin(payloadBin[10]) & 0x20
                    
                    # Get position accuracy flag.
                    if posAcc > 0:
                        posAcc = True
                    else:
                        posAcc = False
                    
                    # Set position accuracy flag
                    retVal.update({'posAcc': posAcc})
                    
                    # Get raw longitude and latitude.
                    lon = ((self.__vector2Bin(payloadBin[10]) & 0x1f) << 23) | ((self.__vector2Bin(payloadBin[11]) & 0x3f) << 17) | ((self.__vector2Bin(payloadBin[12]) & 0x3f) << 11) | ((self.__vector2Bin(payloadBin[13]) & 0x3f) << 5) | ((self.__vector2Bin(payloadBin[14]) & 0x3e) >> 1)
                    lat = ((self.__vector2Bin(payloadBin[14]) & 0x01) << 21) | ((self.__vector2Bin(payloadBin[15]) & 0x1f) << 20) | ((self.__vector2Bin(payloadBin[16]) & 0x3f) << 14) | ((self.__vector2Bin(payloadBin[17]) & 0x3f) << 8) | ((self.__vector2Bin(payloadBin[18]) & 0x3f) << 2) | ((self.__vector2Bin(payloadBin[19]) & 0x30) >> 4)
                    
                    # Try to get the latitude and longitude given the data we have.
                    cmpLatLon = self.__getLocation(lat, lon)
                    
                    # If we have a valid latitude and longitude.
                    if type(cmpLatLon) == dict:
                        # Set position and position metadata
                        retVal.update(cmpLatLon)
                        retVal.update({'locationMeta': self.__getLocMeta(payloadType)})
                    
                    # Get course over ground
                    cog = ((self.__vector2Bin(payloadBin[19]) & 0x0f) << 8) | ((self.__vector2Bin(payloadBin[20]) & 0x3f) << 2) | ((self.__vector2Bin(payloadBin[21]) & 0x30) >> 4)
                    
                    # If we have a valid course over ground...
                    if cog != 3600:
                        # Convert course over ground to be in tenths of a degree.
                        cog = round(cog / 10.0, 1)
                        
                        # Course over the ground.
                        retVal.update({'courseOverGnd': cog})
                    
                    # Get heading
                    heading = ((self.__vector2Bin(payloadBin[21]) & 0x0f) << 5) | ((self.__vector2Bin(payloadBin[22]) & 0x3e) >> 1)
                    
                    # If we have a valid course over ground...
                    if heading != 511:
                        # Course over the ground.
                        retVal.update({'heading': heading})
                    
                    # Get the timestamp.
                    timestamp = ((self.__vector2Bin(payloadBin[22]) & 0x01) << 5) | ((self.__vector2Bin(payloadBin[23]) & 0x3e) >> 1)
                    
                    # Set the timestamp.
                    retVal.update({'timestamp': timestamp})
                    
                    # Get the maneuver indicator / blue sign
                    maneuver = ((self.__vector2Bin(payloadBin[23]) & 0x01) << 1) | ((self.__vector2Bin(payloadBin[24]) & 0x20) >> 5)
                    
                    # If we have a non-default value
                    if maneuver > 0:
                        # Set the maneuver indicator.
                        retVal.update({'maneuverBlueSign': maneuver})
                    
                    # Get the spare bits
                    spare = (self.__vector2Bin(payloadBin[23]) & 0x1c) >> 2
                    
                    # If we have a non-zero value in the spare bits...
                    if spare > 0:
                        # Set the spare bits
                        retVal.update({'spare': spare})
                    
                    # Get the spare bits
                    raim = (self.__vector2Bin(payloadBin[23]) & 0x02) >> 1
                    
                    # If we have a non-zero value in the spare bits...
                    if raim > 0:
                        raim = True
                    else:
                        raim = False
                    
                    # Set the spare bits
                    retVal.update({'raim': raim})
                    
                    # Add radio status.
                    retVal.update(self.__getRadioStatus('radioStatus', payloadBin))
                
                # Base station report
                # From http://catb.org/gpsd/AIVDM.html
                elif payloadType == 4:
                    # Set the repeat indicator.
                    retVal.update(self.__getRepeatIndicator(payloadBin))
                    
                    # Set the MMSI.
                    retVal.update(self.__getMMSI(payloadBin))
                    
                    # Get the UTC year, month, day, hour, minute, and second.
                    utcYear = ((self.__vector2Bin(payloadBin[6]) & 0x0f) << 10) | ((self.__vector2Bin(payloadBin[7]) & 0x3f) << 4) | ((self.__vector2Bin(payloadBin[8]) & 0x3c) >> 2)
                    utcMonth = ((self.__vector2Bin(payloadBin[8]) & 0x03) << 2) | ((self.__vector2Bin(payloadBin[9]) & 0x30) >> 4)
                    utcDay = ((self.__vector2Bin(payloadBin[9]) & 0x0f) << 1) | ((self.__vector2Bin(payloadBin[10]) & 0x20) >> 5)
                    utcHour = (self.__vector2Bin(payloadBin[10]) & 0x1f)
                    utcMinute = (self.__vector2Bin(payloadBin[11]) & 0x3f)
                    utcSecond = (self.__vector2Bin(payloadBin[12]) & 0x3f)
                    
                    # Set the UTC time data.
                    retVal.update({'utcYear': utcYear, 'utcMonth': utcMonth, 'utcDay': utcDay, 'utcHour': utcHour, 'utcMinute': utcMinute, 'utcSecond': utcSecond})
                    
                    # Get raw longitude and latitude.
                    lon = ((self.__vector2Bin(payloadBin[13]) & 0x1f) << 23) | ((self.__vector2Bin(payloadBin[14]) & 0x3f) << 17) | ((self.__vector2Bin(payloadBin[15]) & 0x3f) << 11) | ((self.__vector2Bin(payloadBin[16]) & 0x3f) << 5) | ((self.__vector2Bin(payloadBin[17]) & 0x3e) >> 1)
                    lat = ((self.__vector2Bin(payloadBin[17]) & 0x01) << 26) | ((self.__vector2Bin(payloadBin[18]) & 0x1f) << 20) | ((self.__vector2Bin(payloadBin[19]) & 0x3f) << 14) | ((self.__vector2Bin(payloadBin[20]) & 0x3f) << 8) | ((self.__vector2Bin(payloadBin[21]) & 0x3f) << 2) | ((self.__vector2Bin(payloadBin[22]) & 0x30) >> 4)
                    
                    # Try to get the latitude and longitude given the data we have.
                    cmpLatLon = self.__getLocation(lat, lon)
                    
                    # If we have a valid latitude and longitude.
                    if type(cmpLatLon) == dict:
                        # Set position and position metadata
                        retVal.update(cmpLatLon)
                    
                    # Get the EPFD
                    epfd = (self.__vector2Bin(payloadBin[17]) & 0x0f)
                    
                    # If we have something that's defined...
                    if epfd > 0:
                        # Set the EPFD data.
                        retVal.update({'epfd': epfd, 'epfdMeta': self.__getEPFDMeta(epfd)})
                    
                    # Get spare bits
                    spare = ((self.__vector2Bin(payloadBin[23]) & 0x0f) << 4) | ((self.__vector2Bin(payloadBin[24]) & 0x3c) >> 2)
                    
                    # Set spare bits
                    if spare > 0:
                        retVal.update({'spare': spare})
                    
                    # Get the spare bits
                    raim = (self.__vector2Bin(payloadBin[24]) & 0x02) >> 1
                    
                    # If we have a non-zero value in the spare bits...
                    if raim > 0:
                        raim = True
                    else:
                        raim = False
                    
                    # Set the spare bits
                    retVal.update({'raim': raim})
                    
                    # Add radio status.
                    retVal.update(self.__getRadioStatus('radioStatus', payloadBin))
        
        else:
            print("Unsupported sentence")
        
        # Return our data.
        return retVal
