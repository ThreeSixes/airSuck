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
        
        if config['enabled']:
            # Aircraft results filter.
            self.__acRes = {
                'nNumber': True, 
                'regName': True, 
                'countryCode': True, 
                'city': True, 
                'state': True, 
                'yearMfg': True,
                'acMfg.mfgName': True,
                'acMfg.modelName': True,
                'acMfg.engCt': True,
                'acMfg.acCat': True,
                'engMfg.mfgName': True,
                'engMfg.modelName': True,
                'engMfg.engType': True
            }
            
            # FAA Registration type.
            self.__faaRegType = [
                None,
                'Individual',
                'Partnership',
                'Corporation',
                'Co-Owned',
                'Government',
                'Non Citizen Corp',
                'Non Citizen Co-Owned'
            ]
            
            # FAA aircraft type
            self.__faaAcType = [
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
            ]
            
            # FAA engine type
            self.__faaEngType = [
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
            ]
            
            # FAA aircraft category code
            self.__faaAcCat = [
                None,
                'Land',
                'Sea',
                'Amphibian'
            ]
            
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
                self.__config['enabled'] = False
    
    def getRegData(self, icaoAAHx):
        """
        Get aircraft registration data.
        """
        
        # Set up default return value
        retVal = {'regData': False}
        
        # Make sure we're a lower case string.
        icaoAAHx = str(icaoAAHx).lower()
        
        # Do we want to even attempt looking up aircraft registrations?
        if config['enabled'] == True:
            try:
                res = self.__sDBColl.find({'modeSHex': icaoAAHx}, self.__acRes)
                pprint(res)
            except:
                None
        
        return retVal