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
from pprint import pprint


#################
# Configuration #
#################

# Which queue do we subscribe to?
targetSub = "ssrFeed"
targetHost = "127.0.0.1"

# How long should it take to expire planes in seconds.
expireTime = 300


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


    def enqueueData(self, statusData):
        """
        enqueueDate(statusData)
        
        Put status data on a queue for processing
        """
        
        #Debug print instead of dumping data onto another queue.
        print(json.dumps(statusData))
        
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
            
            # Set our datetime stamp for this data.
            data.update({"dts": ssrWrapped['dts']})
            
            # Automatically grab any emergency data we have ahead of time.
            if 'emergency' in ssrWrapped:
                # Inherit the emergency flag from anything with the emergency flag from ANY frame.
                data.update({'emergency': ssrWrapped['emergency']})
                
                # Get a mode A squawk emergency description if one exists.
                if 'aSquawkEmergency' in ssrWrapped:
                    data.update({'emergencyData': ssrWrapped['aSquawkEmergency']})
                
                # If we have more specific emergency data from an extended status squitter use it instead of a gneeric mode A squawk message.
                if 'es' in ssrWrapped:
                    esText = ["No emergency", # This really shouldn't come through without emergency = True.
                        "General emergency (sqwk 7700)",
                        "Lifeguard/Medical",
                        "Minimum Fuel",
                        "No comms (sqwk 7600)",
                        "Unlawful interference (sqwk 7500)",
                        "Downed aircraft",
                        "Reserved"]
                    
                    data.update({'emergencyData': esText[ssrWrapped['es']]})
            
            # Do we hvae mode s?
            if ssrWrapped['mode'] == "s":
                
                # Do we have data we care about?
                if ssrWrapped['df'] == 11:
                    
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                
                elif ssrWrapped['df'] == 17:
                    
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
                    
                    # Aircraft category
                    if 'heading' in ssrWrapped:
                        data.update({"heading": ssrWrapped['heading']})
                    
                    # Altitude
                    if 'alt' in ssrWrapped:
                        data.update({"alt": ssrWrapped['alt']})
                    
                    # Vertical rate data
                    if 'vertRate' in ssrWrapped:
                        data.update({"vertRate": ssrWrapped['vertRate']})
                    
                    # Velo
                    # Needs some more logic.
                    
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
                    
                    # Handle location data
                    # This needs a lot of logic.
                    
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
            
            elif (ssrWrapped['mode'] == "ac") and ('emergency' in ssrWrapped):
                
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
