#!/usr/bin/python

"""
faaIngest by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""
import config as config
import csv
import traceback
import datetime
import pymongo
import zipfile
import os
import shutil
import pycurl
from libAirSuck import asLog
from pprint import pprint

class importFaaDb:
    def __init__(self):
        """
        Handle the FAA aircraft database files.
        """
        
        # Build logger.
        self.__logger = asLog(config.ssrRegMongo['logMode'])
        self.__logger.log("AirSuck FAA database import starting...")
        
        # Master list of aircraft properties.
        self.__acList = {}
        
        # Master list of engine properties.
        self.__engList = {}
        
        try:
            #MongoDB config
            faaRegMongo = pymongo.MongoClient(config.ssrRegMongo['host'], config.ssrRegMongo['port'])
            mDB = faaRegMongo[config.ssrRegMongo['dbName']]
            tempCollName = "%s_tmp" %config.ssrRegMongo['coll']
            
            # Set up the temporary colleciton.
            self.__mDBColl = mDB[tempCollName]
            
            # Nuke it if it exists.
            try:
                self.__mDBColl.drop()
            except:
                # Probably means it doesn't exist. We DGAF if it blows up.
                None
        
        except:
            tb = traceback.format_exc()
            self.__logger.log("Failed to connect to MongoDB:\n%s" %tb)
            
            raise
    
    def __getFaaData(self):
        """
        Download and decompress FAA data.
        """
        
        # Final location the zip file should end up.
        fileTarget = "%s%s" %(config.ssrRegMongo['tempPath'], config.ssrRegMongo['tempZip'])
        
        self.__logger.log("Downloading FAA database to %s..." %fileTarget)
        
        try:
            try:
                # Try to create our directory
                os.makedirs(config.ssrRegMongo['tempPath'])
                
            except OSError:
                # Already exists. We DGAF.
                None
            
            except:
                raise
            
            # Open the file and download the FAA DB into it.
            with open(fileTarget, 'wb') as outZip:
                # Use cURL to snag our database.
                crl = pycurl.Curl()
                crl.setopt(crl.URL, config.ssrRegMongo['faaDataURL'])
                crl.setopt(crl.WRITEDATA, outZip)
                crl.perform()
                crl.close()
        
        except:
            raise
        
        self.__logger.log("Unzipping relevatnt files from %s..." %fileTarget)
        
        try:
            # Open our zip file
            zipF = zipfile.ZipFile(fileTarget, 'r')
            
            # Extract master file
            zipF.extract(config.ssrRegMongo['masterFile'], config.ssrRegMongo['tempPath'], config.ssrRegMongo['tempPath'])
            
            # Extract aircraft file.
            zipF.extract(config.ssrRegMongo['acFile'], config.ssrRegMongo['tempPath'], config.ssrRegMongo['tempPath'])
            
            # Extract engine file.
            zipF.extract(config.ssrRegMongo['engFile'], config.ssrRegMongo['tempPath'], config.ssrRegMongo['tempPath'])
        
        except:
            raise
        
        finally:
            zipF.close()
        
        return
    
    def __nukeFaaData(self):
        """
        Delete FAA data files downloaded above.
        """
        
        self.__logger.log("Deleting %s..." %fileTarget)
        
        try:
            # Nuke the temporary directory and all files under it.
            shutil.rmtree(config.ssrRegMongo['tempPath'])
        
        except:
            raise
    
    def __loadAcftRef(self):
        """
        Load eircraft reference data from file.
        """
        dataRow = False
        
        targetFile = "%s%s" %(config.ssrRegMongo['tempPath'], config.ssrRegMongo['acFile'])
        
        self.__logger.log("Processing aicraft reference data in %s..." %targetFile)
        
        with open(targetFile, 'rb') as csvFile:
            for row in csv.reader(csvFile):
                # Blank the row, create template.
                thisRow = {}
                
                if dataRow:
                    
                    # Type-correct our CSV data.
                    try:
                        thisRow.update({'mfgName': row[1].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'modelName': row[2].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'acType': int(row[3].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'engType': int(row[4].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'acCat': int(row[5].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'buldCert': int(row[6].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'engCt': int(row[7].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'seatCt': int(row[8].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'weight': int(row[9].replace("CLASS ", "").strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'cruiseSpd': int(row[10].strip())})
                    except:
                        None
                    
                    self.__acList.update({row[0].strip(): thisRow})
                    
                else:
                    dataRow = True
        
        return
    
    def __loadEngine(self):
        """
        Load engine reference data from file.
        """
        dataRow = False
        
        targetFile = "%s%s" %(config.ssrRegMongo['tempPath'], config.ssrRegMongo['engFile'])
        
        self.__logger.log("Processing engine reference data in %s..." %targetFile)
        
        with open(targetFile, 'rb') as csvFile:
            for row in csv.reader(csvFile):
                
                # Blank the row, create template.
                thisRow = {}
                
                if dataRow:
                    # Type-correct our CSV data.
                    try:
                        thisRow.update({'mfgName': row[1].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'modelName': row[2].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'engType': int(row[3].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'engHP': int(row[4].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'thrust': int(row[5].strip())})
                    except:
                        None
                    
                    # Tack our row on.
                    self.__engList.update({row[0].strip(): thisRow})
                    
                else:
                    dataRow = True
        
        return
    
    def __processMaster(self):
        """
        Load master aircraft data from file. This should be called AFTER __loadAcftRef and __loadEngine.
        """
        dataRow = False
        
        targetFile = "%s%s" %(config.ssrRegMongo['tempPath'], config.ssrRegMongo['masterFile'])
        
        self.__logger.log("Processing master aicraft data in %s..." %targetFile)
        
        with open(targetFile, 'rb') as csvFile:
            for row in csv.reader(csvFile):
                
                # Blank the row, create template.
                thisRow = {}
                
                if dataRow:
                    # Type-correct our CSV data.
                    try:
                        thisRow.update({'nNumber': "N%s" %row[0].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'serial': row[1].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'acMfg': self.__acList[row[2].strip()]})
                    except:
                        None
                    
                    try:
                        thisRow.update({'engMfg': self.__engList[row[3].strip()]})
                    except:
                        None
                    
                    try:
                        thisRow.update({'yearMfg': int(row[4].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'regType': int(row[5].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'regName': row[6].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'street1': row[7].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'street2': row[8].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'city': row[9].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'state': row[10].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'zip': row[11].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'region': row[12].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'countyCode': row[13].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'countryCode': row[14].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'lastActDate': datetime.datetime.strptime(row[15].strip(), '%Y%m%d')})
                    except:
                        None
                    
                    try:
                        thisRow.update({'certIssDate': datetime.datetime.strptime(row[16].strip(), '%Y%m%d')})
                    except:
                        None
                    
                    try:
                        thisRow.update({'airWorthClass': row[17].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'acType': int(row[18].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'engType': int(row[19].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'statCode': row[20].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'modeSInt': int(row[21].strip())})
                    except:
                        None
                    
                    try:
                        thisRow.update({'fractOwner': row[22].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'airWorthyDate': datetime.datetime.strptime(row[23].strip(), '%Y%m%d')})
                    except:
                        None
                    
                    try:
                        thisRow.update({'otherName1': row[24].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'otherName2': row[25].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'otherName3': row[26].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'otherName4': row[27].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'otherName5': row[28].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'expireDate': datetime.datetime.strptime(row[29].strip(), '%Y%m%d')})
                    except:
                        None
                    
                    try:
                        thisRow.update({'uid': row[30].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'kitMfr': row[31].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'kitMdl': row[32].strip()})
                    except:
                        None
                    
                    try:
                        thisRow.update({'modeSHex': row[33].strip().lower()})
                    except:
                        None
                    
                    # Insert the row.
                    try:
                        self.__mDBColl.insert(thisRow)
                    except:
                        raise
                    
                else:
                    dataRow = True
        
        return
    
    def migrateDb(self):
        """
        Swap out the old database for the new.
        """
        
        self.__logger.log("Migrate new processed aircraft data to live data...")
        
        try:
            # Try to overwrite the main collection.
            self.__mDBColl.renameCollection(config.ssrRegMongo['coll'], True)
        except:
            raise
        
        return
    
    def run(self):
        """
        Do all the work in sequence.
        """
        
        try:
            # Grab and decompress file.
            self.__getFaaData()
            
            # Pull aircraft reference data.
            self.__loadAcftRef()
            
            # Pull aircraft engine data.
            self.__loadEngine()
            
            # Insert master aircraft records combined with record from the engine and aicraft records.
            self.__processMaster()
            
            # Swap the database.
            self.__migrateDb()
        
        except:
            tb = traceback.format_exc()
            print("Unhandled exception:\n%s" %tb)
        
        finally:
            try:
                # Drop the temporary collection.
                self.__mDBColl.drop()
            except:
                # We DGAF it this doesn't work.
                None
            
            try:
                # Drop the temporary collection.
                self.__nukeFaaData()
            except:
                # We DGAF it this doesn't work.
                None


ifdb = importFaaDb()
ifdb.run()

