#!/usr/bin/python

"""
dump1090Connector by ThreeSixes (https://github.com/ThreeSixes)

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
import traceback
import socket
from pprint import pprint
from libAirSuck import ssrParse
from libAirSuck import asLog
from libAirSuck import handler1090

##########
# Config #
##########

#dump1090 sources
dump1909Srcs = config.d1090ConnSettings['connClientList']
alive = True

####################
# dataSource class #
####################

class dataSource(threading.Thread):
	""" dataSource class
	
	Takes four arguments: rQ (strictRedis object), myName (client-identifying string), dump1090Src (dump1090 source dictionary), rQinfo (Redis queue config data).
	
	A generic class that represents a given dump1090 data source
	"""
	
	def __init__(self, myName, dump1090Src):
		logger.log("Init thread for %s." %myName)
		threading.Thread.__init__(self)
		
		# Extend properties to be class-wide.
		self.myName = myName
		self.dump1090Src = dump1090Src
		self.__ssrParser = ssrParse()
		self.__watchdogFail = False
		self.__backoff = 1.0
		
		# Our class-wide socket object.
		self.__dump1090Sock = None
		
		# This keeps track of the number of seconds since our last connection.
		self.__lastEntry = 0
	
	# Make sure we have data. If we don't throw an exception.
	def __watchdog(self):
		"""
		Check this thread to see if it has not recieved data in the given thread timeout.
		"""
		
		try:
			# Check to see if our last entry was inside the timeout window.
			if self.__lastEntry >= self.dump1090Src['threadTimeout']:
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
			logger.log("%s watchdog: No data recieved in %s sec." %(self.myName, str(self.dump1090Src['threadTimeout'])))
			
			# Close the connection.
			self.__dump1090Sock.close()
		
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
		
		# Create a new socket object.
		self.__dump1090Sock = socket.socket()
		
		# We're not connected so set the flag.
		notConnected = True
		
		# Keep trying to connect until it works.
		while notConnected:
			# Print message
			logger.log("%s connecting to %s:%s." %(self.myName, self.dump1090Src["host"], self.dump1090Src["port"]))
			
			# Attempt to connect.
			try:
				# Connect up
				self.__dump1090Sock.connect((self.dump1090Src["host"], self.dump1090Src["port"]))
				logger.log("%s connected." %self.myName)
				
				# We connected so now we can move on.
				notConnected = False
				
				# Reset the lastEntry counter.
				self.__lastEntry = 0
				
				# Reset the watchdog state.
				self.__watchdogFail = False
				
				# Reset the backoff value
				self.__handleBackoff(True)
				
			except Exception as e:
				if type(e) == socket.error:
					# If we weren't able to connect, dump a message
					if e.errno == errno.ECONNREFUSED:
						#Print some messages
						logger.log("%s refused connection to %s:%s." %(self.myName, self.dump1090Src["host"], self.dump1090Src["port"]))
					
					elif e.errno == errno.ECONNRESET:
						#Print some messages
						logger.log("%s reset connection to %s:%s." %(self.myName, self.dump1090Src["host"], self.dump1090Src["port"]))
					
					else:
						# Dafuhq happened!?
						tb = traceback.format_exc()
						logger.log("%s socket error.\n%s" %(self.myName, tb))
				else:
					# Dafuhq happened!?
					tb = traceback.format_exc()
					logger.log("%s went boom connecting.\n%s" %(self.myName, tb))
				
				# In the event our connect fails, try again after the configured delay
				logger.log("%s sleeping %s sec." %(self.myName, str(self.dump1090Src["reconnectDelay"] * self.__backoff)))
				time.sleep(self.dump1090Src["reconnectDelay"] * self.__backoff)
				
				# Handle backoff.
				self.__handleBackoff()
		
		# Set 1 second timeout for blocking operations.
		self.__dump1090Sock.settimeout(1.0)
		
		# The watchdog should be run every second.
		self.__lastEntry = 0
		self.__myWatchdog = threading.Timer(1.0, self.__watchdog)
		self.__myWatchdog.start()
	
	# Disconnect the source and re-create the socket object.
	def __disconnectSource(self):
		"""
		Disconnect from our host.
		"""
		
		logger.log("%s disconnecting." %self.myName)
		
		try:	
			# Close the connection.
			self.__dump1090Sock.close()
		except:
			tb = traceback.format_exc()
			logger.log("%s threw exception disconnecting.\n%s" %(self.myName, tb))
			
		# Reset the lastEntry counter.
		self.__lastEntry = 0
		
		try:
			# Stop the watchdog.
			self.__myWatchdog.cancel()
		except:
			# Don't do anything.
			None
	
	def run(self):
		"""run
		
		dataSource worker.
		"""
		myName = self.myName
		dump1090Src = self.dump1090Src
		
		logger.log("%s running." %self.myName)
		
		# Do stuff.
		while (True):
			# Attempt to connect.
			self.__connectSource()
			
			# Try to read a line from our established socket.
			try:
				# Get lines of data from dump1090
				for thisLine in self.__readLines(self.__dump1090Sock):
					
					# Date time string
					dtsStr = str(datetime.datetime.utcnow())
					
					# If we're debugging yet.
					if config.d1090ConnSettings['debug']:
						logger.log("Got line %s from %s." %(thisLine, self.myName))
					
					# Create our data entry dict.
					thisEntry = {}
					
					#Make sure we didn't trim microseconds because if we did the mongoDump script gets pissed off.
					if (len(dtsStr) == 19):
						dtsStr = dtsStr + ".000000"
					
					# Add metadata.
					thisEntry.update({'dataOrigin': 'dump1090', 'type': 'airSSR', 'dts': dtsStr, 'src': config.d1090ConnSettings['myName'], 'entryPoint': 'dump1090ConnClt', 'data': thisLine, 'clientName': self.myName})
					
					# If we have position data for this source...
					if 'srcPos' in self.dump1090Src:
						# If we have a list...
						if type(self.dump1090Src['srcPos']) == list:
							
							# If our list has two elements...
							if len(self.dump1090Src['srcPos']) == 3:
								
								# If we have good position data add it to any outgoing data.
								thisEntry.update({"srcLat": self.dump1090Src['srcPos'][0], "srcLon": self.dump1090Src['srcPos'][1], "srcPosMeta": self.dump1090Src['srcPos'][2]})
					
					# If we're debugging...
					if config.d1090ConnSettings['debug']:
						logger.log("%s queueing: %s." %(thisLine, self.myName))
					
					# Try to queue our data.
					submitted = h1090.handleADSBDict(thisEntry)
					
					# If we were able to submit our data
					if submitted:
						# Reset our last entry.
						self.__lastEntry = 0
				
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
						logger.log("%s went boom processing data.\n%s" %(self.myName, tb))
						
						# Close the connection.
						self.__disconnectSource()
				else:
					# Dafuhq happened!?
					tb = traceback.format_exc()
					logger.log("%s went boom processing data.\n%s" %(self.myName, tb))
					
					# Close the connection.
					self.__disconnectSouce()
	
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
					yield line
			
			except socket.timeout:
				continue
			
			except Exception as e:
				# See if we have a socket error...
				if type(e) == socket.error:
					# If we weren't able to connect, dump a message
					if e.errno == errno.ECONNREFUSED:
						#Print some messages
						logger.log("%s refused connection to %s:%s." %(self.myName, self.dump1090Src["host"], self.dump1090Src["port"]))
						data = False
						line = ""
						
						raise e
					
					elif e.errno == errno.ECONNRESET:
						#Print some messages
						logger.log("%s reset connection to %s:%s." %(self.myName, self.dump1090Src["host"], self.dump1090Src["port"]))
						data = False
						line = ""
						
						raise e
					
					else:
						# Dafuhq happened!?
						tb = traceback.format_exc()
						logger.log("%s choked reading buffer with socket error.\n%s" %(self.myName, tb))
						data = False
						line = ""
				
				else:
					tb = traceback.format_exc()
					logger.log("%s choked reading buffer.\n%s" %(self.myName, tb))
					data = False
					line = ""
			
			# See if our watchdog is working.
			if self.__watchdogFail:
				logger.log("%s watchdog terminating readLines." %self.myName)
				data = False
				break


#######################
# Main execution body #
#######################

# Set up the logger.
logger = asLog(config.d1090ConnSettings['logMode'])

# ... and go.
logger.log("Dump1090 client connector starting...")

# Set up our dump1090 handler.
h1090 = handler1090(config.d1090ConnSettings['logMode'])
h1090.setDebug(config.d1090ConnSettings['debug'])

# Threading setup
threadLock = threading.Lock()
threadList = []

# Spin up our client threads.
for thisName, connData in dump1909Srcs.iteritems():
	logger.log("Spinning up thread for %s." %thisName)
	client = dataSource(thisName, connData)
	client.daemon = True
	client.start()
	threadList.append(client)

# Fix bug that prevents keyboard interrupt from killing dump1090Connector.py
while True: time.sleep(10)

# Shut down
for t in threadList:
	t.join()
