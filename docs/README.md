#AirSuck block diagram describing communication between various components.
```
     +---------------------+
     | Dump1090 managed    |
     | by client as thread |                            (2)             +-------+
     +--------+------------+   +--------+       +------------------+    |AIS TCP|
              ^                |Dump1090| <---+ |dump1090ConnClt.py|    |Source |
              |                +--------+  TCP  +-------+----------+    +---+---+
              |                                         |                   ^
      +-------+--------+           +----------------+   | Redis         TCP |
  (1) |AirSuckClient.py| +-------> |AirSuckServer.py|   |                   |
      +----------------+   TCP     +--------+-------+   |       +-----------+---+
                                            |           +-------+AisConnector.py| (3)
                                            +-----------+       +---------------+
                                            |
                      +----------------+    |    +---------------+     +------------+
                  (4) |Redis connector | <--+--> |Redis connector+----->mongoDump.py| (5)
                      |pub/sub queue   |         |reilable queue |     +------+-----+
                      +-------+--------+         +---------------+            |
                              |                              (4)              |
                              |Redis                                     +----v----+
    +-----------------+       |      +-----------------+                 |MongoDB  |
(6) |ssrStateEngine.py<-------+------>aisStateEngine.py| (6)             |airConn  |
    +-------------+---+              +--+--------------+                 |collecion|
                  |                     |                                +---------+
                  +------------+--------+
                               |
          +-------------+      |Redis  +---------------+ (8)                (9)
          |Redis state  |      |       |Redis state    |             +-----------------+
      (7) |pub/sub queue<------+------->reliable queue +------------->stateMongoDump.py|
          +-----+-------+              +---------------+             +----------+------+
                |                                                               |
                +-------------------+                                           |
     (10)       |                   |  (11)                   (12)        +-----v----+
 +--------------v---+         +-----v------+             +-----------+    |MongoDB   |
 |All client scripts|         |NodeJS:     <-------------+Web browser|    |airState  |
 +------------------+         |stateNode.js|    HTTP     +-----------+    |collection|
                              +------------+                              +----------+
```
##Component roundup:

### 1) The airSuckClient.py and airSuckServer.py. These two scripts are designed to run as a client/server pair with remote connections in mind. The server can accept many client connections, and the client manages the dump1090 thread which also includes a watchdog that will restart the dump1090 client in the event of a failure. The client and server components also send each other keepalives and have watchdogs that re-estabish the connections in the event they are disrupted.
  - One instance of airSuckServer.py can accept many client connections. The clients connect to the server on TCP 8091 by default.
  - See the airSuckClientSettings and airSuckSrvSettings sections of config.py for related configuration.
  - airSuckServer utilizes Redis to make sure no duplicate frames are processed.
### 2) dump1090ConnClt.py is a client that connects to a dump1090 instance with the --net option specified. This script connects to a given dump1090 instance being run inside a LAN. It has connection watchdogs as well.
  - One instance of dump1090ConnClt.py can connect to many dump1090 instances. The default TCP port the connection uses is 30002.
  - See d1090ConnSettings in config.py for configuration options.
  - This piece of software also utilizes Redis to make sure no duplicate frames are processed.
### 3) aisConnector.py is a client that connects to an AIS TCP source in the same fashion dump1090ConnClt.py connects to dump1090. This supports only TCP connections to AIS sources. The aisConnector.py script also assembles AIS frame fragments.
  - One instance of aisConnector.py can connecto to many AIS sources. The default port is 1002.
  - See the aisConnSettings of config.py for availiable configuration options.
  - aisConnector.py utilizes Redis for frame defragmentation and deduplication.
### 4) The redis connector queues - These queues recieve JSON data from the connector scripts. The pub/sub queues are used by the state engine componenets for each protocol and the reliable queue is used to send data to the mongoDB connector storage component.
  - See the connRel and connPub sections of the config files for configuration options.
### 5) mongoDump.py stores raw connector data to a mongoDB instance if it is configured to do so. Connector data is raw data with a small amount of metadata in JSON format.
  - See the connMongo section of config.py for configuration options.
### 6) ssrStateEngine.py and aisStateEngine.py are two scripts that keep track of data coming from the pub/sub queues (4). They are used to process the raw frame data, keep vehicle state information, and submit data to the state queues (8). ssrStateEngine.py handles ADS-B information from dump1090 but can be extended to handle other binary ADS-B formats. aisStateEngine.py handles fully assembled AIS frames.
  - See the d1090ConnSettings and aisConnSettings sections of config.py for configuration options.
### 7) The pub/sub state queue handles processed and decoded frames. The pub/sub queue is used by all client applications to receive data.
  - See the statePub section of config.py for configuration options related to this queue.
### 8) The redis state reliable queue is used to queue data for the stateMongoDump.py script.
  - See the stateRel section of config.py for configuration options related to this queue.
### 9) stateMongoDump.py is used to pull state data off of the reliable state queue and store it in mongoDB.
 - See the stateMongo section of config.py for config options related to stateMongoDump.py
###10) The client scripts are found under the clients/ folder. They can be used for testing and development purposes.
 - Most of the clients use configuration options from the various queues they monitor.
###11) stateNode.js is a NodeJS client that rebroadcasts the stream of vehicle data to a web browser and serves a web page that displays all of the vehciles. The NodeJS application leverages express and socket.io to serve and brodcast the JSON data from the state queue.
 - This uses config.js under the node/ folder for configuration options.
 - stateNode.js serves the JSON stream and all relevant files from TCP 8090 using HTTP.
###12) And end-user can view and search the information from the state queue which is overlayed on Google Maps.
 - Various configuration options can be found under vehicles.js and many settings from vehicles.js are overriden by airAIS.js and airSSR.js to be speicific to the type of incoming data.

Notes:
 - There are many independent scripts that make up the airSuck project. The reason for this is to support running various compnonents on many servers in a distributed fashion, or to be run on one host.
 - config.py contains many variables staring with "gen" and these options can be overriden in any section of config.py. They're provided by default in order to speed up simple installations of airSuck.
 - If airSuck is being run in a distributed fashion across many hosts it's important to make sure the sections of the configuration that deal with redis queues and dedpe tables are consistent across the multiple hosts. Misconfiguration can result in data not being processed between the connector, state engine, and client layers as well as failure to deduplicate input data from multiple dump1090 or AIS sources.
 - This project was designed to run under the Supervisor (http://supervisord.org/) package. The supervisor folder in the airSuck project contains template config files which can be copied to /etc/supvervisor/conf.d/. Copy all the .config files under the supervisor folder you want to run on a given host.
 - config.py is used as the configuration file for all the Python components of the software and should be placed in the root of the airSuck folder. A template config.py is stored under the config/ folder.
 - config.js is used as the configuration file for the Node.JS component of the software, and the file should be placed in the node/ folder. A template config.js is stored under the config/ folder.
 - airSuckServer.py, dump1090ConnClt.py, and aisConnector.py all support deduplication of incoming data frames. If multiple sources of data put the same frames into the system only the first of the identical frames will be processed.
 