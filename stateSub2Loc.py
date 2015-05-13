#!/usr/bin/python

############
# Imports. #
############

import redis
import time
import json
import threading
from pprint import pprint

#################
# Configuration #
#################

# Which queue do we subscribe to?
targetSub = "airStateFeed"
targetHost = 'brick'

##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the ADSB channel for new data.
    """
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)
        
    def worker(self, work):
        #Do work on the data returned from the subscriber.
        stateJson = str(work['data'])
        stateWrapped = json.loads(stateJson)
        
        # Make sure we got good data from json.loads
        if (type(stateWrapped) == dict):
            locStr = ""
            
            if 'lat' in stateWrapped:
                if 'idInfo' in stateWrapped:
                    locStr = stateWrapped['idInfo'] + " [" + stateWrapped['addr'] + "]: "
                else:
                    locStr = "[" + stateWrapped['addr'] + "]: "
                    
                locStr = locStr + str(stateWrapped['lat']) + ", " + str(stateWrapped['lon'])
                
                if 'alt' in stateWrapped:
                    locStr = locStr + " @ " + str(stateWrapped['alt']) + "ft"
                    
                if 'vertRate' in stateWrapped:
                    signExtra = ""
                    
                    if stateWrapped['vertRate'] > 0:
                        signExtra = "+"
                        
                    locStr = locStr + " (" + signExtra + str(stateWrapped['vertRate']) + "ft/min)"
                
                if 'heading' in stateWrapped:
                    locStr = locStr + " - " + str(stateWrapped['heading']) + " deg"
                
                if 'category' in stateWrapped:
                    locStr = locStr + " ; cat " + stateWrapped['category']
                
                if 'vertStat' in stateWrapped:
                    locStr = locStr + " (" + stateWrapped['vertStat'] + ")"
                
                print(locStr)
        
        
    def run(self):
        for work in self.pubsub.listen():
            self.worker(work)

if __name__ == "__main__":
    print("airSuck state queue viewer starting...")
    r = redis.Redis(targetHost)
    client = SubListener(r, [targetSub])
    # We want the faote of our SubListener instance to be tied to the main thread process.
    client.daemon = True
    client.start()
    
    try:
        # Fix bug that doesn't allow Ctrl + C to kill the script
        while True: time.sleep(10)
    except KeyboardInterrupt:
        # Die incely.
        quit()
    except Exception as e:
        print("Unhandled exception:")
        pprint(e)
