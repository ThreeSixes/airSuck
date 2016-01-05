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
    def __init__(self):
        """
        airSuckUtil is a class that contains utility functions to assist with airSuck computations.
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
        startLat = math.radians(float(coordsA[0]))
        startLong = math.radians(float(coordsA[1]))
        endLat = math.radians(float(coordsB[0]))
        endLong = math.radians(float(coordsB[1]))
        
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
            
            elif ((aInt >= 5100) and (aInt <= 5377)):
                aMeta = "Internal ARTCC / DoD in US, not on RADAR"
            
            elif (aInt >= 4401 and aInt <= 4433) or (aInt >= 4466 and aInt <= 4477):
                aMeta = "Special ops by LEO"
            
            elif (aInt >= 7601 and aInt <= 7607) or (aInt >= 7701 and aInt <= 7707):
                aMeta = "Special ops by Federal LEO"
            
            elif (aInt >= 5001 and aInt <= 5057) or (aInt >= 5063 and aInt <= 5077) or (aInt >= 5401 and aInt <= 5477) or (aInt >= 6101 and aInt <= 6177) or (aInt >= 6401 and aInt <= 6477) or (aInt == 7501) or (aInt == 7577):
                aMeta = "DoD aircraft, NORAD assigned"
            
            elif ((aInt > 0) and (aInt <= 77)) or ((aInt >= 4200) and (aInt <= 4377)) or ((aInt >= 4500) and (aInt <= 4777)) or ((aInt >= 5100) and (aInt <= 5377)) or ((aInt >= 5500) and (aInt <= 5577)):
                aMeta = "Internal ARTCC"
            
            elif ((aInt >= 500) and (aInt <= 1177)) or ((aInt >= 1300) and (aInt <= 4177)) or ((aInt >= 5600) and (aInt <= 6077)) or ((aInt >= 6200) and (aInt <= 6377)) or ((aInt >= 6500) and (aInt <= 7077)) or ((aInt >= 7100) and (aInt <= 7377)) or ((aInt >= 7610) and (aInt <= 7677)) or ((aInt >= 7710) and (aInt <= 7776)):
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
        
        # Set a blank return value.
        retVal = ""
        
        # Ship types...
        shipTypes = ["Not available",
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
            "Wing in ground",
            "Wing in ground, Hazardous cat A",
            "Wing in ground, Hazardous cat B",
            "Wing in ground, Hazardous cat C",
            "Wing in ground, Hazardous cat D",
            "Wing in ground, Reserved",
            "Wing in ground, Reserved",
            "Wing in ground, Reserved",
            "Wing in ground, Reserved",
            "Wing in ground, Reserved",
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
            "High speed craft",
            "High speed craft, Hazardous cat A",
            "High speed craft, Hazardous cat B",
            "High speed craft, Hazardous cat C",
            "High speed craft, Hazardous cat D",
            "High speed craft, Reserved",
            "High speed craft, Reserved",
            "High speed craft, Reserved",
            "High speed craft, Reserved",
            "High speed craft",
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
            "Passenger",
            "Passenger, Hazardous cat A",
            "Passenger, Hazardous cat B",
            "Passenger, Hazardous cat C",
            "Passenger, Hazardous cat D",
            "Passenger, Reserved",
            "Passenger, Reserved",
            "Passenger, Reserved",
            "Passenger, Reserved",
            "Passenger",
            "Cargo",
            "Cargo, Hazardous cat A",
            "Cargo, Hazardous cat B",
            "Cargo, Hazardous cat C",
            "Cargo, Hazardous cat D",
            "Cargo, Reserved",
            "Cargo, Reserved",
            "Cargo, Reserved",
            "Cargo, Reserved",
            "Cargo",
            "Tanker",
            "Tanker, Hazardous cat A",
            "Tanker, Hazardous cat B",
            "Tanker, Hazardous cat C",
            "Tanker, Hazardous cat D",
            "Tanker, Reserved",
            "Tanker, Reserved",
            "Tanker, Reserved",
            "Tanker, Reserved",
            "Tanker",
            "Other",
            "Other, Hazardous cat A",
            "Other, Hazardous cat B",
            "Other, Hazardous cat C",
            "Other, Hazardous cat D",
            "Other, Reserved",
            "Other, Reserved",
            "Other, Reserved",
            "Other, Reserved",
            "Other"]
        
        try:
            # Attempt to set ship type.
            retVal = shipTypes[shipType]
        
        except IndexError:
            # Do nothing because sometimes we lack valid data.
            pass
        
        except Exception as e:
            # Pass any other exceptoins back up the chain.
            raise e
        
        return retVal
    
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
    
    def isoCCtoCountry(self, isoCC):
        """
        Convert a given ISO country code string to a country name.
        """
        
        # Return value
        retVal = {}
        
        # A table of ISO country codes to country name.
        isoCC2country = {
            "AD": {"country": "Andorra (Principality of)"},
            "AE": {"country": "United Arab Emirates"},
            "AF": {"country": "Afghanistan"},
            "AG": {"country": "Antigua and Barbuda"},
            "AI": {"country": "Anguilla"},
            "AL": {"country": "Albania (Republic of)"},
            "AM": {"country": "Armenia (Republic of)"},
            "AN": {"country": "Netherlands Antilles"},
            "AO": {"country": "Angola (Republic of)"},
            "AQ": {"country": "Adelie Land"},
            "AR": {"country": "Argentine Republic"},
            "AT": {"country": "Austria"},
            "AU": {"country": "Australia"},
            "AZ": {"country": "Azerbaijani Republic"},
            "BA": {"country": "Bosnia and Herzegovina"},
            "BB": {"country": "Barbados"},
            "BD": {"country": "Bangladesh (People's Republic of)"},
            "BE": {"country": "Belgium"},
            "BF": {"country": "Burkina Faso"},
            "BG": {"country": "Bulgaria (Republic of)"},
            "BH": {"country": "Bahrain (Kingdom of)"},
            "BI": {"country": "Burundi (Republic of)"},
            "BJ": {"country": "Benin (Republic of)"},
            "BM": {"country": "Bermuda"},
            "BN": {"country": "Brunei Darussalam"},
            "BO": {"country": "Bolivia (Plurinational State of)"},
            "BR": {"country": "Brazil (Federative Republic of)"},
            "BS": {"country": "Bahamas (Commonwealth of the)"},
            "BT": {"country": "Bhutan (Kingdom of)"},
            "BW": {"country": "Botswana (Republic of)"},
            "BY": {"country": "Belarus (Republic of)"},
            "BZ": {"country": "Belize"},
            "CA": {"country": "Canada"},
            "CC": {"country": "Cocos (Keeling) Islands"},
            "CF": {"country": "Central African Republic"},
            "CG": {"country": "Congo (Republic of the)"},
            "CG": {"country": "Democratic Republic of the Congo"},
            "CH": {"country": "Switzerland (Confederation of)"},
            "CI": {"country": "Cote d'Ivoire (Republic of)"},
            "CK": {"country": "Cook Islands"},
            "CL": {"country": "Chile"},
            "CM": {"country": "Cameroon (Republic of)"},
            "CN": {"country": "China (People's Republic of)"},
            "CN-HK": {"country": "Hong Kong (Special Administrative Region of China)"},
            "CN-MO": {"country": "Macao (Special Administrative Region of China)"},
            "CN-TW": {"country": "Taiwan (Province of China)"},
            "CO": {"country": "Colombia (Republic of)"},
            "CR": {"country": "Costa Rica"},
            "CU": {"country": "Cuba"},
            "CV": {"country": "Cape Verde (Republic of)"},
            "CX": {"country": "Christmas Island (Indian Ocean)"},
            "CY": {"country": "Cyprus (Republic of)"},
            "CZ": {"country": "Czech Republic"},
            "DE": {"country": "Germany (Federal Republic of)"},
            "DJ": {"country": "Djibouti (Republic of)"},
            "DK": {"country": "Denmark"},
            "DM": {"country": "Dominica (Commonwealth of)"},
            "DO": {"country": "Dominican Republic"},
            "DZ": {"country": "Algeria (People's Democratic Republic of)"},
            "EC": {"country": "Ecuador"},
            "EE": {"country": "Estonia (Republic of)"},
            "EG": {"country": "Egypt (Arab Republic of)"},
            "ER": {"country": "Eritrea"},
            "ES": {"country": "Spain"},
            "ET": {"country": "Ethiopia (Federal Democratic Republic of)"},
            "FI": {"country": "Finland"},
            "FJ": {"country": "Fiji (Republic of)"},
            "FK": {"country": "Falkland Islands (Malvinas)"},
            "FM": {"country": "Micronesia (Federated States of)"},
            "FO": {"country": "Faroe Islands"},
            "FR": {"country": "France"},
            "FR-GF": {"country": "Guiana (French Department of)"},
            "FR-GP": {"country": "Guadeloupe (French Department of)"},
            "FR-MQ": {"country": "Martinique (French Department of)"},
            "FR-PF": {"country": "French Polynesia"},
            "FR-PM": {"country": "Saint Pierre and Miquelon (Territorial Collectivity of)"},
            "FR-RE": {"country": "Reunion (French Department of)"},
            "FR-TF": {"country": "Crozet Archipelago"},
            "FR-TF": {"country": "Kerguelen Islands"},
            "FR-TF": {"country": "Saint Paul and Amsterdam Islands"},
            "FR-WF": {"country": "Wallis and Futuna Islands"},
            "GA": {"country": "Gabonese Republic"},
            "GB": {"country": "Togolese Republic"},
            "GB": {"country": "United Kingdom of Great Britain and Northern Ireland"},
            "GD": {"country": "Grenada"},
            "GE": {"country": "Georgia"},
            "GH": {"country": "Ghana"},
            "GI": {"country": "Gibraltar"},
            "GL": {"country": "Greenland"},
            "GM": {"country": "Gambia (Republic of the)"},
            "GN": {"country": "Guinea (Republic of)"},
            "GQ": {"country": "Equatorial Guinea (Republic of)"},
            "GR": {"country": "Greece"},
            "GT": {"country": "Guatemala (Republic of)"},
            "GW": {"country": "Guinea-Bissau (Republic of)"},
            "GY": {"country": "Guyana"},
            "HN": {"country": "Honduras (Republic of)"},
            "HR": {"country": "Croatia (Republic of)"},
            "HT": {"country": "Haiti (Republic of)"},
            "ID": {"country": "Indonesia (Republic of)"},
            "IS": {"country": "Iceland"},
            "IE": {"country": "Ireland"},
            "IL": {"country": "Israel (State of)"},
            "IN": {"country": "India (Republic of)"},
            "IQ": {"country": "Iraq (Republic of)"},
            "IR": {"country": "Iran (Islamic Republic of)"},
            "IT": {"country": "Italy"},
            "JM": {"country": "Jamaica"},
            "JO": {"country": "Jordan (Hashemite Kingdom of)"},
            "JP": {"country": "Japan"},
            "KE": {"country": "Kenya (Republic of)"},
            "KG": {"country": "Kyrgyz Republic"},
            "KH": {"country": "Cambodia (Kingdom of)"},
            "KI": {"country": "Kiribati (Republic of)"},
            "KM": {"country": "Comoros (Union of the)"},
            "KN": {"country": "Saint Kitts and Nevis (Federation of)"},
            "KP": {"country": "Democratic People's Republic of Korea"},
            "KR": {"country": "Korea (Republic of)"},
            "KW": {"country": "Kuwait (State of)"},
            "KY": {"country": "Cayman Islands"},
            "KZ": {"country": "Kazakhstan (Republic of)"},
            "LA": {"country": "Lao People's Democratic Republic"},
            "LB": {"country": "Lebanon"},
            "LC": {"country": "Saint Lucia"},
            "LI": {"country": "Liechtenstein (Principality of)"},
            "LK": {"country": "Sri Lanka (Democratic Socialist Republic of)"},
            "LR": {"country": "Liberia (Republic of)"},
            "LS": {"country": "Lesotho (Kingdom of)"},
            "LT": {"country": "Lithuania (Republic of)"},
            "LU": {"country": "Luxembourg"},
            "LV": {"country": "Latvia (Republic of)"},
            "LY": {"country": "Socialist People's Libyan Arab Jamahiriya"},
            "MA": {"country": "Morocco (Kingdom of)"},
            "MC": {"country": "Monaco (Principality of)"},
            "MD": {"country": "Moldova (Republic of)"},
            "ME": {"country": "Montenegro"},
            "MG": {"country": "Madagascar (Republic of)"},
            "MH": {"country": "Marshall Islands (Republic of the)"},
            "MK": {"country": "The Former Yugoslav Republic of Macedonia"},
            "ML": {"country": "Mali (Republic of)"},
            "MM": {"country": "Myanmar (Union of)"},
            "MN": {"country": "Mongolia"},
            "MR": {"country": "Mauritania (Islamic Republic of)"},
            "MS": {"country": "Montserrat"},
            "MT": {"country": "Malta"},
            "MU": {"country": "Mauritius (Republic of)"},
            "MV": {"country": "Maldives (Republic of)"},
            "MW": {"country": "Malawi"},
            "MX": {"country": "Mexico"},
            "MY": {"country": "Malaysia"},
            "MZ": {"country": "Mozambique (Republic of)"},
            "NA": {"country": "Namibia (Republic of)"},
            "NC": {"country": "New Caledonia"},
            "NE": {"country": "Niger (Republic of the)"},
            "NG": {"country": "Nigeria (Federal Republic of)"},
            "NI": {"country": "Nicaragua"},
            "NL-AW": {"country": "Aruba"},
            "NL": {"country": "Netherlands (Kingdom of the)"},
            "NO": {"country": "Norway"},
            "NP": {"country": "Nepal (Federal Democratic Republic of)"},
            "NR": {"country": "Nauru (Republic of)"},
            "NU": {"country": "Niue"},
            "NZ": {"country": "New Zealand"},
            "OM": {"country": "Oman (Sultanate of)"},
            "PA": {"country": "Panama (Republic of)"},
            "PE": {"country": "Peru"},
            "PG": {"country": "Papua New Guinea"},
            "PH": {"country": "Philippines (Republic of the)"},
            "PK": {"country": "Pakistan (Islamic Republic of)"},
            "PL": {"country": "Poland (Republic of)"},
            "PN": {"country": "Pitcairn Island"},
            "PS": {"country": "Palestine (In accordance with Resolution 99 Rev. Antalya 2006)"},
            "PT-20": {"country": "Azores"},
            "PT-30": {"country": "Madeira"},
            "PT": {"country": "Portugal"},
            "PW": {"country": "Palau (Republic of)"},
            "PY": {"country": "Paraguay (Republic of)"},
            "QA": {"country": "Qatar (State of)"},
            "RO": {"country": "Romania"},
            "RS": {"country": "Serbia (Republic of)"},
            "RU": {"country": "Russian Federation"},
            "RW": {"country": "Rwanda (Republic of)"},
            "SA": {"country": "Saudi Arabia (Kingdom of)"},
            "SB": {"country": "Solomon Islands"},
            "SC": {"country": "Seychelles (Republic of)"},
            "SE": {"country": "Sweden"},
            "SG": {"country": "Singapore (Republic of)"},
            "SH": {"country": "Ascension Island"},
            "SH": {"country": "Saint Helena"},
            "SI": {"country": "Slovenia (Republic of)"},
            "SK": {"country": "Slovak Republic"},
            "SL": {"country": "Sierra Leone"},
            "SM": {"country": "San Marino (Republic of)"},
            "SN": {"country": "Senegal (Republic of)"},
            "SO": {"country": "Somali Democratic Republic"},
            "SR": {"country": "Suriname (Republic of)"},
            "SS": {"country": "Sudan (Republic of the)"},
            "ST": {"country": "Sao Tome and Principe (Democratic Republic of)"},
            "SV": {"country": "El Salvador (Republic of)"},
            "SY": {"country": "Syrian Arab Republic"},
            "SZ": {"country": "Swaziland (Kingdom of)"},
            "TC": {"country": "Turks and Caicos Islands"},
            "TD": {"country": "Chad (Republic of)"},
            "TH": {"country": "Thailand"},
            "TJ": {"country": "Tajikistan"},
            "TM": {"country": "Turkmenistan"},
            "TN": {"country": "Tunisia"},
            "TO": {"country": "Tonga (Kingdom of)"},
            "TR": {"country": "Turkey"},
            "TT": {"country": "Trinidad and Tobago"},
            "TV": {"country": "Tuvalu"},
            "TZ": {"country": "Tanzania (United Republic of)"},
            "UA": {"country": "Ukraine"},
            "UG": {"country": "Uganda (Republic of)"},
            "HU": {"country": "Hungary (Republic of)"},
            "UR": {"country": "Uruguay (Eastern Republic of)"},
            "US-AK": {"country": "Alaska (State of)"},
            "US-AS": {"country": "American Samoa"},
            "US": {"country": "United States of America"},
            "US-MP": {"country": "Northern Mariana Islands (Commonwealth of the)"},
            "US-PR": {"country": "Puerto Rico"},
            "US-VI": {"country": "United States Virgin Islands"},
            "UZ": {"country": "Uzbekistan (Republic of)"},
            "VA": {"country": "Vatican City State"},
            "VC": {"country": "Saint Vincent and the Grenadines"},
            "VE": {"country": "Venezuela (Bolivarian Republic of)"},
            "VG": {"country": "British Virgin Islands"},
            "VN": {"country": "Viet Nam (Socialist Republic of)"},
            "VU": {"country": "Vanuatu (Republic of)"},
            "WS": {"country": "Samoa (Independent State of)"},
            "YE": {"country": "Yemen (Republic of)"},
            "YU": {"country": "Yugoslavia"},
            "ZA": {"country": "South Africa (Republic of)"},
            "ZM": {"country": "Zambia (Republic of)"},
            "ZW": {"country": "Zimbabwe (Republic of)"}
        }
        
        try:
            retVal = isoCC2country[isoCC]
        
        except KeyError:
            # We have a missing bit of data aparently. Keep going.
            pass
        
        return retVal
    
    
    def getMMSIMeta(self, mmsi, cc2Country=False):
        """
        getMMSIMeta(mmsi)
        
        Get metatdata from a given MMSI address. This is based on the following table:
        http://www.vtexplorer.com/vessel-tracking-mmsi-mid-codes.html
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
        mid2isoCC = {
            "201": {"isoCC": "AL"},
            "202": {"isoCC": "AD"},
            "203": {"isoCC": "AT"},
            "204": {"isoCC": "PT-20"},
            "205": {"isoCC": "BE"},
            "206": {"isoCC": "BY"},
            "207": {"isoCC": "BG"},
            "208": {"isoCC": "VA"},
            "209": {"isoCC": "CY"},
            "210": {"isoCC": "CY"},
            "211": {"isoCC": "DE"},
            "212": {"isoCC": "CY"},
            "213": {"isoCC": "GE"},
            "214": {"isoCC": "MD"},
            "215": {"isoCC": "MT"},
            "216": {"isoCC": "AM"},
            "218": {"isoCC": "DE"},
            "219": {"isoCC": "DK"},
            "220": {"isoCC": "DK"},
            "224": {"isoCC": "ES"},
            "225": {"isoCC": "ES"},
            "226": {"isoCC": "FR"},
            "227": {"isoCC": "FR"},
            "228": {"isoCC": "FR"},
            "230": {"isoCC": "FI"},
            "231": {"isoCC": "FO"},
            "232": {"isoCC": "GB"},
            "233": {"isoCC": "GB"},
            "234": {"isoCC": "GB"},
            "235": {"isoCC": "GB"},
            "236": {"isoCC": "GI"},
            "237": {"isoCC": "GR"},
            "238": {"isoCC": "HR"},
            "239": {"isoCC": "GR"},
            "240": {"isoCC": "GR"},
            "241": {"isoCC": "GR"},
            "242": {"isoCC": "MA"},
            "243": {"isoCC": "HU"},
            "244": {"isoCC": "NL"},
            "245": {"isoCC": "NL"},
            "246": {"isoCC": "NL"},
            "247": {"isoCC": "IT"},
            "248": {"isoCC": "MT"},
            "249": {"isoCC": "MT"},
            "250": {"isoCC": "IE"},
            "251": {"isoCC": "IS"},
            "252": {"isoCC": "LI"},
            "253": {"isoCC": "LU"},
            "254": {"isoCC": "MC"},
            "255": {"isoCC": "PT-30"},
            "256": {"isoCC": "MT"},
            "257": {"isoCC": "NO"},
            "258": {"isoCC": "NO"},
            "259": {"isoCC": "NO"},
            "261": {"isoCC": "PL"},
            "262": {"isoCC": "ME"},
            "263": {"isoCC": "PT"},
            "264": {"isoCC": "RO"},
            "265": {"isoCC": "SE"},
            "266": {"isoCC": "SE"},
            "267": {"isoCC": "SK"},
            "268": {"isoCC": "SM"},
            "269": {"isoCC": "CH"},
            "270": {"isoCC": "CZ"},
            "271": {"isoCC": "TR"},
            "272": {"isoCC": "UA"},
            "273": {"isoCC": "RU"},
            "274": {"isoCC": "MK"},
            "275": {"isoCC": "LV"},
            "276": {"isoCC": "EE"},
            "277": {"isoCC": "LT"},
            "278": {"isoCC": "SI"},
            "279": {"isoCC": "RS"},
            "301": {"isoCC": "AI"},
            "303": {"isoCC": "US-AK"},
            "304": {"isoCC": "AG"},
            "305": {"isoCC": "AG"},
            "306": {"isoCC": "AN"},
            "307": {"isoCC": "NL-AW"},
            "308": {"isoCC": "BS"},
            "309": {"isoCC": "BS"},
            "310": {"isoCC": "BM"},
            "311": {"isoCC": "BS"},
            "312": {"isoCC": "BZ"},
            "314": {"isoCC": "BB"},
            "316": {"isoCC": "CA"},
            "319": {"isoCC": "KY"},
            "321": {"isoCC": "CR"},
            "323": {"isoCC": "CU"},
            "325": {"isoCC": "DM"},
            "327": {"isoCC": "DO"},
            "329": {"isoCC": "FR-GP"},
            "330": {"isoCC": "GD"},
            "331": {"isoCC": "GL"},
            "332": {"isoCC": "GT"},
            "334": {"isoCC": "HN"},
            "336": {"isoCC": "HT"},
            "338": {"isoCC": "US"},
            "339": {"isoCC": "JM"},
            "341": {"isoCC": "KN"},
            "343": {"isoCC": "LC"},
            "345": {"isoCC": "MX"},
            "347": {"isoCC": "FR-MQ"},
            "348": {"isoCC": "MS"},
            "350": {"isoCC": "NI"},
            "351": {"isoCC": "PA"},
            "352": {"isoCC": "PA"},
            "353": {"isoCC": "PA"},
            "354": {"isoCC": "PA"},
            "355": {"isoCC": "PA"},
            "356": {"isoCC": "PA"},
            "357": {"isoCC": "PA"},
            "358": {"isoCC": "US-PR"},
            "359": {"isoCC": "SV"},
            "361": {"isoCC": "FR-PM"},
            "362": {"isoCC": "TT"},
            "364": {"isoCC": "TC"},
            "366": {"isoCC": "US"},
            "367": {"isoCC": "US"},
            "368": {"isoCC": "US"},
            "369": {"isoCC": "US"},
            "370": {"isoCC": "PA"},
            "371": {"isoCC": "PA"},
            "372": {"isoCC": "PA"},
            "373": {"isoCC": "PA"},
            "374": {"isoCC": "PA"},
            "375": {"isoCC": "VC"},
            "376": {"isoCC": "VC"},
            "377": {"isoCC": "VC"},
            "378": {"isoCC": "VG"},
            "379": {"isoCC": "US-VI"},
            "401": {"isoCC": "AF"},
            "403": {"isoCC": "SA"},
            "405": {"isoCC": "BD"},
            "408": {"isoCC": "BH"},
            "410": {"isoCC": "BT"},
            "412": {"isoCC": "CN"},
            "413": {"isoCC": "CN"},
            "416": {"isoCC": "CN-TW"},
            "417": {"isoCC": "LK"},
            "419": {"isoCC": "IN"},
            "422": {"isoCC": "IR"},
            "423": {"isoCC": "AZ"},
            "425": {"isoCC": "IQ"},
            "428": {"isoCC": "IL"},
            "431": {"isoCC": "JP"},
            "432": {"isoCC": "JP"},
            "434": {"isoCC": "TM"},
            "436": {"isoCC": "KZ"},
            "437": {"isoCC": "UZ"},
            "438": {"isoCC": "JO"},
            "440": {"isoCC": "KR"},
            "441": {"isoCC": "KR"},
            "443": {"isoCC": "PS"},
            "445": {"isoCC": "KP"},
            "447": {"isoCC": "KW"},
            "450": {"isoCC": "LB"},
            "451": {"isoCC": "KG"},
            "453": {"isoCC": "CN-MO"},
            "455": {"isoCC": "MV"},
            "457": {"isoCC": "MN"},
            "459": {"isoCC": "NP"},
            "461": {"isoCC": "OM"},
            "463": {"isoCC": "PK"},
            "466": {"isoCC": "QA"},
            "468": {"isoCC": "SY"},
            "470": {"isoCC": "AE"},
            "473": {"isoCC": "YE"},
            "475": {"isoCC": "YE"},
            "477": {"isoCC": "CN-HK"},
            "478": {"isoCC": "BA"},
            "501": {"isoCC": "AQ"},
            "503": {"isoCC": "AU"},
            "506": {"isoCC": "MM"},
            "508": {"isoCC": "BN"},
            "510": {"isoCC": "FM"},
            "511": {"isoCC": "PW"},
            "512": {"isoCC": "NZ"},
            "514": {"isoCC": "KH"},
            "515": {"isoCC": "KH"},
            "516": {"isoCC": "CX"},
            "518": {"isoCC": "CK"},
            "520": {"isoCC": "FJ"},
            "523": {"isoCC": "CC"},
            "525": {"isoCC": "ID"},
            "529": {"isoCC": "KI"},
            "531": {"isoCC": "LA"},
            "533": {"isoCC": "MY"},
            "536": {"isoCC": "US-MP"},
            "538": {"isoCC": "MH"},
            "540": {"isoCC": "NC"},
            "542": {"isoCC": "NU"},
            "544": {"isoCC": "NR"},
            "546": {"isoCC": "FR-PF"},
            "548": {"isoCC": "PH"},
            "553": {"isoCC": "PG"},
            "555": {"isoCC": "PN"},
            "557": {"isoCC": "SB"},
            "559": {"isoCC": "US-AS"},
            "561": {"isoCC": "WS"},
            "563": {"isoCC": "SG"},
            "564": {"isoCC": "SG"},
            "565": {"isoCC": "SG"},
            "567": {"isoCC": "TH"},
            "570": {"isoCC": "TO"},
            "572": {"isoCC": "TV"},
            "574": {"isoCC": "VN"},
            "576": {"isoCC": "VU"},
            "578": {"isoCC": "FR-WF"},
            "601": {"isoCC": "ZA"},
            "603": {"isoCC": "AO"},
            "605": {"isoCC": "DZ"},
            "607": {"isoCC": "FR-TF"},
            "608": {"isoCC": "SH"},
            "609": {"isoCC": "BI"},
            "610": {"isoCC": "BJ"},
            "611": {"isoCC": "BW"},
            "612": {"isoCC": "CF"},
            "613": {"isoCC": "CM"},
            "615": {"isoCC": "CG"},
            "616": {"isoCC": "KM"},
            "617": {"isoCC": "CV"},
            "618": {"isoCC": "FR-TF"},
            "619": {"isoCC": "CI"},
            "621": {"isoCC": "DJ"},
            "622": {"isoCC": "EG"},
            "624": {"isoCC": "ET"},
            "625": {"isoCC": "ER"},
            "626": {"isoCC": "GA"},
            "627": {"isoCC": "GH"},
            "629": {"isoCC": "GM"},
            "630": {"isoCC": "GW"},
            "631": {"isoCC": "GQ"},
            "632": {"isoCC": "GN"},
            "633": {"isoCC": "BF"},
            "634": {"isoCC": "KE"},
            "635": {"isoCC": "FR-TF"},
            "636": {"isoCC": "LR"},
            "637": {"isoCC": "LR"},
            "642": {"isoCC": "LY"},
            "644": {"isoCC": "LS"},
            "645": {"isoCC": "MU"},
            "647": {"isoCC": "MG"},
            "649": {"isoCC": "ML"},
            "650": {"isoCC": "MZ"},
            "654": {"isoCC": "MR"},
            "655": {"isoCC": "MW"},
            "656": {"isoCC": "NE"},
            "657": {"isoCC": "NG"},
            "659": {"isoCC": "NA"},
            "660": {"isoCC": "FR-RE"},
            "661": {"isoCC": "RW"},
            "662": {"isoCC": "SS"},
            "663": {"isoCC": "SN"},
            "664": {"isoCC": "SC"},
            "665": {"isoCC": "SH"},
            "666": {"isoCC": "SO"},
            "667": {"isoCC": "SL"},
            "668": {"isoCC": "ST"},
            "669": {"isoCC": "SZ"},
            "670": {"isoCC": "TD"},
            "671": {"isoCC": "GB"},
            "672": {"isoCC": "TN"},
            "674": {"isoCC": "TZ"},
            "675": {"isoCC": "UG"},
            "676": {"isoCC": "CG"},
            "677": {"isoCC": "TZ"},
            "678": {"isoCC": "ZM"},
            "679": {"isoCC": "ZW"},
            "701": {"isoCC": "AR"},
            "710": {"isoCC": "BR"},
            "720": {"isoCC": "BO"},
            "725": {"isoCC": "CL"},
            "730": {"isoCC": "CO"},
            "735": {"isoCC": "EC"},
            "740": {"isoCC": "FK"},
            "745": {"isoCC": "FR-GF"},
            "750": {"isoCC": "GY"},
            "755": {"isoCC": "PY"},
            "760": {"isoCC": "PE"},
            "765": {"isoCC": "SR"},
            "770": {"isoCC": "UR"},
            "775": {"isoCC": "VE"}
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
            midCtry = mid2isoCC[midStr]
            
            # Set the country data.
            retVal.update({'mmsiCC': midCtry['isoCC']})
            
            # If we explicitly want the country name...
            if cc2Country:
                retVal.update({'mmsiCountry': self.isoCCtoCountry[midCtry['isoCC']]})
        
        except KeyError:
            # Do nothing because sometimes there's a bad value.
            pass
        
        except Exception as e:
            # Pass the exception back up the stack.
            raise e
        
        # Send the data back along.
        return retVal
    
    def getICAOMeta(self, icaoAAInt, cc2Country=False):
        """
        Get metadata from ICAO addresses - based on the table here by Ralf D. Kloth:
        http://www.kloth.net/radio/icao24alloc.php
        """
        
        # Store return value.
        retVal = {}
        
        # Store our ICAO blocks for searching.
        icaoPrefixes = [
            # 4-bit prefixes.
            {
                "mask": 0b111100000000000000000000,
                0b000100000000000000000000: "RU",
                0b101000000000000000000000: "US"
            },
            
            # 6-bit prefixes
            {
                "mask": 0b111111000000000000000000,
                0b001100000000000000000000: "IT",
                0b001101000000000000000000: "ES",
                0b001110000000000000000000: "FR",
                0b001111000000000000000000: "DE",
                0b010000000000000000000000: "UK",
                0b011110000000000000000000: "CN",
                0b011111000000000000000000: "AU",
                0b100000000000000000000000: "IN",
                0b100001000000000000000000: "JP",
                0b110000000000000000000000: "CA",
                0b111000000000000000000000: "AR",
                0b111001000000000000000000: "BR"
            },
            
            # 9-bit prefixes
            {
                "mask": 0b111111111000000000000000,
                0b000000001000000000000000: "ZA",
                0b000000010000000000000000: "EG",
                0b000000011000000000000000: "LY",
                0b000000100000000000000000: "MA",
                0b000000101000000000000000: "TN",
                0b000010100000000000000000: "DZ",
                0b000011010000000000000000: "MX",
                0b000011011000000000000000: "VE",
                0b010001000000000000000000: "AT",
                0b010001001000000000000000: "BE",
                0b010001010000000000000000: "BG",
                0b010001011000000000000000: "DK",
                0b010001100000000000000000: "FI",
                0b010001101000000000000000: "GR",
                0b010001110000000000000000: "HU",
                0b010001111000000000000000: "NO",
                0b010010000000000000000000: "NL",
                0b010010001000000000000000: "PO",
                0b010010010000000000000000: "PT",
                0b010010011000000000000000: "CZ",
                0b010010100000000000000000: "RO",
                0b010010101000000000000000: "SE",
                0b010010110000000000000000: "CH",
                0b010010111000000000000000: "TU",
                0b010011000000000000000000: "YU",
                0b010100001000000000000000: "UA",
                0b011100010000000000000000: "SA",
                0b011100011000000000000000: "KR",
                0b011100100000000000000000: "KP",
                0b011100101000000000000000: "IQ",
                0b011100110000000000000000: "IR",
                0b011100111000000000000000: "IL",
                0b011101000000000000000000: "JO",
                0b011101001000000000000000: "LB",
                0b011101010000000000000000: "MY",
                0b011101011000000000000000: "PH",
                0b011101100000000000000000: "PK",
                0b011101101000000000000000: "SG",
                0b011101110000000000000000: "LK",
                0b011101111000000000000000: "SY",
                0b100010000000000000000000: "TH",
                0b100010001000000000000000: "VN",
                0b100010100000000000000000: "ID",
                0b110010000000000000000000: "NZ",
                0b111100000000000000000000: "ICAO"
            },
            
            # 12-bit prefixes
            {
                "mask": 0b111111111111000000000000,
                0b000000000110000000000000: "MZ",
                0b000000110010000000000000: "BI",
                0b000000110100000000000000: "CM",
                0b000000110110000000000000: "CG",
                0b000000111000000000000000: "CI",
                0b000000111110000000000000: "GA",
                0b000001000000000000000000: "ET",
                0b000001000010000000000000: "GQ",
                0b000001000100000000000000: "GH",
                0b000001000110000000000000: "GN",
                0b000001001100000000000000: "KE",
                0b000001010000000000000000: "LR",
                0b000001010100000000000000: "MG",
                0b000001011000000000000000: "MW",
                0b000001011100000000000000: "ML",
                0b000001100010000000000000: "NE",
                0b000001100100000000000000: "NG",
                0b000001101000000000000000: "UG",
                0b000001101100000000000000: "CF",
                0b000001101110000000000000: "RW",
                0b000001110000000000000000: "SN",
                0b000001111000000000000000: "SO",
                0b000001111100000000000000: "SS",
                0b000010000000000000000000: "TZ",
                0b000010000100000000000000: "TD",
                0b000010001000000000000000: "GB",
                0b000010001010000000000000: "ZM",
                0b000010001100000000000000: "CG",
                0b000010010000000000000000: "AO",
                0b000010011010000000000000: "GM",
                0b000010011100000000000000: "BF",
                0b000010101000000000000000: "BS",
                0b000010101100000000000000: "CO",
                0b000010101110000000000000: "CR",
                0b000010110000000000000000: "CU",
                0b000010110010000000000000: "SV",
                0b000010110100000000000000: "GT",
                0b000010110110000000000000: "GY",
                0b000010111000000000000000: "HT",
                0b000010111010000000000000: "HN",
                0b000010111110000000000000: "JA",
                0b000011000000000000000000: "NI",
                0b000011000010000000000000: "PA",
                0b000011000100000000000000: "DO",
                0b000011000110000000000000: "TT",
                0b000011001000000000000000: "SR",
                0b010011001010000000000000: "IE",
                0b010011001100000000000000: "IS",
                0b011100000000000000000000: "AF",
                0b011100000010000000000000: "BD",
                0b011100000100000000000000: "MM",
                0b011100000110000000000000: "KW",
                0b011100001000000000000000: "LA",
                0b011100001010000000000000: "NP",
                0b011100001110000000000000: "KH",
                0b100010010000000000000000: "YE",
                0b100010010100000000000000: "BH",
                0b100010010110000000000000: "AE",
                0b100010011000000000000000: "PG",
                0b110010001000000000000000: "FJ",
                0b111010000000000000000000: "CL",
                0b111010000100000000000000: "EC",
                0b111010001000000000000000: "PY",
                0b111010001100000000000000: "PE",
                0b111010010000000000000000: "UR",
                0b111010010100000000000000: "BO"
            },
            
            # 14-bit prefixes
            {
                "mask": 0b111111111111110000000000,
                0b000000000100000000000000: "ZW",
                0b000000110000000000000000: "BW",
                0b000000110101000000000000: "KM",
                0b000001001000000000000000: "GW",
                0b000001001010000000000000: "LS",
                0b000001011010000000000000: "MV",
                0b000001011110000000000000: "MR",
                0b000001100000000000000000: "MU",
                0b000001101010000000000000: "QA",
                0b000001110100000000000000: "SC",
                0b000001110110000000000000: "SL",
                0b000001111010000000000000: "SZ",
                0b000010010100000000000000: "BJ",
                0b000010010110000000000000: "CV",
                0b000010011000000000000000: "DJ",
                0b000010011110000000000000: "ST",
                0b000010101010000000000000: "BB",
                0b000010101011000000000000: "BZ",
                0b000010111100000000000000: "VC",
                0b000011001010000000000000: "AG",
                0b000011001100000000000000: "GD",
                0b001000000001000000000000: "NA",
                0b001000000010000000000000: "ER",
                0b010011001000000000000000: "CY",
                0b010011010000000000000000: "LU",
                0b010011010010000000000000: "MT",
                0b010011010100000000000000: "MC",
                0b010100000000000000000000: "SM",
                0b010100000001000000000000: "AL",
                0b010100000001110000000000: "HR",
                0b010100000010110000000000: "LV",
                0b010100000011110000000000: "LT",
                0b010100000100110000000000: "MD",
                0b010100000101110000000000: "SK",
                0b010100000110110000000000: "SI",
                0b010100000111110000000000: "UZ",
                0b010100010000000000000000: "BY",
                0b010100010001000000000000: "EE",
                0b010100010010000000000000: "MK",
                0b010100010011000000000000: "BA",
                0b010100010100000000000000: "GE",
                0b010100010101000000000000: "TJ",
                0b011000000000000000000000: "AM",
                0b011000000000100000000000: "AZ",
                0b011000000001000000000000: "KG",
                0b011000000001100000000000: "TM",
                0b011010000000000000000000: "BT",
                0b011010000001000000000000: "FM",
                0b011010000010000000000000: "MN",
                0b011010000011000000000000: "KN",
                0b011010000100000000000000: "PW",
                0b011100001100000000000000: "OM",
                0b100010010101000000000000: "BN",
                0b100010010111000000000000: "SB",
                0b100010011001000000000000: "ICAO",
                0b100100000000000000000000: "MH",
                0b100100000001000000000000: "CK",
                0b100100000010000000000000: "WS",
                0b110010001010000000000000: "NR",
                0b110010001100000000000000: "LC",
                0b110010001101000000000000: "TO",
                0b110010001110000000000000: "KI",
                0b110010010000000000000000: "VU",
                0b111100001001000000000000: "ICAO"
            }
        ]
        
        # Loop through each block size
        for thisPrefix in icaoPrefixes:
            # Pull our mask out...
            thisMask = thisPrefix.pop('mask')
            
            # Loop through each block we have in a given prefix.
            for blockPrefix, thisEntity in thisPrefix.iteritems():
                
                # See if our mask anded with the ICAO int matches the block prefix.
                if (thisMask & icaoAAInt) == blockPrefix:
                    # Add metadata.
                    retVal.update({'icaoAACC': thisEntity})
                    
                    # If we explicitly want the country name...
                    if cc2Country:
                        retVal.update({'icaoAACountry': self.isoCCtoCountry(retVal['icaoAACC'])['country']})
        
        return retVal
    