#!/usr/bin/python

"""
mongoDump by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

try:
	import config
except:
	raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

import sys
import redis
import pymongo
import time
import json
import datetime
import traceback
from libAirSuck import asLog
from pprint import pprint

#Redis queue name
targetQ = "airReliable"

# Redis instance for queueing.
rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])

#Delay this many seconds if the queue is empty to prevent
#stupid amounts of CPU utilization.
checkDelay = config.connMongo['checkDelay']

#MongoDB config
connMongo = pymongo.MongoClient(config.connMongo['host'], config.connMongo['port'])
mDB = connMongo[config.connMongo['dbName']]
mDBColl = mDB[config.connMongo['coll']]

# Convert datetime objects expressed as a string back to datetime
def str2Datetime(strDateTime):
    """
    Convert utcnow() datetime string back to a datetime object.
    """
    retVal = None
    
    try:
        # Check the length of the string since frames received on the second sometimes lack the %f portion of the data.
        if (len(strDateTime) == 19):
            strDateTime = strDateTime + ".000000"
        
        # Attempt to convert the date.
        retVal = datetime.datetime.strptime(strDateTime, "%Y-%m-%d %H:%M:%S.%f")
    
    except:
        tb = traceback.format_exc()
        logger.log("Failed to convert string to datetime:\n%s" %tb)
    
    return retVal

# Decapsulate the JSON data.
def dejsonify(msg):
        return json.loads(msg)

# Insert records into specified mongo instance
def serializeADSB(entry):
        mDBColl.insert(entry)

# Set up the logger.
logger = asLog(config.connMongo['logMode'])

# If this mongo engine is enabled...
if config.connMongo['enabled'] == True:
    # Infinite fucking loop.
    logger.log("Dumping connector data from queue to MongoDB.")
    while(True) :
            try:
                    # Pull oldest entry from the queue.
                    dQd = rQ.rpop(config.connRel['qName'])
                    
                    # If we have no data sleep for our configured delay to save CPU.
                    if(dQd == None):
                        time.sleep(checkDelay)
                    else:
                            # We have data so we should break it out of JSON formatting.
                            xDqd = dejsonify(dQd)
                            xDqd['dts'] = str2Datetime(xDqd['dts'])
                            serializeADSB(xDqd)
                    
            except KeyboardInterrupt:
                quit()
            except:
                tb = traceback.format_exc()
                logger.log("Failed to pull from the Redis queue. Sleeping %s sec.\n%s" %(checkDelay, tb))
else:
    logger.log("The connector mongoDB engine is not enabled in the configuration.")
