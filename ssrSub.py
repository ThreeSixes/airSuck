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
targetSub = "ssrFeed"

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
    print("ADSB subscription queue viewer starting...")
    r = redis.Redis()
    client = SubListener(r, [targetSub])
    client.start()
