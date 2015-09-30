#!/usr/bin/python

"""
sub2parse by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

############
# Imports. #
############

import sys
sys.path.append("..")

try:
	import config
except:
	raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

import redis
import time
import json
import threading
import binascii
from pprint import pprint
from libAirSuck import ssrParse


#################
# Configuration #
#################

# Set up the SSR parser
ssrEngine = ssrParse()
# Turn on decoding of names
#ssrEngine.setReturnNames(True)

##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the SSR channel for new data formatted as a hex string
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
            if ssrWrapped['type'] == "airSSR":
                # Set up dict to hold our reprocessed data.
                ssrParsed = {}
                
                # Get relevant data added by sources, etc.
                ssrParsed.update({"src": ssrWrapped['src']})
                ssrParsed.update({"dts": ssrWrapped['dts']})
                ssrParsed.update({"type": ssrWrapped['type']})
                ssrParsed.update({"dataOrigin": ssrWrapped['dataOrigin']})
                ssrParsed.update({"data": ssrWrapped['data']})
                
                # Get the hex data as a string
                strMsg = ssrWrapped['data']
                
                # Convert the ASCII hex data to a byte array.
                binData = bytearray(binascii.unhexlify(strMsg))
                
                # Parse the SSR data as a dict.
                parsed = ssrEngine.ssrParse(binData)
                
                # Add the processed fields to our existing info.
                ssrParsed.update(parsed)
                
                # Now sort the data by key alphabetically for easy viewing.
                sorted(ssrParsed)
                
                # Flatten the data so it's more easily searched.
                jsonData = json.dumps(ssrParsed)
                
                # Dump the data
                print(jsonData)
    
    def run(self):
        for work in self.pubsub.listen():
            self.worker(work)

if __name__ == "__main__":
    print("ADSB subscription queue data parsing test engine starting...")
    
    # Set up Redis queues.
    r = redis.Redis(host=config.connPub['host'], port=config.connPub['port'])
    
    # Start up our ADS-B parser
    client = SubListener(r, [config.connPub['qName']])
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
