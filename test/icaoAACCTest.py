#!/usr/bin/python

import sys
sys.path.append("..")

from libAirSuck import airSuckUtil
from pprint import pprint

asu = airSuckUtil()

targetICAOHx = ["a41e94", "a37986", "a4e0b9"]

# Loop
for aa in targetICAOHx:
    icaoAAInt = int(aa, 16)
    print("Data for %s: %s" %(aa, asu.getICAOMeta(icaoAAInt)))

# Fixed tests.
print("Egyptair plane: ")
pprint(asu.getICAOMeta(65703))

print("Alaska Airlines plane: ")
pprint(asu.getICAOMeta(10845522))

print("Ethiopia Air plane:")
pprint(asu.getICAOMeta(262230))
