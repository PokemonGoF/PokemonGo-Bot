# -*- coding: utf-8 -*-

import struct
from math import asin, atan, cos, exp, log, pi, sin, sqrt, tan

from colorama import init
from networkx.algorithms.clique import find_cliques

import networkx as nx
import numpy as np

init()

TIME_PERIODS = (
    (60, 'minute'),
    (3600, 'hour'),
    (86400, 'day'),
    (86400*7, 'week')
)

FORT_CACHE = {}
def fort_details(bot, fort_id, latitude, longitude):
    """
    Lookup fort metadata and (if possible) serve from cache.
    """

    if fort_id not in FORT_CACHE:
        """
        Lookup the fort details and cache the response for future use.
        """
        request = bot.api.create_request()
        request.fort_details(fort_id=fort_id, latitude=latitude, longitude=longitude)
        try:
            response_dict = request.call()
            FORT_CACHE[fort_id] = response_dict['responses']['FORT_DETAILS']
        except Exception:
            pass

    # Just to avoid KeyErrors
    return FORT_CACHE.get(fort_id, {})

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


def float_equal(f1, f2, epsilon=1e-8):
  if f1 > f2:
    return f1 - f2 < epsilon
  if f2 > f1:
    return f2 - f1 < epsilon
  return True


# pseudo mercator projection
EARTH_RADIUS_MAJ = 6378137.0
EARTH_RADIUS_MIN = 6356752.3142
RATIO = (EARTH_RADIUS_MIN / EARTH_RADIUS_MAJ)
ECCENT = sqrt(1.0 - RATIO**2)
COM = 0.5 * ECCENT


def coord2merc(lat, lng):
    return lng2x(lng), lat2y(lat)


def merc2coord(vec):
    return y2lat(vec[1]), x2lng(vec[0])


def y2lat(y):
    ts = exp(-y / EARTH_RADIUS_MAJ)
    phi = pi / 2.0 - 2 * atan(ts)
    dphi = 1.0
    for i in range(15):
        if abs(dphi) < 0.000000001:
            break
        con = ECCENT * sin(phi)
        dphi = pi / 2.0 - 2 * atan (ts * pow((1.0 - con) / (1.0 + con), COM)) - phi
        phi += dphi
    return rad2deg(phi)


def lat2y(lat):
    lat = min(89.5, max(lat, -89.5))
    phi = deg2rad(lat)
    sinphi = sin(phi)
    con = ECCENT * sinphi
    con = pow((1.0 - con) / (1.0 + con), COM)
    ts = tan(0.5 * (pi * 0.5 - phi)) / con
    return 0 - EARTH_RADIUS_MAJ * log(ts)


def x2lng(x):
    return rad2deg(x) / EARTH_RADIUS_MAJ


def lng2x(lng):
    return EARTH_RADIUS_MAJ * deg2rad(lng);


def deg2rad(deg):
    return deg * pi / 180.0


def rad2deg(rad):
    return rad * 180.0 / pi


def find_biggest_cluster(radius, points, order=None):
    graph = nx.Graph()
    for point in points:
            if order is 'lure_info':
                f = point['latitude'], point['longitude'], point['lure_info']['lure_expires_timestamp_ms']
            else:
                f = point['latitude'], point['longitude'], 0
            graph.add_node(f)
            for node in graph.nodes():
                if node != f and distance(f[0], f[1], node[0], node[1]) <= radius*2:
                    graph.add_edge(f, node)
    cliques = list(find_cliques(graph))
    if len(cliques) > 0:
        max_clique = max(list(find_cliques(graph)), key=lambda l: (len(l), sum(x[2] for x in l)))
        merc_clique = [coord2merc(x[0], x[1]) for x in max_clique]
        clique_x, clique_y = zip(*merc_clique)
        best_point = np.mean(clique_x), np.mean(clique_y)
        best_coord = merc2coord(best_point)
        return {'latitude': best_coord[0], 'longitude': best_coord[1], 'num_points': len(max_clique)}
    else:
        return None
