from cprMath import cprMath

cprDecoder = cprMath()

surface = False
dataPoints = [
	# Formatted in [[even lat, even lon], [odd lat, odd lon], last format]
	[[92095, 39846], [88385, 125818], 1],
	[[26825, 26641], [36192, 128497], 1]
]

# Debug for our mental heath.
cprDecoder.debugToggle(True)

for thisPoint in dataPoints:
	coords = cprDecoder.decodeCPR(thisPoint[0], thisPoint[1], thisPoint[2], surface)
	if coords != False:
		print str(coords[0]) + ", " + str(coords[1])
	else:
		print "Bad data."