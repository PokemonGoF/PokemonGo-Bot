import struct
from math import cos, asin, sqrt


def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) * 1000

def i2f(int):
    return struct.unpack('<d', struct.pack('<Q', int))[0]
	
def print_green(message)
    print('\033[92m' + message + '\033[0m');

def print_yellow(message)
    print('\033[93m' + message + '\033[0m');

def print_red(message)
    print('\033[91m' + message + '\033[0m');