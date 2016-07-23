# -*- coding: utf-8 -*-

import time
import struct
import s2sphere

from colorama import init
from math import cos, asin, sqrt
from geopy.distance import VincentyDistance, vincenty

init()

def distance(lat1, lon1, lat2, lon2):
    return vincenty((lat1, lon2), (lat2, lon2)).meters

def i2f(int):
    return struct.unpack('<d', struct.pack('<Q', int))[0]

def filtered_forts(lat, lng, forts):
    forts = [(fort, distance(lat, lng, fort['latitude'], fort['longitude'])) for fort in forts if fort.get('type',None) == 1 and ("enabled" in fort or lure_info in fort) and (fort.get('cooldown_complete_timestamp_ms',-1) < time.time() * 1000)]
    sorted_forts = sorted(forts, lambda x,y : cmp(x[1],y[1]))
    return [x[0] for x in sorted_forts]

#from pokemongodev slack @erhan
def get_neighbours(loc, level=15, spread=700):
    distance = VincentyDistance(meters=spread)
    center = (loc[0], loc[1], 0)
    p1 = distance.destination(point=center, bearing=45)
    p2 = distance.destination(point=center, bearing=225)
    p1 = s2sphere.LatLng.from_degrees(p1[0], p1[1])
    p2 = s2sphere.LatLng.from_degrees(p2[0], p2[1])
    rect = s2sphere.LatLngRect.from_point_pair(p1, p2)
    region = s2sphere.RegionCoverer()
    region.min_level = level
    region.max_level = level
    cells = region.get_covering(rect)
    return sorted([c.id() for c in cells])

def print_green(message):
    print(u'\033[92m' + message.decode('utf-8') + '\033[0m');

def print_yellow(message):
    print(u'\033[93m' + message.decode('utf-8') + '\033[0m');

def print_red(message):
    print(u'\033[91m' + message.decode('utf-8') + '\033[0m');
