# -*- coding: utf-8 -*-

import struct
from math import cos, asin, sqrt
from colorama import init
init()

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) * 1000

def convert(distance, from_unit, to_unit): # Converts units
    # Ex: Convert distance from meters to feet
    # convert(100.0,"m","ft")
    conversions = {
        "mm": {"mm": 1.0, "cm": 1.0 / 10.0, "m": 1.0 / 1000.0, "km": 1.0 / 1000000, "ft": 0.00328084, "yd": 0.00109361, "mi": 1.0 / 1609340.0007802},
        "cm": {"mm": 10.0, "cm": 1.0, "m": 1.0 / 100, "km": 1.0 / 100000, "ft": 0.0328084, "yd": 0.0109361, "mi": 1.0 / 160934.0},
        "m": {"mm": 1000, "cm": 100.0, "m": 1.0, "km": 1.0 / 1000.0, "ft": 3.28084, "yd": 1.09361, "mi": 1.0 / 1609.34},
        "km": {"mm": 100000, "cm": 10000.0, "m": 1000.0, "km": 1.0, "ft": 3280.84, "yd": 1093.61, "mi": 1.0 / 1.60934},
        "ft": {"mm": 1.0 / 328.084, "cm": 1.0 /32.8084, "m": 1.0 / 3.28084, "km": 1 / 3280.84, "ft": 1.0, "yd": 1.0 / 3.0, "mi": 1.0 / 5280.0},
        "yd": {"mm": 1.0 / 328.084, "cm": 1.0 /32.8084, "m": 1.0 / 3.28084, "km": 1 / 1093.61, "ft": 3.0, "yd": 1.0, "mi": 1.0 / 1760.0},
        "mi": {"mm": 1609340.0007802, "cm": 160934.0, "m": 1609.34, "km": 1.60934, "ft": 5280.0, "yd": 1760.0, "mi": 1.0}
    }
    return distance * conversions[from_unit][to_unit]

def dist_to_str(distance, unit):
    return '{}{}'.format(distance, unit)

def i2f(int):
    return struct.unpack('<d', struct.pack('<Q', int))[0]

def print_green(message):
    print(u'\033[92m' + message.decode('utf-8') + '\033[0m');

def print_yellow(message):
    print(u'\033[93m' + message.decode('utf-8') + '\033[0m');

def print_red(message):
    print(u'\033[91m' + message.decode('utf-8') + '\033[0m');
