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

import socket
import select
import config
import redis
import time
import json
import datetime
import threading
import errno
import binascii
import hashlib
import traceback
from libAirSuck import ssrParse
from pprint import pprint

########################
# d1090Connector class #
########################

class d1090Connector():
	"""d1090Connector class
	This class is a connector for dump1090 data submitted through the dump1090 client. The class accpets no arguments.
	"""

	def __init__(self):		
		# Class-wide list of connections.
		self.__conns = []
		self.__connAddrs = {}
		
		# Buffer size settings.
		self.__buffSz = 4096 # 4K
		
		# Should we keep running?
		self.__keepRunning = True
		
		# Redis queues and entities
		self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
		self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
		self.__dedeupe = redis.StrictRedis(host=config.d1090ConnSettings['dedupeHost'], port=config.d1090ConnSettings['dedupePort'])
		
		# Create our SSR parser.
		self.__ssrParser = ssrParse()
	
	# Send a "ping" to connected hosts.
	def __sendPing(self):
		"""
		__sendPing()
		
		Send a ping to all connected hosts.
		"""
		
		# For each client we have send the ping JSON sentence.
		for thisSock in self.__conns:
			
			# If we're not the listener send data.
			if thisSock != self.__listenSock:
				# We have something from a client so let's try to handle it.
				try:
					# Get the incoming data from our socket.
					thisSock.send("{\"ping\": \"abcdef\"}\n")
				
				except KeyboardInterrupt:
					logger.log("Keyboard interrupt. Shutting down.")
					self.__keepRunning = False
					self.__myPinger.cancel()
				
				except:
					# Kill the socket so the main loop will throw an exception.
					thisSock.close()
					self.__conns.remove(thisSock)
					killedClient = self.__connAddrs.pop(thisSock)
					
					# Log
					logger.log("Can't ping %s:%s. Disconnecting them." %(killedClient[0], str(killedClient[1])))
		
		try:
			# Respawn the pinger.
			self.__myPinger = threading.Timer(config.d1090ConnSettings['clientPingInterval'], self.__sendPing)
			self.__myPinger.start()
		
		except KeyboardInterrupt:
			self.__keepRunning = False
	
	def __formatSSRMsg(self, strMsg):
		"""
		__formatSSRMsg(strMsg)
		
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
	def __splitMlat(self, strMsg):
		"""
		__splitMlat(strMsg)
		
		Split MLAT and SSR data int an array. Index 0 being MLAT, and Index 1 being SSR.
		"""
		
		# Split out MLAT and SSR at char boundaries.
		retVal = [strMsg[0:12], strMsg[12:]]
		
		return retVal
	
	# Convert the message to JSON format
	def __jsonify(self, dataDict):
		""" __jsonify(dataDict)
		
		Convert a given dictionary to a JSON string.
		"""
		
		retVal = json.dumps(dataDict)
		return retVal
	
	# Convert JSON string to a dict.
	def __jsonStr2Dict(self, thisStr):
		"""__jsonStr2Dict(thisStr)
		
		Convert a given JSON string to a dict. If the conversion fails this function returns null, otherwise it returns a dict.
		"""
		
		try:
			# Get a dict from the incoming JSON string.
			retVal = json.loads(thisStr)
		except:
			# If it doesn't work just set retVal to none.
			retVal = None
			
			tb = traceback.format_exc()
			logger.log("Failed to parse JSON data.\nString: %s\n%s" %(thisStr, tb))
		
		return retVal

	# Get one line from TCP output, from:
	# http://synack.me/blog/using-python-tcp-sockets
	def __splitLines(self, dataStr):
		"""__splitLines(dataStr)
		
		Split JSON data into lines for individual processing
		"""
		
		# Split on newlines.
		retVal = dataStr.split("\n")
		
		return retVal

	# Queue the ADS-B data for processing.
	def __queueADSB(self, msg, dedupeFlag):
		"""__queueADSB(msg)
		
		Accepts a JSON string and queues it in the Redis database, assuming a duplicate string hasn't been queued within the last n seconds specified in config.py, and we're not dealing with MLAT data. (dedupeFlag = False prevents dedupliation operations.)
		"""
		jsonMsg = self.__jsonify(msg)
		
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


	def __handleIncoming(self, data):
		"""
		__handleIncoming(data)
		
		Try to do something useful with incoming data from our TCP socket. Accepts one argument: the incoming data. Returns nothing.
		"""
		
		# Create a holder for our entry which is none by default.
		thisEntry = self.__jsonStr2Dict(data)
		
		# Check to make sure we have a dict from the JSON parser. If not something went wrong.
		if type(thisEntry) == dict:
			# Tag our data with an entry point.
			thisEntry.update({'entryPoint': 'dump1090ConnSrv'})
			
			# Extract our SSR info.
			ssrData = thisEntry['data']
			
			# Todo: handle MLAT data here.
			if ssrData.find('@') >= 0:
				# This doesn't get deduplicated.
				dedupeFlag = False
				
				# Properly format the "line"
				ssrData = self.__formatSSRMsg(ssrData)
				
				# Split MLAT data from SSR data.
				lineParts = self.__splitMlat(ssrData)
				
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
				formattedSSR = self.__formatSSRMsg(ssrData)
				binData = bytearray(binascii.unhexlify(formattedSSR))
				
				# Properly format the "line"
				thisEntry.update({ 'data': formattedSSR })
				
				# Parse our data and add it to the stream.
				thisEntry.update(self.__ssrParser.ssrParse(binData))
				
			# If the SSR parser got something good out of the SSR data...
			if thisEntry["mode"] != "invalid":
				# Queue up our data.
				self.__queueADSB(thisEntry, dedupeFlag)
		
		return
	
	# This is the prinicipal method that handles data.
	def run(self):
		"""run()
		
		This method is the main method that runs for the connector.
		"""
		
		logger.log("Starting dump1090 connector server on %s:%s..." %(config.d1090ConnSettings['connListenHost'], config.d1090ConnSettings['connListenPort']))
		
		try:
			# Build our TCP socket to recieve the magical happy JSON data we need!
			self.__listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.__listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.__listenSock.bind((config.d1090ConnSettings['connListenHost'], config.d1090ConnSettings['connListenPort']))
			self.__listenSock.listen(10)
			
			# Add our listener socket to our connection list.
			self.__conns.append(self.__listenSock)
		
		except :
			tb = traceback.format_exc()
			logger.log("Exception while trying to open incoming socket:\n%s" %tb)
		
		
		# Fire up ping process
		self.__sendPing()
		
		# Keep processing data as long as we want to keep running.
		while self.__keepRunning:
			
			try:
				# Get the list sockets which are ready to be read through select
				readSockets, writeSockets, errorSockets = select.select(self.__conns,[],[])
			except KeyboardInterrupt:
				logger.log("Keyboard interrupt. Shutting down.")
				self.__keepRunning = False
				self.__myPinger.cancel()
				
				continue
			
			# For each of our sockets...
			for sock in readSockets:
				
				# Create non-string type for data.
				data = None
				
				# If we have a new incoming connection
				if sock == self.__listenSock:
					# Handle the case in which there is a new connection recieved through listenSock
					sockDesc, cltAddr = self.__listenSock.accept()
					
					# Add the new conneciton to the array
					self.__conns.append(sockDesc)
					self.__connAddrs.update({sockDesc: cltAddr})
					
					# Log connection.
					logger.log("New connection from %s:%s" %(cltAddr[0], cltAddr[1]))
					
				# If we have data from a connection.
				else:
					# We have something from a client so let's try to handle it.
					try:
						# Get the incoming data from our socket.
						
						data = sock.recv(self.__buffSz)
						
					except KeyboardInterrupt:
						logger.log("Keyboard interrupt. Shutting down.")
						self.__keepRunning = False
						continue
					
					# Client disconnected.
					except:
						try:
							# Remove the socet from the connection list and keep going.
							self.__conns.remove(sock)
							killedClient = self.__connAddrs.pop(sock)
							
							# Log
							logger.log("Disconnected client %s:%s" %(killedClient[0], killedClient[1]))
						except:
							# Don't do anything since sometimes there's a race condition from the watchdog removing clients and triggering exceptions here.
							None
						
						# Close the socket.
						sock.close()
						
						continue
				
				# If we have some sort of data try to do something useful with it.
				if type(data) is str:
					for thisLine in self.__splitLines(data):
						if thisLine !="":
							self.__handleIncoming(thisLine)
		
		# Shut down our listener socket.
		self.__listenSock.close()
		
		# Print shutdown message.
		logger.log("dump1090Connector runner stopped.")
		
		return

#######################
# Main execution body #
#######################

# If this isn't being executed directly...
if __name__ == "__main__":
	
	# Set up the logger.
	logger = asLog(config.d1090ConnSettings['logMode'])
	
	# If the dump1090 connector should be run
	if config.d1090ConnSettings['enabled']:
		# Create our connector object.
		connector = d1090Connector()
		
		# And run it.
		connector.run()
	else:
		logger.log("The dump1090 connector shouldn't be run according to the configuration.")
