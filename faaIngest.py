#!/usr/bin/env python

"""
faaIngest by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""
import csv
from datetime import datetime
import os
import shutil
import traceback
from urllib import request
import zipfile
import pymongo
import config
from libAirSuck import asLog


class ImportFaaDb:
    """
    Import the FAA database from a zip file.
    """
    def __init__(self):
        """
        Handle the FAA aircraft database files.
        """

        # Build logger.
        self.__logger = asLog(config.ssrRegMongo['logMode'])
        self.__logger.log("AirSuck FAA database import starting...")
        # Master list of aircraft properties.
        self.__ac_list = {}
        # Master list of engine properties.
        self.__eng_list = {}
        #try:
        #    #MongoDB config
        #    faa_reg_mongo = pymongo.MongoClient(
        #        config.ssrRegMongo['host'], config.ssrRegMongo['port'])
        #    m_db = faa_reg_mongo[config.ssrRegMongo['dbName']]
        #    temp_coll_name = "%s_tmp" %config.ssrRegMongo['coll']
        #    # Set up the temporary colleciton.
        #    self.__m_db_coll = m_db[temp_coll_name]
        #    # Nuke it if it exists.
        #    try:
        #        self.__m_db_coll.drop()
        #    except:
        #        # Probably means it doesn't exist. We DGAF if it blows up.
        #        None
        #except:
        #    self.__logger.log("Failed to connect to MongoDB:\n%s" %traceback.format_exc())
        #    raise

        # Aircraft reference fields
        self.__aircraft_ref_fields = [
            {'fieldName': 'mfgName', 'index': 1, 'convert': self.__faa_to_str},
            {'fieldName': 'modelName', 'index': 2, 'convert': self.__faa_to_str},
            {'fieldName': 'acType', 'index': 3, 'convert': self.__faa_to_int},
            {'fieldName': 'engType', 'index': 4, 'convert': self.__faa_to_int},
            {'fieldName': 'acCat', 'index': 5, 'convert': self.__faa_to_int},
            {'fieldName': 'buldCert', 'index': 6, 'convert': self.__faa_to_int},
            {'fieldName': 'engCt', 'index': 7, 'convert': self.__faa_to_int},
            {'fieldName': 'seatCt', 'index': 8, 'convert': self.__faa_to_int},
            {'fieldName': 'weight', 'index': 9, 'convert': self.__faa_to_int,
             'erase_str': 'CLASS '},
            {'fieldName': 'cruiseSpd', 'index': 10, 'convert': self.__faa_to_int}
        ]
        # Aircraft Engine fields
        self.__aircraft_engine_fields = [
            {'fieldName': 'mfgName', 'index': 1, 'convert': self.__faa_to_str},
            {'fieldName': 'modelName', 'index': 2, 'convert': self.__faa_to_str},
            {'fieldName': 'engType', 'index': 3, 'convert': self.__faa_to_int},
            {'fieldName': 'engHP', 'index': 4, 'convert': self.__faa_to_int},
            {'fieldName': 'thrust', 'index': 5, 'convert': self.__faa_to_int}
        ]

        # Aircraft master fields
        self.__aircraft_master_fields = [
            {'fieldName': 'nNumeer', 'index': 0, 'convert': self.__faa_to_str,
             'prefix_str': 'N', 'to_upper': True},
            {'fieldName': 'serial', 'index': 1, 'convert': self.__faa_to_str},
            {'fieldName': 'acMfg', 'index': 2, 'convert': self.__faa_to_str},
            {'fieldName': 'engMfg', 'index': 3, 'convert': self.__faa_to_str},
            {'fieldName': 'yearMfg', 'index': 4, 'convert': self.__faa_to_int},
            {'fieldName': 'regType', 'index': 5, 'convert': self.__faa_to_int},
            {'fieldName': 'regName', 'index': 6, 'convert': self.__faa_to_str},
            {'fieldName': 'street1', 'index': 7, 'convert': self.__faa_to_str},
            {'fieldName': 'street2', 'index': 8, 'convert': self.__faa_to_str},
            {'fieldName': 'city', 'index': 9, 'convert': self.__faa_to_str},
            {'fieldName': 'state', 'index': 10, 'convert': self.__faa_to_str},
            {'fieldName': 'zip', 'index': 11, 'convert': self.__faa_to_str},
            {'fieldName': 'region', 'index': 12, 'convert': self.__faa_to_str},
            {'fieldName': 'countyCode', 'index': 13, 'convert': self.__faa_to_str},
            {'fieldName': 'countryCode', 'index': 14, 'convert': self.__faa_to_str},
            {'fieldName': 'lastActDate', 'index': 15, 'convert': self.__faa_to_date},
            {'fieldName': 'certIssDate', 'index': 16, 'convert': self.__faa_to_date},
            {'fieldName': 'airWorthClass', 'index': 17, 'convert': self.__faa_to_str},
            {'fieldName': 'acType', 'index': 18, 'convert': self.__faa_to_int},
            {'fieldName': 'engType', 'index': 19, 'convert': self.__faa_to_int},
            {'fieldName': 'statCode', 'index': 20, 'convert': self.__faa_to_str},
            {'fieldName': 'modeSInt', 'index': 21, 'convert': self.__faa_to_int},
            {'fieldName': 'fractOwner', 'index': 22, 'convert': self.__faa_to_str},
            {'fieldName': 'airWorthyDate', 'index': 23, 'convert': self.__faa_to_date},
            {'fieldName': 'otherName1', 'index': 24, 'convert': self.__faa_to_str},
            {'fieldName': 'otherName2', 'index': 25, 'convert': self.__faa_to_str},
            {'fieldName': 'otherName3', 'index': 26, 'convert': self.__faa_to_str},
            {'fieldName': 'otherName4', 'index': 27, 'convert': self.__faa_to_str},
            {'fieldName': 'otherName5', 'index': 28, 'convert': self.__faa_to_str},
            {'fieldName': 'expireDate', 'index': 29, 'convert': self.__faa_to_date},
            {'fieldName': 'uid', 'index': 30, 'convert': self.__faa_to_str},
            {'fieldName': 'kitMfr', 'index': 31, 'convert': self.__faa_to_str},
            {'fieldName': 'kitMdl', 'index': 32, 'convert': self.__faa_to_str},
            {'fieldName': 'modeSHex', 'index': 33, 'convert': self.__faa_to_str,
             'to_lower': True}
        ]


    def __faa_to_int(self, entry, erase_str=None, default=None):
        """
        Convert an FAA DB field to an integer.
        """

        ret_val = None
        # Erase a string from this field before converting?
        if erase_str is not None:
            entry.replace(erase_str, "")
        try:
            ret_val = int(entry.strip())
        except ValueError:
            ret_val = default
        return ret_val


    def __faa_to_str(self, entry, default=None, erase_str=None, prefix_str=None,
                     to_lower=False, to_upper=False):
        """
        Convert an FAA DB field to an string.
        """

        ret_val = None
        try:
            ret_val = str(entry).strip()
            # Erase a string from this field before converting?
            if erase_str is not None:
                entry.replace(erase_str, "")
            # Tack on a prefix to the string?
            if prefix_str is not None:
                entry = "%s%s" %(prefix_str, entry)
            # Make the string lower case?
            if to_lower:
                entry = entry.lower()
            # Make the string upper case?
            if to_upper:
                entry = entry.upper()
        except ValueError:
            ret_val = default
        return ret_val

    def __faa_to_date(self, entry, default=None):
        """
        Convert an FAA DB date to a date.
        """

        ret_val = None
        try:
            ret_val = datetime.strptime(entry.strip(), '%Y%m%d')
        except ValueError:
            ret_val = default
        return ret_val


    def __download_faa_data(self):
        """
        Download FAA database.
        """

        # Final location the zip file should end up.
        file_target = "%s%s" %(config.ssrRegMongo['tempPath'],
                               config.ssrRegMongo['tempZip'])
        try:
            self.__make_temp_dir()
        except PermissionError:
            self.__logger.log("Permission error creating %s..." %config.ssrRegMongo['tempPath'])
            raise SystemExit
        # Open the file and download the FAA DB into it.
        self.__logger.log("Downloading FAA database to %s..." %file_target)
        request.urlretrieve(config.ssrRegMongo['faaDataURL'], file_target)
        self.__logger.log("Unzipping relevant files from %s..." %file_target)


    def __make_temp_dir(self):
        """
        Make the temporary directory for handling downloaded FAA data.
        """
        if not os.path.exists(config.ssrRegMongo['tempPath']):
            if not os.path.isdir(config.ssrRegMongo['tempPath']):
                # Try to create our directory
                os.makedirs(config.ssrRegMongo['tempPath'])


    def __decompress_faa_data(self):
        """
        Decompress FAA data.
        """

        # Final location the zip file should end up.
        file_target = "%s%s" %(config.ssrRegMongo['tempPath'],
                               config.ssrRegMongo['tempZip'])
        try:
            self.__make_temp_dir()
        except PermissionError:
            self.__logger.log("Permission error creating %s..." %config.ssrRegMongo['tempPath'])
        try:
            # Open our zip file
            zip_f = zipfile.ZipFile(file_target, 'r')
            # Extract master file
            zip_f.extract(config.ssrRegMongo['masterFile'],
                          config.ssrRegMongo['tempPath'])
            # Extract aircraft file.
            zip_f.extract(config.ssrRegMongo['acFile'],
                          config.ssrRegMongo['tempPath'])
            # Extract engine file.
            zip_f.extract(config.ssrRegMongo['engFile'],
                          config.ssrRegMongo['tempPath'])
        except zipfile.BadZipfile:
            self.__logger.log("Bad FAA database zip file.")
        except PermissionError:
            self.__logger.log("Permissions error extract files from FAA database zip file.")
            raise SystemExit
        finally:
            if 'zip_f' in locals():
                zip_f.close()


    def __nuke_faa_data(self):
        """
        Delete FAA data files downloaded above.
        """

        self.__logger.log("Deleting %s..." %config.ssrRegMongo['tempPath'])
        # Nuke the temporary directory and all files under it.
        shutil.rmtree(config.ssrRegMongo['tempPath'])

    def __load_acft_ref(self):
        """
        Load eircraft reference data from file.
        """

        load_count = 0
        data_row = False
        target_file = "%s%s" %(config.ssrRegMongo['tempPath'],
                               config.ssrRegMongo['acFile'])
        self.__logger.log("Processing aicraft reference data in %s..." %target_file)
        with open(target_file, 'r') as csv_file:
            for row in csv.reader(csv_file):
                # Blank the row, create template.
                this_row = {}
                if data_row:
                    load_count += 1
                    # Type-correct our CSV data.
                    try:
                        for conversion in self.__aircraft_ref_fields:
                            args = {'entry': row[conversion['index']]}
                            if 'erase' in conversion:
                                args.update({'erase_str': conversion['erase']})
                            if 'default' in conversion:
                                args.update({'default': conversion['erase']})
                            converted_data = conversion['convert'](**args)
                            if converted_data is not None:
                                this_row.update({
                                    conversion['fieldName']: conversion['convert'](**args)
                                })
                    except:
                        self.__logger.log("Failed to auto-correct Aircraft Ref:\n%s"
                                          %traceback.format_exc())
                    self.__ac_list.update({row[0].strip(): this_row})
                else:
                    data_row = True
        self.__logger.log("Processed %s aicraft reference entries." %load_count)

    def __load_engine(self):
        """
        Load engine reference data from file.
        """

        load_count = 0
        data_row = False
        target_file = "%s%s" %(config.ssrRegMongo['tempPath'],
                               config.ssrRegMongo['engFile'])
        self.__logger.log("Processing engine reference data in %s..." %target_file)
        with open(target_file, 'r') as csv_file:
            for row in csv.reader(csv_file):
                # Blank the row, create template.
                this_row = {}
                if data_row:
                    load_count += 1
                    # Type-correct our CSV data.
                    try:
                        for conversion in self.__aircraft_engine_fields:
                            args = {'entry': row[conversion['index']]}
                            if 'default' in conversion:
                                args.update({'default': conversion['erase']})
                            converted_data = conversion['convert'](**args)
                            if converted_data is not None:
                                this_row.update({
                                    conversion['fieldName']: conversion['convert'](**args)
                                })
                    except:
                        self.__logger.log("Failed to auto-correct engine data:\n%s"
                                          %traceback.format_exc())
                    # Tack our row on.
                    self.__eng_list.update({row[0].strip(): this_row})
                else:
                    data_row = True
        self.__logger.log("Processed %s aircraft engine entries." %load_count)


    def __process_master(self):
        """
        Load master aircraft data from file.
        This should be called AFTER __loadAcftRef and __loadEngine.
        """

        data_row = False
        load_count = 0
        target_file = "%s%s" %(config.ssrRegMongo['tempPath'],
                               config.ssrRegMongo['masterFile'])
        self.__logger.log("Processing master aicraft data in %s..." %target_file)
        with open(target_file, 'r') as csv_file:
            for row in csv.reader(csv_file):
                # Blank the row, create template.
                this_row = {}
                if data_row:
                    load_count += 1
                    # Type-correct our CSV data.
                    try:
                        for conversion in self.__aircraft_master_fields:
                            args = {'entry': row[conversion['index']]}
                            if 'default' in conversion:
                                args.update({'default': conversion['default']})
                            if 'erase_str' in conversion:
                                args.update({'erase_str': conversion['erase_str']})
                            if 'prefix_str' in conversion:
                                args.update({'prefix_str': conversion['prefix_str']})
                            if 'to_lower' in conversion:
                                args.update({'to_lower': conversion['to_lower']})
                            if 'to_upper' in conversion:
                                args.update({'to_upper': conversion['to_upper']})
                            converted_data = conversion['convert'](**args)
                            if converted_data is not None:
                                this_row.update({
                                    conversion['fieldName']: conversion['convert'](**args)
                                })
                    except:
                        self.__logger.log("Failed to auto-correct Aircraft Ref:\n%s"
                                          %traceback.format_exc())
                    self.__ac_list.update({row[0].strip(): this_row})
                else:
                    data_row = True
        self.__logger.log("Processed %s master aircraft entries." %load_count)

        # Insert the row.
        #try:
        #    self.__m_db_coll.insert(this_row)
        #except:
        #    raise


    def migrate_db(self):
        """
        Swap out the old database for the new.
        """

        self.__logger.log("Migrate new processed aircraft data to live data...")
        # Try to overwrite the main collection.
        #self.__m_db_coll.renameCollection(config.ssrRegMongo['coll'], True)

    def run(self):
        """
        Do all the work in sequence.
        """

        try:
            # When did we start?
            run_start_dts = datetime.utcnow()
            # Grab FAA database file from their website.
            self.__download_faa_data()
            # Decompress FAA database.
            self.__decompress_faa_data()
            # Pull aircraft reference data.
            self.__load_acft_ref()
            # Pull aircraft engine data.
            self.__load_engine()
            # Insert master aircraft records combined with
            # record from the engine and aicraft records.
            self.__process_master()
            # Swap the database.
            #self.__migrate_db()
            # When did we stop?
            run_end_dts = datetime.utcnow()
            # How long did we run?
            runtime = run_end_dts - run_start_dts
            self.__logger.log("Runtime was %s sec." %runtime.seconds)
        except (SystemExit, KeyboardInterrupt):
            self.__logger.log("Exit.")
        #finally:
            #try:
            #    # Drop the temporary collection.
            #    self.__m_db_coll.drop()
            #except:
            #    # We DGAF it this doesn't work.
            #    self.__logger.log("Failed to drop data collection.")
            # TODO: Reactivate this seciton.
            #try:
            #    # Drop the temporary collection.
            #    self.__nuke_faa_data()
            #except:
            #    # We DGAF it this doesn't work.
            #    self.__logger.log("Failed to nuke the FAA data.")

IFDB = ImportFaaDb()
IFDB.run()
