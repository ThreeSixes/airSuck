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
import ssrParse
from socket import socket
from pprint import pprint


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
	 
	def __init__(self, myName, dump1090Src,):
		print("Init thread for " + myName)
		threading.Thread.__init__(self)
		
		# Extend properties to be class-wide.
		self.myName = myName
		self.dump1090Src = dump1090Src
		self.__ssrParser = ssrParse.ssrParse()
		
		# Redis queues and entities
		self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
		self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
		self.__dedeupe = redis.StrictRedis(host=config.d1090ConnSettings['dedupeHost'], port=config.d1090ConnSettings['dedupePort'])
	
	def run(self):
		"""run
		
		dataSource worker.
		"""
		myName = self.myName
		dump1090Src = self.dump1090Src
		
		print(myName + " running.")
		
		# Do stuff.
		while (alive):
			dump1090Sock = socket()
			
			# Attempt to connect.
			try:
				# Connect up
				print(myName + " connecting to " + dump1090Src["host"] + ":" + str(dump1090Src["port"]))
				dump1090Sock.connect((dump1090Src["host"], dump1090Src["port"]))
				print(myName + " connected.")
				
			except Exception as e:
					# If we weren't able to connect, dump a message
					if e.errno == errno.ECONNREFUSED:
						
						#Print some messages
						print(myName + " failed to connect to " + dump1090Src["host"] + ":" + str(dump1090Src["port"]))
						print(myName + " sleeping " + str(dump1090Src["reconnectDelay"]) + " sec")
					else:
						# Something besides connection refused happened. Let's figure out what happened.
						pprint(e)
					
					# In the event our connect fails, try again after the configured delay
					time.sleep(dump1090Src["reconnectDelay"])
			
			# Try to read a lone from our established socket.
			try:
				# Get lines of data from dump1090
				for thisLine in self.readLines(dump1090Sock):
					
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
						
						# Parse the frame.
						binData = bytearray(binascii.unhexlify(lineParts[1]))
						
						# Set MLAT data and SSR data.
						thisEntry.update({ 'mlatData': lineParts[0], 'data': lineParts[1] })
						
						# Add parsed data.
						thisEntry.update(self.__ssrParser.ssrParse(binData))
						
					else:
						# This gets fed to the deduplicator.
						dedupeFlag = True
						
						# Format our SSR data a hex string and bytearray.
						formattedSSR = self.formatSSRMsg(thisLine)
						binData = bytearray(binascii.unhexlify(formattedSSR))
						
						# Properly format the "line"
						thisEntry.update({ 'data': formattedSSR })
						
						# Create an entry to be queued.
						thisEntry.update({ 'dataOrigin': 'dump1090', 'type': 'airSSR', 'dts': dtsStr, 'src': myName })
						
						# Parse our data and add it to the stream.
						thisEntry.update(self.__ssrParser.ssrParse(binData))
						
					# Queue up our data.
					self.queueADSB(thisEntry, dedupeFlag)
				
				dump1090Sock.close()
					
			# Try to catch what blew up. This needs to be significantly improved and should result in a delay and another connection attempt.
			except Exception as e:
				# Dafuhq happened!?
				print(myName + " went boom.")
				pprint(e)
	
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
			data = sock.recv(recvBuffer)
			buffer += data
			
			while buffer.find(delim) != -1:
				line, buffer = buffer.split('\n', 1)
				yield line
		return
	
	# Convert the data we want to send to JSON format.
	def queueADSB(self, msg, dedupeFlag):
		"""queueADSB(msg)
		
		Accepts a JSON string and queues it in the Redis database, assuming a duplicate string hasn't been queued within the last n seconds specified in redisQueues['dudeupeTableExp'], and we're not dealing with MLAT data. (dedupeFlag = False prevents dedupliation operations.)
		"""
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
		
		return
		

#######################
# Main execution body #
#######################

# ... and go.
print("Dump1090 connector starting...")

# Threading setup
threadLock = threading.Lock()
threadList = []

# Create a shared redis instance
r = redis.StrictRedis()

# Spin up our client threads.
for thisName, connData in dump1909Srcs.iteritems():
	print("Spinning up thread for " + thisName)
	client = dataSource(thisName, connData)
	client.daemon = True
	client.start()
	threadList.append(client)

# Fix bug that prevents keyboard interrupt from killing dump1090Connector.py
while True: time.sleep(10)

# Shut down
for t in threadList:
	t.join()
