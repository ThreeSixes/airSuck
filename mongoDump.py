#!/usr/bin/python

"""
mongoDump by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

import sys
import redis
import pymongo
import time
import json
import datetime
from pprint import pprint

#Redis queue name
targetQ = "airReliable"

# Redis instance for queueing.
rQ = redis.StrictRedis()

#Delay this many seconds if the queue is empty to prevent
#stupid amounts of CPU utilization.
checkDelay = 0.1

#MongoDB config
mDB = pymongo.MongoClient().airSuck

# Convert datetime objects expressed as a string back to datetime
def toDatetime(strDateTime):
    """
    Convert utcnow() datetime string back to a datetime object.
    """
    return datetime.datetime.strptime(strDateTime, "%Y-%m-%d %H:%M:%S.%f")

# Decapsulate the JSON data.
def dejsonify(msg):
        return json.loads(msg)

# Insert records into specified mongo instance
def serializeADSB(entry):
        mDB.airSSR.insert(entry)

# Infinite fucking loop.
print("Dumping SSR data from queue to MongoDB.")
while(True) :
        try:
                # Pull oldest entry from the queue.
                dQd = rQ.rpop(targetQ)
    
                # If we have no data sleep for our configured delay to save CPU.
                if(dQd == None):
                    time.sleep(checkDelay)
                else:
                        # We have data so we should break it out of JSON formatting.
                        xDqd = dejsonify(dQd)
                        xDqd['dts'] = toDatetime(xDqd['dts'])
                        serializeADSB(xDqd)
                
        except KeyboardInterrupt:
            quit()
        except:
            print("Failed to pull from the Redis queue. Sleeping " + str(checkDelay) + " sec")
            pprint(sys.exc_info())
