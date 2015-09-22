# Test decoding of AIS frames. Test subjects go in the someFrames array.
from aisParse import aisParse
from pprint import pprint
import binascii

# Load AIS parser.
parser = aisParse()

# Three sample frames
someFrames = [
    #"!AIVDM,1,1,,A,15ND6u0P1@G6W1NIaNGEGwwh0@QB,0*0B",
    #"!AIVDM,1,1,,A,1mNLuDPP00o9hoFJMQcT=Owf0000,0*5C",
    #"!AIVDM,1,1,,A,1G7IP7001po2F5BJKwfbSHcj0000,0*04",
    #"!AIVDM,1,1,,A,1ENIDI0000o>0ClJ5LMM7DEl2000,0*7D",
    #"!AIVDM,1,1,,A,1UNPDm?P00G>21nJ7nC00?wj0000,0*7C",
    #"!AIVDM,1,1,,A,152OiD000oG5Lh<JStUpD6h200S0,0*44",
    "!AIVDM,1,1,,A,1C8hLj0000o><JLJ7K6PsWr20000,0*7D",
    "!AIVDM,1,1,,B,15N9QTg00Do725fJ7Qf>0K6j00S3,0*7A",
    #"!AIVDM,1,1,,A,403OtViuvJE;`o?lfhJ;1u7026`d,0*42",
    "!AIVDM,1,1,,A,4@3QiWAuvJE;Wo=vUTJE:KG00<1u,0*4B",
    "!AIVDM,1,1,,B,403OtViuvJE;jo?lfhJ;1u7026`d,0*4B",
    "!AIVDM,1,1,,B,4@3QiWAuvJE;io=vUTJE:KG00@MV,0*55"#,
    #"!AIVDM,1,1,,A,3ENO73UP00o=pm0J?nVKQ?wn2000,0*5C",
    #"!AIVDM,1,1,,A,8ENJJN0j2P00000000000@J50000,0*6C",
    #"!AIVDM,1,1,,A,B52QlLh0<eim4sVQM1LaKwrUoP06,0*24",
    #"!AIVDM,1,1,,A,Evkb9Mq1WV:VQ4Ph94c@6;Q@1a@;ShvA==bd`00003vP000,2*4C",
    #"!AIVDM,1,1,,A,HE2KRclU1=3PPPP00000001`3550,0*07",
    #"!AIVDM,2,1,1,A,5URvPH02>AWK<Dlr221A8U@tr1<D4MDhj2222216DhH@@6I?0@T3lU30CQ;5DhH8,0*1E",
    #"!AIVDM,2,2,1,A,8888880,2*25"
]

# Actviate name-parsing
#parser.setReturnNames(True)

# For each frame
for thisFrame in someFrames:
    
    # Get our dict of info from the parsed frame.
    data = parser.aisParse(thisFrame)

    # Dump the dict.
    pprint(data)