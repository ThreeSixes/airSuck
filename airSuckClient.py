#!/usr/bin/python

"""
airSuckClient by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

###########
# Imports #
###########

try:
    import config
except:
    raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

# Load the config _very_ early.
asConfig = config.airSuckClientSettings

# If we have an attached GPS...
if asConfig['gps']:
    # Do GPS things.
    from gps import *

import datetime
import json
import re
import socket
import time
import threading
import traceback
import Queue
import atexit
import signal
import sys
import errno
from libAirSuck import asLog
from subprocess import Popen, PIPE, STDOUT
from pprint import pprint


#########################
# dump1090Handler class #
#########################

class airSuckClient():
    
    # Class consructor
    def __init__(self):
        """
        dump1090Handler handles the dump1090 executable to grab ADS-B, and makes sure it's running. If the process jams it's restarted.
        """
        # Init message.
        logger.log("Init airSuckClient...")
        
        # Build the command we need to run dump1090 in a fashion Popen can understand.
        self.popenCmd = [asConfig['dump1090Path']] + asConfig['dump1090Args'].split(" ")
        
        # Pre-compiled regex used to verify dump1090 ADS-B data.
        self.__re1090 = re.compile("[@*]([a-fA-F0-9])+;")
        #self.__re1090Mlat = re.compile("[@*]([a-fA-F0-9])+;")
        
        # Watchdog setup.
        self.__myWatchdog = None
        self.__lastADSB = 0
        self.__watchdog1090Restart = False
        self.__lastSrvKeepalive = 0
        self.__keepAliveTimer = 0
        self.__maxTimeSrv = 2.0 * asConfig['keepaliveInterval']
        self.__keepaliveJSON = "{\"keepalive\": \"abcdef\"}"
        
        # Backoff counters
        self.__backoff1090 = 1.0
        self.__backoffSrv = 1.0
        
        # Networking.
        self.__serverSock = None
        self.__serverConnected = False
        self.__rxBuffSz = 128
        
        # Should we keep going?
        self.__keepRunning = True
        
        # Queue worker running?
        self.__queueWorkerRunning = False
        
        # RX watcher running?
        self.__rxWatcherRunning = False
        
        # Dump1090 running?
        self.__dump1090Running = False
        
        # Global dump1090 process holder.
        self.__proc1090 = None
        
        # GPSD stuff...
        # Do we have an initial position?
        self.__gpsdData = False
        
        # Is there anything prohibiting the start of the GPS worker?
        self.__startGpsWorker = asConfig['gps']
    
    def __clientWatchdog(self):
        """
        Master watchdog for the software client.
        """
        
        # If we're connected to the server do the network checks.
        if self.__serverConnected:
            
            try:
                # Check to see if we got data from dump1090.
                if self.__lastSrvKeepalive >= self.__maxTimeSrv:
                    
                    # Raise an exception.
                    raise IOError()
                
                else:        
                    # Increment our last entry.
                    self.__lastSrvKeepalive += 1
            
            except IOError:
                # Print the error message
                logger.log("airSuck client watchdog: No keepalive for %s sec." %self.__maxTimeSrv)
                
                # Flag our connection as dead.
                self.__serverConnected = False
                
                # Disconnect.
                self.__disconnectSouce()
            
            except KeyboardInterrupt:
                # Pass the keyboard interrupt exception up the stack.
                raise KeyboardInterrupt
            
            except SystemExit:
                # pass the system exit exception up the stack.
                raise SystemExit
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck client watchdog threw exception:\n%s" %tb)
                
                # Flag our connection as dead.
                self.__serverConnected = False
                
                # Disconnect.
                self.__disconnectSouce()
            
            try:
                # If we're connected.
                if self.__serverConnected:
                    
                    # If it's time to send the keepalive...
                    if self.__keepAliveTimer >= asConfig['keepaliveInterval']:
                        self.__keepAliveTimer = 0
                    
                    if self.__keepAliveTimer == 0:
                        # Send the ping.
                        self.__send(self.__keepaliveJSON)
                    
                    # Roll the keepalive timer.
                    self.__keepAliveTimer += 1
                
                else:
                    # Reset the keeplaive timer.
                    self.__keepAliveTimer = 0
            
            except KeyboardInterrupt:
                # Pass the keyboard interrupt exception up the stack.
                raise KeyboardInterrupt
            
            except SystemExit:
                # pass the system exit exception up the stack.
                raise SystemExit
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck client watchdog threw exception:\n%s" %tb)
                
                # Flag our connection as dead.
                self.__serverConnected = False
                
                # Disconnect.
                self.__disconnectSouce()
                
                # Set flag indicating whether we restarted because of the watchdog.
                self.__watchdog1090Restart = False
        
        # If we're running dump1090 handle timing it out.
        if asConfig['dump1090Enabled']:
            try:
                # Check to see if we got data from dump1090.
                if self.__lastADSB >= asConfig['dump1090Timeout']:
                    
                    # Set watchdog restart flag.
                    self.__watchdog1090Restart = True
                    
                    try:
                        # Kill dump1090
                        self.__proc1090.kill()
                    
                    except KeyboardInterrupt:
                        # Pass the keyboard interrupt exception up the stack.
                        raise KeyboardInterrupt
                    
                    except SystemExit:
                        # pass the system exit exception up the stack.
                        raise SystemExit
                    
                    except:
                        # Do nothing in the event it fails.
                        pass
                    
                    # Raise an exception.
                    raise IOError()
                
                else:        
                    # Increment our last entry.
                    self.__lastADSB += 1
            
            except IOError:
                # Print the error message
                logger.log("airSuck client watchdog: No data from dump1090 in %s sec." %asConfig['dump1090Timeout'])
                
                try:
                    # Stop dump1090.
                    self.__proc1090.kill()
                
                except:
                    # Do nothing, since it won't die nicely in some cases.
                    pass
                
                finally:
                    # Flag dump1090 as down.
                    self.__dump1090Running = False
                    self.__proc1090 = None
            
            except KeyboardInterrupt:
                # Pass the keyboard interrupt exception up the stack.
                raise KeyboardInterrupt
            
            except SystemExit:
                # pass the system exit exception up the stack.
                raise SystemExit
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck client watchdog threw exception:\n%s" %tb)
        
        # Restart our watchdog.
        self.__myWatchdog = threading.Timer(1.0, self.__clientWatchdog)
        self.__myWatchdog.start()
    
    def __rxWatcher(self):
        """
        Handle data recieved from our connected socket.
        """
        
        # Flag the RX watcher as running
        self.__rxWatcherRunning = True
        
        # Loop guard
        keepRunning = True
        
        # Empty buffer string.
        buff = ""
        
        # While we're connected
        while keepRunning:
            try:
                if self.__serverConnected == True:
                    # Get data.
                    buff = buff + self.__serverSock.recv(self.__rxBuffSz)
                    
                    # If we have a newline check of our string and clear the buffer.
                    if buff.find("\n"):
                        # If we got our JSON sentence reset the counter.
                        if buff == self.__keepaliveJSON + "\n":
                            self.__lastSrvKeepalive = 0
                            
                            # If we're debugging log the things.
                            if asConfig['debug']:
                                logger.log("RX Keepalive: %s" %buff.strip())
                        
                        # Reset data stuff.
                        buff = ""
                        
                        # Attempt to send another keepalive.
                        self.__send(self.__keepaliveJSON)
            
            except KeyboardInterrupt:
                # We don't want to keep running.
                keepRunning = False
                
                # Flag the RX watcher as not running
                self.__rxWatcherRunning = False
                
                # Pass the exception up the chain.
                raise KeyboardInterrupt
            
            except SystemExit:
                # We don't want to keep running.
                keepRunning = False
                
                # Flag the RX watcher as not running
                self.__rxWatcherRunning = False
                
                # pass the system exit exception up the stack.
                raise SystemExit
            
            except socket.timeout:
                # If we time out do nothing. This is intentional.
                None
            
            except Exception as e:
                # We don't want to keep running.
                keepRunning = False
                
                # Flag the RX watcher as not running
                self.__rxWatcherRunning = False
                
                # We probably disconnected.
                self.__serverConnected = False
                
                if 'errno' in e:
                    # If something goes wrong...
                    if e.errno == 32:
                        # We expect this to break this way sometimes.
                        raise IOError
                    
                    else:
                        tb = traceback.format_exc()
                        logger.log("Exception in airSuck client rxWatcher:\n%s" %tb)
    
    def __gpsWorker(self):
        """
        This monitors GPSD for new data and updates our class-wide GPS vars.
        """
        
        logger.log("Starting GPS worker...")
        
        # We shouldn't start another GPS worker unless we have an exception.
        self.__startGpsWorker = False
        
        # If loading GPS worked...
        canHasGps = False
        
        try:
            # If we have a gps set it up.
            if asConfig['gps']:
                self.__gps = gps(mode=WATCH_ENABLE)
                # We're up!
                canHasGps = True
            
            try:
                # Keep doing the things.
                while(canHasGps):
                    # Get the "next" data...
                    self.__gps.next()
                    
                    # Set our flag to let the system know we have an initial reading.
                    self.__gpsdData = True
            
            # If we have an keyboard interrupt or system exit pass it on.
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            
            except SystemExit:
                raise SystemExit
            
            except:
                # Whatever else happens we want to log.
                tb = traceback.format_exc()
                logger.log("GPS worker blew up:\n%s" %tb)
                
                # Dump message and wait 30 sec before clearing the fail flag.
                logger.log("GPS worker sleeping 30 sec.")
                time.sleep(30.0)
                
                # Now we want to try and start again.
                self.__startGpsWorker = True
            
        except:
            # Flag the gpsWorker thread as down.
            self.__gpsWorkerRunning = False
            self.__gpsWorkerFail = True
            
            # Whatever else happens we want to log.
            tb = traceback.format_exc()
            logger.log("GPS worker blew up trying to activte the GPS:\n%s" %tb)
            
            # Dump message and wait 30 sec before clearing the fail flag.
            logger.log("GPS worker sleeping 30 sec.")
            time.sleep(30.0)
            
            # Now we want to try and start again.
            self.__startGpsWorker = True
    
    def __handleBackoffSrv(self, reset=False):
        """
        Handle the backoff algorithm for reconnect delay. Accepts one optional argument, reset which is a boolean value. When reset is true, the backoff value is set back to 1. Returns no data.
        """
        
        # If we're resetting the backoff set it to 1.0.
        if reset:
            self.__backoffSrv = 1.0
        else:
            # backoff ^ 2 for each iteration, ending at 4.0.
            if self.__backoffSrv == 1.0:
                self.__backoffSrv = 2.0
            
            elif self.__backoffSrv == 2.0:
                self.__backoffSrv = 4.0
        
        return
    
    def __handleBackoff1090(self, reset=False):
        """
        Handle the backoff algorithm for restart delay. Accepts one optional argument, reset which is a boolean value. When reset is true, the backoff value is set back to 1. Returns no data.
        """
        
        # If we're resetting the backoff set it to 1.0.
        if reset:
            self.__backoff1090 = 1.0
        
        else:
            # backoff ^ 2 for each iteration, ending at 4.0.
            if self.__backoff1090 == 1.0:
                
                self.__backoff1090 = 2.0
            elif self.__backoff1090 == 2.0:
                
                self.__backoff1090 = 4.0
        
        return

    def __createBaseJSON(self):
        """
        Creates a base JSON dictionary with information generic to all output.
        """
        
        # Get the timestamp data.
        dtsStr = str(datetime.datetime.utcnow())
        
        # Create basic JSON dictionary.
        retVal = {"clientName": asConfig['myName'], "dataOrigin": "airSuckClient", "dts": dtsStr}
        
        # If we have gps support enabled...
        if asConfig['gps']:
            try:
                # And if we have an initial reading plus a fix...
                if self.__gpsdData and (self.__gps.fix.mode > 1):
                    # Update dictionary with GPS-related data.
                    retVal.update({"srcLat": self.__gps.fix.latitude, "srcLon": self.__gps.fix.longitude, "srcPosMeta": "gps"})
                
                elif asConfig['reportPos']:
                    try:
                        # Update dictionary with GPS-related data.
                        retVal.update({"srcLat": float(asConfig['myPos'][0]), "srcLon": float(asConfig['myPos'][1]), "srcPosMeta": "manual"})
                    
                    except:
                        logger.log("Improperly formatted position data from config.py.")
            
            except:
                tb = traceback.format_exc()
                logger.log("Failed to get GPS position data:%s" %tb)
        
        else:
            # Handle GPS and related config data here.
            if asConfig['reportPos']:
                try:
                    # Update dictionary with GPS-related data.
                    retVal.update({"srcLat": float(asConfig['myPos'][0]), "srcLon": float(asConfig['myPos'][1]), "srcPosMeta": "manual"})
                
                except:
                    logger.log("Improperly formatted position data from config.py.")
        
        return retVal

    def __verifyADSB(self, line):
        """
        Verifies the formattting of the potential ADS-B frame. If the incoming data doesn't match the regex the method returns False. If it matches it will return True.
        """
        
        # Assume we don't have good data by default.
        retVal = False
        
        # If we get a match...
        if self.__re1090.match(line) is not None:
            retVal = True
            
            # If we're debugging log the things.
            if asConfig['debug']:
                logger.log("%s appears to be valid ADS-B." %line.strip())
        
        # And return...
        return retVal
    
    def __handleADSB(self, adsb):
        """
        Place holder method that should result in the data being JSON wrapped and sent over the network.
        """
        
        
        # Reset watchdog value.
        self.__lastADSB = 0
        
        # Build a dictionary with minimal information to send.
        adsbDict = {"type": "airSSR", "data": adsb.strip()}
        adsbDict.update(self.__createBaseJSON())
        
        try:
            # JSONify the dictionary.
            adsbJSON = json.dumps(adsbDict)
        
        except:
            tb = traceback.format_exc()
            logger.log("Exception occured creating JSON dictionary:\n%s" %tb)
        
        # If we're debugging log the things.
        if asConfig['debug']:
            logger.log("Enqueue: %s" %adsbJSON)
        
        try:
            # Put it on the queue.
            clientQ.put(adsbJSON)
        
        except:
            tb = traceback.format_exc()
            logger.log("dump1090 exception putting data on queue:\n%s" %tb)
        
        return
    
    def __stdoutWorker(self):
        """
        Handle STDOUT output from dump1090.
        """
        
        try:
            # While we're still running...
            while self.__proc1090.poll() is None:
                
                # Grab the current line from STDOUT.
                output = self.__proc1090.stdout.readline()
                
                # If we're debugging dump the raw data
                if asConfig['debug']:
                    logger.log("dump1090 stdout: %s" %output.strip())
                
                # If it seems to be valid ADS-B then use it.
                if self.__verifyADSB(output):
                    # If we're debugging...
                    if asConfig['debug']:
                        logger.log("Passing %s to __handleADSB." %output.strip())
                    
                    self.__handleADSB(output)
            
            # Get any 'straggling' output.
            output = self.__proc1090.communicate()[0]
            
            # If we're debugging dump the raw data
            if asConfig['debug']:
                logger.log("dump1090 stdout: %s" %output.strip())
            
            # If it seems to be valid ADS-B then use it.
            if self.__verifyADSB(output):
                self.__handleADSB(output)
        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except SystemExit:
            raise SystemExit
        
        except AttributeError:
            # Just die nicely.
            pass
        
        except IOError:
            # Just die nicely.
            None
    
    def __stderrWorker(self):
        """
        Handle STDERR output from dump1090.
        """
        
        try:
            # While we're still running...
            while self.__proc1090.poll() is None:
                # Get our STDERR output minus the newline char.
                output = self.__proc1090.stderr.readline().replace("\n", "")
                
                # If we're debugging...
                if asConfig['debug']:
                    # If there's something on the line print it.
                    if output.strip() != "":
                        logger.log("dump1090 stderr: %s" %output)
            
            # See if there's any data that wasn't picked up by our loop and print it, too.
            output = self.__proc1090.communicate()[1].replace("\n", "")
            
            # If we're debugging...
            if asConfig['debug']:
                if output.strip() != "":
                    logger.log("dump1090 stderr: %s" %output)
            
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except SystemExit:
            raise SystemExit
        
        except AttributeError:
            # Just die nicely.
            pass
            
        except IOError:
            # Just die nicely.
            None

    def __connectServer(self):
        """
        Connects to our host.
        """
        
        # Create a new socket object.
        self.__serverSock = socket.socket()
        
        # Print message
        logger.log("airSuck client connecting to %s:%s..." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
        
        # Attempt to connect.
        try:
            # Connect up
            self.__serverSock.connect((asConfig['connSrvHost'], asConfig['connSrvPort']))
            logger.log("airSuck client connected.")
            
            # We're connected now.
            self.__serverConnected = True
            
            # Reset the last keepalive counter.
            self.__lastSrvKeepalive = 0
            
            # Reset the watchdog state.
            self.__watchdogFail = False
            
            # Reset the backoff value
            self.__handleBackoffSrv(True)
            
            # Set 1 second timeout for blocking operations.
            self.__serverSock.settimeout(1.0)
            
            # The TX and RX watchdogs should be run every second.
            self.__lastSrvKeepalive = 0
        
        except KeyboardInterrupt:
            # Pass it up the stack.
            raise KeyboardInterrupt
        
        except SystemExit:
            # Pass it up the stack.
            raise SystemExit
        
        except socket.error, v:
            # Connection refused.
            if v[0] == errno.ECONNREFUSED:
                logger.log("%s:%s refused connection." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
            
            # Connection refused.
            elif v[0] == errno.ECONNRESET:
                logger.log("%s:%s reset connection." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
                
            # Connection timeout.
            elif v[0] == errno.ETIMEDOUT:
                logger.log("Connection to %s:%s timed out." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
            
            # DNS or address error.
            elif v[0] == -2:
                logger.log("%s:%s DNS resolution failure or invalid address." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
            
            # Something else happened.
            else:
                logger.log("%s:%s unhandled socket error: %s (%s)" %(asConfig['connSrvHost'], asConfig['connSrvPort'], v[1], v[0]))
            
            # Set backoff delay.
            boDelay = asConfig['reconnectDelay'] * self.__backoffSrv
            
            # In the event our connect fails, try again after the configured delay
            logger.log("airSuck client sleeping %s sec." %boDelay)
            time.sleep(boDelay)
            
            # Handle backoff.
            self.__handleBackoffSrv()
        
        except Exception as e:
            # Dafuhq happened!?
            tb = traceback.format_exc()
            logger.log("airSuck client went boom connecting:\n%s" %tb)
                
            # Set backoff delay.
            boDelay = asConfig['reconnectDelay'] * self.__backoffSrv
            
            # In the event our connect fails, try again after the configured delay
            logger.log("airSuck client sleeping %s sec." %boDelay)
            time.sleep(boDelay)
            
            # Handle backoff.
            self.__handleBackoffSrv()
    
    def __disconnectSouce(self):
        """
        Disconnect from our host.
        """
        
        logger.log("airSuck client disconnecting.")
        
        # Clear the server connected flag.
        self.__serverConnected = False
        
        try:
            # Close the connection.
            self.__serverSock.close()
        
        except:
            tb = traceback.format_exc()
            logger.log("airSuck client threw exception disconnecting.\n%s" %tb)
        
        # Reset the last keepalive counter.
        self.__lastSrvKeepalive = 0

    def __send(self, data):
        """
        Sends specified data to the airSuck destination server.
        """
        
        # If we think we're connected try to send the infos. If not, do nothing.
        if self.__serverConnected:
            try:
                # If we're debugging log the things.
                if asConfig['debug']:
                    logger.log("Netsend: %s" %data)
                
                # Send the data to the server.
                sendRes = self.__serverSock.send("%s\n" %data)
                
                # If we weren't able to send anything...
                if sendRes == 0:
                    # Cause a small explosion.
                    raise RuntimeError("Socked failed to send data. The connection is down.")
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck client send exception:\n%s" %tb)
                
                # Flag our connection as dead in the event we fail to send.
                self.__serverConnected = False
                
                # Disconnect.
                self.__disconnectSouce()
    
    def __queueWorker(self):
        """
        Sends data on the queue to the remote server.
        """
        
        self.__queueWorkerRunning = True
        
        logger.log("airSuck client queue worker starting...")
        
        while True:
            try:
                # Grab the JSON put on the queue
                someJSON = clientQ.get()
                
                # If we're debugging log the things.
                if asConfig['debug']:
                    logger.log("Dequeue: %s" %someJSON)
                
                # And then send it over the network.
                self.__send(someJSON)
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck client queue worker caught exception reading from queue:\n%s" %tb)
                
                # Flag the queue worker as down.
                self.__queueWorkerRunning = False
    
    def __kill1090(self):
        """
        Kill the dump1090 process.
        """
        logger.log("Attempting to kill dump1090...")
        
        try:
            if self.__proc1090.poll() is None:
                self.__proc1090.kill()
                logger.log("dump1090 killed.")
        
        except AttributeError:
            # The process is already dead.
            logger.log("dump1090 not running.")
        
        except:
            # Unhandled exception.
            tb = traceback.format_exc()
            logger.log("Exception thrown while killing dump1090:\n%s" %tb)
        
        # Flag dumpairSuckClient1090 as down.
        self.__dump1090Running = False
        
        # Blank the object.
        self.__proc1090 = None
    
    def __worker(self):
        """
        The main worker method that spins up the dump1090 executable and takes data from stdout.
        """
        
        # We want to keep going.
        keepRunning = True
        
        # Start our watchdog process.
        self.__myWatchdog = threading.Timer(1.0, self.__clientWatchdog)
        self.__myWatchdog.start()
        
        # Make sure we kill dump1090 when we shut down.
        atexit.register(self.__kill1090)
        
        # Keep running and restarting dump1090 unless the program is killed.
        while keepRunning:
            # If we have GPS enabled and there's no reason we shouldn't start it.
            if asConfig['gps'] and self.__startGpsWorker:
                try:
                    # Start the GPS worker thread.
                    gpsWorker = threading.Thread(target=self.__gpsWorker)
                    gpsWorker.daemon = True
                    gpsWorker.start()
                
                except KeyboardInterrupt:
                    # Pass it on...
                    raise KeyboardInterrupt
                
                except SystemExit:
                    # Pass it up.
                    raise SystemExit
                
                except:
                    tb = traceback.format_exc()
                    logger.log("airSuck client worker blew up starting the GPS worker:\n%s" %tb)
            
            try:
                # If we're supposed to keep running and the server is connected.
                if keepRunning and (not self.__serverConnected):
                    self.__connectServer()
            
            except KeyboardInterrupt:
                # Pass it on...
                raise KeyboardInterrupt
            
            except SystemExit:
                # Pass it up.
                raise SystemExit
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck client worker blew up:\n%s" %tb)
                
                self.__disconnectSouce()
            
            try:
                # If the RX watcher is not running
                if (not self.__rxWatcherRunning):
                    # Start the RX watcher...
                    rxListener = threading.Thread(target=self.__rxWatcher)
                    rxListener.daemon = True
                    rxListener.start()
            
            except KeyboardInterrupt:
                # Stop looping.
                keepRunning = False
                
                # Flag the RX watcher as not running
                self.rxWatcherRunning = False
                
                # Raise the keyboard interrupt.
                raise KeyboardInterrupt
            
            except SystemExit:
                
                # Stop looping.
                keepRunning = False
                
                # Flag the RX watcher as not running
                self.rxWatcherRunning = False
                
                # Pass the exception up the chain to our runner.
                raise SystemExit
            
            except:
                # Log the exception
                tb = traceback.format_exc()
                logger.log("airSuck client rxListener blew up:\n%s" %tb)
                
                # Flag the RX watcher as not running
                self.rxWatcherRunning = False
            
            try:
                # If the queue worker isn't running...
                if (not self.__queueWorkerRunning):
                    # Start our queue worker.
                    queueThread = threading.Thread(target=self.__queueWorker)
                    queueThread.daemon = True
                    queueThread.start()
            
            except KeyboardInterrupt:
                
                # Pass the exception up the chain to our runner.
                raise KeyboardInterrupt
            
            except SystemExit:
                
                # Pass the exception up the chain to our runner.
                raise SystemExit
            
            except:
                # Something else unknown happened.
                tb = traceback.format_exc()
                logger.log("dump1090 worker threw exception:\n%s" %tb)
            
            try:
                # Make sure Dump1090 is supposed to start, and that we're supposed to keep it running.
                if (asConfig['dump1090Enabled']) and (not self.__dump1090Running):
                    
                    # We have don't have dump1090 started.
                    if self.__proc1090 == None:
                        # Start dump1090.
                        self.__proc1090 = Popen(self.popenCmd, stdout=PIPE, stderr=PIPE)
                        
                        # If we have dump1090 working
                        if self.__proc1090 is not None:
                            logger.log("dump1090 started with PID %s." %self.__proc1090.pid)
                            
                            # Flag dump1090 as runningo.
                            self.__dump1090Running = True
                            
                            # Reset the backoff since we manged to start.
                            self.__handleBackoff1090(True)
                            
                            # Start the watchdog after resetting lastADSB.
                            self.__lastADSB = 0
                            
                            # Set up some threads to listen to the dump1090 output.
                            stdErrListener = threading.Thread(target=self.__stderrWorker)
                            stdOutListener = threading.Thread(target=self.__stdoutWorker)
                            stdErrListener.daemon = True
                            stdOutListener.daemon = True
                            stdErrListener.start()
                            stdOutListener.start()
                        
                        # If we intend to restart dump1090 and we didn't kill dump1090 because of the watchdog...
                        if (not self.__dump1090Running) and (not self.__watchdog1090Restart):
                            
                            # Handle backoff algorithm before it restarts.
                            boDly = self.__backoff1090 * asConfig['dump1090Delay']
                            logger.log("dump1090 sleeping %s sec before restart." %boDly)
                            time.sleep(boDly)
                            
                            # Flag dump1090 as down.
                            self.__dump1090Running = False
                            self.__proc1090 = None
                            
                            # Run the backoff handler.
                            self.__handleBackoff1090()
            
            except KeyboardInterrupt:
                # We don't want to keep running since we were killed.
                keepRunning = False
                
                
                # Flag dump1090 as down.
                self.__dump1090Running = False
                self.__proc1090 = None
                
                # Pass the exception up the chain to our runner.
                raise KeyboardInterrupt
            
            except SystemExit:
                # Flag dump1090 as down.
                self.__dump1090Running = False
                self.__proc1090 = None
                
                # Raise the exception again.
                raise SystemExit
            
            except OSError:
                # Dump an error since the OS reported dump1090 can't run.
                logger.log("Unable to start dump1090. Please ensure dump1090 is at %s." %asConfig['dump1090Path'])
                
                
                # Flag dump1090 as down.
                self.__dump1090Running = False
                self.__proc1090 = None
                
                # Flag the thread for death.
                keepRunning = False
                
                # Attempt to kill dump1090
                self.__kill1090()
            
            except:
                # Something else unknown happened.
                tb = traceback.format_exc()
                logger.log("dump1090 worker threw exception:\n%s" %tb)
                
                # Flag dump1090 as down.
                self.__dump1090Running = False
                self.__proc1090 = None
                
                # Attempt to kill dump1090
                self.__kill1090()
            
            try:
                # Wait 0.1 seconds before looping.
                time.sleep(0.1)
            
            except KeyboardInterrupt:
                # We don't want to keep running since we were killed.
                keepRunning = False
                
                # Raise the exception again.
                raise KeyboardInterrupt
            
            except SystemExit:
                # We don't want to keep running since we were killed.
                keepRunning = False
                
                # Raise the exception again.
                raise SystemExit
    
    def __exitHandler(self, x=None, y=None):
        """
        When we're instructed to exit these are the things we should do.
        """
        
        logger.log("Caught signal that wants us to die.")
        
        try:
            # Try to kill dump1090.
            self.__kill1090()
        
        except:
            pass
        
        # Raise this exception to kill the program nicely.
        sys.exit(0)
    
    def run(self):
        logger.log("Starting dump1090 worker.")
        
        # NOTE:
        # Since dump1090 has a bad habit of not dying unless we implement signal
        # handlers for signals that result in the death of the client.
        
        try:
            signal.signal(signal.SIGTERM, self.__exitHandler)
           
        except:
            tb = traceback.format_exc()
            logger.log("Death signal handler blew up setting signal handlers:\n%s" %tb)
        
        try:
            # Attempt to start the worker.
            self.__worker()
        
        except KeyboardInterrupt:
            # Make damn sure dump1090 is dead.
            try:
                self.__kill1090()
            except:
                pass
            
            # Pass the keyboard interrupt up the chain to our main execution
            raise KeyboardInterrupt
        
        except SystemExit:
            # Make damn sure dump1090 is dead.
            try:
                self.__kill1090()
            except:
                pass
            # Pass the exception up the stack.
            
            raise SystemExit
        
        except Exception as e:
            # Make damn sure dump1090 is dead.
            try:
                self.__kill1090()
            except:
                pass
            
            # Pass the exception up the stack.
            raise e


#######################
# Main execution body #
#######################

if __name__ == "__main__":
    
    # Set up our global logger.
    logger = asLog(asConfig['logMode'])
    
    # Log startup message.
    logger.log("Starting the airSuck client...")
    
    # If we're debugging...
    if asConfig['debug']:
        # Dump our config.
        logger.log("Configuration:\n%s" %asConfig)
    
    # Set up our global objects.
    asc = airSuckClient()
    clientQ = Queue.Queue()
    
    # Do we have at least one data source configured?
    noDS = True
    
    try:
        # If we are configured to run the dump1090 client add it to our thread list.
        if asConfig['dump1090Enabled']:
            # Set the data source config flag.
            noDS = False
        
        # If we are configured to run the dump1090 client add it to our thread list.
        if asConfig['aisEnabled']:
            # Set the data source config flag.
            noDS = False
        
        # Start our comms thread.
        threadClient = threading.Thread(target=asc.run())
        threadClient.daemon = True
        threadClient.start()
        
        # If we didn't have a configured data source dump a helpful message.
        if noDS:
            logger.log("No data sources enabled for the airSuck client. Please enable at least one source in config.py by setting dump1090Enabled and/or aisEnabled to True.")
    
    except KeyboardInterrupt:
        logger.log("Keyboard interrupt.")
    
    except SystemExit:
        logger.log("System exit.")
    
    except:
        tb = traceback.format_exc()
        logger.log("Unhandled exception in airSuck client:\n%s" %tb)
    
    logger.log("Shutting down the airSuck client.")