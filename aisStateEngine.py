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
        self.__redHash = redis.StrictRedis(host=config.aisStateEngine['hashHost'], port=config.aisStateEngine['hashPort'])
        
        # Subscribe the the connector pub/sub queue.
        self.__psObj = self.__psQ.pubsub() 
        self.__psObj.subscribe(channels)
        
        # Things we want to just forward to the state engine.
        # incoming name -> state engine name
        self.__desiredData = {
            'dts': 'dts',
            'channel': 'lastChannel',
            'courseOverGnd': 'courseOverGnd',
            'dataOrigin': 'dataOrigin',
            'heading': 'heading',
            'lat': 'lat',
            'locationMeta': 'locationMeta',
            'lon': 'lon',
            'mmsi': 'addr',
            'navStat': 'navStat',
            'posAcc': 'posAcc',
            'raim': 'raim',
            'sentenceType': 'sentenceType',
            'src': 'lastSrc',
            'turnRt': 'turnRt',
            'type': 'type',
            'velo': 'velo',
            'veloType': 'veloType'
        }
        
        # Conversion table for type fixing. field -> type
        self.__subject2Type = {
            'courseOverGnd': float,
            'heading': float,
            'isAssembled': bool,
            'isFrag': bool,
            'lat': float,
            'lon': float,
            'addr': int,
            'navStat': int,
            'padBits': int,
            'payloadType': int,
            'posAcc': bool,
            'radioStatus': int,
            'raim': bool,
            'repeatIndicator': int,
            'spare': int,
            'timestamp': int,
            'turnRt': int,
            'velo': float,
            'epfd': int,
            'radioStatus': int,
            'utcDay': int,
            'utcHour': int,
            'utcMinute': int,
            'utcMonth': int,
            'utcSecond': int,
            'utcYear': int,
            'posAcc': bool
        }
    
    def updateState(self, objName, cacheData):
        """
        updateState
        
        Update state engine with data from incoming frames given the data in the dict cacheData. objName is the mmsi of the AIS source.
        
        Returns all data in the cache.
        """
        
        retVal = {}
        
        try:
            # Create properly-formatted name for the state hash table we're creating.
            fullName = str('aisState-' + str(objName))
            
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
            self.__redHash.expire(fullName, config.aisStateEngine['hashTTL'])
            
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
        
        return retVal

    def enqueueData(self, statusData):
        """
        enqueueDate(statusData)
        
        Put status data on a queue for processing
        """
        
        # Things that shouldn't be stored in the mongoDB go in this list.
        poplist = [
            'locationMeta',
            'epfdMeta'
        ]
        
        # Debug print instead of dumping data onto another queue.
        jsonData = json.dumps(statusData)
        
        # Publish the data on the queue.
        self.__sPsQ.publish(config.statePub['qName'], jsonData)
        
        # If we actually want to store the state data in MongoDB...
        if config.stateMongo['enabled'] == True:
            
            # Remove things we don't want stored in the mongoDB.
            for popThing in poplist:
                if popThing in statusData:
                    statusData.pop(popThing, None)
            
            jsonData = json.dumps(statusData)
            self.__sRQ.rpush(config.stateRel['qName'], jsonData)
            
        return

    def worker(self, work):
        # Do work on the data returned from the subscriber.
        aisJson = str(work['data'])
        
        # Get wrapped AIS data.
        aisWrapped = json.loads(aisJson)
        
        # Make sure we got good data from json.loads
        if (type(aisWrapped) == dict):
            
            # Make sure we have non-fragmented AIS data that includes an MMSI...
            if ('mmsi' in aisWrapped) and (aisWrapped['type'] == "airAIS") and (aisWrapped['isFrag'] == False):
                
                # Set up our data structure
                data = {}
                
                for thisField, newName in self.__desiredData.iteritems():
                    if thisField in aisWrapped:
                        data.update({newName: aisWrapped[thisField]})
                
                # Set lastSeen
                data.update({'lastSeen': data['dts']})
                
                # Enqueue processed state data.
                self.enqueueData(self.updateState(aisWrapped['mmsi'], data))
    
    def run(self):
        for work in self.__psObj.listen():
            self.worker(work)

if __name__ == "__main__":
    # If we're enabled in config...
    
    if config.aisStateEngine['enabled'] == True:
        print("AIS state engine starting...")
        
        # Start up our AIS parser
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
    else:
        print("AIS state engine not enabled in config.")