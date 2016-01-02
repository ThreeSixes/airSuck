import sys
sys.path.append("..")

try:
	import config
except:
	raise IOError("No configuration present. Please copy config/config.py to the airSuck folder and edit it.")

import hashlib
import datetime
import redis
import traceback
import binascii
import asLog
import ssrParse
import json
import re

class handler1090:
	def __init__(self, logMode):
		# Set up the logger.
		self.__logger = asLog.asLog(logMode)
		
		# Redis queues and entities
		self.__rQ = redis.StrictRedis(host=config.connRel['host'], port=config.connRel['port'])
		self.__psQ = redis.StrictRedis(host=config.connPub['host'], port=config.connPub['port'])
		self.__dedeupe = redis.StrictRedis(host=config.d1090Settings['dedupeHost'], port=config.d1090Settings['dedupePort'])
		
		# Set the debug flag to off by defualt.
		self.__debugOn = False
		
		# Load the SSR parser.
		self.__ssrParser = ssrParse.ssrParse()
		
		# Compile a regex to verify dump1090 data formatting.
		self.__regex1090 = re.compile("[@*]([a-fA-F0-9])+;")
	
	def __formatSSRMsg(self, strMsg):
		"""
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
	
	def __splitMlat(self, strMsg):
		"""
		Split MLAT and SSR data int an array. Index 0 being MLAT, and Index 1 being SSR.
		"""
		
		# Return the relevant chunks of MLAT data.
		retVal = [strMsg[0:12], strMsg[12:]]
		
		return retVal
	
	def __jsonify(self, dataDict):
		"""		
		Convert a given dictionary to a JSON string.
		"""
		
		retVal = json.dumps(dataDict)
		
		return retVal
	
	def __queueADSB(self, msg, dedupeFlag = True):
		"""
		Accepts a JSON string and queues it in the Redis database, assuming a duplicate string hasn't been queued within the last n seconds specified in redisQueues['dudeupeTableExp'], and we're not dealing with MLAT data. (dedupeFlag = False prevents dedupliation operations.)
		"""
		
		# Set default return value
		retVal = False
		
		# If we have something in the data field that's longer than 2 chars...
		if len(msg['data']) >= 4:
			jsonMsg = self.__jsonify(msg)
			
			# Looks like we have arrived.
			retVal = True
			
			# Set up a hashed version of our data.
			dHash = "ssr-" + hashlib.md5(msg['data']).hexdigest()
			
			# See if we already have the key in the redis cache, or if we're supposed to dedupe this frame at all.
			if ((self.__dedeupe.exists(dHash) == False) or (dedupeFlag == False)):
				# Set the key and insert lame value.
				self.__dedeupe.setex(dHash, config.d1090Settings['dedupeTTLSec'], "X")
			
			# If we are configured to use the connector mongoDB forward the traffic to it.
			if config.connMongo['enabled'] == True:
				self.__rQ.rpush(config.connRel['qName'], jsonMsg)
				
				# Put data on the pub/sub queue.
				self.__psQ.publish(config.connPub['qName'], jsonMsg)
				
				# If we're debugging
				if self.__debugOn:
					self.__logger.log("Enqueued: %s" %str(msg['data']))
			
			else:
			# If we're debugging
				if self.__debugOn:
					self.__logger.log("Dedupe: %s" %str(msg['data']))
		
		return retVal
	
	def setDebug(self, debugOn):
		"""
		Turn debugging on or off.
		"""
		
		if debugOn == True:
			self.__debugOn = True
			self.__logger.log("handler1090 debugging on.")
		else:
			self.__logger.log("handler1090 debugging off.")
		
		return
	
	def handleADSBDict(self, jsonMsg):
		"""
		Handle ADS-B JSON data. If we successfully handle the ADS-B JSON data this returns true. If not it returns false. The return value does not reflect the ADS-B being dropped on the queue. It returns true if we have valid data that might or might not be queued depending on being deduplicated.
		"""
		# Set return value with default failure.
		retVal = False
		
		# Set our "line"...
		thisLine = jsonMsg['data']
		
		# If we have valid data...
		if self.__regex1090.match(thisLine):
			
			# If we have MLAT data...
			if thisLine.find('@') >= 0:
				# This doesn't get deduplicated.
				dedupeFlag = False
				
				# Properly format the "ADS-B"
				thisLine = self.__formatSSRMsg(thisLine)
				
				# Split MLAT data from SSR data.
				lineParts = self.splitMlat(thisLine)
				
				try:
					# Parse the frame.
					binData = bytearray(binascii.unhexlify(lineParts[1]))
				
				except:
					# Blank our incoming data and dump an error.
					binData = ""
					formattedSSR = ""
				
				self.__logger.log("%s got invlaid hex SSR data: %s" %(self.myName, lineParts[1]))
				
				# Set MLAT data and SSR data.
				jsonMsg.update({'mlatData': lineParts[0], 'data': lineParts[1]})
				
				# Add parsed data.
				jsonMsg.update(self.__ssrParser.ssrParse(binData))
			
			else:
				# This gets fed to the deduplicator.
				dedupeFlag = True
				
				# Format our SSR data a hex string and bytearray.
				formattedSSR = self.__formatSSRMsg(thisLine)
				
				try:
					# Parse the frame.
					binData = bytearray(binascii.unhexlify(formattedSSR))
				
				except:
					# Blank our incoming data and dump an error.
					binData = ""
					formattedSSR = ""
					self.__logger.log("%s got invlaid hex SSR data: %s" %(self.myName, formattedSSR))
				
				# Properly format the "line"
				jsonMsg.update({'data': formattedSSR})
				
				# Parse our data and add it to the stream.
				jsonMsg.update(self.__ssrParser.ssrParse(binData))
			
			# If we're in debug mode...
			if self.__debugOn:
				self.__logger.log("Submitting to queuer: %s" %jsonMsg)
			
			# Try to queue up our data.
			retVal = self.__queueADSB(jsonMsg, dedupeFlag)
		
		else:
			# If we're debugging...
			if self.__debugOn:
				logger.log("Dump1090 frame didn't match regex.")
		
		# Return success.
		return retVal