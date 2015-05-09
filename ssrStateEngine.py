#!/usr/bin/python

############
# Imports. #
############

import redis
import time
import json
import threading
import binascii
import datetime
from cprMath import cprMath
from pprint import pprint


#################
# Configuration #
#################

# Which queue do we subscribe to?
targetHost = "brick"
targetSub = "ssrFeed"
destReliable = "airState"
destPubSub = "airStateFeed"

# How long should it take to expire planes in seconds.
expireTime = 300

# CPR stuff.
cprProc = cprMath()


##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the SSR channel for new incoming data.
    """
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)    
    
    def updateState(self, objName, cacheData):
        """
        updateState
        
        Update state engine with data from incoming frames given the data in the dict cacheData. objName is the name of the ICAO AA in hex, or emergency squawk code.
        
        Returns all data in the cache.
        """
        
        # Create properly-formatted name for the state hash table we're creating.
        fullName = str('state:' + objName)
        
        # Delete the original timestamp.
        thisTime = cacheData.pop('dts', None)
        
        # Set the first seen data.
        self.redis.hsetnx(fullName, 'firstSeen', thisTime)
        # Set last seen either way.
        self.redis.hset(fullName, 'lastSeen', thisTime)
        
        # Update or create cached data, if we have more than just a name
        if type(cacheData) == dict:
            
            # Set each specified value.
            for thisKey in cacheData:
                self.redis.hset(fullName, thisKey, cacheData[thisKey])
        
        # Set expiration on the hash entry.
        self.redis.expire(fullName, expireTime)
        
        retVal = self.redis.hgetall(fullName)
        retVal.update({'addr': objName})
        
        return retVal
    

    def pullState(self, objName):
        """
        pullState(objName)
        
        Pull state information for a given object name. Returns a dict with existing data.
        """
        
        # Try to pull data...
        dataPull = self.redis.hgetall('state:' + objName)
        
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
                
        return retVal
    

    def enqueueData(self, statusData):
        """
        enqueueDate(statusData)
        
        Put status data on a queue for processing
        """
        
        # Debug print instead of dumping data onto another queue.
        jsonData = json.dumps(statusData)
        #print(jsonData)
        try:
            self.redis.rpush(destReliable, jsonData)
            self.redis.publish(destPubSub, jsonData)
        except Exception as e:
            pprint(e)
        
        #if 'lat' in statusData:
        #    print(statusData['addr'] + " - " + \
        #        str(statusData['lat']) + ", " + str(statusData['lon']) + \
        #        ": eLat " + str(statusData['evenLat']) + ", eLon " + str(statusData['evenLon']) + \
        #        ", oLat " + str(statusData['oddLat']) + ", oLon " + str(statusData['oddLon']) +  \
        #        ", lastFmt " + str(statusData['lastFmt']))
        
        return
    

    def worker(self, work):
        # Do work on the data returned from the subscriber.
        ssrJson = str(work['data'])
        
        # Get wrapped SSR data.
        ssrWrapped = json.loads(ssrJson)
        
        # Make sure we got good data from json.loads
        if (type(ssrWrapped) == dict):
            
            # Set up our data structure
            data = {}
            
            # Do we hvae mode s?
            if ssrWrapped['mode'] == "s":
                
                # Do we have data we care about?
                if ssrWrapped['df'] == 11:
                    
                    # Try to get existing data.
                    data = self.pullState(ssrWrapped['icaoAAHx'])
                    
                    # Check for emergency conditions.
                    data.update(self.getEmergencyInfo(ssrWrapped))
                    
                    # Set the last sensor we got a frame from
                    data.update({"lastSrc": ssrWrapped['src']})
                    
                    # Set our datetime stamp for this data.
                    data.update({"dts": ssrWrapped['dts']})
                    
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                
                elif ssrWrapped['df'] == 17:
                    
                    # Try to get existing data.
                    data = self.pullState(ssrWrapped['icaoAAHx'])
                    
                    # Check for emergency conditions.
                    data.update(self.getEmergencyInfo(ssrWrapped))
                    
                    # Set the last sensor we got a frame from
                    data.update({"lastSrc": ssrWrapped['src']})
                    
                    # Set our datetime stamp for this data.
                    data.update({"dts": ssrWrapped['dts']})
                    
                    # Filter for the data we need:
                    # Mode A squawk code.
                    if 'aSquawk' in ssrWrapped:
                        data.update({"aSquawk": ssrWrapped['aSquawk']})
                    
                    # ID data
                    if 'idInfo' in ssrWrapped:
                        data.update({"idInfo": ssrWrapped['idInfo']})
                    
                    # Aircraft category
                    if 'category' in ssrWrapped:
                        data.update({"category": ssrWrapped['category']})
                    
                    # Aircraft heading
                    if 'heading' in ssrWrapped:
                        data.update({"heading": ssrWrapped['heading']})
                    
                    # Altitude
                    if 'alt' in ssrWrapped:
                        data.update({"alt": ssrWrapped['alt']})
                    
                    # Vertical rate data
                    if 'vertRate' in ssrWrapped:
                        data.update({"vertRate": ssrWrapped['vertRate']})
                    
                    # Velocity data
                    
                    # For airborne aircraft
                    if ssrWrapped['fmt'] == 19:
                        if 'gndspeed' in ssrWrapped:
                            data.update({"velo": ssrWrapped['gndspeed'], "veloType": "gnd"})
                        if 'airspeed' in ssrWrapped:
                            data.update({"velo": ssrWrapped['airspeed'], "veloType": "air", "airspeedRef": ssrWrapped['airspeedRef']})
                    # Deal with vehicles on the ground here...
                    
                    # Vertical status
                    # Needs moe logic
                    
                    # Supersonic?
                    if 'supersonic' in ssrWrapped:
                        data.update({"supersonic": ssrWrapped['supersonic']})
                    
                    # Surveillance status
                    if 'ss' in ssrWrapped:
                        data.update({"survStat": ssrWrapped['ss']})
                    
                    # Work on location data.
                    # This needs a decent amount of logic
                    
                    # UTC flag
                    if 'utc' in ssrWrapped:
                        data.update({"utc": ssrWrapped['utc']})
                    
                    
                    # This needs more logic for decoding CPR, etc.
                    if 'evenOdd' in ssrWrapped:
                        
                        # Update data with even and odd raw values.
                        if ssrWrapped['evenOdd'] == 0:
                            # Set even data.
                            data.update({"evenLat": ssrWrapped['rawLat'], "evenLon": ssrWrapped['rawLon'], "evenTs": ssrWrapped['dts'], "lastFmt": ssrWrapped['evenOdd']})
                        else:
                            # Set odd data.
                            data.update({"oddLat": ssrWrapped['rawLat'], "oddLon": ssrWrapped['rawLon'], "oddTs": ssrWrapped['dts'], "lastFmt": ssrWrapped['evenOdd']})
                        
                        # This functionality needs to be broken out as a function.
                        
                        # If we have even and odd lat/lon data
                        if ("evenTs" in data) and ("oddTs" in data):
                            
                            # Pull even and odd data.
                            evenData = [data['evenLat'], data['evenLon']]
                            oddData = [data['oddLat'], data['oddLon']]
                            
                            #if data['lastFmt'] == 0:
                            #    hackFmt = 1
                            #else:
                            #    hackFmt = 0
                            
                            hackFmt = data['lastFmt']
                            
                            # Decode location
                            locData = cprProc.decodeCPR(evenData, oddData, hackFmt, False)
                            
                            # Location data
                            if type(locData) == list:
                                # Set location data.
                                data.update({"lat": locData[0], "lon": locData[1]})
                        
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                    
                    # Figure out how to clear the emergency flag if we no longer have an emergency.
            
            elif (ssrWrapped['mode'] == "ac") and ('emergency' in ssrWrapped):
                
                # Check for emergency conditions.
                data.update(self.getEmergencyInfo(ssrWrapped))
                
                # Enqueue processed state data.
                self.enqueueData(self.updateState('A-' + ssrWrapped['aSquawk'], data))
            
            # Get the hex data as a string
            #pprint(ssrWrapped)
    
    def run(self):
        for work in self.pubsub.listen():
            self.worker(work)

if __name__ == "__main__":
    print("SSR state engine starting...")
    
    # Set up Redis queues.
    r = redis.Redis(host=targetHost)
    
    # Start up our ADS-B parser
    client = SubListener(r, [targetSub])
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
