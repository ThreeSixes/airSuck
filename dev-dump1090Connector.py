#!/usr/bin/python

"""
dump1090Connector by ThreeSixes (https://github.com/ThreeSixes)

This project is licensed under GPLv3. See COPYING for dtails.

This file is part of the airSuck project (https://github.com/ThreeSixes/airSUck).
"""

###########
# Imports #
###########

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
import ssrParse
import config
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
		
		# Buffer size settings.
		self.__buffSz = 4096 # 4K
		
		# Should we keep running?
		self.__keepRunning = True
		
		# Reliable queue object
		self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
		
		# Pub/sub queue object
		self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
		
		# Dedupe object
		self.__dedupe = redis.StrictRedis(host=config.d1090ConnSettings['dedupeHost'], port=config.d1090ConnSettings['dedupePort'])
		
		# Create our SSR parser.
		self.__ssrParser = ssrParse.ssrParse()
	
	def __log(self, logEvt):
		"""
		__log(logEvt)
		
		Log data to stdout with a timestamp.
		"""
		
		# Get timestamp.
		dts = str(datetime.datetime.utcnow())
		
		# Keep the log looking pretty and uniform.
		if len(dts) == 19:
			dts = dts + ".000000"
		
		print(dts + " - " + logEvt)
	
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
		
		return retVal
	
	# Queue the ADS-B data for processing.
	def __queueADSB(self, msg, dedupeFlag):
		"""__queueADSB(msg)
		
		Accepts a JSON string and queues it in the Redis database, assuming a duplicate string hasn't been queued within the last n seconds specified in config.py, and we're not dealing with MLAT data. (dedupeFlag = False prevents dedupliation operations.)
		"""
		
		# Create JSON message.
		jsonMsg = self.__jsonify(msg)
		
		# Don't actually enqueue data. Just test.
		print("Enqueue " + jsonMsg)
		
		# See if we already have the key in the redis cache, or if we're supposed to dedupe this frame at all.
		#if ((self.__dedupe.exists(msg['data']) == False) or (dedupeFlag == False)):
			# Set the key and insert lame value.
			#self.__dedupe.setex(msg['data'], config.d1090ConnSettings['dedupeTTLSec'], "X")
			
			# If the system is configured to use mongoDB connector data...
			#if config.connMongo['enabled']:
				# Push the JSON data onto our reliable queue.
			#	self.__rQ.rpush(config.connRel['qName'], jsonMsg)
			
			# Publish the data to our pub/sub queue.
			#self.__psQ.publish(config.connPub['qName'], jsonMsg)
		
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
		
		self.__log("Starting dump1090 connector...")
		
		try:
			# Build our TCP socket to recieve the magical happy JSON data we need!
			listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			listenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			listenSock.bind((config.d1090ConnSettings['connListenHost'], config.d1090ConnSettings['connListenPort']))
			listenSock.listen(10)
			
			# Add our listener socket to our connection list.
			self.__conns.append(listenSock)
		
		except Exception as e:
			self.__log("Exception while trying to open incoming socket:\n" + str(e))
		
		# Keep processing data as long as we want to keep running.
		while self.__keepRunning:
			
			try:
				# Get the list sockets which are ready to be read through select
				readSockets, writeSockets, errorSockets = select.select(self.__conns,[],[])
			except KeyboardInterrupt:
				self.__log("Keyboard interrupt. Shutting down.")
				self.__keepRunning = False
				continue
			
			# For each of our sockets...
			for sock in readSockets:
				
				# Create non-string type for data.
				data = None
				
				# If we have a new incoming connection
				if sock == listenSock:
					# Handle the case in which there is a new connection recieved through listenSock
					sockDesc, cltAddr = listenSock.accept()
					
					# Add the new conneciton to the array
					self.__conns.append(sockDesc)
					
					# Log connection.
					self.__log("New connection from " + str(cltAddr[0]) + ":" + str(cltAddr[1]))
					
				# If we have data from a connection.
				else:
					# We have something from a client so let's try to handle it.
					try:
						# Get the incoming data from our socket.
						data = sock.recv(self.__buffSz)
						
					except KeyboardInterrupt:
						self.__log("Keyboard interrupt. Shutting down.")
						self.__keepRunning = False
						continue
					
					# Client disconnected.
					except:
						self.__log("Client " + str(cltAddr[0]) + ":" + str(cltAddr[1]) + " disconnected")
						
						# Close the socket.
						sock.close()
						
						# Remove the socet from the connection list and keep going.
						self.__conns.remove(sock)
						continue
				
				# If we have some sort of data try to do something useful with it.
				if type(data) is str:
					self.__handleIncoming(data)
		
		# Shut down our listener socket.
		listenSock.close()
		
		# Print shutdown message.
		self.__log("dump1090Connector runner stopped.")

#######################
# Main execution body #
#######################

# If this isn't being executed directly...
if __name__ == "__main__":
	# If the dump1090 connector should be run
	if config.d1090ConnSettings['enabled']:
		# Create our connector object.
		connector = d1090Connector()
		
		# And run it.
		connector.run()
	else:
		print("The dump1090 connector shouldn't be run according to the configuration.")
	