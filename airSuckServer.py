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
		
		# Constraints for latitude and longitude. Used by expectedVars.
		latConstraint = {'min': -90, 'max': 90}
		lonConstraint = {'min': -180, 'max': 180}
		
		# Input JSON data check and type conversion happens here. We create this variable in the constructor rather than in __verifyJSON() since it's used over and over again.
		self.__expectedVars = {
			"clientName": {'mandatory': True, 'type': str}, # Mandatory string with the client's name..
			"dataOrigin": {'mandatory': True, 'type': str, 'possVals': ['airSuckClient']}, # Mandatory string describing the data origin.
			"dts": {'mandatory': True, 'type': str}, # Mandatory date time indicating when the message was recieved.
			"type": {'mandatory': True, 'type': str, 'possVals': ['airSSR', 'airAIS']}, # Mandatory string with specific possible values.
			"data": {'mandatory': True, 'type': str}, # Mandatory string containing the data.
			"clientLat": {'mandatory': False, 'type': float, 'constraints': latConstraint}, # Optoinal float containing the client's latitude.
			"clientLon": {'mandatory': False, 'type': float, 'constraints': lonConstraint}, # Optional float containing the client's longitude.
			"clientPosMeta": {'mandatory': False, 'type': str, 'possVals': ['manual', 'gps']} # Optional string containg metadata about the client's posistion data.
		}
	
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
					sendRes = thisSock.send(self.__keepaliveJSON + "\n")
					
					# If we weren't able to send anything...
					if sendRes == 0:
						# Cause a small explosion.
						raise RuntimeError("Socked failed to send data. The connection is down.")
				
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
		
		# See if we have bad data...
		failboat = False
		
		try:
			# Loop through all the data items we get.
			for entry, entryParams in self.__expectedVars.iteritems():
				
				# Create a holder for our value of the specified type.
				thisVal = entryParams['type']
				
				# See if the key is mandatory.
				if entryParams['mandatory']:
					# If we have the specified mandatory entry...
					if entry in dataDict:
						# Awesome. Keep going.
						pass
					else:
						# Throw an exception.
						raise RuntimeError("Missing mandatory key %s." %entry)
				
				# Check for each value if we pass our 'mandatory' value checks...
				if entry in dataDict:
					# See if we are type-correct... If this throws an exception we screwed up.
					thisVal = entryParams['type'](dataDict[entry]) 
					
					# Check for possible values.
					if 'possVals' in entryParams:
						# See if we have a good value.
						goodVal = False
						
						# Loop through expected values to see if we a valid entry.
						for expectedVal in entryParams['possVals']:
							# If we have a match
							if thisVal == expectedVal:
								# Flag this as a good value.
								goodVal = True
						
						# If we don't have good data...
						if goodVal == False:
							# Raise an exception.
							raise RuntimeError("Value for %s not in list of possible values." %entry)
					
					# Check for constraints
					if 'constraints' in entryParams:
						
						# If we have a minimum.
						if 'min' in entryParams['constraints']:
							if thisVal < entryParams['constraints']['min']:
								raise RuntimeError("Value for %s violated minimum constraint." %entry)
						
						# If we have a maximum.
						if 'max' in entryParams['constraints']:
							if thisVal > entryParams['constraints']['max']:
								raise RuntimeError("Value for %s violated maximum constraint." %entry)
					
					# Add our good stuff to the accumulator since we're good.
					accumulator.update({entry: thisVal})
			
			
			# If we're debugging...
			if config.airSuckSrvSettings['debug']:
				logger.log("Type-corrected data: %s" %accumulator)
			
		except RuntimeError:
			# If we're debuggging.
			# Do debugging things.
			
			# Dump our exception.
			tb = traceback.format_exc()
			logger.log("Unable to verify JSON data:\n%s" %tb)
			
			# Flag failure.
			failboat = True
		
		except:
			# Get traceback and display it.
			tb = traceback.format_exc()
			logger.log("Unhandled exception verifying JSON:\n%s" %tb)
			
			# Do some extra debugging stuff if that's our thing.
			
			failboat = True
		
		# If we have good data return good data.
		if failboat == False:
			# Add our accumulated data to the return value.
			retVal.update(accumulator)
		
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
		# A blank dict to hold our data.
		retVal = {}
		
		try:
			# Get a dict from the incoming JSON string.
			retVal = json.loads(thisStr)
		
		except ValueError:
			# If it doesn't work just set retVal to none.
			retVal = None
			
			if config.airSuckSrvSettings['debug']:
				tb = traceback.format_exc()
				logger.log("Failed to parse JSON data.\nString: %s\n%s" %(thisStr, tb))
			
			else:
				logger.log("Failed to parse JSON data.")
		
		except Exception as e:
			# If it doesn't work just set retVal to none.
			retVal = None
			
			tb = traceback.format_exc()
			logger.log("Unhandled exception parsing JSON:\n%s\nString: %s" %(thisStr, tb))
			
			raise e
		
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
		Try to do something useful with incoming data from our TCP socket. Accepts one argument: the incoming data. Returns nothing.
		"""
		
		# Create temporary holder for data.
		thisEntry = {}
		
		try:
			# Update our data holder with values from the data string.
			thisEntry.update(self.__jsonStr2Dict(data))
			
			# If we don't have a blank dict...
			if len(thisEntry) > 0:
				try:
					# Type-correct our JSON data and make sure it's all there.
					thisEntry.update(self.__verifyJSON(thisEntry))
				
				except:
					# If we're debugging...
					if config.airSuckSrvSettings['debug']:
						tb = traceback.format_exc()
						logger.log("AirSuck server blew up verifying JSON:\n%s" %tb)
				
				# Add chain-of-custody data.
				thisEntry.update({'entryPoint': 'airSuckServer', 'src': config.airSuckSrvSettings['myName']})
				
				# If we're supposed to debug...
				if config.airSuckSrvSettings['debug']:
					logger.log("Handling: %s" %thisEntry)
				
				# Handle the entry dictionary and set our flag.
				d1090Status = h1090.handleADSBDict(thisEntry)
				
				# If it worked reset the lastADSB counter.
				if (not d1090Status) and config.airSuckSrvSettings['debug']:
					logger.log("Failed to queue %s." %thisEntry)
			
			else:
				if config.airSuckSrvSettings['debug']:
					tb = traceback.format_exc()
					logger.log("Unable to proces incoming JSON data:\n%s" %tb)
				else:
					logger.log("Unable to proces incoming JSON data.")
		
		except:
			tb = traceback.format_exc()
			logger.log("Failed to handle incoming data: %s\n%s" %(data, tb))
		
		return
	
	# This is the prinicipal method that handles data.
	def run(self):
		"""
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
	
	# If we're debugging...
	if config.airSuckSrvSettings['debug']:
		pprint(config.airSuckSrvSettings)
	
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
