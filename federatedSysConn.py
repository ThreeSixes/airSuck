#!/usr/bin/python

"""
federatedSysConn by ThreeSixes (https://github.com/ThreeSixes)

Federated system connector - connects airSuck instances together by retransmitting data that's placed on the connector queue.

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSuck).
"""

###########
# Imports #
###########


try:
    import config
except:
    raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

import time
import threading
import socket
import redis
import traceback
from libAirSuck import asLog
from pprint import pprint


####################################
# Federated system connector class #
####################################

class fedSysConn():
    def __init__(self, logger, config):
        """
        Federated system connector class. This handles transferring data between airSuck instances.
        """
        
        logger.log("Init fedreated system connector...")
        
        # Set up the logger.
        self.__logger = logger
        
        # Debuging off by default.
        self.__debugOn = False
        
        # Local reference to config data.
        self.__config = config
        
        # Should we keep runing?
        self.__keepRunning = True
        
        # Class-wide list of connections.
        self.__conns = []
        self.__connAddrs = {}
        
        # Keepalive stuff
        self.__keepaliveJSON = "{\"keepalive\": \"abcdef\"}"
        
        # Buffer size settings.
        self.__buffSz = 4096 # 4K
        
        # Set the ping timer.
        self.__pingTimer = 0
    
    def __sendKeepalive(self):
        """
        send keeaplive.
        """
        
        self.__logger.log("I'd be pinging now.")
    
    def __watchdog(self):
        """
        Watchdog - 1 second checks for timeouts.
        """
        
        try:
            self.__logger.log("Watch, dawg!")
            
            # If we want to keep running...
            if self.__keepRunning:
                # Do the watchdog work here...
                pass
                
                # Restart our watchdog.
                self.__fscWatchdog = threading.Timer(1.0, self.__watchdog)
                self.__fscWatchdog.start()
            
            # If we want to die and are debugging...
            elif self.__debugOn:
                self.__logger.log("Dropping out of watchdog.")
        
        except Exception as e:
            # Flag the thread to shut down.
            self.__keepRunning = False
            
            raise e
        
        # If we are configured to listen for connecitons..
        if self.__config.federatedSysConn['listen']:
            # If we've reached the time to ping, do the ping.
            if self.__pingTimer >= self.__config.federatedSysConn['keepalive']:
                # Send a keepalive.
                self.__sendKeepalive()
                
                # Reset ping timer.
                self.__pingTimer = 0
            
            # Roll our timeru.
            self.__pingTimer += 1
    
    def __worker(self):
        """
        Class worker.
        """
        
        # Not connected.
        notConnected = True
        
        # Start watchdog.
        self.__watchdog()
        
        # While we want to stay running...
        while self.__keepRunning:
            # If we are configured to listen and don't have a running listener.
            if self.__config.federatedSysConn['listen'] and notConnected:
                try:
                    self.__logger.log("Federated system connector listening on %s:%s..." %(self.__config.federatedSysConn['listenHost'], self.__config.federatedSysConn['listenPort']))
                    
                    # Build our TCP socket to recieve the magical happy JSON data we need!
                    self.__listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.__listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.__listenSock.bind((self.__config.federatedSysConn['listenHost'], self.__config.federatedSysConn['listenPort']))
                    self.__listenSock.listen(10)
                    
                    # Add our listener socket to our connection list.
                    self.__conns.append(self.__listenSock)
                    
                    # We're connected.
                    notConnected = False
                
                except:
                    tb = traceback.format_exc()
                    self.__logger.log("Exception while trying to open incoming socket:\n%s" %tb)
                    
                    # Flag the thread to shut down.
                    self.__keepRunning = False
                
                try:
                    self.__logger.log("Doing the thigns...")
                
                except (KeyboardInterrupt, SystemExit) as e:
                    
                    self.__logger.log("Shutting worker down...")
                    
                    # Flag the worker to let it know we want to die.
                    self.__keepRunning = False
                    
                    # Pass the reason for death up the stack.
                    raise e
                
                except Exception as e:
                    # If we're debugging...
                    if self.__debugOn:
                        # Do the traceback thing.
                        tb = traceback.format_exc()
                        self.__logger.log("Unhandled exception in worker:\n%s" %tb)
                    
                    # Flag the worker to let it know we want to die.
                    self.__keepRunning = False
                    
                    raise e
            
            try:
                # Wait before continuing..
                time.sleep(0.1)
            
            except Exception as e:
                # Flag the thread to shut down.
                self.__keepRunning = False
                
                raise e
        
        # If we're debugging...
        if self.__debugOn:
            self.__logger.log("Leaving worker.")
    
    def setDebug(self, debug):
        """
        Turn debugging on or off. Accepts one boolean argument. True for debugging on, false for debuggin off.
        """
        
        self.__debugOn = debug
    
    def run(self):
        """
        Starts the principal worker.
        """
        
        try:
            # Start the worker.
            self.__worker()
        
        except Exception as e:
            self.__keepRunning = False
            
            # Pass the exception up the stack whatever it may be.
            raise e
        
        finally:
            # Stop the watcher.
            try:
                # Try to shut it down.
                self.__fscWatchdog.cancel()
            
            except:
                # Don't do anything.
                pass
            
            try:
                # Stop istening.
                self.__listenSock.close()
            
            except:
                pass


#######################
# Main execution body #
#######################

# If this isn't being executed directly...
if __name__ == "__main__":
    
    # Set up the logger.
    logger = asLog(config.federatedSysConn['logMode'])
    
    # Log our startup.
    logger.log("Starting the airSuck federated system connector...")
    
    # If we're debugging...
    if config.federatedSysConn['debug']:
        pprint(config.federatedSysConn)
    
    # If the dump1090 connector should be run
    if config.federatedSysConn['enabled']:
        
        try:
            # Create our federated system connector object.
            fsc = fedSysConn(logger, config)
            
            # Set debugging...
            fsc.setDebug(config.federatedSysConn['debug'])
            
            # Spin up the thread for the connector.
            fscWorker = threading.Thread(target=fsc.run)
            fscWorker.daemon = True
            fscWorker.start()
            
            while True:
                # Loop until exception. This ensures when a keyboard interrupt happens we catch it.
                time.sleep(10)
        
        except SystemExit:
            logger.log("Caught system shutdown.")
        
        except KeyboardInterrupt:
            logger.log("Caught keyboard interrupt. Shutting down.")
        
        except:
            tb = traceback.format_exc()
            logger.log("Caught exception:\n%s" %tb)
    
    else:
        logger.log("The airSuck server shouldn't be run according to the configuration.")
    
    logger.log("Federated system connector exiting.")
    