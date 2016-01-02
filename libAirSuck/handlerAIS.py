import sys
sys.path.append("..")

try:
    import config
except:
    raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

import hashlib
import datetime
import redis
import traceback
import binascii
import json
import asLog
import aisParse
import re

class handlerAIS:
    def __init__(self, logMode, enqueOn=True):
        # Set up logger.
        self.__logger = asLog.asLog(logMode)
        
        # Redis queues and entities
        self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
        self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
        self.__frag = redis.StrictRedis(host=config.aisSettings['fragHost'], port=config.aisSettings['fragPort'])
        self.__dedupe = redis.StrictRedis(host=config.aisSettings['dedupeHost'], port=config.aisSettings['dedupePort'])
        
        # Load AIS parser.
        self.__aisParser = aisParse.aisParse()
        
        # Debug flag.
        self.__debugOn = False
        
        # Do we want to actually enqueue data?
        self.__enqueueOn = enqueOn
        
        # Regex to verify AIS data.
        self.__regexAIS = re.compile("!AIVD[MO]\\,[1-9]{1}\\,[1-9]{1}\\,([0-9]{0,1})\\,[0-3A-B]{1}\\,([0-9\\:\\;\\<\\=\\>\\?\\@A-W\\`a-w]+)\\,[0-5]\\*[A-F0-9]{2}")
    
    # Convert the message to JSON format
    def __jsonify(self, dataDict):
        """
        Convert a given dictionary to a JSON string.
        """
        
        retVal = ""
        
        try:
            retVal = json.dumps(dataDict)
        
        except Exception as e:
            tb = traceback.format_exc()
            self.__logger.log("Failed to JSON wrap %s: %s" %(dataDict, tb))
        
        return retVal
    
    # Defragment AIS messages.
    def __defragAIS(self, fragment):
        """
        Attempt to assemble AIS data from a number of fragments. Fragment is a decapsulated AIS message fragment.
        """
        
        # By default assume we don't have an assembled payload
        isAssembled = False
        
        # Set up a hashed version of our data given the host the data arrived on, the fragment count, and the message ID.
        fHash = "aisFrag-" + hashlib.md5(fragment['src'] + "-" + str(fragment['fragCount']) + '-' + str(fragment['messageID'])).hexdigest()
        
        # Create a fragment name.
        fragName = str(fragment['fragNumber'])
        
        # Attempt to get data from our hash table.
        hashDat = self.__frag.hgetall(fHash)
        hashDatLen = len(hashDat)
        
        # If we already have a fragment...
        if hashDatLen > 0:
            # If we have all the fragments we need...
            if hashDatLen == (fragment['fragCount'] - 1):
            
                # Create a holder for our payload
                payload = ""
                
                # Push our new fragment into the dict.
                hashDat.update({fragName: fragment['payload']})
                
                # Assemble the stored fragments in order.
                for i in range(1, fragment['fragCount'] + 1):
                    payload = payload + hashDat[str(i)]
                
                # Make sure we properly reassign the payload to be the full payload.
                fragment.update({'payload': payload})
                
                # Set assembled flag.
                isAssembled = True
            
            else:
                # Since we don't have all the fragments we need add the latest fragment to the list.
                self.__frag.hset(fHash, fragName, fragment['payload'])
        
        else:
            # Create our new hash object.
            self.__frag.hset(fHash, fragName, fragment['payload'])
        
        # If we have an assembled payload clean up some info and queue it.
        if isAssembled:
            # Nuke the hash object.
            self.__frag.expire(fHash, -1)
            
            # Update the fragment data.
            fragment.update({'isAssembled': True, 'isFrag': False, 'data': payload})
            
            # Set the fragment to include parsed data.
            fragment = self.__aisParser.aisParse(fragment)
            
            # The fragment number is no longer valid since the count tells us how many we had.
            fragment.pop('fragNumber')
            
            # Enqueue our assembled payload.
            self.__queueAIS(fragment)
        
        else:
            # Set the expiration time on the fragmoent hash.
            self.__frag.expire(fHash, config.aisSettings['fragTTLSec'])   
    
    # Convert the data we want to send to JSON format.
    def __queueAIS(self, msg):
        """
        Drop the msg on the appropriate redis connector queue(s) as a JSON string.
        """
        
        # Create a new dict to enqueue so the original doesn't get manipulated.
        enqueueMe = {}
        enqueueMe.update(msg)
        
        # If we have a payload specified drop it.
        if 'payload' in msg:
            enqueueMe.pop('payload')
        
        # Build a JSON string.
        jsonMsg = self.__jsonify(enqueueMe)
        
        # If we have something other than an empty string...
        if jsonMsg != "":
            
            # Should we actually enqueue the data?
            if self.__enqueueOn:
                # Set up a hashed version of our data.
                dHash = "ais-" + hashlib.md5(enqueueMe['data']).hexdigest()
                
                # If we dont' already have a frame like this one OR the frame is a fragment...
                if (self.__dedupe.exists(dHash) == False) or (enqueueMe['isFrag'] == True):
                    
                    # Make sure we're not handling a fragment. Since some fragments can be short there's a good chance of collision.
                    if enqueueMe['isFrag'] == False:
                        # Set the key and insert lame value.
                        self.__dedupe.setex(dHash, config.aisSettings['dedupeTTLSec'], "X")
                        
                        # If we are configured to use the connector mongoDB forward the traffic to it.
                        if config.connMongo['enabled'] == True:
                            self.__rQ.rpush(config.connRel['qName'], jsonMsg)
                            
                        # Put data on the pub/sub queue.
                        self.__psQ.publish(config.connPub['qName'], jsonMsg)
                        
                        # If we're debugging
                        if self.__debugOn:
                            self.__logger.log("Enqueue: %s" %jsonMsg)
            
            else:
                # Just dump the JSON data as a string.
                self.__logger.log(jsonMsg)
        
        return 
    
    def setDebug(self, debugOn):
        """
        Turn debugging on or off.
        """
        
        if debugOn == True:
            self.__debugOn = True
            self.__logger.log("handlerAIS debugging on.")
        else:
            self.__debugOn = False
            self.__logger.log("handlerAIS debugging off.")
        
        return
    
    def handleAISDict(self, aisData):
        """
        Handle an incoming AIS dictionary. Returns true if that data was handled, if not false. A return value of true does not indicate the data was queued because it may have been dropped by deduplication.
        """
        
        # Set up return value.
        retVal = False
        
        # Check the AIS data to make sure we actually have AIS.
        if self.__regexAIS.match(aisData['data']):
            
            # If we have an unfragmented frame process it. If not, handle the fragment.
            if (aisData['fragCount'] == 1) and (aisData['fragNumber'] == 1):
                try:
                    # Parse our AIS data and add it to the stream.
                    aisData.update(self.__aisParser.aisParse(aisData))
                    
                    # Enqueue our data.
                    self.__queueAIS(aisData)
                    
                    # Seems to have worked.
                    retVal = True
                
                except Exception as e:
                    # If we're debugging
                    if self.__debugOn:
                        tb = traceback.format_exc()
                        self.__logger.log("Error handling AIS data: %s\n%s" %(aisData, tb))
                        
                        raise e
            
            else:
                try:
                    # Enqueue our fragment.
                    self.__queueAIS(aisData)
                    
                    # Since we aren't frame 1 of 1 for a given message we're a fragment.
                    aisData['isFrag'] = True
                    
                    # Handle fragments.
                    self.__defragAIS(aisData)
                    
                    # Seems to have worked.
                    retVal = True
                
                except Exception as e:
                    # If we're debugging
                    if self.__debugOn:
                        tb = traceback.format_exc()
                        self.__logger.log("Error handling AIS data: %s\n%s" %(aisData, tb))
                    
                    raise e
        
        else:
            # if we're debugging...
            if self.__debugOn:
                logger.log("AIS frame didn't match regex.")
        
        # Return success
        return retVal
    