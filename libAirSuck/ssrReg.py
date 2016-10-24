"""
ssrReg by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

###########
# Imports #
###########

import pymongo
import traceback
from pprint import pprint

#################
# cprMath class #
#################

class ssrReg():
    def __init__(self, config, logger):
        """
        ssrReg is a class that queries a database looking for aircraft registration information.
        """
        
        # Logger
        self.__logger = logger
        
        # Pass configuration on.
        self.__config = config
        
        # If we are actually going to process registration data...
        if config.ssrRegMongo['enabled'] == True:
            
            # Translate FAA data to a more generic type.
            self.__faaFilter = {
                'nNumber': 'tailNo'
            }
            
            # Aircraft results filter.
            self.__acRes = {
                'nNumber': True, 
                'regName': True, 
                'countryCode': True, 
                'city': True, 
                'state': True, 
                'yearMfg': True,
                'regType': True,
                'acMfg.mfgName': True,
                'acMfg.modelName': True,
                'acMfg.engCt': True,
                'acMfg.acCat': True,
                'engMfg.mfgName': True,
                'engMfg.modelName': True,
                'engMfg.engType': True
            }
            
            # FAA Registration type.
            self.__faaRegType = (
                None,
                'Individual',
                'Partnership',
                'Corporation',
                'Co-Owned',
                'Government',
                'Non Citizen Corp',
                'Non Citizen Co-Owned'
            )
            
            # FAA aircraft type
            self.__faaAcType = (
                None,
                'Glider',
                'Balloon',
                'Blimp/Dirigible',
                'Fixed Wing Single Engine',
                'Fixed Wing Multi Engine',
                'Rotorcraft',
                'Weight-shift-control',
                'Powered Parachute',
                'Gyroplane'
            )
            
            # FAA engine type
            self.__faaEngType = (
                'None',
                'Reciprocating',
                'Turbo-prop',
                'Turbo-shaft',
                'Turbo-jet',
                'Turbo-fan',
                'Ramjet',
                '2 Cycle',
                '4 Cycle',
                'Unknown',
                'Electric',
                'Rotary'
            )
            
            # FAA aircraft category code
            self.__faaAcCat = (
                None,
                'Land',
                'Sea',
                'Amphibian'
            )
            
            # Build aircraft registration DB.
            try:
                #MongoDB config
                ssrRegMongo = pymongo.MongoClient(config.ssrRegMongo['host'], config.ssrRegMongo['port'])
                sDB = ssrRegMongo[config.ssrRegMongo['dbName']]
                self.__sDBColl = sDB[config.ssrRegMongo['coll']]
                
            except:
                tb = traceback.format_exc()
                logger.log("Failed to connect to aircraft reistration DB:\n%s" %tb)
                
                # Disable lookups.
                self.__config.ssrRegMongo['enabled'] = False
    
    def getRegData(self, icaoAAHx):
        """
        Get aircraft registration data.
        """
        
        # Set up default return value
        retVal = {'regData': False}
        
        # Do we want to even attempt looking up aircraft registrations?
        if self.__config.ssrRegMongo['enabled'] == True:
            # Make sure we're a lower case string.
            icaoAAHx = str(icaoAAHx).lower()
            
            try:
                # Snag the result.
                res = self.__sDBColl.find({'modeSHex': icaoAAHx}, self.__acRes)
                theThing = next(res, None)
                
                # If we have an entry...
                if theThing != None:
                    
                    # Registration strings, etc.
                    regTail = ""
                    regName = ""
                    regAircraft = ""
                    regEngine = ""
                    regAuthority = ""
                    
                    # Do we have a tail number?
                    if 'nNumber' in theThing.keys():
                        # Set the tail number.
                        regTail = theThing['nNumber']
                        
                        # Automatically trip registration data.
                        retVal.update({'regData': True})
                    
                    # Do we have a registrant's name?
                    if 'regName' in theThing.keys():
                        # Set the tail number.
                        regName = theThing['regName']
                        
                        # Automatically trip registration data.
                        retVal.update({'regData': True})
                    
                    # What about a registrant city?
                    if 'city' in theThing.keys():
                        # Add it to the string.
                        regName = "%s, %s" %(regName, theThing['city'])
                    
                    # What about a registrant state?
                    if 'state' in theThing.keys():
                        # Add it to the string.
                        regName = "%s, %s" %(regName, theThing['state'])
                    
                    # What about a registrant country?
                    if 'countryCode' in theThing.keys():
                        # Add it to the string.
                        regName = "%s, %s" %(regName, theThing['countryCode'])
                    
                    # Registratoin type?
                    if 'regType' in theThing.keys():
                        # Add it tot he string.
                        regName = "%s (%s)" %(regName, self.__faaRegType[theThing['regType']])
                    
                    # Do we have a manufacturing year?
                    if 'yearMfg' in theThing.keys():
                        # Add it to the string.
                        regAircraft = str(theThing['yearMfg'])
                        
                        # Automatically trip registration data.
                        retVal.update({'regData': True})
                    
                    # If we have aicraft manufacturer data...
                    if 'acMfg' in theThing.keys():
                         
                        # Make?
                        if 'mfgName' in theThing['acMfg'].keys():
                            regAircraft = regAircraft + " %s" %theThing['acMfg']['mfgName']
                            
                            # Automatically trip registration data.
                            retVal.update({'regData': True})
                        
                        # Model?
                        if 'modelName' in theThing['acMfg'].keys():
                            regAircraft = regAircraft + " %s" %theThing['acMfg']['modelName']
                            
                            # Automatically trip registration data.
                            retVal.update({'regData': True})
                        
                        # Category?
                        if 'acCat' in theThing['acMfg'].keys():
                            regAircraft = regAircraft + " (%s)" %self.__faaAcCat[theThing['acMfg']['acCat']]
                            
                            # Automatically trip registration data.
                            retVal.update({'regData': True})
                        
                        # # Engine count?
                        # if 'engCt' in theThing['acMfg'].keys():
                        #     regEngine = "%sx " %theThing['acMfg']['engCt']
                        #     
                        #     # Automatically trip registration data.
                        #     retVal.update({'regData': True})
                    
                    # Do we have engine manufacturer data?
                    # if 'engMfg' in theThing.keys():
                    #     # Engine make?
                    #     if 'mfgName' in theThing['engMfg'].keys():
                    #         regEngine = "%s%s" %(regEngine, theThing['acMfg']['mfgName'])
                    #         
                    #         # Automatically trip registration data.
                    #         retVal.update({'regData': True})
                    #     
                    #     # Engine make?
                    #     if 'modelName' in theThing['engMfg'].keys():
                    #         regEngine = "%s %s" %(regEngine, theThing['acMfg']['modelName'])
                    #         
                    #         # Automatically trip registration data.
                    #         retVal.update({'regData': True})
                    #     
                    #     # Engine type?
                    #     if 'engType' in theThing['engMfg'].keys():
                    #         regEngine = "%s (%s)" %(regEngine, self.__faaEngType[theThing['engMfg']['engType']])
                    #         
                    #         # Automatically trip registration data.
                    #         retVal.update({'regData': True})
                    
                    # Set our properties.
                    if retVal['regData'] == True:
                        # Set the registration authority.
                        retVal.update({'regAuthority': 'FAA'})
                        
                        # Tail number
                        if regTail != "":
                            retVal.update({'regTail': regTail})
                        
                        # Registration name
                        if regName != "":
                            retVal.update({'regName': regName})
                        
                        # Aircraft type
                        if regAircraft != "":
                            retVal.update({'regAircraft': regAircraft})
                            
                        # Engine properties
                        if regEngine != "":
                            retVal.update({'regEngine': regEngine})
            
            except:
                raise

        
        return retVal