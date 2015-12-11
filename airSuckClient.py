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
import Queue
from libAirSuck import asLog
from subprocess import Popen, PIPE, STDOUT
from pprint import pprint


##########################
# airSuckConnector class #
##########################

class airSuckComms():
    def __init__(self):
        """
        airSuckComms handles connecting to the airSuck server to submit recieved frames.
        """
        
        logger.log("Init airSuckComms...")
        
        # Setup watchdogs.
        self.__myWatchdogRX = None
        self.__myWatchdogTX = None
        self.__lastKeepalive = 0
        self.__maxTime = 2.0 * asConfig['keepaliveInterval']
        self.__backoff = 1.0
        self.__keepaliveJSON = "{\"keepalive\": \"abcdef\"}\n"
        
        # Networking.
        self.__serverSock = None
        self.__serverConnected = False
        self.__rxBuffSz = 128
        
        # Should we keep going?
        self.__keepRunning = True
    
    def __watchdogRX(self):
        """
        Check to make sure dump1090 is still giving us data. If not this should be called to stop it.
        """
        
        try:
            # Check to see if we got data from dump1090.
            if self.__lastKeepalive >= self.__maxTime:
                
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
            logger.log("airSuck comms RX watchdog: No keepalive for %s sec." %self.__maxTime)
            
            # Stop the watchdogs.
            self.__myWatchdogRX.cancel()
            self.__myWatchdogTX.cancel()
            self.__disconnectSouce()
        
        except:
            tb = traceback.format_exc()
            logger.log("airSuck comms RX watchdog threw exception:\n%s" %tb)
            
            # Disconnect.
            self.__disconnectSouce()
    
    def __watchdogTX(self):
        """
        Send a keepalive frame to the server so it knows we're still connected.
        """
        
        try:
            # Send the keepalive.
            
            # Restart our watchdog.
            self.__myWatchdogTX = threading.Timer(asConfig['keepaliveInterval'], self.__watchdogTX)
            self.__myWatchdogTX.start()
            
            if self.__serverConnected:
                # Send the ping.
                self.__serverSock.send(self.__keepaliveJSON)
        
        except KeyboardInterrupt:
            # Pass the keyboard interrupt exception up the stack.
            raise KeyboardInterrupt
        
        except:
            tb = traceback.format_exc()
            logger.log("airSuck comms TX watchdog threw exception:\n%s" %tb)
            
            # Disconnect.
            self.__disconnectSouce()
    
    def __rxWatcher(self):
        """
        Handle data recieved from our connected socket.
        """
        
        # Empty buffer string.
        buff = ""
        
        try:
            
            # While we're connected
            while True:
                # Get data.
                buff = buff + self.__serverSock.recv(self.__rxBuffSz)
                
                # If we have a newline check of our string and clear the buffer.
                if buff.find("\n"):
                    # If we got our JSON sentence reset the counter.
                    if buff == self.__keepaliveJSON:
                        self.__lastKeepalive = 0
                    
                    # Reset data stuff.
                    buff = ""
                    
                    self.__serverSock.send("")
        
        except socket.timeout:
            # If we time out do nothing. This is intentional.
            None
        
        except Exception as e:
            if 'errno' in e:
                # If something goes wrong...
                if e.errno == 32:
                    # We expect this to break this way sometimes.
                    raise IOError
                
                else:
                    tb = traceback.format_exc()
                    logger.log("Exception in airSuck comms rxWatcher:\n%s" %tb)
    
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
    
    def __connectServer(self):
        """
        Connects to our host.
        """
        
        # Create a new socket object.
        self.__serverSock = socket.socket()
        
        # We're not connected so set the flag.
        notConnected = True
        
        # Keep trying to connect until it works.
        while notConnected:
            # Print message
            logger.log("airSuck comms connecting to %s:%s." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
            
            # Attempt to connect.
            try:
                # Connect up
                self.__serverSock.connect((asConfig['connSrvHost'], asConfig['connSrvPort']))
                logger.log("airSuck comms connected.")
                
                # We're connected now.
                self.__serverConnected = True
                notConnected = False
                
                # Reset the last keepalive counter.
                self.__lastKeepalive = 0
                
                # Reset the watchdog state.
                self.__watchdogFail = False
                
                # Reset the backoff value
                self.__handleBackoff(True)
                
                # Set 1 second timeout for blocking operations.
                self.__serverSock.settimeout(1.0)
                
                # The TX and RX watchdogs should be run every second.
                self.__lastKeepalive = 0
                
                self.__myTXWatchdog = threading.Timer(1.0, self.__watchdogTX)
                self.__myTXWatchdog.start()
                
                self.__myRXWatchdog = threading.Timer(1.0, self.__watchdogRX)
                self.__myRXWatchdog.start()
                
                # RX watcher...
                rxListener = threading.Thread(target=self.__rxWatcher)
                rxListener.daemon = True
                rxListener.start()
                
                # Just loop until death or taxes.
                while self.__serverConnected:
                    time.sleep(0.1)
                
            except KeyboardInterrupt:
                # Pass it up the stack.
                raise KeyboardInterrupt
            
            except Exception as e:
                if 'errno' in e:
                    # If we weren't able to connect, dump a message
                    if e.errno == errno.ECONNREFUSED:
                        #Print some messages
                        logger.log("airSuck comms failed to connect to %s:%s." %(asConfig['connSrvHost'], asConfig['connSrvPort']))
                    
                    else:
                        # Dafuhq happened!?
                        tb = traceback.format_exc()
                        logger.log("airSuck comms went boom connecting:\n%s" %tb)
                
                # Set backoff delay.
                boDelay = asConfig['reconnectDelay'] * self.__backoff
                
                # In the event our connect fails, try again after the configured delay
                logger.log("airSuck comms sleeping %s sec." %boDelay)
                time.sleep(boDelay)
                
                # Handle backoff.
                self.__handleBackoff()
    
    # Disconnect the source and re-create the socket object.
    def __disconnectSouce(self):
        """
        Disconnect from our host.
        """
        
        logger.log("airSuck comms disconnecting.")
        
        # Clear the server connected flag.
        self.__serverConnected = False
        
        try:
            # Close the connection.
            self.__serverSock.close()
            
        except:
            tb = traceback.format_exc()
            logger.log("airSuck comms threw exception disconnecting.\n%s" %tb)
        
        # Reset the last keepalive counter.
        self.__lastKeepalive = 0
            
        try:
            # Stop the watchdogs.
            self.__myTXWatchdog.cancel()
            self.__myRXWatchdog.cancel()
            
        except:
            # Don't do anything.
            None
    
    def __send(self, data):
        """
        Sends specified data to the airSuck destination server.
        """
        
        # If we think we're connected try to send the infos. If not, do nothing.
        if self.__serverConnected:
            try:
                self.__serverSock.send("%s\n" %data)
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck comms send exception:\n%s" %tb)
                
                # Disconnect.
                self.__disconnectSource()
    
    def __queueWorker(self):
        """
        Sends data on the queue to the remote server.
        """
        
        while True:
            try:
                # Grab the JSON put on the queue
                someJSON = clientQ.get()
                
                # And then send it over the network.
                self.__send(someJSON)
            
            except:
                tb = traceback.format_exc()
                logger.log("airSuck comms caught exception reading from queue:\n%s" %tb)
    
    def __worker(self):
        """
        Principal workhorse of the class.
        """
        
        try:
            queueThread = threading.Thread(target=self.__queueWorker)
            queueThread.daemon = True
            queueThread.start()
            
            # While we 'want' to keep running...
            while self.__keepRunning:
                self.__connectServer()
        
        except KeyboardInterrupt:
            # Pass it on...
            raise KeyboardInterrupt
        
        except:
            tb = traceback.format_exc()
            print("airSuckComms worker blew up:\n%s" %tb)
            
            self.__disconnectSouce()
    
    def run(self):
        """
        Run the airSuck client.
        """
        
        logger.log("Starting airSuck comms worker.")
        
        try:
            self.__worker()
        
        except KeyboardInterrupt:
            # Pass the keyboard interrupt up the chain to our main execution
            raise KeyboardInterrupt


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
        
        # Keepalive sentence.
        self.__keepAliveDat = "{\"ping\": \"abcdef\"}\n"
    
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
        adsbDict = {"dataOrigin": "dump1090Clt", "dts": dtsStr, "type": "airSSR", "data": adsb.replace("\n", "")}
        
        # JSONify the dictionary.
        adsbJSON = json.dumps(adsbDict)
        
        # Log for now.
        logger.log("Send -> %s" %adsbJSON)
        
        try:
            # Put it on the queue.
            clientQ.put(adsbJSON)
        except:
            tb = traceback.format_exc()
            logger.log("dump1090 exception putting data on queue:\n%s" %tb)
    
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
            
        except IOError:
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
                    stdErrListener.daemon = True
                    stdOutListener.daemon = True
                    stdErrListener.start()
                    stdOutListener.start()
                    
                    # Go into a loop while our threads run.
                    while True:
                        time.sleep(10)
            
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
                
                # Attempt to kill dump1090
                self.killMe()
                
                # Try to stop the watchdog.
                if self.__myWatchdog1090 is not None:
                    self.__myWatchdog1090.cancel()
            
            except:
                # Something else unknown happened.
                tb = traceback.format_exc()
                logger.log("dump1090 worker threw exception:\n%s" %tb)
                
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
    
    # Set up our global objects.
    instance1090 = dump1090Handler()
    instanceAS = airSuckComms()
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
        #thread1090 = threading.Thread(target=instance1090.run())
        threadComms = threading.Thread(target=instanceAS.run())
        #thread1090.daemon = True
        threadComms.daemon = True
        threadComms.start()
        #thread1090.start()
        
    except KeyboardInterrupt:
        logger.log("Keyboard interrupt.")
        
    except:
        tb = traceback.format_exc()
        logger.log("Unhandled exception in airSuck client:\n%s" %tb)
    
    # If we didn't have a configured data source dump a helpful message.
    if noDS:
        logger.log("No data sources enabled for the airSuck client. Please enable at least one source in config.py by setting dump1090Enabled and/or aisEnabled to True.")
    
    logger.log("Shutting down the airSuck client.")
    