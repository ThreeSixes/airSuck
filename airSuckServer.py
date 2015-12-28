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
from libAirSuck import asLog
from libAirSuck import handler1090
from pprint import pprint

########################
# airSuck server class #
########################

class airSuckServer():
	"""airSuckServer class
	This class is a server for the airSuck stack. It accepts data from the airSuck client.
	"""

	def __init__(self):		
		# Class-wide list of connections.
		self.__conns = []
		self.__connAddrs = {}
		
		# Keepalive stuff
		self.__keepaliveJSON = "{\"keepalive\": \"abcdef\"}"
		
		# Buffer size settings.
		self.__buffSz = 4096 # 4K
		
		# Should we keep running?
		self.__keepRunning = True
	
	# Send a "ping" to connected hosts.
	def __sendPing(self):
		"""
		Send a ping to all connected hosts.
		"""
		
		# For each client we have send the ping JSON sentence.
		for thisSock in self.__conns:
			
			# If we're not the listener send data.
			if thisSock != self.__listenSock:
				# We have something from a client so let's try to handle it.
				try:
					# If we're supposed to debug...
					if config.airSuckSrvSettings['debug']:
						logger.log("Send keepalive.")
					
					# Get the incoming data from our socket.
					thisSock.send(self.__keepaliveJSON + "\n")
				
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
					logger.log("Can't send a keepalive to %s:%s. Disconnecting them." %(killedClient[0], str(killedClient[1])))
		
		try:
			# Respawn the pinger.
			self.__myPinger = threading.Timer(config.d1090ConnSettings['clientPingInterval'], self.__sendPing)
			self.__myPinger.start()
		
		except KeyboardInterrupt:
			self.__keepRunning = False
	
	# Verify incoming JSON data from clients.
	def __verifyJSON(self, dataDict):
		"""
		Type-check incoming JSON data to make sure it's sane. We accept a data dictionary and return a dictionary with relevant and valid data. The returned dictionary will be empty if something blows up.
		"""
		
		# Blank return dict.
		retVal = {}
		
		# Temporary storage for values.
		accumulator = {}
		
		# Attempt to convert these elements to their relevant type...
		expectedVars = {
			"clientName": {'mandatory': True, 'type': str}, # Mandatory string with the client's name..
			"dataOrigin": {'mandatory': True, 'type': str, 'possVals': ['airSuckClient']}, # Mandatory string describing the data origin.
			"dts": {'mandatory': True, 'type': str}, # Mandatory date time indicating when the message was recieved.
			"type": {'mandatory': True, 'type': str, 'possVals': ['airSSR', 'airAIS']}, # Mandatory string with specific possible values.
			"data": {'mandatory': True, 'type': str}, # Mandatory string containing the data.
			"clientLat": {'mandatory': False, 'type': float}, # Optoinal float containing the client's latitude.
			"clientLon": {'mandatory': False, 'type': float}, # Optional float containing the client's longitude.
			"clientPosMeta": {'mandatory': False, 'type': str} # Optional string containg metadata about the client's posistion data.
		}
		
		# If we have good data return good data.
		if failboat == False:
			# Add our accumulated data to the return value.
			retVal.updated(accumulator)
		
		# Return our data.
		return retVal
	
	# Convert the message to JSON format
	def __jsonify(self, dataDict):
		"""
		Convert a given dictionary to a JSON string.
		"""
		
		retVal = json.dumps(dataDict)
		return retVal
	
	# Convert JSON string to a dict.
	def __jsonStr2Dict(self, thisStr):
		"""
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
		"""
		Split JSON data into lines for individual processing
		"""
		
		# Split on newlines.
		retVal = dataStr.split("\n")
		
		return retVal

	def __handleIncoming(self, data):
		"""
		__handleIncoming(data)
		
		Try to do something useful with incoming data from our TCP socket. Accepts one argument: the incoming data. Returns nothing.
		"""
		
		# Create a holder for our entry which is none by default.
		thisEntry = self.__jsonStr2Dict(data)
		
		thisEntry.update({'entryPoint': 'dump1090ConnClt'})
		
		# If we're supposed to debug...
		if config.airSuckSrvSettings['debug']:
			logger.log("Handling: %s" %thisEntry)
		
		# Handle the entry dictionary and set our flag.
		d1090Status = h1090.handleADSBDict(thisEntry)
		
		# If it worked reset the lastADSB counter.
		if (not d1090Status) and config.airSuckSrvSettings['debug']:
			logger.log("Failed to queue %s." %thisEntry)
		
		return
	
	# This is the prinicipal method that handles data.
	def run(self):
		"""run()
		
		This method is the main method that runs for the connector.
		"""
		
		logger.log("Starting airSuck server on %s:%s..." %(config.d1090ConnSettings['connListenHost'], config.d1090ConnSettings['connListenPort']))
		
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
						
						# Do we have keepalive JSON?
						if thisLine.strip() == self.__keepaliveJSON:
							# If we're supposed to debug...
							if config.airSuckSrvSettings['debug']:
								logger.log("Received keepalive.")
						
						# If we have a non-blank line...
						elif thisLine !="":
							# If we're supposed to debug...
							if config.airSuckSrvSettings['debug']:
								logger.log("Incoming: %s" %data.strip())
							
							# Handle incoming data.
							self.__handleIncoming(thisLine)
		
		# Shut down our listener socket.
		self.__listenSock.close()
		
		# Print shutdown message.
		logger.log("airSuck server runner stopped.")
		
		return

#######################
# Main execution body #
#######################

# If this isn't being executed directly...
if __name__ == "__main__":
	
	# Set up the logger.
	logger = asLog(config.airSuckSrvSettings['logMode'])
	
	# Log our startup.
	logger.log("Starting the airSuck server...")
	
	# If the dump1090 connector should be run
	if config.airSuckSrvSettings['enabled']:
		# Set up the dump1090 handler.
		h1090 = handler1090(config.airSuckSrvSettings['logMode'])
		
		# Configure the dump1090 handler's debug mode based on our configured mode.
		h1090.setDebug(config.airSuckSrvSettings['debug'])
		
		# Create our connector object.
		airSuckSrv = airSuckServer()
		
		# And run it.
		airSuckSrv.run()
	else:
		logger.log("The airSuck server shouldn't be run according to the configuration.")
