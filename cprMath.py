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
    
    """
    Compact position reporting modulus function. Accepts an numerator and divisor. Returns a float.
    """
    def __cprMod(self, numerator, divisor):
        retVal = 0.0
        
        # Make sure everything is a float, and get the modulus.
        numerator = numerator * 1.0
        divisor = divisor * 1.0
        modulus = (numerator % divisor) * 1.0
        
        # Modulus must be positive.
        if modulus < 0:
            modulus = divisor + modulus
        
        return modulus
    
    """
    Compact Position Reporting NL function for calculating latitude. Accepts one argument - the latitude. Returns a float.
    """
    def __cprNL(self, lat):
        retVal = 0.0
        
        # The latitude index is symmetric at the equatior.
        if lat < 0:
            lat = abs(lat) * 1.0
        
        # Get the NL value.
        if lat < 10.47047130:
            retVal = 59.0
        elif lat < 14.82817437:
            retVal = 58.0
        elif lat < 18.18626357:
            retVal = 57.0
        elif lat < 21.02939493:
            retVal = 56.0
        elif lat < 23.54504487:
            retVal = 55.0
        elif lat < 25.82924707:
            retVal = 54.0
        elif lat < 27.93898710:
            retVal = 53.0
        elif lat < 29.91135686:
            retVal = 52.0
        elif lat < 31.77209708:
            retVal = 51.0
        elif lat < 33.53993436:
            retVal = 50.0
        elif lat < 35.22899598:
            retVal = 49.0
        elif lat < 36.85025108:
            retVal = 48.0
        elif lat < 38.41241892:
            retVal = 47.0
        elif lat < 39.92256684:
            retVal = 46.0
        elif lat < 41.38651832:
            retVal = 45.0
        elif lat < 42.80914012:
            retVal = 44.0
        elif lat < 44.19454951:
            retVal = 43.0
        elif lat < 45.54626723:
            retVal = 42.0
        elif lat < 46.86733252:
            retVal = 41.0
        elif lat < 48.16039128:
            retVal = 40.0
        elif lat < 49.42776439:
            retVal = 39.0
        elif lat < 50.67150166:
            retVal = 38.0
        elif lat < 51.89342469:
            retVal = 37.0
        elif lat < 53.09516153:
            retVal = 36.0
        elif lat < 54.27817472:
            retVal = 35.0
        elif lat < 55.44378444:
            retVal = 34.0
        elif lat < 56.59318756:
            retVal = 33.0
        elif lat < 57.72747354:
            retVal = 32.0
        elif lat < 58.84763776:
            retVal = 31.0
        elif lat < 59.95459277:
            retVal = 30.0
        elif lat < 61.04917774:
            retVal = 29.0
        elif lat < 62.13216659:
            retVal = 28.0
        elif lat < 63.20427479:
            retVal = 27.0
        elif lat < 64.26616523:
            retVal = 26.0
        elif lat < 65.31845310:
            retVal = 25.0
        elif lat < 66.36171008:
            retVal = 24.0
        elif lat < 67.39646774:
            retVal = 23.0
        elif lat < 68.42322022:
            retVal = 22.0
        elif lat < 69.44242631:
            retVal = 21.0
        elif lat < 70.45451075:
            retVal = 20.0
        elif lat < 71.45986473:
            retVal = 19.0
        elif lat < 72.45884545:
            retVal = 18.0
        elif lat < 73.45177442:
            retVal = 17.0
        elif lat < 74.43893416:
            retVal = 16.0
        elif lat < 75.42056257:
            retVal = 15.0
        elif lat < 76.39684391:
            retVal = 14.0
        elif lat < 77.36789461:
            retVal = 13.0
        elif lat < 78.33374083:
            retVal = 12.0
        elif lat < 79.29428225:
            retVal = 11.0
        elif lat < 80.24923213:
            retVal = 10.0
        elif lat < 81.19801349:
            retVal = 9.0
        elif lat < 82.13956981:
            retVal = 8.0
        elif lat < 83.07199445:
            retVal = 7.0
        elif lat < 83.99173563:
            retVal = 6.0
        elif lat < 84.89166191:
            retVal = 5.0
        elif lat < 85.75541621:
            retVal = 4.0
        elif lat < 86.53536998:
            retVal = 3.0
        elif lat < 87.00000000:
            retVal = 2.0
        else:
            retVal = 1.0
        
        return retVal
    
    """
    Compact position reporting N function. Accepts two arguments: the latitude value, and the even/odd flag as an integer. Returns the NL value as a float.
    """
    def __cprN(self, lat, evenOdd):
        # Get NL value.
        nl = self.__cprNL(lat) - (evenOdd * 1.0)
        
        # Make sure NL is at least 1.
        if nl < 1:
            nl = 1.0
        
        return nl
    
    """
    Compact position reporting dLon function. Accepts two or three arguments: latitude, even/odd format as integer/float, and surface as a boolean value [defaults to False if not specified]. Returns the DLon value as a float.
    """
    def __cprDLon(self, lat, evenOdd, surface = False):
        retVal = 0.0
        
        # If we don't have a surface position...
        if surface == False:
            retVal = 360.0 / self.__cprN(lat, evenOdd)
        else:
            retVal = 90.0 / self.__cprN(lat, evenOdd)
        
        return retVal    
    
    """
    Get global position data from a set of even and odd formatted CPR data. Accepts five arguments even CPR latitude, even CPR longitude, odd CPR latitude, odd CPR longitude, and even\odd flag as an integer or float. Returns a list containing the decoded latitude and longitude.
    """
    def decodeGlobalCPR(self, evenLat, evenLon, oddLat, oddLon, lastFmt):
        # Retun values
        retVal = [0.0, 0.0]
        
        # Air DLAT/DLON values.
        airDLat = 6.0
        airDLon = 6.101694915
        
        # Compute latitude index (j)
        j = int(math.floor(((59.0 * evenLat) - (60.0 * oddLat)) / 131072) + 0.5)
        rLatEven = airDLat * (self.__cprMod(j, 60.0) + (evenLat / 131072))
        rLatOdd = airDLat * (self.__cprMod(j, 59.0) + (oddLat / 131072))
        
        if rLatEven >= 270:
            rLatEven = rLatEven - 360.0
        if rlatOdd >= 270:
            rLatOdd = rLatOdd - 360.0
        
        # Boundary check the rLat values.
        if (rLatEven < -90) or (rLatEven > 90) or (rLatOdd < -90) or (rLatOdd > 90):
            raise ValueError("rLat value out of bounds. rLatEven = " + str(rLatEven) + "rLatOdd = " +str(rLatOdd))
        
        # Boundary check the NL values for the even and odd rLat values.
        if self.__cprNL(rLatEven) != self.__cprNL(rLatOdd):
            raise ValueError("rLat values are not in the same latitude zone.")
        
        # Compute the N(i) and m [longitude index] values using the last format we got.
        if lastFmt > 0:
            # Odd.
            ni = self.__cprN(rLatOdd, 1.0)
            m = int(math.floor(((((evenLon * (self.__cprNL(rLatOdd) - 1.0) - (oddLon * self.__cprNL(rLatOdd))) / 131072.0) + 0.5))))
            
            # Get the decoded latitude and longitude
            decLon = self.__cprDLon(rLatOdd, 1.0, False) * ((self.__cprMod(m, ni) + oddLon) / 131072.0)
            decLat = rLatOdd
        else:
            # Even
            ni = self.__cprN(rLatEven, 0.0)
            m = int(math.floor(((((evenLon * (self.__cprNL(rLatEven) - 1.0) - (oddLon * self.__cprNL(rLatEven))) / 131072.0) + 0.5))))
            
            # Get the decoded latitude and longitude
            decLon = self.__cprDLon(rLatEven, 0.0, False) * ((self.__cprMod(m, ni) + evenLon) / 131072.0)
            decLat = rLatEven
        
        retVal = [decLat, decLon]
        
        # Return them.
        return retVal
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    