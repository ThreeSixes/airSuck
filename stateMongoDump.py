#!/usr/bin/python
import sys
import redis
import pymongo
import time
import json
import datetime
from pprint import pprint

#Redis queue name
targetQ = "airState"

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
def serializeState(entry):
        mDB.airState.insert(entry)

# Infinite fucking loop.
print("Dumping state data from queue to MongoDB.")
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
                    serializeState(xDqd)
                
        except KeyboardInterrupt:
            quit()
        except Exception as e:
            print("Failed to pull from the Redis queue. Sleeping " + str(checkDelay) + " sec")
            pprint(e)
            pprint(sys.exc_info())
