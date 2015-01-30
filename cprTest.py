from cprMath import cprMath

cprDecoder = cprMath()

surface = False
dataPoints = [
	# Formatted in [[even lat, even lon], [odd lat, odd lon], last format]
	[[92095, 39846], [88385, 125818], 1], # This decodes correctly, from http://www.lll.lu/~edward/edward/adsb/DecodingADSBposition.html
	[[24745, 21412], [15637, 50148], 1]  # This doesn't decode properly. It's on the wrong side of the world, should be off the coast of Florida near -80.xxx, 24-25.xxx
]

# Debug for our mental heath.
cprDecoder.debugToggle(True)

for thisPoint in dataPoints:
	coords = cprDecoder.decodeCPR(thisPoint[0], thisPoint[1], thisPoint[2], surface)
	if coords != False:
		print(str(coords[0]) + ", " + str(coords[1]))
	else:
		print("Bad data.")