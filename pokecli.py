#!/usr/bin/env python
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

import os
import re
import json
import struct
import logging
import requests
import argparse
import working
import time
import ssl
import sys

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

from pgoapi import PGoApi
from pgoapi.utilities import f2i

from google.protobuf.internal import encoder
from geopy.geocoders import GoogleV3
from s2sphere import CellId, LatLng

log = logging.getLogger(__name__)

global config

def get_pos_by_name(location_name):
    geolocator = GoogleV3()
    loc = geolocator.geocode(location_name)

    log.info('Your given location: %s', loc.address.encode('utf-8'))
    log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

    return (loc.latitude, loc.longitude, loc.altitude)

def get_cellid(lat, long):
    origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
    walk = [origin.id()]

    # 10 before and 10 after
    next = origin.next()
    prev = origin.prev()
    for i in range(10):
        walk.append(prev.id())
        walk.append(next.id())
        next = next.next()
        prev = prev.prev()
    return ''.join(map(encode, sorted(walk)))

def encode(cellid):
    output = []
    encoder._VarintEncoder()(output.append, cellid)
    return ''.join(output)

def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"

    # If config file exists, load variables from json
    load   = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a", "--auth_service", help="Auth Service ('ptc' or 'google')",
        required=required("auth_service"))
    parser.add_argument("-u", "--username", help="Username", required=required("username"))
    parser.add_argument("-p", "--password", help="Password", required=required("password"))
    parser.add_argument("-l", "--location", help="Location", required=required("location"))
    parser.add_argument("-s", "--spinstop", help="SpinPokeStop",action='store_true')
    parser.add_argument("-w", "--walk", help="Walk instead of teleport with given speed (meters per second, e.g. 2.5)", type=float, default=0)
    parser.add_argument("-c", "--cp",help="Set CP less than to transfer(DEFAULT 100)",type=int,default=100)
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-t", "--test", help="Only parse the specified location", action='store_true')
    parser.set_defaults(DEBUG=False, TEST=False)
    config = parser.parse_args()

    # Passed in arguments shoud trump
    for key in config.__dict__:
        if key in load and config.__dict__[key] == None:
            config.__dict__[key] = load[key]

    if config.auth_service not in ['ptc', 'google']:
      log.error("Invalid Auth service specified! ('ptc' or 'google')")
      return None

    return config

def main():
    # instantiate pgoapi
    api = PGoApi()
    # log settings
    # log format
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    # log level for http request class
    logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    logging.getLogger("pgoapi").setLevel(logging.DEBUG)
    # log level for internal pgoapi class
    logging.getLogger("rpc_api").setLevel(logging.INFO)
    logging.getLogger('pokecli').setLevel(logging.DEBUG)

    config = init_config()
    if not config:
        return

    if config.debug:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("pgoapi").setLevel(logging.DEBUG)
        logging.getLogger("rpc_api").setLevel(logging.DEBUG)

    position = get_pos_by_name(config.location)
    if config.test:
        return

    # provide player position on the earth
    api.set_position(*position)

    if not api.login(config.auth_service, config.username, config.password):
        return

    # chain subrequests (methods) into one RPC call

    # get player profile call
    # ----------------------
    api.get_player()

    response_dict = api.call()
    player_profile = response_dict['responses']['GET_PLAYER']['profile']

    for currency in player_profile.get('currency',[]):
        player_profile[currency['type']] = currency.get('amount', 0)

    log.info('#' * 30)
    log.info('Profile:')
    log.info('Username: {username}'.format(**player_profile))
    log.info('Bag Size: {item_storage}'.format(**player_profile))
    log.info('Pokemon Storage: {poke_storage}'.format(**player_profile))
    log.info('Account Creation: {creation_time}'.format(**player_profile))
    log.info('Pokecoin: {POKECOIN}'.format(**player_profile))
    log.info('Stardust: {STARDUST}'.format(**player_profile))
    log.info('#' * 30)
    log.info("log configuration:")
    for l in ['pokecli', 'requests', 'pgoapi', 'rpc_api']:
        log.info('%s: %s', l, logging.getLevelName(logging.getLogger(l).level))
    log.info('#' * 30)

    pos = 1
    x = 0
    y = 0
    dx = 0
    dy = -1
    steplimit=10
    steplimit2 = steplimit**2
    origin_lat=position[0]
    origin_lon=position[1]
    while(True):
        for step in range(steplimit2):
            #starting at 0 index
            log.debug('looping: step {} of {}'.format((step+1), steplimit**2))
            log.debug('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(steplimit2, x, y, pos, dx, dy))
            # Scan location math
            if -steplimit2 / 2 < x <= steplimit2 / 2 and -steplimit2 / 2 < y <= steplimit2 / 2:
                position=(x * 0.0025 + origin_lat, y * 0.0025 + origin_lon, 0)
                if config.walk > 0:
                    api.walk(config.walk, *position)
                else:
                    api.set_position(*position)
                log.debug('Position: %s', position)
            if x == y or x < 0 and x == -y or x > 0 and x == 1 - y:
                (dx, dy) = (-dy, dx)

            (x, y) = (x + dx, y + dy)
            # get map objects call
            # ----------------------
            timestamp = "\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000"
            cellid = get_cellid(position[0], position[1])
            api.get_map_objects(latitude=f2i(position[0]), longitude=f2i(position[1]), since_timestamp_ms=timestamp, cell_id=cellid)

            response = api.call()
            map_objects = response.get('responses', {}).get('GET_MAP_OBJECTS', {})

            if map_objects.get('status') == 1:
                map_cells=map_objects['map_cells']
                log.debug('Found %s map cells', len(map_cells))
                for cell in map_cells:
                    working.work_on_cell(cell,api,position,config)
            time.sleep(10)

if __name__ == '__main__':
    main()
