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

import datetime
import json
import re
import socket
import time
import threading
import traceback
from libAirSuck import asLog
from subprocess import Popen, PIPE, STDOUT
from pprint import pprint


##########################
# airSuckConnector class #
##########################

class airSuckClient():
    def __init__(self):
        """
        airSuckClient handles connecting to the airSuck server to submit recieved frames.
        """
        
        logger.log("Init airSuckClient...")
        
        # Setup watchdogs.
        self.__myWatchdogRX = None
        self.__myWatchdogTX = None
        self.__lastKeepalive = 0
        self.__maxTime = 2.0 * asConfig['keepaliveInterval']
    
    def __watchdogRX(self):
        """
        Check to make sure dump1090 is still giving us data. If not this should be called to stop it.
        """
        
        try:
            # Check to see if we got data from dump1090.
            if self.__lastRX >= self.__maxTime:
                
                # Raise an exception.
                raise IOError()
            
            else:        
                # Increment our last entry.
                self.__lastKeepalive += 1
                
                # Restart our watchdog.
                self.__myWatchdogRX = threading.Timer(1.0, self.__watchdogRX)
                self.__myWatchdogRX.start()
            
        except IOError:
            # Print the error message
            logger.log("airSuck RX watchdog: No keepalive %s sec." %self.__maxTime)
            # Stop the watchdog.
            self.__myWatchdogRX.cancel()
        
        except:
            tb = traceback.format_exc()
            logger.log("airSuck RX watchdog threw exception:\n%s" %tb)
            
            # Stop the watchdog.
            self.__myWatchdogRX.cancel()
    
    def __watchdogTX(self):
        """
        Send a keepalive frame to the server so it knows we're still connected.
        """
        
        try:
            # Restart our watchdog.
            self.__myWatchdogTX = threading.Timer(asConfig['keepaliveInterval'], self.__watchdogTX)
            self.__myWatchdogTX.start()
        
        except:
            tb = traceback.format_exc()
            logger.log("airSuck client RX watchdog threw exception:\n%s" %tb)
            
            # Stop the watchdog.
            self.__myWatchdogTX.cancel()
    
    def __handleBackoff(self, reset=False):
        """
        Handle the backoff algorithm for reconnect delay. Accepts one optional argument, reset which is a boolean value. When reset is true, the backoff value is set back to 1. Returns no data.
        """
        
        # If we're resetting the backoff set it to 1.0.
        if reset:
            self.__backoff = 1.0
        else:
            # backoff ^ 2 for each iteration, ending at 4.0.
            if self.__backoff == 1.0:
                self.__backoff = 2.0
            
            elif self.__backoff == 2.0:
                self.__backoff = 4.0
        
        return
    
    def __worker(self):
        """
        Principal workhorse of the class.
        """
        
        logger.log("Starting airSuck client worker.")
    
    def run(self):
        """
        Run the airSuck client.
        """
        
        # Start the worker.
        self.__worker()


#########################
# dump1090Handler class #
#########################

class dump1090Handler():
    
    # Class consructor
    def __init__(self):
        """
        dump1090Handler handles the dump1090 executable to grab ADS-B, and makes sure it's running. If the process jams it's restarted.
        """
        # Init message.
        logger.log("Init dump1090Handler...")
        
        # Build the command we need to run dump1090 in a fashion Popen can understand.
        self.popenCmd = [asConfig['dump1090Path']] + asConfig['dump1090Args'].split(" ")
        
        # Pre-compiled regex used to verify dump1090 ADS-B data.
        self.__re1090 = re.compile("[@*]([a-fA-F0-9])+;")
        
        # Watchdog setup.
        self.__myWatchdog1090 = None
        self.__lastADSB = 0
        self.__watchdog1090Restart = False
        
        # Backoff counter
        self.__backoff1090 = 1.0
    
    # Make sure we have data. If we don't throw an exception.
    def __watchdog1090(self):
        """
        Check to make sure dump1090 is still giving us data. If not this should be called to stop it.
        """
        # Set flag indicating whether we restarted because of the watchdog.
        self.__watchdog1090Restart = False
        
        try:
            # Check to see if we got data from dump1090.
            if self.__lastADSB >= asConfig['dump1090Timeout']:
                # Set watchdog restart flag.
                self.__watchdog1090Restart = True
                
                # Kill dump1090
                self.__proc1090.kill()
                
                # Raise an exception.
                raise IOError()
            
            else:        
                # Increment our last entry.
                self.__lastADSB += 1
                
                # Restart our watchdog.
                self.__myWatchdog1090 = threading.Timer(1.0, self.__watchdog1090)
                self.__myWatchdog1090.start()
            
        except IOError:
            # Print the error message
            logger.log("dump1090 watchdog: No data from dump1090 in %s sec." %asConfig['dump1090Timeout'])
            # Stop the watchdog.
            self.__myWatchdog1090.cancel()
        
        except:
            tb = traceback.format_exc()
            logger.log("dump1090 watchdog threw exception:\n%s" %tb)
            
            # Stop the watchdog.
            self.__myWatchdog1090.cancel()
    
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

    def __verifyADSB(self, line):
        """
        Verifies the formattting of the potential ADS-B frame. If the incoming data doesn't match the regex the method returns False. If it matches it will return True.
        """
        
        # Assume we don't have good data by default.
        retVal = False
        
        # If we get a match...
        if self.__re1090.match(line) is not None:
            retVal = True
        
        # And return...
        return retVal
    
    def __handleADSB(self, adsb):
        """
        Place holder method that should result in the data being JSON wrapped and sent over the network.
        """
        
        # Reset watchdog value.
        self.__lastADSB = 0
        
        # Build a dictionary with minimal information to send.
        dtsStr = str(datetime.datetime.utcnow())
        adsbDict = {'dts': dtsStr, "type": "airSSR", "data": adsb.replace("\n", "")}
        
        # JSONify the dictionary.
        adsbJSON = json.dumps(adsbDict)
        
        # Log for now.
        logger.log("Send -> %s" %adsbJSON)

    def killMe(self):
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
    
    def __stdoutWorker(self):
        """
        Handle STDOUT output from dump1090.
        """
        
        try:
            # While we're still running...
            while self.__proc1090.poll() is None:
                
                # Grab the current line from STDOUT.
                output = self.__proc1090.stdout.readline()
                
                # If it seems to be valid ADS-B then use it.
                if self.__verifyADSB(output):
                    self.__handleADSB(output)
            
            # Get any 'straggling' output.
            output = self.__proc1090.communicate()[0]
            
            # If it seems to be valid ADS-B then use it.
            if self.__verifyADSB(output):
                self.__handleADSB(output)
        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except ValueError:
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
                
                # If there's something on the line print it.
                if output.strip() != "":
                    logger.log("dump1090: %s" %output)
            
            # See if there's any data that wasn't picked up by our loop and print it, too.
            output = self.__proc1090.communicate()[1].replace("\n", "")
            
            if output.strip() != "":
                logger.log("dump1090: %s" %output)
        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        
        except ValueError:
            # Just die nicely.
            None
    
    def __worker(self):
        """
        The main worker method that spins up the dump1090 executable and takes data from stdout.
        """
        
        # We want to keep going.
        keepRunning = True
        
        # Keep running and restarting dump1090 unless the program is killed.
        while keepRunning:
            try:
                # Start dump1090.
                self.__proc1090 = Popen(self.popenCmd, stdout=PIPE, stderr=PIPE)
                
                if self.__proc1090 is not None:
                    logger.log("dump1090 started with PID %s." %self.__proc1090.pid)
                    
                    # Reset the backoff since we manged to start.
                    self.__handleBackoff1090(True)
                    
                    # Start the watchdog after resetting lastADSB.
                    self.__lastADSB = 0
                    self.__myWatchdog1090 = threading.Timer(1.0, self.__watchdog1090)
                    self.__myWatchdog1090.start()
                    
                    # Set up some threads to listen to the dump1090 output.
                    stdErrListener = threading.Thread(target=self.__stderrWorker)
                    stdOutListener = threading.Thread(target=self.__stdoutWorker)
                    stdErrListener.start()
                    stdOutListener.start()
                    stdErrListener.join()
                    stdOutListener.join()
                
            except KeyboardInterrupt:
                # We don't want to keep running since we were killed.
                keepRunning = False
               
                # Pass the exception up the chain to our runner.
                raise KeyboardInterrupt
            
            except OSError:
                # Dump an error since the OS reported dump1090 can't run.
                logger.log("Unable to start dump1090. Please ensure dump1090 is at %s." %asConfig['dump1090Path'])
                
                # Flag the thread for death.
                keepRunning = False
            
            except:
                # Something else unknown happened.
                tb = traceback.format_exc()
                logger.log("dump1090 worker threw exception:\n%s" %tb)
            
            finally:
                # Attempt to kill dump1090
                self.killMe()
                
                # Try to stop the watchdog.
                if self.__myWatchdog1090 is not None:
                    self.__myWatchdog1090.cancel()
            
            # If we intend to restart dump1090 and we didn't kill dump1090 because of the watchdog...
            if keepRunning and (not self.__watchdog1090Restart):
                # Handle backoff algorithm before it restarts.
                boDly = self.__backoff1090 * asConfig['dump1090Delay']
                logger.log("dump1090 sleeping %s sec before restart." %boDly)
                time.sleep(boDly)
                
                # Run the backoff handler.
                self.__handleBackoff1090()
    
    def run(self):
        logger.log("Starting dump1090 worker.")
        
        try:
            self.__worker()
        
        except KeyboardInterrupt:
            # Pass the keyboard interrupt up the chain to our main execution
            raise KeyboardInterrupt


#######################
# Main execution body #
#######################

if __name__ == "__main__":
    # Get the config.
    asConfig = config.airSuckClientSettings
    
    # Set up our global logger.
    logger = asLog(asConfig['logMode'])
    
    # Log startup message.
    logger.log("Starting the airSuck client...")
    
    # Set up our dump1090 handler instance.
    instance1090 = dump1090Handler()
    instanceAS = airSuckClient()
    
    # We'll store our threads here:
    threadList = []
    
    # Do we have at least one data source configured?
    noDS = True
    
    # Master connected flag...
    serverConnected = False
    
    try:
        # Start the main connector.
        threadList.append(threading.Thread(target=instanceAS.run()))
        
        # If we are configured to run the dump1090 client add it to our thread list.
        if asConfig['dump1090Enabled']:
            # Set the data source config flag.
            noDS = False
            
            # Add the dump1090 thread.
            threadList.append(threading.Thread(target=instance1090.run()))
        
        # If we are configured to run the dump1090 client add it to our thread list.
        if asConfig['aisEnabled']:
            # Set the data source config flag.
            noDS = False
            
            # Add the AIS thread.
            #threadList.append(threading.Thread(target=instance1090.run()))
    
    except KeyboardInterrupt:
        logger.log("Keyboard interrupt.")
    
    # If we're configured to run at least one client start our threads.
    if len(threadList) > 0:
        try:
            # Start each thread.
            for thisThread in threadList:
                thisThread.start()
                
            # Join each thread.
            for thisThread in threadList:
                thisThread.join()
        
        except:
            tb = traceback.format_exc()
            logger.log("Unhandled exception in airSuck client:\n%s" %tb)
    
    # If we didn't have a configured data source dump a helpful message.
    if noDS:
        logger.log("No data sources enabled for the airSuck client. Please enable at least one source in config.py by setting dump1090Enabled and/or aisEnabled to True.")
    
    logger.log("Shutting down the airSuck client.")
    