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
        
        # Get our time
        thisTime = str(datetime.datetime.utcnow())
        
        # Create properly-formatted name for the state hash table we're creating.
        fullName = str('state:' + objName)
        
        # Do we have a firstSeen key?
        if self.redis.hsetnx(fullName, 'firstSeen', thisTime) == 0:
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
        
        pprint(statusData)
        
        return

    def worker(self, work):
        # Do work on the data returned from the subscriber.
        ssrJson = str(work['data'])
        
        # Get wrapped SSR data.
        ssrWrapped = json.loads(ssrJson)
        
        # Make sure we got good data from json.loads
        if (type(ssrWrapped) == dict):
            
            # Do we hvae mode s?
            if ssrWrapped['mode'] == "s":
                
                # Do we have data we care about?
                if ssrWrapped['df'] == 11:
                    
                    # Filter for the data we need:
                    data = {'df': 11}
                    
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                
                elif ssrWrapped['df'] == 17:
                    
                    # Filter for the data we need:
                    data = {'df': 17}
                    
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
            
            elif (ssrWrapped['mode'] == "ac") and ('emergency' in ssrWrapped):
                
                # Enqueue processed state data.
                self.enqueueData(self.updateState('A-' + ssrWrapped['aSquawk'], False))
            
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
