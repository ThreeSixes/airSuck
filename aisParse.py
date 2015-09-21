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
        
        # From http://catb.org/gpsd/AIVDM.html
        if (retVal['sentenceType'] == "AIVDM") or (retVal['sentenceType'] == "AIVDO"):
            
            # Create a binary version of the payload data for parsing.
            payloadBin = bytearray(sentenceParts[5])
            
            if retVal['fragmentNumber'] == 1:
                # Get the payload type.
                payloadType = self.__vector2Bin(payloadBin[0])
                
                # Get the payload type data.
                retVal.update({'payloadType': payloadType})
                
                # If we have a position type A report
                if (payloadType) >= 1 and (payloadType <= 3):
                    
                    # Get the repeat indicator.
                    repeatInidicator = self.__vector2Bin(payloadBin[1]) >> 6
                    
                    # Get the payload type data.
                    retVal.update({'repeatIndicator': repeatInidicator})
                    
                    # Get the vessel's MMSI.
                    mmsi = ((self.__vector2Bin(payloadBin[1]) & 0x0f) << 26) | ((self.__vector2Bin(payloadBin[2]) & 0x3f) << 20) | ((self.__vector2Bin(payloadBin[3]) & 0x3f) << 14) | ((self.__vector2Bin(payloadBin[4]) & 0x3f) << 8) | ((self.__vector2Bin(payloadBin[5]) & 0x3f) << 2) | ((self.__vector2Bin(payloadBin[6]) & 0xc0) >> 4)
                    
                    # Set the MMSI.
                    retVal.update({'mmsi': mmsi})
                    
                    # Get navigation status
                    navStat = self.__vector2Bin(payloadBin[6]) & 0x0f
                    
                    # Set that navigation status
                    retVal.update({'navStat': navStat})
                    
                    # Get rate of turn
                    turnRt = ((self.__vector2Bin(payloadBin[7]) & 0x3f) << 2) | ((self.__vector2Bin(payloadBin[8]) & 0xc0) >> 4)
                    
                    # Set rate of turn
                    retVal.update({'turnRt': turnRt})
                    
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
        
        else:
            print("Unsupported sentence")
        
        # Return our data.
        return retVal
