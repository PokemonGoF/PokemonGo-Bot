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
import argparse
import time
import ssl
import sys
import codecs
from getpass import getpass
import logging
import requests
from pokemongo_bot import logger
from pokemongo_bot import PokemonGoBot
from pokemongo_bot.cell_workers.utils import print_green, print_yellow, print_red

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context


def init_config():
    parser = argparse.ArgumentParser()
    config_file = "config.json"
    release_config_json = "release_config.json"

    # If config file exists, load variables from json
    load = {}

    # Select a config file code
    parser.add_argument("-cf", "--config", help="Config File to use")
    config_arg = unicode(parser.parse_args().config)
    if os.path.isfile(config_arg):
        with open(config_arg) as data:
            load.update(json.load(data))
    elif os.path.isfile(config_file):
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
        "Transfer all duplicate pokemon with same ID on bot start, except pokemon with highest CP. Accepts a number to prevent transferring pokemon with a CP above the provided value.  Default is 0 (aka transfer none).",
        type=int,
        default=0)
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

    parser.add_argument(
        "-if",
        "--item_filter",
        help=
        "Pass a list of unwanted items to recycle when collected at a Pokestop (e.g, SYNTAX FOR CONFIG.JSON : [\"101\",\"102\",\"103\",\"104\"] to recycle potions when collected, SYNTAX FOR CONSOLE ARGUMENT : \"101\",\"102\",\"103\",\"104\")",
        type=list,
        default=[])

    parser.add_argument("-ev",
                        "--evolve_all",
                        help="(Batch mode) Pass \"all\" or a list of pokemons to evolve (e.g., \"Pidgey,Weedle,Caterpie\"). Bot will start by attempting to evolve all pokemons. Great after popping a lucky egg!",
                        type=str,
                        default=[])

    parser.add_argument("-ec",
                        "--evolve_captured",
                        help="(Ad-hoc mode) Bot will attempt to evolve all the pokemons captured!",
                        type=bool,
                        default=False)

    config = parser.parse_args()
    if not config.username and 'username' not in load:
        config.username = raw_input("Username: ")
    if not config.password and 'password' not in load:
        config.password = getpass("Password: ")

    # Passed in arguments should trump
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
    if isinstance(config.item_filter, basestring):
        #When config.item_filter looks like "101,102,103" needs to be converted to ["101","102","103"]
        config.item_filter= config.item_filter.split(",")
        

    web_index = 'web/index.html'
    if config.gmapkey and os.path.isfile(web_index):
        find_url = 'https:\/\/maps.googleapis.com\/maps\/api\/js\?key=\S*'
        replace_url = "https://maps.googleapis.com/maps/api/js?key=%s&callback=initMap\""
        #Someone make this pretty! (Efficient)
        with open(web_index, "r+") as sources: # r+ is read + write
            lines = sources.readlines()
            for line in lines:
                sources.write(re.sub(r"%s" % find_url, replace_url % config.gmapkey, line))

    if config.evolve_all:
        config.evolve_all = [str(pokemon_name) for pokemon_name in config.evolve_all.split(',')]

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

        while True:
            bot.take_step()

    except KeyboardInterrupt:
        logger.log('[x] Exiting PokemonGo Bot', 'red')
        # TODO Add number of pokemon catched, pokestops visited, highest CP
        # pokemon catched, etc.


if __name__ == '__main__':
    main()
