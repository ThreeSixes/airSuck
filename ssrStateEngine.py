#!/usr/bin/python

############
# Imports. #
############

import redis
import time
import json
import threading
import binascii
import datetime
from cprMath import cprMath
from pprint import pprint


#################
# Configuration #
#################

# Which queue do we subscribe to?
targetHost = "brick"
targetSub = "ssrFeed"
destReliable = "airState"
destPubSub = "airStateFeed"

# How long should it take to expire planes in seconds.
expireTime = 300

# CPR stuff.
cprProc = cprMath()


##############################
# Classes for handling data. #
##############################

class SubListener(threading.Thread):
    """
    Listen to the SSR channel for new incoming data.
    """
    def __init__(self, r, channels, destReliable, destPubSub):
        threading.Thread.__init__(self)
        self.destReliable = destReliable
        self.destPubSub = destPubSub
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)    
    
    def updateState(self, objName, cacheData):
        """
        updateState
        
        Update state engine with data from incoming frames given the data in the dict cacheData. objName is the name of the ICAO AA in hex, or emergency squawk code.
        
        Returns all data in the cache.
        """
        
        # Create properly-formatted name for the state hash table we're creating.
        fullName = str('state:' + objName)
        
        # Delete the original timestamp.
        thisTime = cacheData.pop('dts', None)
        
        # Set the first seen data.
        self.redis.hsetnx(fullName, 'firstSeen', thisTime)
        
        # Update or create cached data, if we have more than just a name
        if type(cacheData) == dict:
            
            cacheData.update({'lastSeen': thisTime})
            
            # Set each specified value.
            for thisKey in cacheData:
                self.redis.hset(fullName, thisKey, cacheData[thisKey])
        
        # Set expiration on the hash entry.
        self.redis.expire(fullName, expireTime)
        
        retVal = self.redis.hgetall(fullName)
        
        retVal.update({'addr': objName})
        
        retVal = self.fixDataTypes(retVal)
        
        return retVal
    

    def pullState(self, objName):
        """
        pullState(objName)
        
        Pull state information for a given object name. Returns a dict with existing data.
        """
        
        # Try to pull data...
        dataPull = self.redis.hgetall('state:' + objName)
        
        # Make sure we have some sort of data.
        if type(dataPull) == dict:
            retVal = dataPull
        
        else:
            # If not, return a blank dict.
            retVal = {}
        
        return retVal
    
    def getEmergencyInfo(self, data):
        """
        getEmergencyInfo(data)
        
        Get stateful emergency info for a given state entry.
        
        Returns a dict containing emergency info.
        """
        
        retVal = {}
        
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
                
        return retVal
    
    
    def fixDataTypes(self, statusData):
        """
        fixDataTypes(self, statusData)
        
        Converts data from strings to their approriate datatypes. This is necessary since REDIS stores everything as a string in hash tables.
        """
        
        retVal = statusData
        
        # Convert values from strings to other things.
        
        # Check for boolean-based data.
        if 'supersonic' in retVal:
            if retVal['supersonic'] == "True":
                retVal['supersonic'] = True
            else:
                retVal['supersonic'] = False
        
        if 'emergency' in retVal:
            if retVal['emergency'] == "True":
                retVal['emergency'] = True
            else:
                retVal['emergency'] = False
        
        # Check for floats.
        if 'heading' in retVal:
            try:
                retVal['heading'] = round(float(retVal['heading']), 1)
            except Exception as e:
                pprint(e)
        
        if 'lat' in retVal:
            try:
                retVal['lat'] = float(retVal['lat'])
            except Exception as e:
                pprint(e)
        
        if 'lon' in retVal:
            try:
                retVal['lon'] = float(retVal['lon'])
            except Exception as e:
                pprint(e)
        
        if 'velo' in retVal:
            try:
                retVal['velo'] = round(float(retVal['velo']), 1)
            except Exception as e:
                pprint(e)
        
        # Check for ints.
        if 'alt' in retVal:
            try:
                retVal['alt'] = int(retVal['alt'])
            except Exception as e:
                pprint(e)
        
        if 'evenLat' in retVal:
            try:
                retVal['evenLat'] = int(retVal['evenLat'])
            except Exception as e:
                pprint(e)
            
        if 'evenLon' in retVal:
            try:
                retVal['evenLon'] = int(retVal['evenLon'])
            except Exception as e:
                pprint(e)
        
        if 'gndspeed' in retVal:
            try:
                retVal['gndspeed'] = int(retVal['gndspeed'])
            except Exception as e:
                pprint(e)
            
        if 'lastFmt' in retVal:
            try:
                retVal['lastFmt'] = int(retVal['lastFmt'])
            except Exception as e:
                pprint(e)
            
        if 'oddLat' in retVal:
            try:
                retVal['oddLat'] = int(retVal['oddLat'])
            except Exception as e:
                pprint(e)
        
        if 'oddLon' in retVal:
            try:
                retVal['oddLon'] = int(retVal['oddLon'])
            except Exception as e:
                pprint(e)
        
        if 'ss' in retVal:
            try:
                retVal['ss'] = int(retVal['ss'])
            except Exception as e:
                pprint(e)
        
        if 'supersonic' in retVal:
            try:
                retVal['supersonic'] = int(retVal['supersonic'])
            except Exception as e:
                pprint(e)
        
        if 'survStat' in retVal:
            try:
                retVal['survStat'] = int(retVal['survStat'])
            except Exception as e:
                pprint(e)
        
        if 'utc' in retVal:
            try:
                retVal['utc'] = int(retVal['utc'])
            except Exception as e:
                pprint(e)
            
        if 'vertRate' in retVal:
            try:
                retVal['vertRate'] = int(retVal['vertRate'])
            except Exception as e:
                pprint(e)
        
        if 'fs' in retVal:
            try:
                retVal['fs'] = int(retVal['fs'])
            except Exception as e:
                pprint(e)
        
        return retVal

    def enqueueData(self, statusData):
        """
        enqueueDate(statusData)
        
        Put status data on a queue for processing
        """
        
        # Debug print instead of dumping data onto another queue.
        jsonData = json.dumps(statusData)
        self.redis.rpush(destReliable, jsonData)
        self.redis.publish(destPubSub, jsonData)
        
        return

    def crcInt2Hex(self, crcInt):
        """
        crcInt2Hex(crcInt)
        
        Convert the CRC value as in intteger to a hex string.
        Returns a hex string.
        """
        
        return binascii.hexlify(chr((crcInt >> 16) & 0xff) + chr((crcInt >> 8) & 0xff) + chr((crcInt & 0xff)))

    def worker(self, work):
        # Do work on the data returned from the subscriber.
        ssrJson = str(work['data'])
        
        # Get wrapped SSR data.
        ssrWrapped = json.loads(ssrJson)
        
        # Make sure we got good data from json.loads
        if (type(ssrWrapped) == dict):
            
            # Set up our data structure
            data = {}
            
            # Do we hvae mode s?
            if ssrWrapped['mode'] == "s":
                
                # Set our good CRC flag to false by default.
                crcGood = False
                
                # Do we have a matching CRC value?
                if ssrWrapped['frameCrc'] == ssrWrapped['cmpCrc']:
                    # See if we have a DF type that doesn't XOR the transmitter's ICAO address with the CRC.
                    if ssrWrapped['df'] in (17, 18, 19):
                        crcGood = True
                else:
                    # See if we have a DF type that XORs the transmitter's ICAO address with the CRC.
                    if ssrWrapped['df'] in (0, 4, 5, 20, 21):
                        # XOR the computed and frame CRC values to get a potential ICAO AA
                        potAA = self.crcInt2Hex(ssrWrapped['frameCrc'] ^ ssrWrapped['cmpCrc'])
                        
                        # See if we're aware of the potential valid AA.
                        data = self.pullState(potAA)
                        
                        # If we have info on the AA, load it.
                        if len(data) > 0:
                            # Make sure we assign the icaoAAHx value, and indicate we have a good CRC value.
                            ssrWrapped.update({'icaoAAHx': potAA})
                            crcGood = True
                
                # Account for DF types that we aren't sure about CRC data that could contain good stuff.
                if ssrWrapped['df'] in (11, 16):
                    crcGood = True
                
                if crcGood == False:
                    print("Bad CRC detected in frame:\n DF " + str(ssrWrapped['df']) + ": " + ssrWrapped['data'])
                
                # If we have an aircraft address specified and a good CRC...
                if ('icaoAAHx' in ssrWrapped) and (crcGood == True):
                    # Try to get existing data, assuming we didn't get it already.
                    if len(data) == 0:
                        data = self.pullState(ssrWrapped['icaoAAHx'])
                    
                    # Mode A squawk code if we have one!
                    if 'aSquawk' in ssrWrapped:
                        data.update({"aSquawk": ssrWrapped['aSquawk']})
                    
                    # Vertical status data
                    if 'vertStat' in ssrWrapped:
                        data.update({"vertStat": ssrWrapped['vertStat']})
                    
                    # Check for emergency conditions.
                    data.update(self.getEmergencyInfo(ssrWrapped))
                    
                    # Set the last sensor we got a frame from
                    data.update({"lastSrc": ssrWrapped['src']})
                    
                    # Set our datetime stamp for this data.
                    data.update({"dts": ssrWrapped['dts']})
                    
                    # Enqueue processed state data.
                    self.enqueueData(self.updateState(ssrWrapped['icaoAAHx'], data))
                        
                    # Scan for emergency flag.
                    if 'emergency' in ssrWrapped:
                        data.update({"emergency": ssrWrapped['emergency']})
                    
                    # ID data
                    if 'idInfo' in ssrWrapped:
                        data.update({"idInfo": ssrWrapped['idInfo']})
                    
                    # Aircraft category
                    if 'category' in ssrWrapped:
                        data.update({"category": ssrWrapped['category']})
                    
                    # Aircraft heading
                    if 'heading' in ssrWrapped:
                        data.update({"heading": ssrWrapped['heading']})
                    
                    # Altitude
                    if 'alt' in ssrWrapped:
                        data.update({"alt": ssrWrapped['alt']})
                    
                    # Vertical rate data
                    if 'vertRate' in ssrWrapped:
                        data.update({"vertRate": ssrWrapped['vertRate']})
                    
                    # Flight status data
                    if 'fs' in ssrWrapped:
                        data.update({"fs": ssrWrapped['fs']})
                        
                    # Velocity data
                    
                    # For airborne aircraft
                    if ((ssrWrapped['df'] == 17) or (ssrWrapped['df'] == 18)) and (ssrWrapped['fmt'] == 19):
                        if 'gndspeed' in ssrWrapped:
                            data.update({"velo": ssrWrapped['gndspeed'], "veloType": "gnd"})
                        if 'airspeed' in ssrWrapped:
                            data.update({"velo": ssrWrapped['airspeed'], "veloType": "air", "airspeedRef": ssrWrapped['airspeedRef']})
                    # Deal with vehicles on the ground here...
                    
                    # Vertical status
                    # Needs moe logic
                    
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
                        
                        # This functionality needs to be broken out as a function.
                        
                        # If we have even and odd lat/lon data
                        if ("evenTs" in data) and ("oddTs" in data):
                            
                            # Pull even and odd data.
                            evenData = [data['evenLat'], data['evenLon']]
                            oddData = [data['oddLat'], data['oddLon']]
                            
                            #if data['lastFmt'] == 0:
                            #    hackFmt = 1
                            #else:
                            #    hackFmt = 0
                            
                            fmt = data['lastFmt']
                            
                            # Decode location
                            try:
                                # Original version:
                                locData = cprProc.cprResolveGlobal(evenData, oddData, fmt)
                                
                                # Location data
                                if type(locData) == list:
                                    # Set location data.
                                    data.update({"lat": locData[0], "lon": locData[1]})
                            
                            except Exception as e:
                                pass
                        
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
                
                # Check for emergency conditions.
                data.update(self.getEmergencyInfo(ssrWrapped))
                
                # Enqueue processed state data.
                self.enqueueData(self.updateState('A-' + ssrWrapped['aSquawk'], data))
            
            # Get the hex data as a string
            #pprint(ssrWrapped)
    
    def run(self):
        for work in self.pubsub.listen():
            self.worker(work)

if __name__ == "__main__":
    print("SSR state engine starting...")
    
    # Set up Redis queues.
    r = redis.Redis(host=targetHost)
    
    # Start up our ADS-B parser
    client = SubListener(r, [targetSub], [destReliable], [destPubSub])
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
