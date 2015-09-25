#!/usr/bin/python

"""
ssrStateEngine by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

############
# Imports. #
############

try:
	import config
except:
	raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

import redis
import time
import json
import threading
import binascii
import datetime
from cprMath import cprMath
from airSuckUtil import airSuckUtil
from pprint import pprint


##################
# Global objects #
##################

# CPR stuff.
cprProc = cprMath()

##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the SSR channel for new incoming data.
    """
    def __init__(self, channels):
        threading.Thread.__init__(self)
        self.asu = airSuckUtil()
        
        # Redis queues and entities
        self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
        self.__sPsQ = redis.StrictRedis(host=config.statePub['host'], port=config.statePub['port'])
        self.__sRQ = redis.StrictRedis(host=config.stateRel['host'], port=config.stateRel['port'])
        self.__redHash = redis.StrictRedis(host=config.ssrStateEngine['hashHost'], port=config.ssrStateEngine['hashPort'])
        
        # Subscribe the the connector pub/sub queue.
        self.__psObj = self.__psQ.pubsub() 
        self.__psObj.subscribe(channels)
        
        # Type fixes.
        self.__subject2Type = {
            'supersonic': bool,
            'emergency': bool,
            'heading': float,
            'lat': float,
            'lon': float,
            'velo': float,
            'alt': int,
            'evenLat': int,
            'evenLon': int,
            'gndspeed': int,
            'lastFmt': int,
            'oddLat': int,
            'oddLon': int,
            'ss': int,
            'supersonic': int,
            'survStat': int,
            'utc': int,
            'vertRate': int,
            'fs': int
        }
        
        # Things that should be rounded.
        self.__subject2Round = {
            'heading': 1,
            'velo': 1,
        }
        
        # Things we want to just forward to the state engine.
        # incoming name -> state engine name
        self.__desiredData = {
            'aSquawk': 'aSquawk',                        
            'vertStat': 'vertStat',
            'src': 'lastSrc',
            'dts': 'dts',                  
            'heading': 'heading',
            'type': 'type'
        }
    
    def updateState(self, objName, cacheData):
        """
        updateState
        
        Update state engine with data from incoming frames given the data in the dict cacheData. objName is the name of the ICAO AA in hex, or emergency squawk code.
        
        Returns all data in the cache.
        """
        
        try:
            # Create properly-formatted name for the state hash table we're creating.
            fullName = str('ssrState-' + objName)
            
            # Delete the original timestamp.
            thisTime = cacheData.pop('dts', None)
            
            # Set the first seen data.
            self.__redHash.hsetnx(fullName, 'firstSeen', thisTime)
            
            # Update or create cached data, if we have more than just a name
            if type(cacheData) == dict:
                
                # Set each specified value.
                for thisKey in cacheData:
                    self.__redHash.hset(fullName, thisKey, cacheData[thisKey])
            
            # Set expiration on the hash entry.
            self.__redHash.expire(fullName, config.ssrStateEngine['hashTTL'])
            
            # Get all the date from our hash.
            retVal = self.__redHash.hgetall(fullName)
            
            # Add the address.
            retVal.update({'addr': objName})
            
            # Adjust datatypes to be correct since redis stores everything as a string.
            retVal = self.fixDataTypes(retVal)
        
        except Exception as e:
            print("Blew up trying to update data in Redis.")
            pprint(e)
        
        return retVal
    

    def pullState(self, objName):
        """
        pullState(objName)
        
        Pull state information for a given object name. Returns a dict with existing data.
        """
        
        # Try to pull data...
        dataPull = self.__redHash.hgetall('ssrState-' + objName)
        
        # Make sure we have some sort of data.
        if type(dataPull) == dict:
            retVal = dataPull
        
        else:
            # If not, return a blank dict.
            retVal = {}
        
        return retVal
    
    def getEmergencyInfo(self, data):
        """
        getEmergencyInfo(data)
        
        Get stateful emergency info for a given state entry.
        
        Returns a dict containing emergency info.
        """
        
        retVal = {}
        
        # Automatically grab any emergency data we have ahead of time.
        if 'emergency' in data:
            # Inherit the emergency flag from anything with the emergency flag from ANY frame.
            retVal.update({'emergency': data['emergency']})
                
            # Get a mode A squawk emergency description if one exists.
            if 'aSquawkEmergency' in data:
                retVal.update({'emergencyData': data['aSquawkEmergency']})
                
            # If we have more specific emergency data from an extended status squitter use it instead of a gneeric mode A squawk message.
            if 'es' in data:
                esText = ["No emergency", # This really shouldn't come through without emergency = True.
                    "General emergency (sqwk 7700)",
                    "Lifeguard/Medical",
                    "Minimum Fuel",
                    "No comms (sqwk 7600)",
                    "Unlawful interference (sqwk 7500)",
                    "Downed aircraft",
                    "Reserved"]
                    
                retVal.update({'emergencyData': esText[data['es']]})
        else:
            # Set emergency to false if there's no emergency.
            retVal = {'emergency': False}
        
        return retVal
    
    # Convert datetime objects expressed as a string back to datetime
    def str2Datetime(self, strDateTime):
        """
        Convert utcnow() datetime string back to a datetime object.
        """
        
        return datetime.datetime.strptime(strDateTime, "%Y-%m-%d %H:%M:%S.%f")
    
    def fixDataTypes(self, statusData):
        """
        fixDataTypes(self, statusData)
        
        Converts data from strings to their approriate datatypes. This is necessary since REDIS stores everything as a string in hash tables.
        """
        
        retVal = statusData
        
        # For each subject we want, try to convert.
        for subject in self.__subject2Type:
            try:
                # Run the conversion.
                if subject in retVal:
                    retVal[subject] = self.__subject2Type[subject](retVal[subject])
            except Exception as e:
                pprint(e)
        
        # Round floats as needed.
        try:
            for thisField, places in self.__subject2Round.iteritems():
                if thisField in retVal:
                    retVal[thisField] = round(retVal[thisField], places)
        except Exception as e:
            pprint(e)
        
        return retVal

    def enqueueData(self, statusData):
        """
        enqueueDate(statusData)
        
        Put status data on a queue for processing
        """
        
        # Debug print instead of dumping data onto another queue.
        jsonData = json.dumps(statusData)
        
        # Publish the data on the queue.
        self.__sPsQ.publish(config.statePub['qName'], jsonData)
        
        # If we actually want to store the state data in MongoDB...
        if config.stateMongo['enabled'] == True:
            
            # We don't want to store mode a metadata in the DB, so just pull it off the dict.
            if 'aSquawkMeta' in statusData:
                statusData.pop('aSquawkMeta', None)
            
            jsonData = json.dumps(statusData)
            self.__sRQ.rpush(config.stateRel['qName'], jsonData)
            
        return

    def crcInt2Hex(self, crcInt):
        """
        crcInt2Hex(crcInt)
        
        Convert the CRC value as in intteger to a hex string.
        Returns a hex string.
        """
        
        return binascii.hexlify(chr((crcInt >> 16) & 0xff) + chr((crcInt >> 8) & 0xff) + chr((crcInt & 0xff)))

    def worker(self, work):
        # Do work on the data returned from the subscriber.
        ssrJson = str(work['data'])
        
        # Get wrapped SSR data.
        ssrWrapped = json.loads(ssrJson)
        
        # Make sure we got good data from json.loads
        if (type(ssrWrapped) == dict):
            
            # Make sure we have SSR data...
            if ssrWrapped['type'] == "airSSR":
                
                # Set up our data structure
                data = {}
                
                # Add desired fields to our data dict.
                try:
                    for thisField, newName in self.__desiredData.iteritems():
                        if thisField in ssrWrapped:
                            data.update({newName: ssrWrapped[thisField]})
                except Exception as e:
                    pprint(e)
                
                ssrWrapped = self.fixDataTypes(ssrWrapped)
                
                # Do we hvae mode s?
                if ssrWrapped['mode'] == "s":
                    
                    # Save space for mode A metadata.
                    metaData = {}
                    
                    # Set our good CRC flag to false by default.
                    crcGood = False
                    
                    # Account for DF types that we aren't sure about CRC data that could contain good stuff.
                    if ssrWrapped['df'] in (11, 16):
                        crcGood = True
                    
                    if crcGood == False:
                        print("Bad CRC detected in frame:\n DF " + str(ssrWrapped['df']) + ": " + ssrWrapped['data'])
                    
                    # Get mode A metadata.
                    if 'aSquawk' in ssrWrapped:
                        # Try to get metadata from the squawk code...
                        aMeta = self.asu.modeA2Meta(ssrWrapped['aSquawk'], self.asu.regionUSA)
                        
                        # If we have usable data, add it.
                        if aMeta != None:
                            # Add the new metadata from the mode A squawk to our global metadata dictionary.
                            data.update({'aSquawkMeta': aMeta})
                    
                    # If we have an aircraft address specified and a good CRC...
                    if ('icaoAAHx' in ssrWrapped) and (crcGood == True):
                        
                        # Check for emergency conditions.
                        data.update(self.getEmergencyInfo(ssrWrapped))
                        
                        # Set our lastSeen time stamp for this data.
                        data.update({"lastSeen": ssrWrapped['dts']})
                        
                        # Enqueue processed state data.
                        self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                        
                        # Figure out how to clear the emergency flag if we no longer have an emergency.
    
    def run(self):
        for work in self.__psObj.listen():
            self.worker(work)

if __name__ == "__main__":
    print("SSR state engine starting...")
    
    # Start up our ADS-B parser
    client = SubListener([config.connPub['qName']])
    client.daemon = True
    # .. and go.
    client.start()
    
    try:
        while True: time.sleep(10)
    except KeyboardInterrupt:
        # Die nicely.
        quit()
    except Exception as e:
        print("Caught unhandled exception")
        pprint(e)
