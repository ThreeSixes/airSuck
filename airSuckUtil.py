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
    
    def getRange(self, posA, posB):
        """
        Get the range between two GPS coordinates provided as lists with lat as [0] and lon as [1] using the haversine algorithm. Returns a distance in km.
        """
        
        dLat = (posB[0] - posA[0]) * self.deg2Rad
        dLon = (posB[1] - posA[1]) * self.deg2Rad
        
        a = math.pow(math.sin(dLat / 2), 2) + math.cos(posA[0] * self.deg2Rad) * math.cos(posB[0] * self.deg2Rad) * math.pow(math.sin(dLon / 2), 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return self.havRad2Km * c
    
    