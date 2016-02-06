#!/usr/bin/python

"""
aisConnector by ThreeSixes (https://github.com/ThreeSixes)

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

import time
import json
import datetime
import threading
import errno
import binascii
import hashlib
import traceback
import socket
from pprint import pprint
from libAirSuck import aisParse
from libAirSuck import asLog
from libAirSuck import handlerAIS

##########
# Config #
##########

# Set enqueue flag from the config file.
enqueueOn = config.aisConnSettings['aisEnqueue']

# Keep track of if we're running.
alive = True


####################
# dataSource class #
####################

class dataSource(threading.Thread):
	def __init__(self, myName, srcName, AISSrc, enqueue=True):
		"""
		Takes two required arguments and one optional: myName (client-identifying string), AISSrc (AISSrc source dictionary), optinally enqueue which should be True or False (by default it will enqueue data, otherwise will print it).
		A generic class that represents a given AIS data source
		"""
		
		logger.log("Init thread for %s." %myName)
		threading.Thread.__init__(self)
		
		# AIS Parser.
		self.__aisParser = aisParse()
		
		# Extend properties to be class-wide.
		self.__myName = myName
		self.__srcName = srcName
		self.__AISSrc = AISSrc
		self.__enqueue = enqueue
		self.__watchdogFail = False
		self.__backoff = 1.0
		
		# Our class-wide socket object.
		self.__aisSock = None
		
		# This keeps track of the number of seconds since our last connection.
		self.__lastEntry = 0
	
	# Make sure we don't have a dead connection.
	def __watchdog(self):
		"""
		Check this thread to see if it has not recieved data in the given thread timeout.
		"""
		
		try:
			# Check to see if our last entry was inside the timeout window.
			if self.__lastEntry >= self.__AISSrc['threadTimeout']:
				# Puke if we have been running for too long without data.
				raise IOError()
			else:
				# Restart our watchdog.
				self.__myWatchdog = threading.Timer(1.0, self.__watchdog)
				self.__myWatchdog.start()
		
		except Exception as e:
			# Set the watchdog failure flag.
			self.__watchdogFail = True
			
			# Stop the watchdog.
			self.__myWatchdog.cancel()
			
			# Prion the error message
			logger.log("%s watchdog: No data recieved in %s sec." %(self.__myName, self.__AISSrc['threadTimeout']))
			
			# Close the connection.
			self.__aisSock.close()
		
		# Increment our last entry.
		self.__lastEntry += 1
	
	# Handle backoff data.
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
	
	# Connect to our data source.
	def __connectSource(self):
		"""
		Connects to our host.
		"""
		
		# Create a new socket object
		self.__aisSock = socket.socket()
		
		# We're not connected so set the flag.
		notConnected = True
		
		# Keep trying to connect until it works.
		while notConnected:
			# Print message
			logger.log("%s connecting to %s:%s..." %(self.__myName, self.__AISSrc["host"], self.__AISSrc["port"]))
			
			# Attempt to connect.
			try:
				# Connect up
				self.__aisSock.connect((self.__AISSrc["host"], self.__AISSrc["port"]))
				logger.log("%s connected." %self.__myName)
				
				# We connected so now we can move on.
				notConnected = False
				
				# Reset the lastEntry counter.
				self.__lastEntry = 0
				
				# Reset the watchdog state.
				self.__watchdogFail = False
				
				# Reset the backoff value
				self.__handleBackoff(True)
			
			except socket.error, v:
				# Get the error number.
				errNum = v[0]
				
				# Connection refused.
				if errNum == errno.ECONNREFUSED:
					logger.log("%s %s:%s refused connection." %(self.__myName, self.__AISSrc["host"], self.__AISSrc["port"]))
				
				# Connection refused.
				elif errNum == errno.ECONNRESET:
					logger.log("%s %s:%s reset connection." %(self.__myName, self.__AISSrc["host"], self.__AISSrc["port"]))
				
				# Connection timeout.
				elif errNum == errno.ETIMEDOUT:
					logger.log("%s %s:%s connection timed out." %(self.__myName, self.__AISSrc["host"], self.__AISSrc["port"]))
				
				# Something else happened.
				else:
					logger.log("%s %s:%s unhandled socket error: %s" %(self.__myName, self.__AISSrc["host"], self.__AISSrc["port"], errNum))
				
				# In the event our connect fails, try again after the configured delay
				logger.log("%s sleeping %s sec." %(self.__myName, (self.__AISSrc["reconnectDelay"] * self.__backoff)))
				time.sleep(self.__AISSrc["reconnectDelay"] * self.__backoff)
				
				# Handle backoff.
				self.__handleBackoff()
				
			except Exception as e:
				# Dafuhq happened!?
				tb = traceback.format_exc()
				logger.log("%s went boom connecting.\n%s" %(self.__myName, tb))
				
				# In the event our connect fails, try again after the configured delay
				logger.log("%s sleeping %s sec." %(self.__myName, (self.__AISSrc["reconnectDelay"] * self.__backoff)))
				time.sleep(self.__AISSrc["reconnectDelay"] * self.__backoff)
				
				# Handle backoff.
				self.__handleBackoff()
		
		# Set 1 second timeout for blocking operations.
		self.__aisSock.settimeout(1.0)
		
		# The watchdog should be run every second.
		self.__lastEntry = 0
		self.__myWatchdog = threading.Timer(1.0, self.__watchdog)
		self.__myWatchdog.start()
	
	# Disconnect the source and re-create the socket object.
	def __disconnectSource(self):
		"""
		Disconnect from our host.
		"""
		
		logger.log("%s disconnecting." %self.__myName)
		
		try:	
			# Close the connection.
			self.__aisSock.close()
		except:
			tb = traceback.format_exc()
			logger.log("%s threw exception disconnecting.\n%s" %(self.__myName, tb))
		
		# Reset the lastEntry counter.
		self.__lastEntry = 0
		
		try:
			# Stop the watchdog.
			self.__myWatchdog.cancel()
		except:
			# Don't do anything.
			None
	
	# Strip metachars.
	def __metaStrip(self, subject):
		"""
		Strip metacharacters from a string.
		
		Returns stripped string.
		"""
		
		# Take any metachars off the end of the string.
		subject = subject.lstrip()
		return subject.rstrip()
	
	
	# Get one line from TCP output, from:
	# http://synack.me/blog/using-python-tcp-sockets
	def __readLines(self, sock, recvBuffer = 4096, delim = '\n'):
		"""
		Read a TCP stream, looking for individual lines of text delimited by \n.
		"""
		buffer = ''
		data = True
		while data:
			try:
				data = sock.recv(recvBuffer)
				buffer += data
				
				while buffer.find(delim) != -1:	
					line, buffer = buffer.split('\n', 1)
					# Debugging...
					yield line
			
			except socket.timeout:
				continue
			
			except Exception as e:
				# If we had a disconnect event drop out of the loop.
				if 'errno' in e:
					if e.errno == 9:
						logger.log("%s disconnected." %self.__myName)
						data = False
						raise e
					
					else:
						tb = traceback.format_exc()
						logger.log("%s choked reading buffer.\n%s" %(self.__myName, tb))
						data = False
						line = ""
				else:
					tb = traceback.format_exc()
					logger.log("%s choked reading buffer.\n%s" %(self.__myName, tb))
					data = False
					line = ""
			
			# See if our watchdog is working.
			if self.__watchdogFail:
				logger.log("%s watchdog terminating readLines." %self.__myName)
				data = False
				break
	
	def __handleLine(self, thisLine):
		"""
		Handle a line of text representing a single AIS sentence.
		"""
		# Remove whitespace.
		thisLine = self.__metaStrip(thisLine)
		
		# Default frame CRC good flag.
		frameCRCGood = False
		
		try:
			# See if we got a valid CRC for this frame.
			frameCRCGood = self.__aisParser.checkFrameCRC(thisLine)
		except:
			tb = traceback.format_exc()
			logger.log("%s choked verifying frame CRC.\n%s" %(self.__myName, tb))
		
		# If we have a good CRC checksum keep moving.
		if frameCRCGood:
			# Date time string
			dtsStr = str(datetime.datetime.utcnow())
			
			# Make sure we didn't trim microseconds because if we did the mongoDump script gets pissed off.
			if (len(dtsStr) == 19):
				dtsStr = dtsStr + ".000000"
			
			# Set this entry up with some initial data.
			thisEntry = {'entryPoint': 'aisConnector', 'dataOrigin': 'aisConn', 'type': 'airAIS', 'dts': dtsStr, 'src': self.__srcName, 'clientName': self.__myName, 'data': thisLine, 'isFrag': False, 'isAssembled': False}
			
			# If we have position data for this source...
			if 'srcPos' in self.__AISSrc:
				# Create a blank dictionary to hold position data.
				posData = {}
				
				try:
					# If we have a list...
					if type(self.__AISSrc['srcPos']) == list:
					
						# If our list has two elements...
						if len(self.__AISSrc['srcPos']) == 3:
						
							# If we have good position data add it to any outgoing data.
							posData.update({"srcLat": self.__AISSrc['srcPos'][0], "srcLon": self.__AISSrc['srcPos'][1], "srcPosMeta": self.__AISSrc['srcPos'][2]})
					
					# Add position data to our entry.
					thisEntry.update(posData)
				
				except:
					tb = traceback.format_exc()
					logger.log("%s invlaid position data in config.py:\n%s" %(self.__myName, tb))
			
			try:
				# Decapsulate the AIS payload and get relevant data.
				thisEntry.update(self.__aisParser.nmeaDecapsulate(thisLine))
			except:
				tb = traceback.format_exc()
				logger.log("%s choked decapsulating frame %s\n%s" %(self.__myName, thisLine, tb))
			
			try:
				# Attempt to handle the frames.
				if hAIS.handleAISDict(thisEntry):
					self.__lastEntry = 0
			
			except:
				tb = traceback.format_exc()
				logger.log("%s error handling AIS frame:\n%s" %(self.__myName, tb))	
	
	def run(self):
		"""
		dataSource worker.
		"""
		
		logger.log("%s running." %self.__myName)
		
		# Do stuff.
		while (True):
			# Attempt to connect.
			self.__connectSource()
			
			# Try to read a lone from our established socket.
			try:				
				# Get lines of data from dump1090
				for thisLine in self.__readLines(self.__aisSock):
					# Do our thing.
					self.__handleLine(thisLine)
				
				# Close the connection.
				self.__disconnectSource()
				
			# Try to catch what blew up. This needs to be significantly improved and should result in a delay and another connection attempt.
			except Exception as e:
				if 'errno' in e:
					if e.errno == 9:
						continue
					else:
						# Dafuhq happened!?
						tb = traceback.format_exc()
						logger.log("%s went boom processing data.\n%s" %(self.__myName, tb))
						
						# Close the connection.
						self.__disconnectSource()
				else:
					# Dafuhq happened!?
					tb = traceback.format_exc()
					logger.log("%s went boom processing data.\n%s" %(self.__myName, tb))
					
					# Close the connection.
					self.__disconnectSource()

#######################
# Main execution body #
#######################

# If I've been called for execution...
if __name__ == "__main__":
	
	# Set up the logger.
	logger = asLog(config.aisConnSettings['logMode'])
	
	# If the AIS engine is enabled in config...
	if config.aisConnSettings['enabled'] == True:
		# ... and go.
		logger.log("AIS connector starting...")
		
		# Set up our AIS handler object.
		hAIS = handlerAIS(config.aisConnSettings['logMode'], enqueueOn)
		hAIS.setDebug(config.aisConnSettings['debug'])
		
		# Threading setup
		threadLock = threading.Lock()
		threadList = []
		
		# Spin up our client threads.
		for thisName, connData in config.aisConnSettings['connClientList'].iteritems():
			logger.log("Spinning up thread for %s" %thisName)
			client = dataSource(thisName, config.aisConnSettings['myName'], connData, enqueueOn)
			client.daemon = True
			client.start()
			threadList.append(client)
		
		# Fix bug that prevents keyboard interrupt from killing dump1090Connector.py
		while True: time.sleep(10)
		
		# Shut down
		for t in threadList:
			t.join()
	else:
		logger.log("AIS connector not enabled in config.")
