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
        adsbJson = str(work['data'])
        adsbWrapped = json.loads(adsbJson)
        
        # Make sure we got good data from json.loads
        if (type(adsbWrapped) == dict):
            print(str(adsbWrapped))
        
        
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
