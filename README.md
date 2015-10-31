AirSuck is an ADS-B/SSR and AIS processing, storage, and display application with Google Maps integration.

Features:
 - GPLv3 license.
 - Uses dump1090 binary output to proces SSR frames.
 - Uses a generic AIS TCP port to get AIS data frames.
 - Supports multiple data sources simultaneously with input data deduplication to prevent data overlap for causing problems.
 - dump1090 MLAT passthrough supported, but not yet implemented.
 - Optionally stores data in MongoDB.
 - Can easily be used in a distributed architecture for scalability.
 - Real-time data display with Google Maps integration uisng Node.JS
 - The architecture is designed to easily integrate with other software projects using Redis queues or MongoDB queries.
 - The libAirSuck package can be used in part or entirely by other python projects to process telemetry data.
   - The libAirSuck package includes aisParse.py, ssrParse.py, airSuckUtil.py, and cprMath.py.

Support for ACARS data and using the FAA downloadable aircraft database to provide additional aircraft data are planned in future releases. 


File list:

"Daemons":
  - aisConnector.py - Handles connections to one or more AIS NMEA TCP source to recieve AIS data.
  - dump1090ConnClt.py - Handles connections to one or more dump1090 instances to recieve ADS-B Modes A, C, and S frames as hex strings with support for MLAT data. All data is passed through the ADS-B decoder and placed on a reliable queue to store raw frames and a pub/sub queue for further processing by the SSR state engine.
  - dump1090ConnSrv.py - Recieves JSON data from dump1090 client connector instances to recieve ADS-B Modes A, C, and S frames as hex strings with support for MLAT data. All data is passed through the ADS-B decoder and placed on a reliable queue to store raw frames and a pub/sub queue for further processing by the SSR state engine.
  - mongoDump.py - Stores incoming raw data from sources in a database for storage and reprocessing if necessary.
  - aisStateEngine.py - Handles processing of stateful AIS data to build vessel and station data, locaions, callsigns, IMOs, etc. This process dumps AIS on a pub/sub queue for halding by other processes, and on a reliable queue for storage in MongoDB.
  - ssrStateEngine.py - Handles processing of stateful ADS-B data to build aircraft location data, call signs, etc. This process dumps aircraft state updates on a pub/sub queue for handling by other processes, and on a reliable queue for storage in MongoDB.
  - stateMongoDump.py - Stores state data in MongoDB for later processing.
  - node/stateNode.js - Node.js server for passing state JSON to a browser or other service. Requires Node.js and the following Node.js packages: redis, express, socket.io
  - node/dump1090Client.js - dump1090 node.js submitter for connecting to dump1090Srv.py. Will be replaced by another script.

Libraries:
  - libAirSuck/ - Package folder for libAirSuck which includes parsers, etc.
  - libAirSuck/aisParse.py - Supports decoding of AIS sentences.
  - libAirSuck/ssrParse.py - Supports decoding of binary ADS-B data into relevant fields.
  - libAirSuck/cprMath.py - Supports handling of Compact Position Reporting data.
  - libAirSuck/airSuckUtil.py - Collection of tools for unit conversion, algorithms and functions for geographic data processing.

Clients:
  - sub2Dump1090.py - Feeds aggregated SSR data on the pub/sub queue from dump1090Connector.py and other sources back into dump1090 instances for testing purposes.
  - sub2Console.py - Dumps JSON strings generated by connector scripts on the feed pub/sub queue (such as dump1090Connector.py) to the Console.
  - sub2Parse.py - Feeds SSR data back through the SSR Parsing library and dumps the decoded frames to the console. This is mostly for debugging and development.
  - stateSub2Console.py - Feeds JSON strings generated by the state engines on the state pub/sub feed to the console.
  - stateSub2Loc.py - Displays updates from the state engine about vehicles that positioning data exists for.
  - stateSub2Geofence.py - Displays updates from the state engines about vehicles that have positioning data and are inside a configured radius around a configured GPS coordinate. This script is pre-configured for vehciles within 3 km of KPDX.

Test files:
  - sub2CrCTest.py - Checks CRC sums and performs XOR operations on frames. This was developed for testing.
  - ssrParseTest.py - Tests decoding of one or more manually entered frames by the ssrParse class. This was developed for testing.
  - cprMathTest.py - Class for testing Compact Position Reporting (CPR) algorithm. This was developed for testing.
  - aisParseTest.py - Tests decoding of AIS sentences.

Support config files:
  - supervisor/airSuck-aisConnector.conf - Supervisor config file to keep aisConector.py running as a daemon.
  - supervisor/airSuck-dump1090ConnClt.conf - Supversior config file to keep dump1090ConnClt.py running as a daemon.
  - supervisor/airSuck-dump1090ConnSrv.conf - Supversior config file to keep dump1090ConnSrv.py running as a daemon.
  - supervisor/airSuck-mongoDump.conf - Supervisor config file to keep mongoDump.py running as a daemon.
  - supervisor/airSuck-aisStateEngine.conf - Supervisor config file to keep aisStateEngine.py running as a daemon.
  - supervisor/airSuck-ssrStateEngine.conf - Supervisor config file to keep ssrStateEngine.py running as a daemon.
  - supervisor/airSuck-stateMongoDump.conf - Supervisor config file to keep stateMongoDump.py running as a daemon.
  - supervisor/airSuck-stateNode.conf - Supervisor config file to keep node/stateNode.js running as a daemon.
  - supervisor/airSuck-dump1090Client.conf - Supervisor config file to keep the dump1090 client node.js script as a daemon.
  - The above files are all split out as individual config files to facilitate running some or all of these files on one or more servers. This makes it easier to split out roles in a multi-host environment.

AirSuck Geospatial viewer web page:
  - node/index.html - Main page served when you're connected to the stateNode service with a browser. This page displays data about vehicles being received by airSuck on Google Maps.
  - node/jquery-2.1.4.min.js - jQuery javascript library served locally. (See https://jquery.com)
  
Documentation:
  - docs/airSuck data dictionary.ods - Data dictionary for JSON data passed between components of airSuck.


Acknowledgements:
  - This project uses code from Bistromath's gr-modes project (https://github.com/bistromath/gr-air-modes), and from MalcomRobb's dump1090 (https://github.com/MalcolmRobb/dump1090).
  - Matthew Lambert for a lot of work on the Google Maps integration.
