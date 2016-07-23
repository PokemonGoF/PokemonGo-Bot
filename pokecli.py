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

## system imports
from argparse import ArgumentParser
from codecs import getwriter
from json import load as read_json
from os.path import isfile
from time import sleep
import logging
import ssl
import sys

## user imports
from bot import PokemonGoBot

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

def init_config():
    parser = ArgumentParser()
    config_file = "config.json"

    # If config file exists, load variables from json
    load = {}
    if isfile(config_file):
        with open(config_file) as data:
            load.update(read_json(data))

    # Read passed in Arguments
    required = lambda x: not x in load
    parser.add_argument("-a", "--auth_service", help="Auth Service ('ptc' or 'google')",
        required=required("auth_service"))
    parser.add_argument("-u", "--username", help="Username", required=required("username"))
    parser.add_argument("-p", "--password", help="Password", required=required("password"))
    parser.add_argument("-l", "--location", help="Location", required=required("location"))
    parser.add_argument("-s", "--spinstop", help="SpinPokeStop", action='store_true')
    parser.add_argument("-v", "--stats", help="Show Stats and Exit", action='store_true')
    parser.add_argument("-w", "--walk", help="Walk instead of teleport with given speed (meters per second, e.g. 2.5)", type=float, default=2.5)
    parser.add_argument("-c", "--cp", help="Set CP less than to transfer(DEFAULT 100)", type=int, default=100)
    parser.add_argument("-k", "--gmapkey",help="Set Google Maps API KEY",type=str,default=None)
    parser.add_argument("--maxsteps",help="Set the steps around your initial location(DEFAULT 5 mean 25 cells around your location)",type=int,default=5)
    parser.add_argument("-d", "--debug", help="Debug Mode", action='store_true')
    parser.add_argument("-t", "--test", help="Only parse the specified location", action='store_true')
    parser.add_argument("-tl", "--transfer_list", help="Transfer these pokemons regardless cp(pidgey,drowzee,rattata)", type=str, default='')
    parser.set_defaults(DEBUG=False, TEST=False)
    config = parser.parse_args()
    

    # Passed in arguments shoud trump
    for key in config.__dict__:
        if key in load and config.__dict__[key] is None:
            config.__dict__[key] = load[key]

    if config.auth_service not in ['ptc', 'google']:
        logging.error("Invalid Auth service ('%s') specified! ('ptc' or 'google')", config.auth_service)
        return None

    return config

def main():
    # log settings
    # log format
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

    sys.stdout = getwriter('utf8')(sys.stdout)
    sys.stderr = getwriter('utf8')(sys.stderr)

    # @eggins clean log
    print '[x] Initializing PokemonGO Bot v1.0'
    sleep(1)
    print '[x] PokemonGo Bot [@PokemonGoF | @eggins | @crack00r | @ethervoid | /r/pokemongodev]'

    config = init_config()
    if not config:
        return

    if config.debug:
        # log level for http request class
        logging.getLogger("requests").setLevel(logging.WARNING)
        # log level for main pgoapi class
        logging.getLogger("pgoapi").setLevel(logging.INFO)
        # log level for internal pgoapi class
        logging.getLogger("rpc_api").setLevel(logging.INFO)

    if config.debug:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("pgoapi").setLevel(logging.DEBUG)
        logging.getLogger("rpc_api").setLevel(logging.DEBUG)

    print '[x] Configuration Initialized'

    try:
        bot = PokemonGoBot(config)
        bot.start()

        while True:
            bot.take_step()
    except KeyboardInterrupt:
        print '[ USER ABORTED, EXITING.. ]'

if __name__ == '__main__':
    main()
