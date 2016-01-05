#!/usr/bin/python

import sys
sys.path.append("..")

from libAirSuck import airSuckUtil
from pprint import pprint

asu = airSuckUtil()

print("Egyptair plane: ")
pprint(asu.getICAOMeta(65703))

print("Alaska Airlines plane: ")
pprint(asu.getICAOMeta(10845522))

print("Ethiopia Air plane:")
pprint(asu.getICAOMeta(262230))
