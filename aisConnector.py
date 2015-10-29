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
from libAirSuck import aisParse


##########
# Config #
##########

# Keep track of if we're running.
alive = True

# Should we enqueue data?
enqueueOn = True


####################
# dataSource class #
####################

class dataSource(threading.Thread):
	""" dataSource class
	
	Takes two required arguments and one optional: myName (client-identifying string), AISSrc (AISSrc source dictionary), optinally enqueue which should be True or False (by default it will enqueue data, otherwise will print it).
	
	A generic class that represents a given AIS data source
	"""
	
	def __init__(self, myName, AISSrc, enqueue=True):
		print("Init thread for " + myName)
		threading.Thread.__init__(self)
		
		# Extend properties to be class-wide.
		self.myName = myName
		self.AISSrc = AISSrc
		self.enqueue = enqueue
		self.__aisParser = aisParse()
		self.__watchdogFail = False
		self.__backoff = 1.0
		
		# Our class-wide socket object.
		self.__aisSock = None
		
		# This keeps track of the number of seconds since our last connection.
		self.__lastEntry = 0
		
		# Redis queues and entities
		self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
		self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
		self.__frag = redis.StrictRedis(host=config.aisConnSettings['fragHost'], port=config.aisConnSettings['fragPort'])
		self.__dedupe = redis.StrictRedis(host=config.aisConnSettings['dedupeHost'], port=config.aisConnSettings['dedupePort'])

	# Make sure we don't have a dead connection.
	def watchdog(self):
		"""
		watchdog()
		
		Check this thread to see if it has not recieved data in the given thread timeout.
		"""
		
		try:
			# Check to see if our last entry was inside the timeout window.
			if self.__lastEntry >= self.AISSrc['threadTimeout']:
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
			print(self.myName + " watchdog: No data recieved in " + str(self.AISSrc['threadTimeout']) + " sec.")
			
			# Close the connection.
			self.__aisSock.close()
		
		# Increment our last entry.
		self.__lastEntry += 1
	
	# Connect to our data source.
	def connectSource(self):
		"""
		connectSource()
		
		Connects to our host.
		"""
		
		# Create a new socket object
		self.__aisSock = socket.socket()
		
		# We're not connected so set the flag.
		notConnected = True
		
		# Keep trying to connect until it works.
		while notConnected:
			# Print message
			print(self.myName + " connecting to " + self.AISSrc["host"] + ":" + str(self.AISSrc["port"]))
			
			# Attempt to connect.
			try:
				# Connect up
				self.__aisSock.connect((self.AISSrc["host"], self.AISSrc["port"]))
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
						print(myName + " failed to connect to " + self.AISSrc["host"] + ":" + str(self.AISSrc["port"]))
				
				else:
					# Dafuhq happened!?
					print(self.myName + " went boom connecting.")
					tb = traceback.format_exc()
					print(tb)
				
				# In the event our connect fails, try again after the configured delay
				print(self.myName + " sleeping " + str(self.AISSrc["reconnectDelay"] * self.__backoff) + " sec.")
				time.sleep(self.AISSrc["reconnectDelay"] * self.__backoff)
		
		# Set 1 second timeout for blocking operations.
		self.__aisSock.settimeout(1.0)
	
	# Disconnect the source and re-create the socket object.
	def disconnectSouce(self):
		"""
		disconnectSource()
		
		Disconnect from our host.
		"""
		
		print(self.myName + " disconnecting.")
		
		try:	
			# Close the connection.
			self.__aisSock.close()
		except:
			print(self.myName + " threw exception disconnecting.")
			tb = traceback.format_exc()
			print(tb)
		
		# Reset the lastEntry counter.
		self.__lastEntry = 0
	
	# Strip metachars.
	def metaStrip(self, subject):
		"""
		metaStrip(subject)
		
		Strip metacharacters from a string.
		
		Returns stripped string.
		"""
		
		# Take any metachars off the end of the string.
		subject = subject.lstrip()
		return subject.rstrip()
	
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
	def queueAIS(self, msg):
		"""queueADSB(msg)
		
		Drop the msg on the appropriate redis connector queue(s) as a JSON string.
		"""
		
		# Create a new dict to enqueue so the original doesn't get manipulated.
		enqueueMe = {}
		enqueueMe.update(msg)
		
		# If we have a payload specified drop it.
		if 'payload' in msg:
			enqueueMe.pop('payload')
		
		# Build a JSON string.
		jsonMsg = self.jsonify(enqueueMe)
		
		# Should we actually enqueue the data?
		if self.enqueue:
			# Set up a hashed version of our data.
			dHash = "ais-" + hashlib.md5(enqueueMe['data']).hexdigest()
			
			# If we dont' already have a frame like this one OR the frame is a fragment...
			if (self.__dedupe.exists(dHash) == False) or (enqueueMe['isFrag'] == True):
				
				# Make sure we're not handling a fragment. Since some fragments can be short there's a good chance of collision.
				if enqueueMe['isFrag'] == False:
					# Set the key and insert lame value.
					self.__dedupe.setex(dHash, config.aisConnSettings['dedupeTTLSec'], "X")
				
				# If we are configured to use the connector mongoDB forward the traffic to it.
				if config.connMongo['enabled'] == True:
					self.__rQ.rpush(config.connRel['qName'], jsonMsg)
				
				# Put data on the pub/sub queue.
				self.__psQ.publish(config.connPub['qName'], jsonMsg)
				
				# Debug
				#print("Q: " + enqueueMe['data'])
		else:
			# Just dump the JSON data as a string.
			print(jsonMsg)
		
		return

	# Defragment AIS messages.
	def defragAIS(self, fragment):
		"""
		defrag(fragment)
		
		Attempt to assemble AIS data from a number of fragments. Fragment is a decapsulated AIS message fragment.
		"""
		
		# By default assume we don't have an assembled payload
		isAssembled = False
		
		# Set up a hashed version of our data given the host the data arrived on, the fragment count, and the message ID.
		fHash = "aisFrag-" + hashlib.md5(fragment['src'] + "-" + str(fragment['fragCount']) + '-' + str(fragment['messageID'])).hexdigest()
		
		# Create a fragment name.
		fragName = str(fragment['fragNumber'])
		
		# Attempt to get data from our hash table.
		hashDat = self.__frag.hgetall(fHash)
		hashDatLen = len(hashDat)
		
		# If we already have a fragment...
		if hashDatLen > 0:
			
			# If we have all the fragments we need...
			if hashDatLen == (fragment['fragCount'] - 1):
				# Create a holder for our payload
				payload = ""
				
				# Push our new fragment into the dict.
				hashDat.update({fragName: fragment['payload']})
				
				# Assemble the stored fragments in order.
				for i in range(1, fragment['fragCount'] + 1):
					payload = payload + hashDat[str(i)]
				
				# Make sure we properly reassign the payload to be the full payload.
				fragment.update({'payload': payload})
				
				# Set assembled flag.
				isAssembled = True
			else:
				# Since we don't have all the fragments we need add the latest fragment to the list.
				self.__frag.hset(fHash, fragName, fragment['payload'])
		else:
			# Create our new hash object.
			self.__frag.hset(fHash, fragName, fragment['payload'])
		
		# If we have an assembled payload clean up some info and queue it.
		if isAssembled:
			# Nuke the hash object.
			self.__frag.expire(fHash, -1)
			
			# Update the fragment data.
			fragment.update({'isAssembled': True, 'isFrag': False, 'data': payload})
			
			# Set the fragment to include parsed data.
			fragment = self.__aisParser.aisParse(fragment)
			
			# The fragment number is no longer valid since the count tells us how many we had.
			fragment.pop('fragNumber')
			
			# Enqueue our assembled payload.
			self.queueAIS(fragment)
		else:
			# Set the expiration time on the fragmoent hash.
			self.__frag.expire(fHash, config.aisConnSettings['fragTTLSec'])
	
	def handleLine(self, thisLine):
		"""
		handleLine(thisLine)
		
		Handle a line of text representing a single AIS sentence.
		"""
		# Remove whitespace.
		thisLine = self.metaStrip(thisLine)
		
		try:
			# Compute the CRC value of the frame.
			frameCRC = self.__aisParser.getFrameCRC(thisLine)
			cmpCRC = self.__aisParser.getCRC(thisLine)
		except:
			tb = traceback.format_exc()
			print(self.myName + " choked getting CRC.")
			print(tb)
		
		# If we have a good CRC checksum keep moving.
		if frameCRC == cmpCRC:
			# Date time string
			dtsStr = str(datetime.datetime.utcnow())
			
			# Make sure we didn't trim microseconds because if we did the mongoDump script gets pissed off.
			if (len(dtsStr) == 19):
				dtsStr = dtsStr + ".000000"
			
			# Set this entry up with some initial data.
			thisEntry = {'entryPoint': 'aisConnector', 'dataOrigin': 'aisConn', 'type': 'airAIS', 'dts': dtsStr, 'src': self.myName, 'data': thisLine, 'isFrag': False, 'isAssembled': False}
			
			try:
				# Decapsulate the AIS payload and get relevant data.
				thisEntry.update(self.__aisParser.nmeaDecapsulate(thisLine))
			except:
				tb = traceback.format_exc()
				print(self.myName + " choked decapsulating frame " + thisLine)
				print(tb)
			
			
			# If we have an unfragmented frame process it. If not, handle the fragment.
			if (thisEntry['fragCount'] == 1) and (thisEntry['fragNumber'] == 1):
				try:
					# Parse our AIS data and add it to the stream.
					thisEntry.update(self.__aisParser.aisParse(thisEntry))
				except:
					tb = traceback.format_exc()
					print(self.myName + " choked decapsulating frame " + thisLine)
					print(tb)
					
				# Enqueue our data.
				self.queueAIS(thisEntry)
			else:
				# Enqueue our fragment.
				self.queueAIS(thisEntry)
				
				# Since we aren't frame 1 of 1 for a given message we're a fragment.
				thisEntry['isFrag'] = True
				try:
					# Handle fragments.
					self.defragAIS(thisEntry)
				except:
					print(self.myName + " error defragmenting data.")
					tb = traceback.format_exc()
					print(tb)
		
		# Reset our lastEntry seconds.
		self.__lastEntry = 0
	
	def run(self):
		"""run
		
		dataSource worker.
		"""
		
		print(self.myName + " running.")
		
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
				
			except Exception as e:
					# If we weren't able to connect, dump a message
					if e.errno == errno.ECONNREFUSED:
						
						#Print some messages
						print(self.myName + " failed to connect to " + self.AISSrc["host"] + ":" + str(self.AISSrc["port"]))
						print(self.myName + " sleeping " + str(self.AISSrc["reconnectDelay"]) + " sec")
						AISSock.close()
					else:
						# Something besides connection refused happened. Let's figure out what happened.
						print(self.myName + " error while trying to connect.")
						tb = traceback.format_exc()
						print(tb)
						AISSock.close()
					
					# In the event our connect fails, try again after the configured delay
					time.sleep(self.AISSrc["reconnectDelay"])
			
			# Try to read a lone from our established socket.
			try:				
				# Get lines of data from dump1090
				for thisLine in self.readLines(self.__aisSock):
					# Do our thing.
					self.handleLine(thisLine)
				
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

#######################
# Main execution body #
#######################

# If I've been called for execution...
if __name__ == "__main__":
	# If the AIS engine is enabled in config...
	if config.aisConnSettings['enabled'] == True:
		# ... and go.
		print("AIS connector starting...")
		
		# Threading setup
		threadLock = threading.Lock()
		threadList = []
		
		# Create a shared redis instance
		r = redis.StrictRedis()
		
		# Spin up our client threads.
		for thisName, connData in config.aisConnSettings['connClientList'].iteritems():
			print("Spinning up thread for " + thisName)
			client = dataSource(thisName, connData, enqueueOn)
			client.daemon = True
			client.start()
			threadList.append(client)
		
		# Fix bug that prevents keyboard interrupt from killing dump1090Connector.py
		while True: time.sleep(10)
		
		# Shut down
		for t in threadList:
			t.join()
	else:
		print("AIS connector not enabled in config.")
