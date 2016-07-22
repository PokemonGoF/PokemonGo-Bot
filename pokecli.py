#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import requests
import argparse
import time
import ssl
import logging
import sys
import codecs

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

from pokemongo_bot import PokemonGoBot
from pokemongo_bot.cell_workers.utils import print_green, print_yellow, print_red

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
    parser.add_argument("-m", "--mode", help="Farming Mode", type=str, default="all")
    parser.add_argument("-w", "--walk", help="Walk instead of teleport with given speed (meters per second, e.g. 2.5)", type=float, default=2.5)
    parser.add_argument("-c", "--cp",help="Set CP less than to transfer(DEFAULT 100)",type=int,default=100)
    parser.add_argument("-k", "--gmapkey",help="Set Google Maps API KEY",type=str,default=None)
    parser.add_argument("--maxsteps",help="Set the steps around your initial location(DEFAULT 5 mean 25 cells around your location)",type=int,default=5)
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
    # log settings
    # log format
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    config = init_config()
    if not config:
        return

    print_green('[x] PokemonGO Bot v1.0')
    print_yellow('[x] Configuration initialized')

    bot = PokemonGoBot(config)
    bot.start()

    print_green('[x] Starting PokemonGo Bot....')

    while(True):
        bot.take_step()

if __name__ == '__main__':
    main()
