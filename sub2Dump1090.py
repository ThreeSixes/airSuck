#!/usr/bin/python

############
# Imports. #
############

import sys
import redis
import time
import json
import threading
import time
from socket import socket
from pprint import pprint

#################
# Configuration #
#################

# Which queue do we subscribe to?
targetSub = "ssrFeed"

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
                print("Connecting to " + dump1090Dst["host"] + ":" + str(dump1090Dst["port"]))
                
                # Connect up.
                dump1090Sock.connect((dump1090Dst["host"], dump1090Dst["port"]))
                print("Connected.")
                
                # Handle incoming data.
                for work in self.pubsub.listen():
                    self.worker(work, dump1090Sock)
                    
                dump1090Sock.close()
                
            except KeyboardInterrupt:
                quit()
                
            except Exception as x:
                print("Failed to connect to " + dump1090Dst["host"] + ":" + str(dump1090Dst["port"]))
                print type(x)
                print x
                print("Sleeping " + str(dump1090Dst["reconnectDelay"]) + " sec")
                time.sleep(dump1090Dst["reconnectDelay"])

# Start up.
if __name__ == "__main__":
    
    # Start up redis, create our threaded client, and start it.
    r = redis.Redis()
    client = SubListener(r, [targetSub])
    client.start()