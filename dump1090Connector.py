#!/usr/bin/python

###########
# Imports #
###########

import redis
import time
import json
import datetime
import threading
import errno
from socket import socket
from pprint import pprint


##########
# Config #
##########

#Target Redis queues
redisQueues = {
	"targetQ": "ssrReliable",	# Reliable queue for DB serialization
	"targetPub": "ssrFeed",		# Pub/sub queue for other subscribers
	"dedupeExp": 3			# Redis hash table entry expiry
}

#dump1090 sources
dump1909Srcs = {
	"tallear": { "host": "127.0.0.1", "port": 40000, "reconnectDelay": 5}
	, "northwind":  { "host": "127.0.0.1", "port": 40001, "reconnectDelay": 5}
	#"tallear": { "host": "tallear", "port": 30002, "reconnectDelay": 5}
	#, "northwind":  { "host": "northwind", "port": 30002, "reconnectDelay": 5}
	#"insurrection":  { "host": "127.0.0.1", "port": 30002, "reconnectDelay": 5}
}


alive = True

####################
# dataSource class #
####################

class dataSource(threading.Thread):
	""" dataSource class
	
	Takes four arguments: rQ (strictRedis object), myName (client-identifying string), dump1090Src (dump1090 source dictionary), rQinfo (Redis queue config data).
	
	A generic class that represents a given dump1090 data source
	"""
	 
	def __init__(self, rQ, myName, dump1090Src, rQInfo):
		print("Init thread for " + myName)
		threading.Thread.__init__(self)
		
		# Extend properties to be class-wide. 
		self.rQ = rQ
		self.myName = myName
		self.dump1090Src = dump1090Src
		self.rQInfo = rQInfo
	
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
						# Properly format the "line"
						thisLine = self.formatSSRMsg(thisLine)
						
						# Split MLAT data from SSR data.
						lineParts = self.splitMlat(thisLine)
						
						# Set MLAT data and SSR data.
						thisEntry.update({ 'mlatData': lineParts[0], 'data': lineParts[1] })
							
					else:
						# Properly format the "line"
						thisEntry.update({ 'data': self.formatSSRMsg(thisLine) })
						
						#threadLock.acquire()
						# Create an entry to be queued.
						thisEntry.update({ 'dataOrigin': 'dump1090', 'type': 'airSSR', 'dts': dtsStr, 'src': myName })
						
						self.queueADSB(thisEntry)
						#threadLock.release()
				
				dump1090Sock.close()
					
			# Try to catch what blew up. This needs to be significantly improved and should result in a delay and another connection attempt.
			except Exception as e:
				# If the transport endpoint is disconnected.
				if e.errno == 107:
					print(myName + " connection dropped.")
				else:
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
	def queueADSB(self, msg):
		"""queueADSB(msg)
		
		Accepts a JSON string and queues it in the Redis database, assuming a duplicate string hasn't been queued within the last n seconds specified in redisQueues['dudeupeTableExp']
		"""
		jsonMsg = self.jsonify(msg)
		# See if we already have the key in the redis cache.
		if (self.rQ.exists(msg['data']) == False):
			# Set the key and insert lame value.
			self.rQ.setex(msg['data'], self.rQInfo['dedupeExp'], "X")
			
			# Drop the data on our reliable DB queue, and the non-persistent queue.
			self.rQ.rpush(self.rQInfo['targetQ'], jsonMsg)
			self.rQ.publish(self.rQInfo['targetPub'], jsonMsg)
		
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
	client = dataSource(r, thisName, connData, redisQueues)
	client.daemon = True
	client.start()
	threadList.append(client)

# Fix bug that prevents keyboard interrupt from killing dump1090Connector.py
while True: time.sleep(10)

# Shut down
for t in threadList:
	t.join()

print("Shutting down.")
