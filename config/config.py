"""
config.py by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This is the configuation file for the airSuck daemons and global client options for queues, except files under the node folder.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

##################################
# Quick-and-dirty setup section. #
##################################

# Most setups can use a single Redis and MongoDB host. Set these here. If you need separate host names, just remove the variables from the config below.
genRedisHost = "<insert host/IP here>" # This machine hosts all the redis instances used by all connetors and servers.
genRedisPort = 6379 # Redis server port default is 6379

genMongoHost = "<insert host/IP here>" # This machine hosts all the mongoDB instances used by all connectors and servers.
genMongoPort = 27017 # MongoDB server port default is 217017

########################################
# Connector and state engine settings. #
########################################

# Dump1090Connector settings
d1090ConnSettings = {
    'enabled': True, # Do we want to run the dump1090 connector? True = yes, False = no
    'connListenHost': "0.0.0.0", #/ Listen on this address for incoming connections. Default is all addresses: "0.0.0.0"
    'connListenPort': 8091, # Dump 1900 connect incoming port.
    'dedupeTTLSec': 3, # Time to live for deduplicated frames. This rejects duplicate frames recieved within 3 sec of each other.
    'dedupeHost': genRedisHost, # This host contains the objects used to deduplicate frames.
    'dedupePort': genRedisPort # Redis port number for dedupe.
};

# SSR State engine settings
ssrStateEngine = {
    'enabled': True, # Do we want to run the state engine? True = yes, False = no
    'expireTime': 300, # Expire vehicles that we haven't seen in this number of seconds. Default is 300 sec (5 min)
    'cprExpireSec': 20 # This specifies how old CPR data can be before we reject it as too old to be valid in sec. Default is 20.
};

#########################################
# Settings for MongoDB storage engines. #
#########################################

# Raw connector data MongoDB storage engine settings
connMongo = {
    'enabled': True, # Turn on storage of connector data before processing? True = on, False = off.
    'host': genMongoHost, # MongoDB server that holds connector data.
    'port': genMongoPort, # Port number for the mongoDB instance.
    'dbName': "airSuck", # Database name.
    'coll': "airSSR", # Collection name for connector data.
    'checkDelay': 0.1 # Delay between checks where we don't have data. This is in seconds and prevents the process from chewing up CPU when there is little or no data.
};

# State data MongoDB storage engine settings
stateMongo = {
    'enabled': True, # Turn on storage of state data after processing? True = on, False = off.
    'host': genMongoHost, # MongoDB server that holds state data.
    'port': genMongoPort, # Port number for the mongoDB instance.
    'dbName': "airSuck", # Database name.
    'coll': "airState", # Collection name for connector data.
    'checkDelay': 0.1 # Delay between checks where we don't have data. This is in seconds and prevents the process from chewing up CPU when there is little or no data. 
};

##########################################################################################################################
# The Redis services can be on a single server or multiple servers. The queues are broken out like this for flexibility. #
##########################################################################################################################

# Connector relaible Redis queue settings - used by multliple scripts.
connRel = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckConnRel" # Queue name.
};

# Connector pub/sub redis queue settings - used by multiple scripts.
connPub = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckConnPub" # Queue name.
};

# State engine reliable Redis queue settings - used by multiple scripts.
stateRel = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckStateRel" # Queue name.
};

# state engine pub/sub redis queue settings - used by multiple scripts.
statePub = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckStatePub" # Queue name.
};
