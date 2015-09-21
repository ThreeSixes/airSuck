# Test decoding of AIS frames. Test subjects go in the someFrames array.
from aisParse import aisParse
from pprint import pprint
import binascii

# Load AIS parser.
parser = aisParse()

# Three sample frames
someFrames = [
    "!AIVDM,1,1,,B,15N9QTg00Do725fJ7Qf>0K6j00S3,0*7A",
    "!AIVDM,1,1,,B,1ENP@H0P00G><TLJ4N@V=gvj0000,0*1A",
    "!AIVDM,1,1,,B,1E?Ebp0vj@o:?wtJMtqkhk4l0000,0*0E"
]

# Actviate name-parsing
#parser.setReturnNames(True)

# For each frame
for thisFrame in someFrames:
    
    # Get our dict of info from the parsed frame.
    data = parser.aisParse(thisFrame)

    # Dump the dict.
    pprint(data)