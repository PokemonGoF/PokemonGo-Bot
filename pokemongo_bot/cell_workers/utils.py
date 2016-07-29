# -*- coding: utf-8 -*-

import struct
from math import cos, asin, sqrt
from colorama import init
from s2sphere import CellId, LatLng
init()

TIME_PERIODS = (
    (60, 'minute'),
    (3600, 'hour'),
    (86400, 'day'),
    (86400*7, 'week')
)


def get_cellid(lat, long, radius=10):
    origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
    walk = [origin.id()]

    # 10 before and 10 after
    next = origin.next()
    prev = origin.prev()
    for i in range(radius):
        walk.append(prev.id())
        walk.append(next.id())
        next = next.next()
        prev = prev.prev()
    return sorted(walk)

def encode(cellid):
    output = []
    encoder._VarintEncoder()(output.append, cellid)
    return ''.join(output)

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * \
        cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) * 1000


def convert(distance, from_unit, to_unit):  # Converts units
    # Example of converting distance from meters to feet:
    # convert(100.0,"m","ft")
    conversions = {
        "mm": {"mm": 1.0,
               "cm": 1.0 / 10.0,
               "m": 1.0 / 1000.0,
               "km": 1.0 / 1000000,
               "ft": 0.00328084,
               "yd": 0.00109361,
               "mi": 1.0 / 1609340.0007802},
        "cm": {"mm": 10.0,
               "cm": 1.0,
               "m": 1.0 / 100,
               "km": 1.0 / 100000,
               "ft": 0.0328084,
               "yd": 0.0109361,
               "mi": 1.0 / 160934.0},
        "m": {"mm": 1000,
              "cm": 100.0,
              "m": 1.0,
              "km": 1.0 / 1000.0,
              "ft": 3.28084,
              "yd": 1.09361,
              "mi": 1.0 / 1609.34},
        "km": {"mm": 100000,
               "cm": 10000.0,
               "m": 1000.0,
               "km": 1.0,
               "ft": 3280.84,
               "yd": 1093.61,
               "mi": 1.0 / 1.60934},
        "ft": {"mm": 1.0 / 328.084,
               "cm": 1.0 / 32.8084,
               "m": 1.0 / 3.28084,
               "km": 1 / 3280.84,
               "ft": 1.0,
               "yd": 1.0 / 3.0,
               "mi": 1.0 / 5280.0},
        "yd": {"mm": 1.0 / 328.084,
               "cm": 1.0 / 32.8084,
               "m": 1.0 / 3.28084,
               "km": 1 / 1093.61,
               "ft": 3.0,
               "yd": 1.0,
               "mi": 1.0 / 1760.0},
        "mi": {"mm": 1609340.0007802,
               "cm": 160934.0,
               "m": 1609.34,
               "km": 1.60934,
               "ft": 5280.0,
               "yd": 1760.0,
               "mi": 1.0}
    }
    return distance * conversions[from_unit][to_unit]


def dist_to_str(distance, unit):
    return '{:.2f}{}'.format(distance, unit)


def format_dist(distance, unit):
    # Assumes that distance is in meters and converts it to the given unit, then a formatted string is returned
    # Ex: format_dist(1500, 'km') returns the string "1.5km"
    return dist_to_str(convert(distance, 'm', unit), unit)


def format_time(seconds):
    # Return a string displaying the time given as seconds or minutes
    num, duration = 0, long(round(seconds))
    runtime = []
    for period, unit in TIME_PERIODS[::-1]:
        num, duration = divmod(duration, period)
        if num:
            p = '{0}{1}'.format(unit, 's'*(num!=1))
            runtime.append('{0} {1}'.format(num, p))

    runtime.append('{0} second{1}'.format(duration, 's'*(duration!=1)))

    return ', '.join(runtime)


def i2f(int):
    return struct.unpack('<d', struct.pack('<Q', int))[0]


def print_green(message):
    print(u'\033[92m' + message.decode('utf-8') + '\033[0m')


def print_yellow(message):
    print(u'\033[93m' + message.decode('utf-8') + '\033[0m')


def print_red(message):
    print(u'\033[91m' + message.decode('utf-8') + '\033[0m')
