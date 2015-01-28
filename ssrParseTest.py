# Test decoding of SSR frames. Test subjects go in the someFrames array.


from ssrParse import ssrParse
from pprint import pprint

# SSRPrase image
parser = ssrParse()

# Three sample frames
someFrames = ["0225", "5da189a7b82d24", "8da15e719941be06306c00b1e7db", "2610"]

# Actviate name-parsing
parser.setReturnNames(True)

# For each frame
for asciiFrame in someFrames:
    # Convert the hex to a string.
    thisFrame = parser.asciiHx2Str(asciiFrame)
    # Get our dict of info from the parsed frame.
    data = parser.ssrParse(thisFrame)

    # Dump the dict.
    pprint(data)