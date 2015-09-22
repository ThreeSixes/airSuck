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
        
        # Sfet metadata string to "none" by default.
        aMeta = None
        
        # Make the squawk code an int to make life a bit easier.
        aInt = int(aSquawk)
        
        # Get data based on region.
        if region == self.regionUSA:
            # Unique Squawk codes
            if aInt == 0:
                aMeta = "Shouldn't be assigned."
            
            if aInt == 1200:
                aMeta = "VFR"
            
            elif aInt == 1201:
                aMeta = "VFR near LAX"
            
            elif aInt == 1202:
                aMeta = "VFR glider, no ATC contact"
            
            elif aInt == 1205:
                aMeta = "VFR LA area helicopters"
            
            elif aInt == 1206:
                aMeta = "VFR LA LEO/First responder/military/public svc helicopters"
                
            elif aInt == 1234:
                aMeta = "VFR pattern work"
            
            elif aInt == 1255:
                aMeta = "Firefighting aircraft"
            
            elif aInt == 1276:
                aMeta = "ADIZ penetration, no ATC contact"
            
            elif aInt == 1277:
                aMeta = "SAR aircraft"
            
            elif aInt == 4400:
                aMeta = "Pressure suit flight above FL600"
            
            elif aInt == 4453:
                aMeta = "High balloon op"
            
            elif aInt == 7400:
                aMeta = "UAV, lost comms"                
            
            elif aInt == 7500:
                aMeta = "Hijacked aircraft"
            
            elif aInt == 7600:
                aMeta = "Radio failure"
            
            elif aInt == 7700:
                aMeta = "General emergency"
            
            elif aInt == 7777:
                aMeta = "Active DoD air defense mission, no ATC clearence"
            
            elif aInt == 100 or aInt == 200 or aInt == 300 or aInt == 400 or aInt == 500 or aInt == 600 or aInt == 700 or aInt == 1000 or aInt == 1100 or aInt == 1300 or aInt == 2000 or aInt == 2100 or aInt == 2200 or aInt == 2300 or aInt == 2400 or aInt == 4000:
                aMeta = "Non-discrete code"
            
            # Squawk code blocks. Each block is expressed as NNxx where xx is the discreet part of each code and NN is the block.
            elif ((aInt >= 101) and (aInt <= 177)) or ((aInt >= 201) and (aInt <= 277)) or ((aInt >= 301) and (aInt <= 377)) or ((aInt >= 401) and (aInt <= 477)):
                aMeta = "Terminal/CERAP/Industry/Unique/Experimental"
            
            elif (aInt >= 1207) and (aInt <= 1272):
                aMeta = "Discrete VFR"
            
            elif (aInt >= 4447) and (aInt <= 4452):
                aMeta = "State/federal LEO/Military spec ops"
            
            elif (aInt == 4440) and (aInt == 4441):
                aMeta = "Ops above FL600 for Lockheed/NASA from Moffett field"
            
            elif (aInt >= 4442) and (aInt <= 4446):
                aMeta = "Ops above FL600 for Lockheed from Air Force Plant 42"
            
            elif (aInt >= 4454) and (aInt <= 4465):
                aMeta = "USAF spec ops above FL600"
            
            elif ((aInt >= 5101) and (aInt <= 5177)) or ((aInt >= 5201) and (aInt <= 5277)) or ((aInt >= 5301) and (aInt <= 5377)):
                aMeta = "DoD in US, not on RADAR"
            
            elif (aInt >= 4401 and aInt <= 4433) or (aInt >= 4466 and aInt <= 4477):
                aMeta = "Special ops by LEO"
            
            elif (aInt >= 7601 and aInt <= 7607) or (aInt >= 7701 and aInt <= 7707):
                aMeta = "Special ops by Federal LEO"
            
            elif (aInt >= 5001 and aInt <= 5057) or (aInt >= 5063 and aInt <= 5077) or (aInt >= 5401 and aInt <= 5077) or (aInt >= 6101 and aInt <= 6177) or (aInt >= 6401 and aInt <= 6477) or (aInt == 7501) or (aInt == 7577):
                aMeta = "DoD aircraft, NORAD assigned"
            
            elif ((aInt >= 1) and (aInt <= 77)) or ((aInt >= 4201) and (aInt <= 4277)) or ((aInt >= 4301) and (aInt <= 4377)) or ((aInt >= 4501) and (aInt <= 4577)) or ((aInt >= 4601) and (aInt <= 4677)) or ((aInt >= 4701) and (aInt <= 4777)) or ((aInt >= 5101) and (aInt <= 5177)) or ((aInt >= 5201) and (aInt <= 5277)) or ((aInt >= 5301) and (aInt <= 5377)) or ((aInt >= 5501) and (aInt <= 5577)):
                aMeta = "Internal ARTCC"
            
            elif ((aInt >= 501) and (aInt <= 577)) or ((aInt >= 601) and (aInt <= 677)) or ((aInt >= 701) and (aInt <= 777)) or ((aInt >= 1001) and (aInt <= 1077)) or ((aInt >= 1101) and (aInt <= 1177)) or ((aInt >= 1301) and (aInt <= 1377)) or ((aInt >= 1401) and (aInt <= 1477)) or ((aInt >= 1501) and (aInt <= 1577)) or ((aInt >= 1601) and (aInt <= 1677)) or ((aInt >= 1701) and (aInt <= 1777)) or ((aInt >= 2001) and (aInt <= 2077)) or ((aInt >= 2101) and (aInt <= 2177)) or ((aInt >= 2201) and (aInt <= 2277)) or ((aInt >= 2301) and (aInt <= 2377)) or ((aInt >= 2401) and (aInt <= 2477)) or ((aInt >= 2501) and (aInt <= 2577)) or ((aInt >= 2601) and (aInt <= 2677)) or ((aInt >= 2701) and (aInt <= 2777)) or ((aInt >= 3001) and (aInt <= 3077)) or ((aInt >= 3101) and (aInt <= 3777)) or ((aInt >= 4001) and (aInt <= 4077)) or ((aInt >= 4101) and (aInt <= 4177)) or ((aInt >= 5601) and (aInt <= 5677)) or ((aInt >= 5701) and (aInt <= 5777)) or ((aInt >= 6001) and (aInt <= 6077)) or ((aInt >= 6201) and (aInt <= 6277)) or ((aInt >= 6301) and (aInt <= 6377)) or ((aInt >= 6501) and (aInt <= 6577)) or ((aInt >= 6601) and (aInt <= 6677)) or ((aInt >= 6701) and (aInt <= 6777)) or ((aInt >= 7001) and (aInt <= 7077)) or ((aInt >= 7101) and (aInt <= 7177)) or ((aInt >= 7201) and (aInt <= 7277)) or ((aInt >= 7301) and (aInt <= 7377)) or ((aInt >= 7610) and (aInt <= 7676)) or ((aInt >= 7710) and (aInt <= 7776)):
                aMeta = "External ARTCC"
            
        return aMeta

    def getCategory(self, category):
        """
        Get description of aicraft categories, given an aicraft category string.
        """
        
        # By default let's assume the category is invalid.
        retVal = "Invalid"
        
        # If we have two chars in our string...
        if len(category) == 2:
            if category == "A0":
                retVal = "Standard aicraft"
            elif category == "A1":
                retVal = "Light aicraft"
            elif category == "A2":
                retVal = "Medium aicraft"
            elif category == "A3":
                retVal = "Heavy aicraft"
            elif category == "A4":
                retVal = "High vortex aicraft"
            elif category == "A5":
                retVal = "Very heavy aicraft"
            elif category == "A6":
                retVal = "High perf/speed aircraft"
            elif category == "A7":
                retVal = "Rotorcraft"
            elif category == "B0":
                retVal = "Non-standard aircraft"
            elif category == "B1":
                retVal = "Glider/sailplane"
            elif category == "B2":
                retVal = "Lighter-than-air aircraft"
            elif category == "B3":
                retVal = "Parachute/skydiver"
            elif category == "B4":
                retVal = "Ultralight/hang glider"
            elif category == "B5":
                retVal = "Reserved"
            elif category == "B6":
                retVal = "UAV"
            elif category == "B7":
                retVal = "Spacecraft"
            elif category == "C0":
                retVal = "Surface vehicle"
            elif category == "C1":
                retVal = "Emergency vehicle"
            elif category == "C2":
                retVal = "Service vehicle"
            elif category == "C3":
                retVal = "Fixed/tehtered obstruction"
            elif category == "C4":
                retVal = "Cluster obstacle"
            elif category == "C5":
                retVal = "Line obstacle"
            elif category == "C6":
                retVal = "Reserved"
            elif category == "C7":
                retVal = "Reserved"
        
        return retVal

    def getAISNavStat(self, navStat):
        """
        getAISNavStat(natvStat)
        
        Accepts a 4-bit number representing navigation status.
        
        Returns a string describing the navigation status.
        """
        
        # Set the default status to be invalid.
        retVal = "Invalid"
        
        # If we have a good code...
        if (navStat >= 0) or (navStat <= 15):
            
            # The 15 "defined" navigational status values.
            statArray = ["Underway using engine",
                "Anchored",
                "Not under command",
                "Restricted manoeuverability",
                "Constrained by draught",
                "Moored",
                "Aground",
                "Fishing",
                "Underway sailing",
                "Reserved (HSC)",
                "Reserved (WIG)",
                "Reserved",
                "Reserved",
                "Reserved",
                "AIS-SART (lifeboat)",
                "Not defined"]
            
            # Set the retun value to the given status.
            retVal = statArray[navStat]
        
        return retVal
        