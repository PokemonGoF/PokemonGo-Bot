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
from pokemongo_bot import logger
if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

from getpass import getpass
from pokemongo_bot import PokemonGoBot
from pokemongo_bot.cell_workers.utils import print_green, print_yellow, print_red


def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"
    release_config_json = "release_config.json"

    # If config file exists, load variables from json
    load = {}
    if os.path.isfile(config_file):
        with open(config_file) as data:
            load.update(json.load(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a",
                        "--auth_service",
                        help="Auth Service ('ptc' or 'google')",
                        required=required("auth_service"))
    parser.add_argument("-u", "--username", help="Username")
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument("-l", "--location", help="Location")
    parser.add_argument("-lc",
                        "--location_cache",
                        help="Bot will start at last known location",
                        type=bool,
                        default=False)
    parser.add_argument("-m",
                        "--mode",
                        help="Farming Mode",
                        type=str,
                        default="all")
    parser.add_argument(
        "-w",
        "--walk",
        help=
        "Walk instead of teleport with given speed (meters per second, e.g. 2.5)",
        type=float,
        default=2.5)
    parser.add_argument("-k",
                        "--gmapkey",
                        help="Set Google Maps API KEY",
                        type=str,
                        default=None)
    parser.add_argument(
        "-ms",
        "--max_steps",
        help=
        "Set the steps around your initial location(DEFAULT 5 mean 25 cells around your location)",
        type=int,
        default=50)
    parser.add_argument(
        "-it",
        "--initial_transfer",
        help=
        "Transfer all pokemon with same ID on bot start, except pokemon with highest CP. Can receive a CP number to not transfer above it",
        type=int,
        default=999999)
    parser.add_argument("-d",
                        "--debug",
                        help="Debug Mode",
                        type=bool,
                        default=False)
    parser.add_argument("-t",
                        "--test",
                        help="Only parse the specified location",
                        type=bool,
                        default=False)
    parser.add_argument(
        "-du",
        "--distance_unit",
        help=
        "Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)",
        type=str,
        default="km")

    config = parser.parse_args()
    if not config.username and not 'username' in load:
        config.username = raw_input("Username: ")
    if not config.password and not 'password' in load:
        config.password = getpass("Password: ")

    # Passed in arguments shoud trump
    for key in config.__dict__:
        if key in load:
            config.__dict__[key] = load[key]

    if config.auth_service not in ['ptc', 'google']:
        logging.error("Invalid Auth service specified! ('ptc' or 'google')")
        return None

    if not (config.location or config.location_cache):
        parser.error("Needs either --use-location-cache or --location.")
        return None

    config.release_config = {}
    if os.path.isfile(release_config_json):
        with open(release_config_json) as data:
            config.release_config.update(json.load(data))

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

    logger.log('[x] PokemonGO Bot v1.0', 'green')
    logger.log('[x] Configuration initialized', 'yellow')

    try:
        bot = PokemonGoBot(config)
        bot.start()

        logger.log('[x] Starting PokemonGo Bot....', 'green')

        while (True):
            bot.take_step()

    except KeyboardInterrupt:
        logger.log('[x] Exiting PokemonGo Bot', 'red')
        # TODO Add number of pokemon catched, pokestops visited, highest CP
        # pokemon catched, etc.


if __name__ == '__main__':
    main()
