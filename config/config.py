"""
config.py by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This is the configuation file for the airSuck daemons and global client options for queues, except files under the node folder.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

##################################
# Quick-and-dirty setup section. #
##################################

###
### These settings are re-used in various sections of the configuration, but can easily be overridden in any section as needed.
###

# The name of this machine.
genName = "<name of this data source>" # This is a string that identifies the local machine.

# Most setups can use a single Redis and MongoDB host. Set these here. If you need separate host names, just remove the variables from the config below.
genRedisHost = "<insert host/IP here>" # This machine hosts all the redis instances used by all connetors and servers.
genRedisPort = 6379 # Redis server port default is 6379

genMongoHost = "<insert host/IP here>" # This machine hosts all the mongoDB instances used by all connectors and servers.
genMongoPort = 27017 # MongoDB server port default is 217017

# Globally set logging settings.
genLogMode   = "stdout" # Set the default logging mode to standard out. You can choose 'stdout', 'syslog', or 'none'.


###########################
# Remote client settings. #
###########################

# airSuck client - for submitting AIS or SSR data to a remote server running the Dump 1090 Connector Server.
airSuckClientSettings = {
    'myName': genName, # A descriptive name for this data source.
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Do we want to run the dump1090 connector? True = yes, False = no
    'connSrvHost': "<hostname or IP>", # Remote connector server to submit data to.
    'connSrvPort': 8091, # Dump 1900 connect incoming port when running as a server.
    'keepaliveInterval': 300.0, # This is how often we try to ping the server, and how long we expect between pings.
    'reconnectDelay': 30.0, # This is the amount of time we want to wait initially before reconnecting.
    'gps': False, # Do we have a GPS position AND PPS support in NTP? Don't set this if NTP isn't configured to use the GPS as a reference clock via PPS output.
    'reportPos': False, # Do we report the client position data specified below? If this and GPS are set to True the position in myPos will be sent when teh GPS does not have a fix.
    'myPos': [0.0, 0.0], # Position data of the client formatted as such: [lat, lon]. This is ignored if GPS is set to true and the GPS has a fix.
    'debug': False, # Debug?
    
    # Dump1090 data source settings.
    'dump1090Enabled': True, # Enable if you want to submit dump1090 data.
    'dump1090Path': "/opt/dump1090/dump1090", # Path to the dump1090 executable.
    'dump1090Args': "--aggressive --gain 40 --raw", # Dump1090 arguments. See dump1090 --help for all possible options.
    'dump1090Timeout': 60.0, # How long should we wait in seconds before considering the dump1090 dead?
    'dump1090Delay': 5.0, # How long should we wait intially before restarting dump1090 after an error?
    
    # AIS source(s)
    'aisEnabled': False, # Do we want to connect to the AIS servers in the list?
    'aisSrvList': { # Dictionary of host(s) to connect to when running the AIS connector.
        "<source name>": { "host": "<hostname or IP>", "port": 1002, "reconnectDelay": 5, "threadTimeout": 300} # Server name, host address, port, reconnect delay (if disconnected), and timeout before reconnecting to AIS source if we don't have data.
    }
}

# airSuck server settings
airSuckSrvSettings = {
    'myName': genName, # A descriptive name for this data source.
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Do we want to run the dump1090 connector? True = yes, False = no
    'srvListenHost': "0.0.0.0", # Listen on this address for incoming connections when a connector server. Default is all addresses: "0.0.0.0"
    'srvListenPort': 8091, # Dump 1900 connect incoming port when running as a server.
    'clientPingInterval': 10.0, # This is how often we want to "ping" a client so if it doesn't get a ping it knows to reconnect (in seconds).
    'debug': False, # Debug?
    'aisEnqueue': True # For debugging we can enable or disable enqueueing data. Turning this on will prevent the AIS engine from passing data on to the AIS state engine and MongoDB.
}


########################################
# Connector and state engine settings. #
########################################

# Dump1090Connector settings
d1090ConnSettings = {
    'myName': genName, # A descriptive name for this data source.
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Do we want to run the dump1090 connector? True = yes, False = no
    'connListenHost': "0.0.0.0", # Listen on this address for incoming connections when a connector server. Default is all addresses: "0.0.0.0"
    'connListenPort': 8091, # Dump 1900 connect incoming port when running as a server.
    'clientPingInterval': 10.0, # This is how often we want to "ping" a client so if it doesn't get a ping it knows to reconnect (in seconds).
    'connClientList': { # Array of hosts to connect to when running client connector script.
        "<source name>": { "host": "<hostname or IP>", "port": 30002, "reconnectDelay": 5, "threadTimeout": 30}, # This can contain additional dictionaries.
        "<another source name>":  { "host": "<hostname or IP>", "port": 30002, "reconnectDelay": 5, "threadTimeout": 120, "srcPos": [33.944128, -118.402787, "manual"]} # Same as above, but we have source position info that enabled CPR local decoding. The srcPos directive is optional.
    },
    'debug': False # Debug?
}

# aisConnector settings
aisConnSettings = {
    'myName': genName, # A descriptive name for this data source.
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Do we want to run the dump1090 connector? True = yes, False = no
    'connClientList': { # Array of hosts to connect to when running client connector script.
        "<server name>": { "host": "<hostname or IP>", "port": 1002, "reconnectDelay": 5, "threadTimeout": 30}, # This can contain additional dictionaries.
        "<another server name>": { "host": "<hostname or IP>", "port": 1002, "reconnectDelay": 5, "threadTimeout": 30, "srcPos": [0.0, 0.0, "manual"]} # This example contains position data [lat, lon, "location type"].
    },
    'aisEnqueue': True, # For debugging we can enable or disable enqueueing data. Turning this on will prevent the AIS engine from passing data on to the AIS state engine and MongoDB.
    'debug': False # Debug?
}

# SSR State engine settings
ssrStateEngine = {
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Do we want to run the state engine? True = yes, False = no
    'hashTTL': 300, # Expire vehicles that we haven't seen in this number of seconds. Default is 300 sec (5 min)
    'cprExpireSec': 20, # This specifies how old CPR data can be before we reject it as too old to be valid in sec. Default is 20.
    'hashHost': genRedisHost, # This Redis host stores the hash values to keep track of state for SSR data.
    'hashPort': genRedisPort, # The port for the above redis instance.
    'debug': False # Debug?
}

# AIS State engine settings
aisStateEngine = {
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Do we want to run the state engine? True = yes, False = no
    'hashTTL': 1200, # Expire vehicles that we haven't seen in this number of seconds. Default is 1200 sec (20 min)
    'hashHost': genRedisHost, # This Redis host stores the hash values to keep track of state for SSR data.
    'hashPort': genRedisPort, # The port for the above redis instance.
    'debug': False # Debug?
}


############################
# Shared library settings. #
############################

# Generic settings for the dump1090 handler. These settings control how the shared dump1090 handler used by the dump1090 connector client and airSuck server work.
d1090Settings = {
    'dedupeTTLSec': 3, # Time to live for deduplicated frames. This rejects duplicate frames recieved within 3 sec of each other.
    'dedupeHost': genRedisHost, # This host contains the objects used to deduplicate frames.
    'dedupePort': genRedisPort # Redis port number for dedupe.
}

# Generic settings for the AIS handler. These settings control how the shared AIS handler used by the AIS connector client and airSuck server work.
aisSettings = {
    'fragTTLSec': 1, # Time to live for frame fragments. This clears fragmented frames no recieved within n sec of each other.
    'fragHost': genRedisHost, # This host contains the objects used to assemble fragemented frames.
    'fragPort': genRedisPort, # Redis port number for hash object redis instance.
    'dedupeTTLSec': 3, # Time to live for deduplicated frames. This rejects duplicate frames recieved within 3 sec of each other.
    'dedupeHost': genRedisHost, # This host contains the objects used to deduplicate AIS payloads.
    'dedupePort': genRedisPort # Redis port number for dedupe.
}

#########################################
# Settings for MongoDB storage engines. #
#########################################

# Raw connector data MongoDB storage engine settings
connMongo = {
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Turn on storage of connector data before processing? True = on, False = off.
    'host': genMongoHost, # MongoDB server that holds connector data.
    'port': genMongoPort, # Port number for the mongoDB instance.
    'dbName': "airSuck", # Database name.
    'coll': "airConn", # Collection name for connector data.
    'checkDelay': 0.1 # Delay between checks where we don't have data. This is in seconds and prevents the process from chewing up CPU when there is little or no data.
}

# State data MongoDB storage engine settings
stateMongo = {
    'logMode': genLogMode, # Use the generic logging mode specified in the quick-and-diry section. This can be changed per application.
    'enabled': True, # Turn on storage of state data after processing? True = on, False = off.
    'host': genMongoHost, # MongoDB server that holds state data.
    'port': genMongoPort, # Port number for the mongoDB instance.
    'dbName': "airSuck", # Database name.
    'coll': "airState", # Collection name for connector data.
    'checkDelay': 0.1 # Delay between checks where we don't have data. This is in seconds and prevents the process from chewing up CPU when there is little or no data. 
}

##########################################################################################################################
# The Redis services can be on a single server or multiple servers. The queues are broken out like this for flexibility. #
##########################################################################################################################

# Connector relaible Redis queue settings - used by multliple scripts.
connRel = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckConnRel" # Queue name.
}

# Connector pub/sub redis queue settings - used by multiple scripts.
connPub = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckConnPub" # Queue name.
}

# State engine reliable Redis queue settings - used by multiple scripts.
stateRel = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckStateRel" # Queue name.
}

# state engine pub/sub redis queue settings - used by multiple scripts.
statePub = {
    'host': genRedisHost, # This host hosts the queue.
    'port': genRedisPort, # This is the port number for the instance hodling the queue.
    'qName': "airSuckStatePub" # Queue name.
}
