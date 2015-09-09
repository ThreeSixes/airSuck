"""
airSuckUtil by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

############
# Imports. #
############

import math

#########################
# AirSuck Utility class #
#########################

class airSuckUtil:
    """
    airSuckUtil is a class that contains utility functions to assist with airSuck computations.
    """
    
    def __init__(self):
        """
        airSuckUtil constructor
        """
        
        # Conversion factors
        self.deg2Rad = float(math.pi / 180.0)
        self.havRad2Km = 6367
        self.km2Mi = 1.60934
        self.kt2Mmh = 1.85200
        self.kt2Mph = 1.15077945
        self.ft2M = 0.3048
        
        # Regions.
        self.regionUSA = 0
    
    def getRange(self, posA, posB):
        """
        Get the range between two GPS coordinates provided as lists with lat as [0] and lon as [1] using the haversine algorithm. Returns a distance in km.
        """
        
        dLat = (posB[0] - posA[0]) * self.deg2Rad
        dLon = (posB[1] - posA[1]) * self.deg2Rad
        
        a = math.pow(math.sin(dLat / 2), 2) + math.cos(posA[0] * self.deg2Rad) * math.cos(posB[0] * self.deg2Rad) * math.pow(math.sin(dLon / 2), 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return self.havRad2Km * c
    
    def bearing2Cardinal(self, bearing):
        """
        Get cardinal directionality from a given bearing. Returns a string indicating the cardinal direction.
        """
        
        retVal = ""
        
        # Create 45 degree sectors starting at 0 to 22.5 degress, ending at 337.5 to 359 degrees.
        if (bearing >= 0) and (bearing <= 22.5):
            retVal = "N"
        elif (bearing > 22.5) and (bearing <=  67.5):
            retVal = "NE"
        elif (bearing > 67.5) and (bearing <=  112.5):
            retVal = "E"
        elif (bearing > 112.5) and (bearing <=  157.5):
            retVal = "SE"
        elif (bearing > 157.5) and (bearing <=  202.5):
            retVal = "S"
        elif (bearing > 202.5) and (bearing <=  247.5):
            retVal = "SW"
        elif (bearing > 247.5) and (bearing <=  292.5):
            retVal = "W"
        elif (bearing > 292.5) and (bearing <=  337.5):
            retVal = "NW"
        elif (bearing > 337.5) and (bearing <  360):
            retVal = "N"
        
        return retVal
    
    def coords2Bearing(self, coordsA, coordsB):
        """
        Get a bearing given two sets of GPS coords, assuming A is the beginning coordinate in the line segment and B is the last coordinate received. Returns a floating point int.
        """
        
        # Set up or starting latitude and longitude.
        startLat = math.radians(coordsA[0])
        startLong = math.radians(coordsA[1])
        endLat = math.radians(coordsB[0])
        endLong = math.radians(coordsB[1])
        
        # Longitude delta.
        dLong = endLong - startLong
        
        # Get Phi
        dPhi = math.log(math.tan(endLat / 2.0 + math.pi / 4.0) / math.tan(startLat / 2.0 + math.pi / 4.0))
        
        if abs(dLong) > math.pi:
            if dLong > 0.0:
                dLong = -(2.0 * math.pi - dLong)
            else:
                dLong = (2.0 * math.pi + dLong)
        
        # Return endoing coordinate.    
        return ((math.degrees(math.atan2(dLong, dPhi)) + 360.0) % 360.0)
    
    def modeA2Meta(self, aSquawk, region):
        """
        Get metadata from mode A squawk codes given an administrative region and a squawk code. Returns a dict.
        The USA region squawk code allocation logic is based on FAA JO 7110.66E
        (http://www.faa.gov/documentLibrary/media/Order/FINAL_Order_7110_66E_NBCAP.pdf)
        """
        # Empty return value
        retVal = None
        
        # By default the data is not notable, and there's no metadata to be assigned.
        notable = False
        aMeta = None
        
        # Make the squawk code an int to make life a bit easier.
        aInt = int(aSquawk)
        
        # Get data based on region.
        if region == self.regionUSA:
            # Unique Squawk codes
            if aInt == 0:
                aMeta = "Code 0000 shouldn't be used."
                notable = True
                
            if aInt == 1200:
                aMeta = "VFR"
            
            elif aInt == 1201:
                aMeta = "VFR near LAX"
            
            elif aInt == 1202:
                aMeta = "VFR glider, no contact with ATC"
            
            elif aInt == 1205:
                aMeta = "VFR helicopters in LA area"
                notable = True
            
            elif aInt == 1206:
                aMeta = "VFR LEO/First responder/military/public service helicopters in LA area"
                notable = True
            
            elif aInt == 1234:
                aMeta = "VFR pattern work"
                notable = True
            
            elif aInt == 1255:
                aMeta = "Firefighting aircraft"
                notable = True
            
            elif aInt == 1276:
                aMeta = "ADIZ penetration, no ATC contact"
                notable = True
            
            elif aInt == 1277:
                aMeta = "SAR aircraft"
                notable = True
            
            elif aInt == 4400:
                aMeta = "Pressure suit flight above FL600"
                notable = True
            
            elif aInt == 4453:
                aMeta = "High balloon op"
                notable = True
            
            elif aInt == 7400:
                aMeta = "Unmanned aircraft, lost comms"
                notable = True
            
            elif aInt == 7500:
                aMeta = "Hijacked aircraft"
                notable = True
            
            elif aInt == 7600:
                aMeta = "Radio failure"
                notable = True
            
            elif aInt == 7700:
                aMeta = "General emergency"
                notable = True
            
            elif aInt == 7777:
                notable = True
                aMeta = "Active DoD air defense mission, no ATC clearence"
            
            # Squawk code blocks. Each block is expressed as NNxx where xx is the discreet part of each code and NN is the block.
            elif (aInt >= 100) and (aInt <= 477):
                aMeta = "Unique/Experimental"
                notable = True
            
            elif (aInt >= 2000 and aInt <= 2077):
                aMeta = "FAA JO 7110.65 assignments over oceanic airspace"
            
            elif aInt >= 1207 and aInt <= 1272:
                aMeta = "Discrete VFR"
            
            elif aInt >= 4447 and aInt <= 4452:
                aMeta = "Special aircraft ops state and federal LEO/Military"
                notable = True
            
            elif aInt == 4440 or aInt == 4441:
                aMeta = "Ops above FL600 for Lockheed/NASA from Moffett field"
                notable = True
            
            elif aInt == 4442 or aInt == 4446:
                aMeta = "Ops above FL600 for Lockheed from Air Force Plant 42"
                notable = True
            
            elif aInt == 4454 or aInt == 4465:
                aMeta = "Air Force special operations above FL600"
                notable = True
            
            elif aInt == 5100 or aInt == 5377:
                aMeta = "DoD aicraft inside US airpace but not on RADAR"
                notable = True
            
            elif (aInt >= 4401 and aInt <= 4433) and (aInt >= 4466 and aInt <= 4477):
                aMeta = "Special aircraft ops by LEO"
                notable = True
            
            elif (aInt >= 5000 and aInt <= 5057) or (aInt >= 5063 and aInt <= 5077) or (aInt >= 5400 and aInt <= 5077) or (aInt >= 6100 and aInt <= 6177) or (aInt >= 6400 and aInt <= 6477) or (aInt == 7501) or (aInt == 7577):
                aMeta = "DoD aircraft, assigned by NORAD"
                notable = True
        
            elif (aInt >= 500 and aInt <= 777) or (aInt >= 1000 and aInt <= 1177) or (aInt >= 1300 and aInt <= 1377) or (aInt >= 1500 and aInt <= 1577) or (aInt >= 2100 and aInt <= 2477) or (aInt >= 4000 and aInt <= 4077):
                aMeta = "FAA JO 7110.65 assignments"
                notable = True
        
        # If we have some sort of info about the squawk code...
        if aMeta != None:
            retVal = {'aMeta': aMeta, 'notable': notable}
        
        return retVal
