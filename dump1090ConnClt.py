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

import redis
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
from libAirSuck import ssrParse

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
		print("Init thread for " + myName + ".")
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
		
		# Redis queues and entities
		self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
		self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
		self.__dedeupe = redis.StrictRedis(host=config.d1090ConnSettings['dedupeHost'], port=config.d1090ConnSettings['dedupePort'])
	
	# Make sure we have data. If we don't throw an exception.
	def watchdog(self):
		"""
		watchdog()
		
		Check this thread to see if it has not recieved data in the given thread timeout.
		"""
		
		try:
			# Check to see if our last entry was inside the timeout window.
			if self.__lastEntry >= self.dump1090Src['threadTimeout']:
				# Puke if we have been running for too long without data.
				raise IOError()
			else:
				# Restart our watchdog.
				self.__myWatchdog = threading.Timer(1.0, self.watchdog)
				self.__myWatchdog.start()
		
		except Exception as e:
			# Set the watchdog failure flag.
			self.__watchdogFail = True
			
			# Stop the watchdog.
			self.__myWatchdog.cancel()
			
			# Prion the error message
			print(self.myName + " watchdog: No data recieved in " + str(self.dump1090Src['threadTimeout']) + " sec.")
			
			# Close the connection.
			self.__dump1090Sock.close()
		
		# Increment our last entry.
		self.__lastEntry += 1
	
	# Connect to our data source.
	def connectSource(self):
		"""
		connectSource()
		
		Connects to our host.
		"""
		
		# Create a new socket object.
		self.__dump1090Sock = socket.socket()
		
		# We're not connected so set the flag.
		notConnected = True
		
		# Keep trying to connect until it works.
		while notConnected:
			# Print message
			print(self.myName + " connecting to " + self.dump1090Src["host"] + ":" + str(self.dump1090Src["port"]))
			
			# Attempt to connect.
			try:
				# Connect up
				self.__dump1090Sock.connect((self.dump1090Src["host"], self.dump1090Src["port"]))
				print(self.myName + " connected.")
				
				# We connected so now we can move on.
				notConnected = False
				
				# Reset the lastEntry counter.
				self.__lastEntry = 0
				
				# Reset the watchdog state.
				self.__watchdogFail = False
				
			except Exception as e:
				if 'errno' in e:
					# If we weren't able to connect, dump a message
					if e.errno == errno.ECONNREFUSED:
						#Print some messages
						print(myName + " failed to connect to " + self.dump1090Src["host"] + ":" + str(self.dump1090Src["port"]))
				
				else:
					# Dafuhq happened!?
					print(self.myName + " went boom connecting.")
					tb = traceback.format_exc()
					print(tb)
				
				# In the event our connect fails, try again after the configured delay
				print(self.myName + " sleeping " + str(self.dump1090Src["reconnectDelay"] * self.__backoff) + " sec.")
				time.sleep(self.dump1090Src["reconnectDelay"] * self.__backoff)
		
		# Set 1 second timeout for blocking operations.
		self.__dump1090Sock.settimeout(1.0)
	
	# Disconnect the source and re-create the socket object.
	def disconnectSouce(self):
		"""
		disconnectSource()
		
		Disconnect from our host.
		"""
		
		print(self.myName + " disconnecting.")
		
		try:	
			# Close the connection.
			self.__dump1090Sock.close()
		except:
			print(self.myName + " threw exception disconnecting.")
			tb = traceback.format_exc()
			print(tb)
		
		# Reset the lastEntry counter.
		self.__lastEntry = 0
	
	def run(self):
		"""run
		
		dataSource worker.
		"""
		myName = self.myName
		dump1090Src = self.dump1090Src
		
		print(myName + " running.")
		
		# Do stuff.
		while (True):
			# Attempt to connect.
			self.connectSource()
			
			# Try to read a line from our established socket.
			try:
				# The watchdog should be run every second.
				self.__lastEntry = 0
				self.__myWatchdog = threading.Timer(1.0, self.watchdog)
				self.__myWatchdog.start()
				
				# Get lines of data from dump1090
				for thisLine in self.readLines(self.__dump1090Sock):
					
					# Date time string
					dtsStr = str(datetime.datetime.utcnow())
					
					# Create our data entry dict.
					thisEntry = {}
					
					#Make sure we didn't trim microseconds because if we did the mongoDump script gets pissed off.
					if (len(dtsStr) == 19):
						dtsStr = dtsStr + ".000000"
					
					# Todo: handle MLAT data here.
					if thisLine.find('@') >= 0:
						# This doesn't get deduplicated.
						dedupeFlag = False
						
						# Properly format the "line"
						thisLine = self.formatSSRMsg(thisLine)
						
						# Split MLAT data from SSR data.
						lineParts = self.splitMlat(thisLine)
						
						try:
							# Parse the frame.
							binData = bytearray(binascii.unhexlify(lineParts[1]))
						except:
							# Blank our incoming data and dump an error.
							binData = ""
							formattedSSR = ""
							print(self.myName + " got invlaid hex SSR data: " + lineParts[1])
						
						# Set MLAT data and SSR data.
						thisEntry.update({ 'mlatData': lineParts[0], 'data': lineParts[1] })
						
						# Add parsed data.
						thisEntry.update(self.__ssrParser.ssrParse(binData))
						
						# Create an entry to be queued.
						thisEntry.update({ 'dataOrigin': 'dump1090', 'type': 'airSSR', 'dts': dtsStr, 'src': myName, 'entryPoint': 'dump1090ConnClt' })
					
					else:
						# This gets fed to the deduplicator.
						dedupeFlag = True
						
						# Format our SSR data a hex string and bytearray.
						formattedSSR = self.formatSSRMsg(thisLine)
						
						try:
							# Parse the frame.
							binData = bytearray(binascii.unhexlify(formattedSSR))
						except:
							# Blank our incoming data and dump an error.
							binData = ""
							formattedSSR = ""
							print(self.myName + " got invlaid hex SSR data: " + formattedSSR)
						
						# Properly format the "line"
						thisEntry.update({ 'data': formattedSSR })
						
						# Parse our data and add it to the stream.
						thisEntry.update(self.__ssrParser.ssrParse(binData))
						
						# Create an entry to be queued.
						thisEntry.update({ 'dataOrigin': 'dump1090', 'type': 'airSSR', 'dts': dtsStr, 'src': myName, 'entryPoint': 'dump1090ConnClt' })
					
					# Queue up our data.
					self.queueADSB(thisEntry, dedupeFlag)
				
				# Close the connection.
				self.disconnectSouce()
				
			# Try to catch what blew up. This needs to be significantly improved and should result in a delay and another connection attempt.
			except Exception as e:
				if 'errno' in e:
					if e.errno == 9:
						continue
					else:
						# Dafuhq happened!?
						print(self.myName + " went boom processing data.")
						tb = traceback.format_exc()
						print(tb)
						
						# Close the connection.
						self.disconnectSouce()
				else:
					# Dafuhq happened!?
					print(self.myName + " went boom processing data.")
					tb = traceback.format_exc()
					print(tb)
					
					# Close the connection.
					self.disconnectSouce()
	
	def formatSSRMsg(self, strMsg):
		"""
		stripDelims(strMsg)
		
		Strip dump1090 delimeter chars from the message, remove whitespace, and convert it to lower case.
		"""
		
		# Remove start and end chars *, @, ;
		strMsg = strMsg.replace('*', '')
		strMsg = strMsg.replace(';', '')
		strMsg = strMsg.replace('@', '')
		
		# Strip any whitespace around the data.
		strMsg = strMsg.strip()
		
		# Make the data lower case, just for giggles.
		strMsg = strMsg.lower()
		
		return strMsg
	
	# Split incoming dump1090 messages with MLAT data.
	def splitMlat(self, strMsg):
		"""
		getMlat(strMsg)
		
		Split MLAT and SSR data int an array. Index 0 being MLAT, and Index 1 being SSR.
		"""
		
		retVal = [strMsg[0:12], strMsg[12:]]
		
		# Do the magic here.
		
		return retVal
	
	# Convert the message to JSON format
	def jsonify(self, dataDict):
		""" jsonify(dataDict)
		
		Convert a given dictionary to a JSON string.
		"""
		
		retVal = json.dumps(dataDict)
		return retVal
	
	# Get one line from TCP output, from:
	# http://synack.me/blog/using-python-tcp-sockets
	def readLines(self, sock, recvBuffer = 4096, delim = '\n'):
		"""readLines(sock)
		
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
					#print("L: " + str(line) + ", B: " + str(buffer))
					yield line
			
			except socket.timeout:
				continue
			
			except Exception as e:
				# If we had a disconnect event drop out of the loop.
				if 'errno' in e:
					if e.errno == 9:
						print(self.myName + " disconnected.")
						data = False
						raise e
					
					else:
						print(self.myName + " choked reading buffer.")
						tb = traceback.format_exc()
						print(tb)
						data = False
						line = ""
				else:
					print(self.myName + " choked reading buffer.")
					tb = traceback.format_exc()
					print(tb)
					data = False
					line = ""
			
			# See if our watchdog is working.
			if self.__watchdogFail:
				print(self.myName + " watchdog terminating readLines.")
				data = False
				break
	
	# Convert the data we want to send to JSON format.
	def queueADSB(self, msg, dedupeFlag):
		"""queueADSB(msg)
		
		Accepts a JSON string and queues it in the Redis database, assuming a duplicate string hasn't been queued within the last n seconds specified in redisQueues['dudeupeTableExp'], and we're not dealing with MLAT data. (dedupeFlag = False prevents dedupliation operations.)
		"""
		
		# If we have something in the data field that's longer than 2 chars...
		if len(msg['data']) >= 4:
			jsonMsg = self.jsonify(msg)
			# See if we already have the key in the redis cache, or if we're supposed to dedupe this frame at all.
			
			# Set up a hashed version of our data.
			dHash = "ssr-" + hashlib.md5(msg['data']).hexdigest()
			
			if ((self.__dedeupe.exists(dHash) == False) or (dedupeFlag == False)):
				# Set the key and insert lame value.
				self.__dedeupe.setex(dHash, config.d1090ConnSettings['dedupeTTLSec'], "X")
				
				# If we are configured to use the connector mongoDB forward the traffic to it.
				if config.connMongo['enabled'] == True:
					self.__rQ.rpush(config.connRel['qName'], jsonMsg)
				
				# Put data on the pub/sub queue.
				self.__psQ.publish(config.connPub['qName'], jsonMsg)
				
				# Debug
				#print("Q: " + str(msg['data']))
				
			# Reset our lastEntry seconds.
			self.__lastEntry = 0
			
			return

#######################
# Main execution body #
#######################

# ... and go.
print("Dump1090 client connector starting...")

# Threading setup
threadLock = threading.Lock()
threadList = []

# Create a shared redis instance
r = redis.StrictRedis()

# Spin up our client threads.
for thisName, connData in dump1909Srcs.iteritems():
	print("Spinning up thread for " + thisName + ".")
	client = dataSource(thisName, connData)
	client.daemon = True
	client.start()
	threadList.append(client)

# Fix bug that prevents keyboard interrupt from killing dump1090Connector.py
while True: time.sleep(10)

# Shut down
for t in threadList:
	t.join()
