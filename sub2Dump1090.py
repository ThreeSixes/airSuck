#!/usr/bin/python

"""
sub2Dump1090 by ThreeSixes (https://github.com/ThreeSixes)

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

import sys
import redis
import time
import json
import threading
import time
import traceback
from libAirSuck import asLog
from socket import socket
from pprint import pprint

#################
# Configuration #
#################


# Submit data to a dump1090 instance via TCP 30001
dump1090Dst = {
    "host": "127.0.0.1",
    "port": 30001,
    "reconnectDelay": 5
}

##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the SSR channel for new data.
    """
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        
        # Set up REDIS feed
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)

    def worker(self, work, dSock):
        """
        worker(self,work) dumps the incoming data fromt he queue to the open TCP socket for dump1090.
        """
        # Break our SSR wrapped data out from the Redis queue
        ssrJson = str(work['data'])
        ssrWrapped = json.loads(ssrJson)
        
        # Make sure we pared the JSON correctly.
        if (type(ssrWrapped) == dict):
            
            # If we have SSR data from dump1090...
            if ssrWrapped['type'] == "airSSR":
                
                # And if the data actually came from dump1090...
                if ssrWrapped['dataOrigin'] == "dump1090":
                    
                    # Define start of data char
                    dataHdr = "*"
                    
                    # Set the data body.
                    dataBody = ssrWrapped['data']
                    
                    # Do we have MLAT data coming in?
                    if 'mlatData' in ssrWrapped:
                        
                        # Set the header to an MLAT header
                        dataHdr = "@"
                        
                        # Prepend the MLAT data on the data body.
                        dataBody = ssrWrapped['mlatData'] + dataBody
                    
                    # Send the data over to the target dump1090
                    dSock.sendall((dataHdr + dataBody + ";\n"))

    def run(self):
        """
        run(self) is how we start the process. This creates a new thread to write data into.
        """
        
        # Set up socket.
        dump1090Sock = socket()
        
        # Infinite loop
        while True:
            try:
                # Attempt a connection.
                logger.log("Connecting to %s:%s" %(dump1090Dst["host"], dump1090Dst["port"]))
                
                # Connect up.
                dump1090Sock.connect((dump1090Dst["host"], dump1090Dst["port"]))
                logger.log("Connected.")
                
                # Handle incoming data.
                for work in self.pubsub.listen():
                    self.worker(work, dump1090Sock)
                
                dump1090Sock.close()
                
            except KeyboardInterrupt:
                quit()
                
            except:
                tb = traceback.format_exc()
                logger.log("Failed to connect to %s:%s\n%s" %(dump1090Dst["host"], dump1090Dst["port"], tb))
                logger.log("Sleeping %s sec" %dump1090Dst["reconnectDelay"])
                time.sleep(dump1090Dst["reconnectDelay"])

# Start up.
if __name__ == "__main__":
    # Set up the logger.
    logger = asLog('stdout')

    # Start up redis, create our threaded client, and start it.
    r = redis.Redis(host=config.connPub['host'], port=config.connPub['port'])
    client = SubListener(r, [config.connPub['qName']])
    client.daemon = True
    client.start()
    
    try:
        while True: time.sleep(10)
    except KeyboardInterrupt:
        # Die nicely.
        quit()
    except Exception:
        tb = traceback.format_exc()
        logger.log("Unexpected exception\n%s" %tb)