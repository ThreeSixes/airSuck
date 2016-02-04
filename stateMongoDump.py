#!/usr/bin/python

"""
stateMongoDump by ThreeSixes (https://github.com/ThreeSixes)

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

# Set up the logger.
logger = asLog(config.stateMongo['logMode'])

# Redis instance for queueing.
rQ = redis.StrictRedis(host=config.stateRel['host'], port=config.stateRel['port'])

#Delay this many seconds if the queue is empty to prevent
#stupid amounts of CPU utilization.
checkDelay = config.stateMongo['checkDelay']

#MongoDB config
stateMongo = pymongo.MongoClient(config.stateMongo['host'], config.stateMongo['port'])
mDB = stateMongo[config.stateMongo['dbName']]
mDBColl = mDB[config.stateMongo['coll']]

# Convert datetime objects expressed as a string back to datetime
def toDatetime(strDateTime):
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
def serializeState(entry):
        mDBColl.insert(entry)

# If the mongo state dumper is enabled...
if config.stateMongo['enabled'] == True:

    # Infinite fucking loop.
    logger.log("Dumping state data from queue to MongoDB.")
    while(True) :
            try:
                    # Pull oldest entry from the queue.
                    dQd = rQ.rpop(config.stateRel['qName'])
                    
                    # If we have no data sleep for our configured delay to save CPU.
                    if(dQd == None):
                        time.sleep(checkDelay)
                    else:
                        # We have data so we should break it out of JSON formatting.
                        xDqd = dejsonify(dQd)
                        
                        if 'firstSeen' in xDqd:
                            if xDqd['firstSeen'] != 'None':
                                xDqd['firstSeen'] = toDatetime(xDqd['firstSeen'])
                        
                        if 'lastSeen' in xDqd:
                            if xDqd['lastSeen'] != 'None':
                                xDqd['lastSeen'] = toDatetime(xDqd['lastSeen'])
                        
                        if 'evenTs' in xDqd:
                            if xDqd['evenTs'] != 'None':
                                xDqd['evenTs'] = toDatetime(xDqd['evenTs'])
                        
                        if 'oddTs' in xDqd:
                            if xDqd['oddTs'] != 'None':
                                xDqd['oddTs'] = toDatetime(xDqd['oddTs'])
                        
                        serializeState(xDqd)
                    
            except KeyboardInterrupt:
                quit()
            except:
                tb = traceback.format_exc()
                logger.log("Failed to pull from the Redis queue. Sleeping %s sec\n%s" %(checkDelay, tb))
                

else:
    logger.log("Connector mongoDB engine not enabled in configuration.")