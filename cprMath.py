###########
# Imports #
###########

import math

#################
# cprMath class #
#################

class cprMath():
    """
    cprMath is a class that supports decoding of CPR data into latitude and longitude data.
    """
    
    # Do we want to debug?
    debugOn = False
    
    def debugToggle(self, onOff):
        """
        debugToggle(onOff)
        
        onOff accepts an boolean value where True turns debugging on and False turns it off. Debugging is off by default.
        
        Returns the state of debugging.
        """
        
        self.debugOn = onOff
        
        if self.debugOn:
            print("debugToggle() cprMath debugging on.")
        
        return onOff
    
    
    def NL(self, lat):
        """
        NL(lat)
        
        Longitude zone lookup table, specified by table A-21 in http://adsb.tc.faa.gov/WG3_Meetings/Meeting9/1090-WP-9-14.pdf
        """
        
        # Set dummy return value.
        retVal = False
        
        if self.debugOn: print(" NL() lat = " + str(lat))
        
        # Lat should be positive since the zones are symmetric above and below the equator
        if lat < 0:
            lat = abs(lat)
            if self.debugOn: print(" NL() lat < 0 lat = abs(lat) = " + str(lat))
        
        # Latitude transition table.
        if lat < 10.47047130: retVal = 59
        elif lat < 14.82817437: retVal = 58
        elif lat < 18.18626357: retVal = 57
        elif lat < 21.02939493: retVal = 56
        elif lat < 23.54504487: retVal = 55
        elif lat < 25.82924707: retVal = 54
        elif lat < 27.93898710: retVal = 53
        elif lat < 29.91135686: retVal = 52
        elif lat < 31.77209708: retVal = 51
        elif lat < 33.53993436: retVal = 50
        elif lat < 35.22899598: retVal = 49
        elif lat < 36.85025108: retVal = 48
        elif lat < 38.41241892: retVal = 47
        elif lat < 39.92256684: retVal = 46
        elif lat < 41.38651832: retVal = 45
        elif lat < 42.80914012: retVal = 44
        elif lat < 44.19454951: retVal = 43
        elif lat < 45.54626723: retVal = 42
        elif lat < 46.86733252: retVal = 41
        elif lat < 48.16039128: retVal = 40
        elif lat < 49.42776439: retVal = 39
        elif lat < 50.67150166: retVal = 38
        elif lat < 51.89342469: retVal = 37
        elif lat < 53.09516153: retVal = 36
        elif lat < 54.27817472: retVal = 35
        elif lat < 55.44378444: retVal = 34
        elif lat < 56.59318756: retVal = 33
        elif lat < 57.72747354: retVal = 32
        elif lat < 58.84763776: retVal = 31
        elif lat < 59.95459277: retVal = 30
        elif lat < 61.04917774: retVal = 29
        elif lat < 62.13216659: retVal = 28
        elif lat < 63.20427479: retVal = 27
        elif lat < 64.26616523: retVal = 26
        elif lat < 65.31845310: retVal = 25
        elif lat < 66.36171008: retVal = 24
        elif lat < 67.39646774: retVal = 23
        elif lat < 68.42322022: retVal = 22
        elif lat < 69.44242631: retVal = 21
        elif lat < 70.45451075: retVal = 20
        elif lat < 71.45986473: retVal = 19
        elif lat < 72.45884545: retVal = 18
        elif lat < 73.45177442: retVal = 17
        elif lat < 74.43893416: retVal = 16
        elif lat < 75.42056257: retVal = 15
        elif lat < 76.39684391: retVal = 14
        elif lat < 77.36789461: retVal = 13
        elif lat < 78.33374083: retVal = 12
        elif lat < 79.29428225: retVal = 11
        elif lat < 80.24923213: retVal = 10
        elif lat < 81.19801349: retVal = 9
        elif lat < 82.13956981: retVal = 8
        elif lat < 83.07199445: retVal = 7
        elif lat < 83.99173563: retVal = 6
        elif lat < 84.89166191: retVal = 5
        elif lat < 85.75541621: retVal = 4
        elif lat < 86.53536998: retVal = 3
        elif lat < 87.00000000: retVal = 2
        else: retVal = 1
        
        if self.debugOn: print(" NL() returning " + str(retVal))
        
        return retVal
    
    
    def cprMod(self, numerator, divisor):
        """
        cprMod(numerator, divisor)
        
        This function provides a specific modulus function for decoding CPR formatted coordinates which will always return a positive nubmer.
        """
        if self.debugOn: print(" cprMod(" + str(numerator) + ", " + str(divisor) + ")")
        
        # Perform initial modulus.
        retVal = numerator % divisor
        
        if self.debugOn: print(" cprMod() numerator % divisor = " + str(retVal))
        
        # If we're < 0...
        if retVal < 0:
            # Bring it back up.
            retVal = retVal + numerator
            if self.debugOn: print(" cprMod() modulo < 0, (modulo += numerator) = " + str(retVal))
        
        if self.debugOn: print(" cprMod() returning " + str(retVal))
        
        return retVal
    
    
    def decodeCPR(self, evenData, oddData, lastFmt, surface, refPos = False):
        """
        decodeCPR(evenData, oddData, lastFmt, surface, [refPos])
        
        Decode CPR formatted position data given evenData and oddData as arrays with index 0 being lat, and index 1 being lon. lastFmt is 1 for an odd frame and 0 for an even frame. Surface is a boolean value that when set true indicates we're decoding a surfce position. refPos is a reference position to be used with surface postition data with lat in [0] and lon in [1]
        
        Returns an array with lat being [0] and lon being [1]
        """
        
        # Set a dummy return value.
        retVal = False
        
        # Make sure we typcasdt our incoming values as floats since our math.floor() if they're ints.
        evenData[0] = float(evenData[0])
        evenData[1] = float(evenData[1])
        oddData[0] = float(oddData[0])
        oddData[1] = float(oddData[1])
        
        # Debug prints to show input data.
        if self.debugOn:
            print("Even CPR lat, lon : " + str(evenData[0]) + ", " + str(evenData[1]))
            print("Odd CPR lat, lon  : " + str(oddData[0]) + ", " + str(oddData[1]))
            print("Last CPR format   : " + str(lastFmt))
            print("Surface position  : " + str(surface))
        
        # "Magic number" based on surface data.
        if surface:
            magicNumber = 90.0
        else:
            magicNumber = 360.0
        
        if self.debugOn: print(" decodeCPR() magicNumber = " + str(magicNumber))
        
        # Get airDlat0, 1
        airDlat0 = magicNumber / 60.0
        airDlat1 = magicNumber / 59.0
        
        if self.debugOn: print(" decodeCPR() airDlat0 = " + str(airDlat0))
        if self.debugOn: print(" decodeCPR() airDlat1 = " + str(airDlat1))
        
        # Compute latitude index.
        j = math.floor((((59.0 * evenData[0]) - (60.0 * oddData[0])) / 131072.0) + 0.5)
        
        if self.debugOn: print(" decodeCPR() j = " + str(j))
        
        # Calculate rlat0 and 1.
        rlat0 = airDlat0 * (self.cprMod(j, 60) + evenData[0] / 131072.0)
        rlat1 = airDlat1 * (self.cprMod(j, 59) + oddData[0] / 131072.0)
        
        if self.debugOn:
            print(" decodeCPR() rlat0 = " + str(rlat0))
            print(" decodeCPR() rlat1 = " + str(rlat1))
        
        # Southern hemisphere values are 270 to 360, so subtract 360 if rlats > 270.
        if rlat0 > 270:
            rlat0 = rlat0 - 360
            if self.debugOn: print(" decodeCPR() S\N hemisphere compensation - rlat0 = " + str(rlat0))
        if rlat1 > 270:
            rlat1 = rlat1 - 360
            if self.debugOn: print(" decodeCPR() S\N hemisphere compensation - rlat1 = " + str(rlat1))
            
        # Check to see that our rlat values exist in the same longitude zone.
        if self.NL(rlat0) == self.NL(rlat1):
            if self.debugOn: print(" decodeCPR() NL(rlat0) == NL(rlat1) = " + str(self.NL(rlat0)))
            
            retVal = [0, 0]
            
            # Compute N(i)
            ni = self.NL(lastFmt) - 1
            
            if self.debugOn: print(" decodeCPR() N(i) = " + str(ni))
            
            # If N(i) < 1, we should set it to 1.
            if ni < 1:
                if self.debugOn: print(" decodeCPR() N(i) < 1, N(i) = 1")
                ni = 1
            
            # Get dlon
            dlon = 360.0 / ni
            
            if self.debugOn: print(" decodeCPR() dlon = " + str(dlon))
            
            # Get longitude index.
            m = math.floor((((evenData[1] * (self.NL(lastFmt) - 1)) - (oddData[1] * self.NL(lastFmt))) / 131072.0) + 0.5)
            
            if self.debugOn: print(" decodeCPR() m = " + str(m))
            
            if lastFmt == 0:
                retVal[0] = rlat0
                retVal[1] = dlon * (self.cprMod(m, ni) + oddData[0] / 131072.0)
            else:
                retVal[0] = rlat1
                retVal[1] = dlon * (self.cprMod(m, ni) + oddData[1] / 131072.0)
            
            # Adjust for E/W.
            if retVal[1] > 270:
                if self.debugOn: print(" decodeCPR() E\W hemisphere compensation - retVal[1] = " + str(retVal[1]))
                retVal[1] = retVal[1] - 360
            
            if self.debugOn:
                print(" decodeCPR() Lat = " + str(retVal[0]))
                print(" decodeCPR() Lon = " + str(retVal[1]))
            
        elif self.debugOn:
            print(" decodeCPR() Failure: NL(rlat0) != NL(rlat1)")
            print("   NL(rlat0) = " + str(self.NL(rlat0)))
            print("   NL(rlat1) = " + str(self.NL(rlat1)))
        
        if self.debugOn: print(" decodeCPR() returning " + str(retVal))
        
        return retVal