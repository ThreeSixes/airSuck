# Test decoding of SSR frames. Test subjects go in the someFrames array.
from libAirSuck import ssrParse
from pprint import pprint
import binascii

# SSRPrase image
parser = ssrParse()

# Three sample frames
someFrames = [
    "0225", # Mode A Squawk 0225
    "2610", # Mode A Squawk 2610/ Mode C altitude 13300 ft.
    "5da189a7b82d24", # DF11 All-call relpy.
    "8da15e719941be06306c00b1e7db", # DF17, airborne veloicty
    "8D75804B580FF2CF7E9BA6F701D0", # DF17, airborne position, even formation
    "8D75804B580FF6B283EB7A157117", # DF17, airborne position, odd formation
    "8D7C6D2B2058F6B9CF9820000000", # DF17, aircraft ID and category info, bad CRC
    "8da11136e11c280000000074397e", # DF17, ES Should squawk 1330
    "280010839b69fd" # DF 5, unknown squawk
    ]

# Actviate name-parsing
parser.setReturnNames(True)

# For each frame
for asciiFrame in someFrames:
    # Convert the hex to a string.
    thisFrame = binascii.unhexlify(asciiFrame)
    
    # Convert our binary data string to a byte array.
    binData = bytearray(thisFrame)

    # Get our dict of info from the parsed frame.
    data = parser.ssrParse(binData)

    # Dump the dict.
    pprint(data)