#!/usr/bin/python

"""
ssrStateEngine by ThreeSixes (https://github.com/ThreeSixes)

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

import redis
import time
import json
import threading
import binascii
import datetime
import traceback
from libAirSuck import cprMath
from libAirSuck import airSuckUtil
from libAirSuck import asLog
from pprint import pprint


##################
# Global objects #
##################

# CPR stuff.
cprProc = cprMath()

##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the SSR channel for new incoming data.
    """
    def __init__(self, channels):
        threading.Thread.__init__(self)
        self.__asu = airSuckUtil()
        
        # Redis queues and entities
        self.__channels = channels
        self.__psQ = None
        self.__sPsQ = None
        self.__sRQ = None
        self.__redHash = None
        self.__psObj = None
        
        # Keep running.
        self.__keepRunning = True
        
        # Conversion table for type fixing. field -> type
        self.__subject2Type = {
            'lat': float,
            'lon': float,
            'heading': float,
            'velo': float,
            'alt': int,
            'evenLat': int,
            'evenLon': int,
            'gndspeed': int,
            'lastFmt': int,
            'oddLat': int,
            'oddLon': int,
            'ss': int,
            'supersonic': int,
            'survStat': int,
            'vertRate': int,
            'fs': int,
            'utcSync': int,
            'icaoAAInt': int,
            'icaoAACC': str,
            'icaoAACountry': str,
            'srcLat': float,
            'srcLon': float
        }
        
        # Float rounding table for type fixer.
        self.__subject2Round = {
            'heading': 1,
            'velo': 1
        }
    
    def updateState(self, objName, cacheData):
        """
        Update state engine with data from incoming frames given the data in the dict cacheData. objName is the name of the ICAO AA in hex, or emergency squawk code.
        
        Returns all data in the cache.
        """
        
        # Blank dictionary.
        retVal = {}
        
        try:
            # Create properly-formatted name for the state hash table we're creating.
            fullName = str('ssrState-' + objName)
            
            # Delete the original timestamp.
            thisTime = cacheData.pop('dts', None)
            
            # Set the first seen data, also figure out if this is the first time we've seen this vehicle since the expire time.
            isNew = self.__redHash.hsetnx(fullName, 'firstSeen', thisTime)
            
            # Update or create cached data, if we have more than just a name
            if type(cacheData) == dict:
                
                # If it's new...
                if isNew == 1:
                    
                    # If we're debugging...
                    if config.ssrStateEngine['debug']:
                        # Log new contact.
                        logger.log("New SSR contact: %s" %objName)
                    
                    # Make sure we have a numeric ICAO AA at this point.
                    #if 'icaoAAInt' in cacheData:
                    #    # Add our metadata about the ICAO AA we have.
                    #    cacheData.update(self.__asu.getICAOMeta(cacheData['icaoAAInt']))
                    #
                    #else:
                    #    # make sure we also have an ICAO AA in hex format...
                    #    if 'icaoAAHx' in cacheData:
                    #        # Get the ICOA AA in integer format
                    #        icaoAAInt = int(cacheData['icaoAAHx'], 16)
                    #        
                    #        # If we're debugging...
                    #        if config.ssrStateEngine['debug']:
                    #            logger.log("Missing icaoAAInt for %s. Got %s." %(cacheData['icaoAAHx'], icaoAAInt))
                    #        
                    #        # Add it to our cache data...
                    #        cacheData.update({'icaoAAInt': icaoAAInt})
                    #        
                    #        # Add our metadata about the ICAO AA we have.
                    #        cacheData.update(self.__asu.getICAOMeta(cacheData['icaoAAInt']))
                
                # If we somehow don't have the CC set we should set it.
                if not ('icaoAACC' in cacheData):
                    try:
                        icaoAAInt = int(objName, 16)
                        cacheData.update(self.__asu.getICAOMeta(icaoAAInt))
                        
                        # Are we debugging?
                        if config.ssrStateEngine['debug']:
                            # And if we now have ICAO AA CC metadata
                            if ('icaoAACC' in cacheData) and (isNew == 1):
                                logger.log("Flag of %s is %s." %(objName, cacheData['icaoAACC']))
                    
                    except:
                        if config.ssrStateEngine['debug']:
                            tb = traceback.format_exc()
                            logger.log("Failed to set ICAO AA CC:\n%s" %tb)
                
                # Set all the remaining values in the cache.
                self.__redHash.hmset(fullName, cacheData)
            
            # Set expiration on the hash entry.
            self.__redHash.expire(fullName, config.ssrStateEngine['hashTTL'])
            
            # Get all the data from our hash.
            retVal = self.__redHash.hgetall(fullName)
            
            # Add the address.
            retVal.update({'addr': objName})
            
            # Adjust datatypes to be correct since redis stores everything as a string.
            retVal = self.fixDataTypes(retVal)
        
        except:
            tb = traceback.format_exc()
            logger.log("Blew up trying to update data in Redis.\n%s" %tb)
        
        return retVal
    

    def pullState(self, objName):
        """
        Pull state information for a given object name. Returns a dict with existing data.
        """
        
        # Try to pull data...
        dataPull = self.__redHash.hgetall('ssrState-' + objName)
        
        # Make sure we have some sort of data.
        if type(dataPull) == dict:
            retVal = dataPull
        
        else:
            # If not, return a blank dict.
            retVal = {}
        
        return retVal
    
    def getEmergencyInfo(self, data):
        """
        Get stateful emergency info for a given state entry.
        
        Returns a dict containing emergency info.
        """
        
        retVal = {}
        
        try:
            
            # Automatically grab any emergency data we have ahead of time.
            if 'emergency' in data:
                # Inherit the emergency flag from anything with the emergency flag from ANY frame.
                retVal.update({'emergency': data['emergency']})
                    
                # Get a mode A squawk emergency description if one exists.
                if 'aSquawkEmergency' in data:
                    retVal.update({'emergencyData': data['aSquawkEmergency']})
                    
                # If we have more specific emergency data from an extended status squitter use it instead of a gneeric mode A squawk message.
                if 'es' in data:
                    esText = ["No emergency", # This really shouldn't come through without emergency = True.
                        "General emergency (sqwk 7700)",
                        "Lifeguard/Medical",
                        "Minimum Fuel",
                        "No comms (sqwk 7600)",
                        "Unlawful interference (sqwk 7500)",
                        "Downed aircraft",
                        "Reserved"]
                        
                    retVal.update({'emergencyData': esText[data['es']]})
            else:
                # Set emergency to false if there's no emergency.
                retVal = {'emergency': False}
        
        except:
            tb = traceback.format_exc()
            logger.log("Caught exception getting emergency state info:\n%s" %tb)
        
        return retVal
    
    # Convert datetime objects expressed as a string back to datetime
    def str2Datetime(self, strDateTime):
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
    
    def fixDataTypes(self, statusData):
        """
        Converts data from strings to their approriate datatypes. This is necessary since REDIS stores everything as a string in hash tables.
        """
        
        retVal = statusData
        
        try:
            # Check for boolean-based data.
            if 'supersonic' in retVal:
                retVal['supersonic'] = self.str2Bool(retVal['supersonic'])
            
            if 'emergency' in retVal:
                retVal['emergency'] = self.str2Bool(retVal['emergency'])
                
            # For each subject we want, try to convert.
            for subject in self.__subject2Type:
                # Run the conversion.
                if subject in retVal:
                    retVal[subject] = self.__subject2Type[subject](retVal[subject])
            
            # For each subject we want, try to convert.
            for subject in self.__subject2Round:
                if subject in retVal:
                    retVal[subject] = round(retVal[subject], self.__subject2Round[subject])
        except:
            tb = traceback.format_exc()
            logger.log("Choked fixing data types.\n%s" %tb)
        
        return retVal

    def enqueueData(self, statusData):
        """
        Put status data on a queue for processing
        """
        
        # Debug print instead of dumping data onto another queue.
        jsonData = json.dumps(statusData)
        
        # Publish the data on the queue.
        self.__sPsQ.publish(config.statePub['qName'], jsonData)
        
        # If we actually want to store the state data in MongoDB...
        if config.stateMongo['enabled'] == True:
            
            # We don't want to store mode a metadata in the DB, so just pull it off the dict.
            if 'aSquawkMeta' in statusData:
                statusData.pop('aSquawkMeta', None)
            
            jsonData = json.dumps(statusData)
            self.__sRQ.rpush(config.stateRel['qName'], jsonData)
            
        return

    def str2Bool(self, thisStr):
        """
        Convert a string representing a boolean value to a boolean value. If the string is "True" or "true" this returns True. Else it returns False.
        """
        
        retVal = False
        
        # Check for boolean-based data.
        if (thisStr == "True") or (thisStr == "true"):
            retVal = True
        
        return retVal

    def crcInt2Hex(self, crcInt):
        """
        Convert the CRC value as in intteger to a hex string.
        Returns a hex string.
        """
        
        return binascii.hexlify(chr((crcInt >> 16) & 0xff) + chr((crcInt >> 8) & 0xff) + chr((crcInt & 0xff)))
    
    def worker(self, work):
        """
        Given an SSR entry do some work.
        """
        try:
            # Do work on the data returned from the subscriber.
            ssrJson = str(work['data'])
            
            # Default value for ssrWrapped that cause the JSON to no be processed unless it's decoded into a dict.
            ssrWrapped = None
            
            try:
                # Get wrapped SSR data.
                ssrWrapped = json.loads(ssrJson)
            
            except ValueError:
                if config.ssrStateEngine['debug']:
                    tb = traceback.format_exc()
                    logger.log("Failed to parse JSON string to dict:\n%s" %tb)
            
            except:
                tb = traceback.format_exc()
                logger.log("Exception parsing JSON data:\n%s" %tb)
            
            # Make sure we got good data from json.loads
            if (ssrWrapped != None) and (type(ssrWrapped) == dict):
                
                try:
                    # Make sure we have SSR data...
                    if ssrWrapped['type'] == "airSSR":
                        
                        # Set up our data structure
                        data = {}
                        
                        ssrWrapped = self.fixDataTypes(ssrWrapped)
                        
                        # Add the type specifier to our data.
                        data.update({'type': ssrWrapped['type']})
                        
                        # Do we hvae mode s?
                        if ssrWrapped['mode'] == "s":
                            
                            # Save space for mode A metadata.
                            metaData = {}
                            
                            # Set our good CRC flag to false by default.
                            crcGood = False
                            
                            # Do we have a matching CRC value?
                            if ssrWrapped['frameCrc'] == ssrWrapped['cmpCrc']:
                                # See if we have a DF type that doesn't XOR the transmitter's ICAO address with the CRC.
                                if ssrWrapped['df'] in (17, 18, 19):
                                    # Make sure we actually have an AA.
                                    if 'icaoAAHx' in ssrWrapped:
                                        crcGood = True
                                        
                                        # Try to pull existing data!
                                        data.update(self.pullState(ssrWrapped['icaoAAHx']))
                                
                            else:
                                # See if we have a DF type that XORs the transmitter's ICAO address with the CRC.
                                if ssrWrapped['df'] in (0, 4, 5, 20, 21):
                                    # XOR the computed and frame CRC values to get a potential ICAO AA
                                    potAA = self.crcInt2Hex(ssrWrapped['frameCrc'] ^ ssrWrapped['cmpCrc'])
                                    
                                    # See if we're aware of the potential valid AA.
                                    data.update(self.pullState(potAA))
                                    
                                    # If we have info on the AA, load it.
                                    if len(data) > 0:
                                        # Make sure we assign the icaoAAHx value, and indicate we have a good CRC value.
                                        ssrWrapped.update({'icaoAAHx': potAA})
                                        crcGood = True
                            
                            # Account for DF types that we aren't sure about CRC data that could contain good stuff.
                            if ssrWrapped['df'] in (11, 16):
                                crcGood = True
                            
                            if crcGood == False:
                                logger.log("Bad CRC detected in frame:\n DF %s: %s" %(ssrWrapped['df'], ssrWrapped['data']))
                            
                            # Get mode A metadata.
                            if 'aSquawk' in ssrWrapped:
                                # Try to get metadata from the squawk code...
                                aMeta = self.__asu.modeA2Meta(ssrWrapped['aSquawk'], self.__asu.regionUSA)
                                
                                # If we have usable data, add it.
                                if aMeta != None:
                                    # Add the new metadata from the mode A squawk to our global metadata dictionary.
                                    data.update({'aSquawkMeta': aMeta})
                            
                            # If we have an aircraft address specified and a good CRC...
                            if ('icaoAAHx' in ssrWrapped) and (crcGood == True):
                                
                                # ICAO AA as integer if we have it.
                                if 'icaoAAInt' in ssrWrapped:
                                    data.update({"icaoAAInt": ssrWrapped['icaoAAInt']})
                                
                                # Mode A squawk code if we have one!
                                if 'aSquawk' in ssrWrapped:
                                    data.update({"aSquawk": ssrWrapped['aSquawk']})
                                
                                # Vertical status data
                                if 'vertStat' in ssrWrapped:
                                    data.update({"vertStat": ssrWrapped['vertStat']})
                                
                                # Category if we have one!
                                if 'category' in ssrWrapped:
                                    data.update({"category": ssrWrapped['category']})
                                
                                # idIfno if we have it!
                                if 'idInfo' in ssrWrapped:
                                    data.update({"idInfo": ssrWrapped['idInfo']})
                                
                                # Client name data
                                if 'clientName' in ssrWrapped:
                                    data.update({"lastClientName": ssrWrapped['clientName']})
                                
                                # ICAO AA country code
                                if 'icaoAACC' in ssrWrapped:
                                    data.update({"icaoAACC": ssrWrapped['icaoAACC']})
                                
                                # ICAO AA country
                                if 'icaoAACountry' in ssrWrapped:
                                    data.update({"icaoAACountry": ssrWrapped['icaoAACountry']})
                                
                                # Check for emergency conditions.
                                data.update(self.getEmergencyInfo(ssrWrapped))
                                
                                # Set the last sensor we got a frame from
                                data.update({"lastSrc": ssrWrapped['src']})
                                
                                # Set our datetime stamp for this data.
                                data.update({"dts": ssrWrapped['dts']})
                                
                                # Set our datetime stamp for this data.
                                data.update({"entryPoint": ssrWrapped['entryPoint']})
                                
                                # Set our lastSeen time stamp for this data.
                                data.update({"lastSeen": ssrWrapped['dts']})
                                
                                # Aircraft heading
                                if 'heading' in ssrWrapped:
                                    data.update({"heading": ssrWrapped['heading'], "headingMeta": "ADS-B"})
                                
                                # Altitude
                                if 'alt' in ssrWrapped:
                                    data.update({"alt": ssrWrapped['alt']})
                                
                                # Vertical rate data
                                if 'vertRate' in ssrWrapped:
                                    data.update({"vertRate": ssrWrapped['vertRate']})
                                
                                # Flight status data
                                if 'fs' in ssrWrapped:
                                    data.update({"fs": ssrWrapped['fs']})
                                    
                                # Source position data
                                if ('srcLat' in ssrWrapped) and ('srcLon' in ssrWrapped) and ('srcPosMeta' in ssrWrapped):
                                    data.update({'srcLat': float(ssrWrapped['srcLat']), 'srcLon': float(ssrWrapped['srcLon']), 'srcPosMeta': ssrWrapped['srcPosMeta']})
                                
                                # For airborne aircraft
                                if ((ssrWrapped['df'] == 17) or (ssrWrapped['df'] == 18)) and (ssrWrapped['fmt'] == 19):
                                    if 'gndspeed' in ssrWrapped:
                                        data.update({"velo": ssrWrapped['gndspeed'], "veloType": "gnd", "veloMeta": "ADS-B"})
                                    if 'airspeed' in ssrWrapped:
                                        data.update({"velo": ssrWrapped['airspeed'], "veloType": "air", "airspeedRef": ssrWrapped['airspeedRef'], "veloMeta": "ADS-B"})
                                
                                # Deal with vehicles on the ground here...
                                
                                
                                # Supersonic?
                                if 'supersonic' in ssrWrapped:
                                    data.update({"supersonic": ssrWrapped['supersonic']})
                                
                                # Surveillance status
                                if 'ss' in ssrWrapped:
                                    data.update({"survStat": ssrWrapped['ss']})
                                
                                # UTC flag
                                if 'utc' in ssrWrapped:
                                    data.update({"utc": ssrWrapped['utc']})
                                
                                # Decode location data.
                                if 'evenOdd' in ssrWrapped:
                                    
                                    # Update data with even and odd raw values.
                                    if ssrWrapped['evenOdd'] == 0:
                                        # Set even data.
                                        data.update({"evenLat": ssrWrapped['rawLat'], "evenLon": ssrWrapped['rawLon'], "evenTs": ssrWrapped['dts'], "lastFmt": ssrWrapped['evenOdd']})
                                    else:
                                        # Set odd data.
                                        data.update({"oddLat": ssrWrapped['rawLat'], "oddLon": ssrWrapped['rawLon'], "oddTs": ssrWrapped['dts'], "lastFmt": ssrWrapped['evenOdd']})
                                    
                                    # If we have even and odd lat/lon data
                                    if ('evenTs' in data) and ('oddTs' in data):
                                        
                                        # Get time delta.
                                        timeDelta = datetime.timedelta(seconds=config.ssrStateEngine['cprExpireSec'])
                                        
                                        # Get the age of our even and odd data.
                                        evenAge = self.str2Datetime(data['lastSeen']) - self.str2Datetime(data['evenTs'])
                                        oddAge = self.str2Datetime(data['lastSeen']) - self.str2Datetime(data['oddTs'])
                                        
                                        # See if our lat/lon timestamps are within n seconds of each other.
                                        if (evenAge < timeDelta) and (oddAge < timeDelta):
                                            
                                            # Pull even and odd data.
                                            evenData = [data['evenLat'], data['evenLon']]
                                            oddData = [data['oddLat'], data['oddLon']]
                                            
                                            fmt = ssrWrapped['evenOdd']
                                            
                                            locData = None
                                            
                                            # Decode location
                                            try:
                                                # If we have data source location data set its position.
                                                if 'srcLat' in data:
                                                    # See if we know where our data source is located...
                                                    myPos = [data['srcLat'], data['srcLon']]
                                                
                                                # If we have CPR Global position data...
                                                if (ssrWrapped['fmt'] >= 9) and (ssrWrapped['fmt'] <= 18) or ((ssrWrapped['fmt'] >= 20) and (ssrWrapped['fmt'] <= 22)):
                                                    # Flag the type of position we got.
                                                    locMeta = "CPRGlobal"
                                                    
                                                    # Decode global position
                                                    locData = cprProc.cprResolveGlobal(evenData, oddData, fmt)
                                                
                                                # If we know where we are and have our current location.
                                                elif (ssrWrapped['fmt'] >= 5) and (ssrWrapped['fmt'] <= 8) and ('srcLat' in data):
                                                    
                                                    # Flag the type of position we got.
                                                    locMeta = "CPRRelative"
                                                    
                                                    # Figure out if we last got ever or odd data and use it.
                                                    if evenAge >= oddAge:
                                                        # Use the even data.
                                                        lastEOData = [data['evenLat'], data['evenLon']]
                                                        thisTgt = 0
                                                    else:
                                                        # Use the odd data.
                                                        lastEOData = [data['oddLat'], data['oddLon']]
                                                        thisTgt = 1
                                                    
                                                    # Decode local position.
                                                    locData = cprProc.cprResolveLocal(myPos, evenData, 0, True)
                                                
                                                # Location data
                                                if type(locData) == list:
                                                    
                                                    # Since we have location data.
                                                    if ('lat' in data) and ('lon' in data):
                                                        
                                                        # See if the we have moved...
                                                        if (data['lat'] != locData[0]) and (data['lon'] != locData[1]):
                                                            
                                                            # Derived heading flag
                                                            derivedHeading = False;
                                                            
                                                            # See if we already have a derived heading
                                                            if 'headingMeta' in data:
                                                                
                                                                # If we already have a GPS derived heading, set our flag.
                                                                if data['headingMeta'] == "GPSDerived":
                                                                    derivedHeading = True;
                                                            
                                                            # If we don't have a heading compute or we've already derived one compute it again assuimng we didn't just get a new one from ADS-B.
                                                            if (not ('heading' in data) or derivedHeading) and not ('heading' in ssrWrapped):
                                                                
                                                                # Get the bearing based on the location we have.
                                                                newHeading = self.__asu.coords2Bearing([data['lat'], data['lon']], [locData[0], locData[1]])
                                                                # Add the heading to the traffic data
                                                                data.update({"heading": newHeading, "headingMeta": "GPSDerived"})
                                                        
                                                    # Set location data.
                                                    data.update({"lat": locData[0], "lon": locData[1], "locationMeta": locMeta})
                                            
                                            except RuntimeError:
                                                # CPR boundary exception...
                                                if config.ssrStateEngine['debug']:
                                                    logger.log("CPR boundary straddle error for %s." %ssrWrapped['icaoAAHx'])
                                            
                                            except:
                                                # Log exception when trying to get ADS-B data.
                                                tb = traceback.format_exc()
                                                logger.log("Error processing ADS-B location for %s:\n%s" %(ssrWrapped['icaoAAHx'], tb))
                                
                                # Enqueue processed state data.
                                self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                                
                                # Figure out how to clear the emergency flag if we no longer have an emergency.
                        
                        elif (ssrWrapped['mode'] == "ac") and ('emergency' in ssrWrapped):
                            
                            # Scan for emergency flag.
                            if 'emergency' in ssrWrapped:
                                data.update({"emergency": ssrWrapped['emergency']})
                            
                            # Mode A squawk code if we have one!
                            if 'aSquawk' in ssrWrapped:
                                data.update({"aSquawk": ssrWrapped['aSquawk']})
                            
                            # Set our lastSeen time stamp for this data.
                            data.update({"lastSeen": ssrWrapped['dts']})
                            
                            # Check for emergency conditions.
                            data.update(self.getEmergencyInfo(ssrWrapped))
                            
                            # Enqueue processed state data.
                            self.enqueueData(self.updateState('A-' + ssrWrapped['aSquawk'], data))
                except:
                        tb = traceback.format_exc()
                        logger.log("Failed to parse data:\n%s" %tb)
                        # Get the hex data as a string
                        #pprint(ssrWrapped)
        
        except:
            tb = traceback.format_exc()
            logger.log("Exception in worker:\n%s" %tb)
    
    def run(self):
        """
        Actually watch the queue.
        """
        
        # Keep running.
        while self.__keepRunning:
            # Redis queues and entities
            self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
            self.__sPsQ = redis.StrictRedis(host=config.statePub['host'], port=config.statePub['port'])
            self.__sRQ = redis.StrictRedis(host=config.stateRel['host'], port=config.stateRel['port'])
            self.__redHash = redis.StrictRedis(host=config.ssrStateEngine['hashHost'], port=config.ssrStateEngine['hashPort'])
            
            # Subscribe the the connector pub/sub queue.
            self.__psObj = self.__psQ.pubsub() 
            self.__psObj.subscribe(self.__channels)
            
            try:
                # Try to run the worker.
                for work in self.__psObj.listen():
                    # Do the work on the incoming JSON.
                    self.worker(work)
            
            except SystemExit:
                self.__keepRunning = False
                
                raise SystemExit
            
            except KeyboardInterrupt:
                self.__keepRunning = False
                
                raise KeyboardInterrupt
            
            except redis.ConnectionError:
                logger.log("Redis connection died.\nWaiting 0.5 seconds before starting again.")
                time.sleep(0.5)
            
            except:
                tb = traceback.format_exc()
                logger.log("Worker blew up:\n%s" %tb)
                logger.log('Waiting 1 second before starting again.')
                time.sleep(1.0)


if __name__ == "__main__":
    # Set up the logger.
    logger = asLog(config.ssrStateEngine['logMode'])

    logger.log("SSR state engine starting...")
    
    # Start up our ADS-B parser
    client = SubListener([config.connPub['qName']])
    client.daemon = True
    # .. and go.
    client.start()
    
    try:
        while True: time.sleep(10)
    except KeyboardInterrupt:
        # Die nicely.
        quit()
    except:
        tb = traceback.format_exc()
        logger.log("Caught unhandled exception.\n%s" %tb)
