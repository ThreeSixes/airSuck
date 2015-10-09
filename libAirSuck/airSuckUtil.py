"""
airSuckUtil by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

############
# Imports. #
############

import math
import traceback

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
            statArray = [
                "Underway using engine",
                "Anchored",
                "Not under command",
                "Restricted maneuverability",
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

    def getAISShipType(self, shipType):
        """
        getAISShipTYpe(shipType)
        
        Get the text description of a given AIS ship type. Accepts a single integer argoument.
        Returns a string.
        """
        
        # Ship types...
        shipTypes = ["Not available (default)",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Reserved",
            "Wing in ground (WIG), all ships of this type",
            "Wing in ground (WIG), Hazardous cat A",
            "Wing in ground (WIG), Hazardous cat B",
            "Wing in ground (WIG), Hazardous cat C",
            "Wing in ground (WIG), Hazardous cat D",
            "Wing in ground (WIG), Reserved",
            "Wing in ground (WIG), Reserved",
            "Wing in ground (WIG), Reserved",
            "Wing in ground (WIG), Reserved",
            "Wing in ground (WIG), Reserved",
            "Fishing",
            "Towing",
            "Towing: len > 200m / breadth > 25m",
            "Dredging/underwater ops",
            "Diving ops",
            "Military ops",
            "Sailing",
            "Pleasure Craft",
            "Reserved",
            "Reserved",
            "High speed craft (HSC), all ships of this type",
            "High speed craft (HSC), Hazardous cat A",
            "High speed craft (HSC), Hazardous cat B",
            "High speed craft (HSC), Hazardous cat C",
            "High speed craft (HSC), Hazardous cat D",
            "High speed craft (HSC), Reserved",
            "High speed craft (HSC), Reserved",
            "High speed craft (HSC), Reserved",
            "High speed craft (HSC), Reserved",
            "High speed craft (HSC)",
            "Pilot Vessel",
            "Search and Rescue vessel",
            "Tug",
            "Port Tender",
            "Anti-pollution equipment",
            "Law Enforcement",
            "Spare - Local Vessel",
            "Spare - Local Vessel",
            "Medical Transport",
            "Noncombatant ship (RR Res #18)",
            "Passenger, all ships of this type",
            "Passenger, Hazardous cat A",
            "Passenger, Hazardous cat B",
            "Passenger, Hazardous cat C",
            "Passenger, Hazardous cat D",
            "Passenger, Reserved",
            "Passenger, Reserved",
            "Passenger, Reserved",
            "Passenger, Reserved",
            "Passenger",
            "Cargo, all ships of this type",
            "Cargo, Hazardous cat A",
            "Cargo, Hazardous cat B",
            "Cargo, Hazardous cat C",
            "Cargo, Hazardous cat D",
            "Cargo, Reserved",
            "Cargo, Reserved",
            "Cargo, Reserved",
            "Cargo, Reserved",
            "Cargo",
            "Tanker, all ships of this type",
            "Tanker, Hazardous cat A",
            "Tanker, Hazardous cat B",
            "Tanker, Hazardous cat C",
            "Tanker, Hazardous cat D",
            "Tanker, Reserved",
            "Tanker, Reserved",
            "Tanker, Reserved",
            "Tanker, Reserved",
            "Tanker",
            "Other Type, all ships of this type",
            "Other Type, Hazardous cat A",
            "Other Type, Hazardous cat B",
            "Other Type, Hazardous cat C",
            "Other Type, Hazardous cat D",
            "Other Type, Reserved",
            "Other Type, Reserved",
            "Other Type, Reserved",
            "Other Type, Reserved",
            "Other Type"]
        
        return shipTypes[shipType]
    
    def getEPFDMeta(self, epfd):
        """
        getPEFDMeta(epfd)
        
        Get EPFD metadata given an EPFD value.
        
        Returns a string.
        """
        
        retVal = ""
        
        # EPFD descriptions
        epfdDesc = ["Undefined",
            "GPS",
            "GLONASS",
            "GPS + GLONASS",
            "Loran-C",
            "Chayka",
            "Integrated nav system",
            "Surveyed",
            "Galileo"]
        
        # If we have an EPFD in range...
        if epfd <= 8:
            retVal = epfdDesc[epfd]
        else:
            retVal = "Unknown"
        
        # Return the string.
        return retVal
    
    def getMMSIMeta(self, mmsi):
        """
        getMMSIMeta(mmsi)
        
        Get metatdata from a given MMSI address
        """
        
        # Empty reuturn dict.
        retVal = {}
        
        # Convert the MMSI to a string because it's easier to parse.
        mmsiStr = str(mmsi)
        
        # The character at which our MID starts
        midCursor = 0
        
        # Type of MMSI address. Defaults to ship.
        mmsiType = "Ship"
        
        # This is our master list of country codes and associated info.
        mid2Country = {
            "201": {"country": "Albania (Republic of)", "isoCC": "AL"},
            "202": {"country": "Andorra (Principality of)", "isoCC": "AD"},
            "203": {"country": "Austria", "isoCC": "AT"},
            "204": {"country": "Azores", "isoCC": "PT-20"},
            "205": {"country": "Belgium", "isoCC": "BE"},
            "206": {"country": "Belarus (Republic of)", "isoCC": "BY"},
            "207": {"country": "Bulgaria (Republic of)", "isoCC": "BG"},
            "208": {"country": "Vatican City State", "isoCC": "VA"},
            "209": {"country": "Cyprus (Republic of)", "isoCC": "CY"},
            "210": {"country": "Cyprus (Republic of)", "isoCC": "CY"},
            "211": {"country": "Germany (Federal Republic of)", "isoCC": "DE"},
            "212": {"country": "Pakistan (Islamic Republic of)", "isoCC": "CY"},
            "213": {"country": "Georgia", "isoCC": "GE"},
            "214": {"country": "Moldova (Republic of)", "isoCC": "MD"},
            "215": {"country": "Malta", "isoCC": "MT"},
            "216": {"country": "Armenia (Republic of)", "isoCC": "AM"},
            "218": {"country": "Germany (Federal Republic of)", "isoCC": "DE"},
            "219": {"country": "Denmark", "isoCC": "DK"},
            "220": {"country": "Denmark", "isoCC": "DK"},
            "224": {"country": "Spain", "isoCC": "ES"},
            "225": {"country": "Spain", "isoCC": "ES"},
            "226": {"country": "France", "isoCC": "FR"},
            "227": {"country": "France", "isoCC": "FR"},
            "228": {"country": "France", "isoCC": "FR"},
            "230": {"country": "Finland", "isoCC": "FI"},
            "231": {"country": "Faroe Islands", "isoCC": "FO"},
            "232": {"country": "United Kingdom of Great Britain and Northern Ireland", "isoCC": "GB"},
            "233": {"country": "United Kingdom of Great Britain and Northern Ireland", "isoCC": "GB"},
            "234": {"country": "United Kingdom of Great Britain and Northern Ireland", "isoCC": "GB"},
            "235": {"country": "United Kingdom of Great Britain and Northern Ireland", "isoCC": "GB"},
            "236": {"country": "Gibraltar", "isoCC": "GI"},
            "237": {"country": "Greece", "isoCC": "GR"},
            "238": {"country": "Croatia (Republic of)", "isoCC": "HR"},
            "239": {"country": "Greece", "isoCC": "GR"},
            "240": {"country": "Greece", "isoCC": "GR"},
            "241": {"country": "Greece", "isoCC": "GR"},
            "242": {"country": "Morocco (Kingdom of)", "isoCC": "MA"},
            "243": {"country": "Hungary (Republic of)", "isoCC": "UR"},
            "244": {"country": "Netherlands (Kingdom of the)", "isoCC": "NL"},
            "245": {"country": "Netherlands (Kingdom of the)", "isoCC": "NL"},
            "246": {"country": "Netherlands (Kingdom of the)", "isoCC": "NL"},
            "247": {"country": "Italy", "isoCC": "IT"},
            "248": {"country": "Malta", "isoCC": "MT"},
            "249": {"country": "Malta", "isoCC": "MT"},
            "250": {"country": "Ireland", "isoCC": "IE"},
            "251": {"country": "Iceland", "isoCC": "IE"},
            "252": {"country": "Liechtenstein (Principality of)", "isoCC": "LI"},
            "253": {"country": "Luxembourg", "isoCC": "LU"},
            "254": {"country": "Monaco (Principality of)", "isoCC": "MC"},
            "255": {"country": "Madeira", "isoCC": "PT-30"},
            "256": {"country": "Malta", "isoCC": "MT"},
            "257": {"country": "Norway", "isoCC": "NO"},
            "258": {"country": "Norway", "isoCC": "NO"},
            "259": {"country": "Norway", "isoCC": "NO"},
            "261": {"country": "Poland (Republic of)", "isoCC": "PL"},
            "262": {"country": "Montenegro", "isoCC": "ME"},
            "263": {"country": "Portugal", "isoCC": "PT"},
            "264": {"country": "Romania", "isoCC": "RO"},
            "265": {"country": "Sweden", "isoCC": "SE"},
            "266": {"country": "Sweden", "isoCC": "SE"},
            "267": {"country": "Slovak Republic", "isoCC": "SK"},
            "268": {"country": "San Marino (Republic of)", "isoCC": "SM"},
            "269": {"country": "Switzerland (Confederation of)", "isoCC": "CH"},
            "270": {"country": "Czech Republic", "isoCC": "CZ"},
            "271": {"country": "Turkey", "isoCC": "TR"},
            "272": {"country": "Ukraine", "isoCC": "UA"},
            "273": {"country": "Russian Federation", "isoCC": "RU"},
            "274": {"country": "The Former Yugoslav Republic of Macedonia", "isoCC": "MK"},
            "275": {"country": "Latvia (Republic of)", "isoCC": "LV"},
            "276": {"country": "Estonia (Republic of)", "isoCC": "EE"},
            "277": {"country": "Lithuania (Republic of)", "isoCC": "LT"},
            "278": {"country": "Slovenia (Republic of)", "isoCC": "SI"},
            "279": {"country": "Serbia (Republic of)", "isoCC": "RS"},
            "301": {"country": "Anguilla", "isoCC": "AI"},
            "303": {"country": "Alaska (State of)", "isoCC": "US-AK"},
            "304": {"country": "Antigua and Barbuda", "isoCC": "AG"},
            "305": {"country": "Antigua and Barbuda", "isoCC": "AG"},
            "306": {"country": "Netherlands Antilles", "isoCC": "AN"},
            "307": {"country": "Aruba", "isoCC": "NL-AW"},
            "308": {"country": "Bahamas (Commonwealth of the)", "isoCC": "BS"},
            "309": {"country": "Bahamas (Commonwealth of the)", "isoCC": "BS"},
            "310": {"country": "Bermuda", "isoCC": "BM"},
            "311": {"country": "Bahamas (Commonwealth of the)", "isoCC": "BS"},
            "312": {"country": "Belize", "isoCC": "BZ"},
            "314": {"country": "Barbados", "isoCC": "BB"},
            "316": {"country": "Canada", "isoCC": "CA"},
            "319": {"country": "Cayman Islands", "isoCC": "KY"},
            "321": {"country": "Costa Rica", "isoCC": "CR"},
            "323": {"country": "Cuba", "isoCC": "CU"},
            "325": {"country": "Dominica (Commonwealth of)", "isoCC": "DM"},
            "327": {"country": "Dominican Republic", "isoCC": "DO"},
            "329": {"country": "Guadeloupe (French Department of)", "isoCC": "FR-GP"},
            "330": {"country": "Grenada", "isoCC": "GD"},
            "331": {"country": "Greenland", "isoCC": "GL"},
            "332": {"country": "Guatemala (Republic of)", "isoCC": "GT"},
            "334": {"country": "Honduras (Republic of)", "isoCC": "HN"},
            "336": {"country": "Haiti (Republic of)", "isoCC": "HT"},
            "338": {"country": "United States of America", "isoCC": "US"},
            "339": {"country": "Jamaica", "isoCC": "JM"},
            "341": {"country": "Saint Kitts and Nevis (Federation of)", "isoCC": "KN"},
            "343": {"country": "Saint Lucia", "isoCC": "LC"},
            "345": {"country": "Mexico", "isoCC": "MX"},
            "347": {"country": "Martinique (French Department of)", "isoCC": "FR-MQ"},
            "348": {"country": "Montserrat", "isoCC": "MS"},
            "350": {"country": "Nicaragua", "isoCC": "NI"},
            "351": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "352": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "353": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "354": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "355": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "356": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "357": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "358": {"country": "Puerto Rico", "isoCC": "US-PR"},
            "359": {"country": "El Salvador (Republic of)", "isoCC": "SV"},
            "361": {"country": "Saint Pierre and Miquelon (Territorial Collectivity of)", "isoCC": "FR-PM"},
            "362": {"country": "Trinidad and Tobago", "isoCC": "TT"},
            "364": {"country": "Turks and Caicos Islands", "isoCC": "TC"},
            "366": {"country": "United States of America", "isoCC": "US"},
            "367": {"country": "United States of America", "isoCC": "US"},
            "368": {"country": "United States of America", "isoCC": "US"},
            "369": {"country": "United States of America", "isoCC": "US"},
            "370": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "371": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "372": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "373": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "374": {"country": "Panama (Republic of)", "isoCC": "PA"},
            "375": {"country": "Saint Vincent and the Grenadines", "isoCC": "VC"},
            "376": {"country": "Saint Vincent and the Grenadines", "isoCC": "VC"},
            "377": {"country": "Saint Vincent and the Grenadines", "isoCC": "VC"},
            "378": {"country": "British Virgin Islands", "isoCC": "VG"},
            "379": {"country": "United States Virgin Islands", "isoCC": "US-VI"},
            "401": {"country": "Afghanistan", "isoCC": "AF"},
            "403": {"country": "Saudi Arabia (Kingdom of)", "isoCC": "SA"},
            "405": {"country": "Bangladesh (People's Republic of)", "isoCC": "BD"},
            "408": {"country": "Bahrain (Kingdom of)", "isoCC": "BH"},
            "410": {"country": "Bhutan (Kingdom of)", "isoCC": "BT"},
            "412": {"country": "China (People's Republic of)", "isoCC": "CN"},
            "413": {"country": "China (People's Republic of)", "isoCC": "CN"},
            "416": {"country": "Taiwan (Province of China)", "isoCC": "CN-TW"},
            "417": {"country": "Sri Lanka (Democratic Socialist Republic of)", "isoCC": "LK"},
            "419": {"country": "India (Republic of)", "isoCC": "IN"},
            "422": {"country": "Iran (Islamic Republic of)", "isoCC": "IR"},
            "423": {"country": "Azerbaijani Republic", "isoCC": "AZ"},
            "425": {"country": "Iraq (Republic of)", "isoCC": "IQ"},
            "428": {"country": "Israel (State of)", "isoCC": "IL"},
            "431": {"country": "Japan", "isoCC": "JP"},
            "432": {"country": "Japan", "isoCC": "JP"},
            "434": {"country": "Turkmenistan", "isoCC": "TM"},
            "436": {"country": "Kazakhstan (Republic of)", "isoCC": "KZ"},
            "437": {"country": "Uzbekistan (Republic of)", "isoCC": "UZ"},
            "438": {"country": "Jordan (Hashemite Kingdom of)", "isoCC": "JO"},
            "440": {"country": "Korea (Republic of)", "isoCC": "KR"},
            "441": {"country": "Korea (Republic of)", "isoCC": "KR"},
            "443": {"country": "Palestine (In accordance with Resolution 99 Rev. Antalya 2006)", "isoCC": "PS"},
            "445": {"country": "Democratic People's Republic of Korea", "isoCC": "KP"},
            "447": {"country": "Kuwait (State of)", "isoCC": "KW"},
            "450": {"country": "Lebanon", "isoCC": "LB"},
            "451": {"country": "Kyrgyz Republic", "isoCC": "KG"},
            "453": {"country": "Macao (Special Administrative Region of China)", "isoCC": "CN-MO"},
            "455": {"country": "Maldives (Republic of)", "isoCC": "MV"},
            "457": {"country": "Mongolia", "isoCC": "MN"},
            "459": {"country": "Nepal (Federal Democratic Republic of)", "isoCC": "NP"},
            "461": {"country": "Oman (Sultanate of)", "isoCC": "OM"},
            "463": {"country": "Pakistan (Islamic Republic of)", "isoCC": "PK"},
            "466": {"country": "Qatar (State of)", "isoCC": "QA"},
            "468": {"country": "Syrian Arab Republic", "isoCC": "SY"},
            "470": {"country": "United Arab Emirates", "isoCC": "AE"},
            "473": {"country": "Yemen (Republic of)", "isoCC": "YE"},
            "475": {"country": "Yemen (Republic of)", "isoCC": "YE"},
            "477": {"country": "Hong Kong (Special Administrative Region of China)", "isoCC": "CN-HK"},
            "478": {"country": "Bosnia and Herzegovina", "isoCC": "BA"},
            "501": {"country": "Adelie Land", "isoCC": "AQ"},
            "503": {"country": "Australia", "isoCC": "AU"},
            "506": {"country": "Myanmar (Union of)", "isoCC": "MM"},
            "508": {"country": "Brunei Darussalam", "isoCC": "BN"},
            "510": {"country": "Micronesia (Federated States of)", "isoCC": "FM"},
            "511": {"country": "Palau (Republic of)", "isoCC": "PW"},
            "512": {"country": "New Zealand", "isoCC": "NZ"},
            "514": {"country": "Cambodia (Kingdom of)", "isoCC": "KH"},
            "515": {"country": "Cambodia (Kingdom of)", "isoCC": "KH"},
            "516": {"country": "Christmas Island (Indian Ocean)", "isoCC": "CX"},
            "518": {"country": "Cook Islands", "isoCC": "CK"},
            "520": {"country": "Fiji (Republic of)", "isoCC": "FJ"},
            "523": {"country": "Cocos (Keeling) Islands", "isoCC": "CC"},
            "525": {"country": "Indonesia (Republic of)", "isoCC": "ID"},
            "529": {"country": "Kiribati (Republic of)", "isoCC": "KI"},
            "531": {"country": "Lao People's Democratic Republic", "isoCC": "LA"},
            "533": {"country": "Malaysia", "isoCC": "MY"},
            "536": {"country": "Northern Mariana Islands (Commonwealth of the)", "isoCC": "US-MP"},
            "538": {"country": "Marshall Islands (Republic of the)", "isoCC": "MH"},
            "540": {"country": "New Caledonia", "isoCC": "NC"},
            "542": {"country": "Niue", "isoCC": "NU"},
            "544": {"country": "Nauru (Republic of)", "isoCC": "NR"},
            "546": {"country": "French Polynesia", "isoCC": "FR-PF"},
            "548": {"country": "Philippines (Republic of the)", "isoCC": "PH"},
            "553": {"country": "Papua New Guinea", "isoCC": "PG"},
            "555": {"country": "Pitcairn Island", "isoCC": "PN"},
            "557": {"country": "Solomon Islands", "isoCC": "SB"},
            "559": {"country": "American Samoa", "isoCC": "US-AS"},
            "561": {"country": "Samoa (Independent State of)", "isoCC": "WS"},
            "563": {"country": "Singapore (Republic of)", "isoCC": "SG"},
            "564": {"country": "Singapore (Republic of)", "isoCC": "SG"},
            "565": {"country": "Singapore (Republic of)", "isoCC": "SG"},
            "567": {"country": "Thailand", "isoCC": "TH"},
            "570": {"country": "Tonga (Kingdom of)", "isoCC": "TO"},
            "572": {"country": "Tuvalu", "isoCC": "TV"},
            "574": {"country": "Viet Nam (Socialist Republic of)", "isoCC": "VN"},
            "576": {"country": "Vanuatu (Republic of)", "isoCC": "VU"},
            "578": {"country": "Wallis and Futuna Islands", "isoCC": "FR-WF"},
            "601": {"country": "South Africa (Republic of)", "isoCC": "ZA"},
            "603": {"country": "Angola (Republic of)", "isoCC": "AO"},
            "605": {"country": "Algeria (People's Democratic Republic of)", "isoCC": "DZ"},
            "607": {"country": "Saint Paul and Amsterdam Islands", "isoCC": "FR-TF"},
            "608": {"country": "Ascension Island", "isoCC": "SH"},
            "609": {"country": "Burundi (Republic of)", "isoCC": "BI"},
            "610": {"country": "Benin (Republic of)", "isoCC": "BJ"},
            "611": {"country": "Botswana (Republic of)", "isoCC": "BW"},
            "612": {"country": "Central African Republic", "isoCC": "CF"},
            "613": {"country": "Cameroon (Republic of)", "isoCC": "CM"},
            "615": {"country": "Congo (Republic of the)", "isoCC": "CG"},
            "616": {"country": "Comoros (Union of the)", "isoCC": "KM"},
            "617": {"country": "Cape Verde (Republic of)", "isoCC": "CV"},
            "618": {"country": "Crozet Archipelago", "isoCC": "FR-TF"},
            "619": {"country": "C?te d'Ivoire (Republic of)", "isoCC": "CI"},
            "621": {"country": "Djibouti (Republic of)", "isoCC": "DJ"},
            "622": {"country": "Egypt (Arab Republic of)", "isoCC": "EG"},
            "624": {"country": "Ethiopia (Federal Democratic Republic of)", "isoCC": "ET"},
            "625": {"country": "Eritrea", "isoCC": "ER"},
            "626": {"country": "Gabonese Republic", "isoCC": "GA"},
            "627": {"country": "Ghana", "isoCC": "GH"},
            "629": {"country": "Gambia (Republic of the)", "isoCC": "GM"},
            "630": {"country": "Guinea-Bissau (Republic of)", "isoCC": "GW"},
            "631": {"country": "Equatorial Guinea (Republic of)", "isoCC": "GQ"},
            "632": {"country": "Guinea (Republic of)", "isoCC": "GN"},
            "633": {"country": "Burkina Faso", "isoCC": "BF"},
            "634": {"country": "Kenya (Republic of)", "isoCC": "KE"},
            "635": {"country": "Kerguelen Islands", "isoCC": "FR-TF"},
            "636": {"country": "Liberia (Republic of)", "isoCC": "LR"},
            "637": {"country": "Liberia (Republic of)", "isoCC": "LR"},
            "642": {"country": "Socialist People's Libyan Arab Jamahiriya", "isoCC": "LY"},
            "644": {"country": "Lesotho (Kingdom of)", "isoCC": "LS"},
            "645": {"country": "Mauritius (Republic of)", "isoCC": "MU"},
            "647": {"country": "Madagascar (Republic of)", "isoCC": "MG"},
            "649": {"country": "Mali (Republic of)", "isoCC": "ML"},
            "650": {"country": "Mozambique (Republic of)", "isoCC": "MZ"},
            "654": {"country": "Mauritania (Islamic Republic of)", "isoCC": "MR"},
            "655": {"country": "Malawi", "isoCC": "MW"},
            "656": {"country": "Niger (Republic of the)", "isoCC": "NE"},
            "657": {"country": "Nigeria (Federal Republic of)", "isoCC": "NG"},
            "659": {"country": "Namibia (Republic of)", "isoCC": "NA"},
            "660": {"country": "Reunion (French Department of)", "isoCC": "FR-RE"},
            "661": {"country": "Rwanda (Republic of)", "isoCC": "RW"},
            "662": {"country": "Sudan (Republic of the)", "isoCC": "SS"},
            "663": {"country": "Senegal (Republic of)", "isoCC": "SN"},
            "664": {"country": "Seychelles (Republic of)", "isoCC": "SC"},
            "665": {"country": "Saint Helena", "isoCC": "SH"},
            "666": {"country": "Somali Democratic Republic", "isoCC": "SO"},
            "667": {"country": "Sierra Leone", "isoCC": "SL"},
            "668": {"country": "Sao Tome and Principe (Democratic Republic of)", "isoCC": "ST"},
            "669": {"country": "Swaziland (Kingdom of)", "isoCC": "SZ"},
            "670": {"country": "Chad (Republic of)", "isoCC": "TD"},
            "671": {"country": "Togolese Republic", "isoCC": "GB"},
            "672": {"country": "Tunisia", "isoCC": "TN"},
            "674": {"country": "Tanzania (United Republic of)", "isoCC": "TZ"},
            "675": {"country": "Uganda (Republic of)", "isoCC": "UG"},
            "676": {"country": "Democratic Republic of the Congo", "isoCC": "CG"},
            "677": {"country": "Tanzania (United Republic of)", "isoCC": "TZ"},
            "678": {"country": "Zambia (Republic of)", "isoCC": "ZM"},
            "679": {"country": "Zimbabwe (Republic of)", "isoCC": "ZW"},
            "701": {"country": "Argentine Republic", "isoCC": "AR"},
            "710": {"country": "Brazil (Federative Republic of)", "isoCC": "BR"},
            "720": {"country": "Bolivia (Plurinational State of)", "isoCC": "BO"},
            "725": {"country": "Chile", "isoCC": "CL"},
            "730": {"country": "Colombia (Republic of)", "isoCC": "CO"},
            "735": {"country": "Ecuador", "isoCC": "EC"},
            "740": {"country": "Falkland Islands (Malvinas)", "isoCC": "FK"},
            "745": {"country": "Guiana (French Department of)", "isoCC": "FR-GF"},
            "750": {"country": "Guyana", "isoCC": "GY"},
            "755": {"country": "Paraguay (Republic of)", "isoCC": "PY"},
            "760": {"country": "Peru", "isoCC": "PE"},
            "765": {"country": "Suriname (Republic of)", "isoCC": "SR"},
            "770": {"country": "Uruguay (Eastern Republic of)", "isoCC": "UR"},
            "775": {"country": "Venezuela (Bolivarian Republic of)", "isoCC": "VE"}
        }
        
        # Figure out if we have certain types of MMSI address.
        if (mmsi >= 800000000) and (mmsi <= 899999999):
            mmsiType = "Diver's radio"
            
            # Where does the MID start?
            midCursor = 1
        
        if (mmsi >= 10000000) and (mmsi <= 99999999):
            mmsiType = "Group of ships"
            
            # Where does the MID start?
            midCursor = 0
        
        if (mmsi >= 1000000) and (mmsi <= 9999999):
            mmsiType = "Coastal station"
            
            # Where does the MID start?
            midCursor = 0
        
        if (mmsi >= 111000000) and (mmsi <= 111999999):
            mmsiType = "SAR aircraft"
            
            # Where does the MID start?
            midCursor = 3
        
        if (mmsi >= 990000000) and (mmsi <= 999999999):
            mmsiType = "Aid to Navigation"
            
            # Where does the MID start?
            midCursor = 2
        
        if (mmsi >= 980000000) and (mmsi <= 989999999):
            mmsiType = "Craft w/ parent ship"
            
            # Where does the MID start?
            midCursor = 2
        
        if (mmsi >= 970000000) and (mmsi <= 970999999):
            mmsiType = "SART (Search and Rescue Xmitter)"
            
            # Where does the MID start?
            midCursor = 3
        
        if (mmsi >= 972000000) and (mmsi <= 972999999):
            mmsiType = "MOB (Man Overboard) device"
            
            # Where does the MID start?
            midCursor = 3
        
        if (mmsi >= 974000000) and (mmsi <= 974999999):
            mmsiType = "EPIRB"
            
            # Where does the MID start?
            midCursor = 3
        
        # Set the mmsiType.
        retVal.update({'mmsiType': mmsiType})
        
        try:
            # Get the MID portion of the MMSI.
            midStr = mmsiStr[midCursor:(midCursor + 3)]
            midCtry = mid2Country[midStr]
            # Set the country data.
            retVal.update({'mmsiCountry': midCtry['country']})
            retVal.update({'mmsiCC': midCtry['isoCC']})
        except:
            print("Failed to derive country data from MID:")
            tb = traceback.format_exc()
            print(tb)
        
        # Send the data back along.
        return retVal