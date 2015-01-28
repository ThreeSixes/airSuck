# Test decoding of SSR frames. Test subjects go in the someFrames array.


from ssrParse import ssrParse
from pprint import pprint

# SSRPrase image
parser = ssrParse()

# Three sample frames
someFrames = [
    "0225", # Mode A Squawk 0225
    "2610", # Mode A Squawk 2610/ Mode C altitude 13300 ft.
    "5da189a7b82d24", # DF11 All-call relpy.
    "8da15e719941be06306c00b1e7db", # DF17, airborne veloicty
    "8D75804B580FF2CF7E9BA6F701D0", # DF17, airborne position, even formation
    "8D75804B580FF6B283EB7A157117" # DF17, airborne position, odd formation
    ]

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