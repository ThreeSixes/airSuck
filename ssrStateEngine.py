#!/usr/bin/python

############
# Imports. #
############

import redis
import time
import json
import threading
import binascii
from pprint import pprint

#################
# Configuration #
#################

# Which queue do we subscribe to?
targetSub = "ssrFeed"
targetHost = "127.0.0.1"


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
    
    def worker(self, work):
        # Do work on the data returned from the subscriber.
        ssrJson = str(work['data'])
        
        # Get wrapped SSR data.
        ssrWrapped = json.loads(ssrJson)
        
        # Make sure we got good data from json.loads
        if (type(ssrWrapped) == dict):
            
            # Get the hex data as a string
            pprint(ssrWrapped)
    
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
