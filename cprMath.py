# This code was derived completely from gr-air-modes by Bistromath at https://github.com/bistromath/gr-air-modes/cpr.py


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

    def __init__(self):
        self.__latz = 15

    def __nz(self, cType):
        return 4 * self.__latz - cType
    
    def __dlat(self, cType, surface):
        if surface == 1:
            tmp = 90.0
        else:
            tmp = 360.0
        
        nzCalc = self.__nz(cType)
        
        if nzCalc == 0:
            return tmp
        else:
            return tmp / nzCalc

    def __lat(self, cType, surface):
        if surface == 1:
            tmp = 90.0
        else:
            tmp = 360.0
        
        nzCalc = self.__nz(cType)
        
        if nzCalc == 0:
            return tmp
        else:
            return tmp / nzCalc
    
    def __nl(self, declatIn):
        if abs(declatIn) >= 87.0:
            return 1.0
        
        return math.floor( (2.0 * math.pi) * math.acos(1.0 - (1.0 - math.cos(math.pi / (2.0 * self.__latz))) / math.cos((math.pi / 180.0) * abs(declatIn)) ** 2)** -1)
    
    def __dlon(self, declatIn, cType, surface):
        if surface:
            tmp = 90.0
        else:
            tmp = 360.0
        
        nlCalc = max(self.__nl(declatIn) - cType, 1)
        
        return tmp / nlCalc
    
    def __decodeLat(self, encLat, cType, myLat, surface):
        tmp1 = dlat(cType, surface)
        tmp2 = float(encLat) / (2 ** 17)
        j = math.floor(myLat / tmp1) + math.floor(0.5 + ((myLat % tmp1) / tmp1) - tmp2)
        
        return tmp1 * (j + tmp2)

    def __decodeLon(self, decLat, encLon, cType, myLon, surface):
        tmp1 = dlon(decLat, cType, surface)
        tmp2 = float(enclon) / (2 ** 17)
        m = math.floor(myLon / tmp1) + math.floor(0.5 + ((myLon % tmp1) / tmp1) - tmp2)
        
        return tmp1 * (m + tmp2)

    def cprResolveLocal(self, myLocation, encodedLocation, cType, surface):
        [myLat, myLon] = myLocation
        [encLat, encLon] = encodedLocation
        
        decodedLat = self.__decodeLat(encLat, cType, myLat, surface)
        decodedLon = self.__decodeLon(decodedLat, encLon, cType, myLon, surface)
        
        return [decodedLat, decodedLon]

    def cprResolveGlobal(self, evenPos, oddPos, mostRecent, myPos = None, surface = None):
        #cannot resolve surface positions unambiguously without knowing receiver position
        if surface and myPos is None:
            raise CPRNoPositionError
        
        dLatEven = self.__dlat(0, surface)
        dLatOdd  = self.__dlat(1, surface)
        
        evenPos = [float(evenPos[0]), float(evenPos[1])]
        oddPos = [float(oddPos[0]), float(oddPos[1])]
        
        j = math.floor(((self.__nz(1) * evenPos[0] - self.__nz(0) * oddPos[0]) / 2 ** 17) + 0.5) #latitude index
        
        rLatEven = dLatEven * ((j % self.__nz(0)) + evenPos[0] / 2 ** 17)
        rLatOdd  = dLatOdd  * ((j % self.__nz(1)) + oddPos[0] / 2 ** 17)
        
        #limit to -90, 90
        if rLatEven > 270.0:
            rLatEven -= 360.0
        if rLatOdd > 270.0:
            rLatOdd -= 360.0
        
        #This checks to see if the latitudes of the reports straddle a transition boundary
        #If so, you can't get a globally-resolvable location.
        if self.__nl(rLatEven) != self.__nl(rLatOdd):
            raise CPRBoundaryStraddleError
        
        if mostRecent == 0:
            rLat = rLatEven
        else:
            rLat = rLatOdd
        
        #disambiguate latitude
        if surface:
            if myPos[0] < 0:
                rLat -= 90
        
        dl = self.__dlon(rLat, mostRecent, surface)
        nlRLat = self.__nl(rLat)
        
        m = math.floor(((evenPos[1] * (nlRLat - 1) - oddPos[1] * nlRLat) / 2 ** 17) + 0.5) #longitude index
        
        #when surface positions straddle a disambiguation boundary (90 degrees),
        #surface decoding will fail. this might never be a problem in real life, but it'll fail in the
        #test case. the documentation doesn't mention it.
        
        if mostRecent == 0:
            encLon = evenPos[1]
        else:
            encLon = oddPos[1]
        
        rLon = dl * ((m % max(nlRLat - mostRecent , 1)) + encLon / 2.0 ** 17)
        
        #print "DL: %f nl: %f m: %f rLon: %f" % (dl, nlRLat, m, rLon)
        #print "evenPos: %x, oddPos: %x, mostRecent: %i" % (evenPos[1], oddPos[1], mostRecent)
        
        if surface:
            #longitudes need to be resolved to the nearest 90 degree segment to the receiver.
            wat = myPos[1]
            if wat < 0:
                wat += 360
                zone = lambda lon: 90 * (int(lon) / 90)
                rLon += (self.__zone(wat) - self.__zone(rlon))
        
        #limit to (-180, 180)
        if rLon > 180:
            rLon -= 360.0
        
        return [rLat, rLon]