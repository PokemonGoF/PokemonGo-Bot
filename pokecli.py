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
import requests
import argparse
import time
import ssl
import logging
import sys
import flask
from flask import Flask, render_template
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
from flask_googlemaps import icons
import threading

import working
import webapp

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

from bot import PokemonGoBot

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
    # log settings
    # log format
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    # log level for http request class
    logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    logging.getLogger("pgoapi").setLevel(logging.INFO)
    # log level for internal pgoapi class
    logging.getLogger("rpc_api").setLevel(logging.INFO)
    # log level for flash server
    logging.getLogger("werkzeug").setLevel(logging.ERROR)



    config = init_config()
    if not config:
        return

    if config.debug:
        logging.getLogger("requests").setLevel(logging.DEBUG)
        logging.getLogger("pgoapi").setLevel(logging.DEBUG)
        logging.getLogger("rpc_api").setLevel(logging.DEBUG)

    bot = PokemonGoBot(config)
    bot.start()

    while(True):
        try:
            bot.take_step()
        except:
            print('Oops, Exception, have a rest then.')
            time.sleep(2)

def register_background_thread(initial_registration=False):
    global search_thread
    search_thread = threading.Thread(target=main)
    search_thread.daemon = True
    search_thread.name = 'search_thread'
    search_thread.start()

def get_map():
    print "get_map" + str(origin_lat) + ", " + str(origin_lon)
    fullmap = Map(
        identifier="fullmap2",
        style='height:100%;width:100%;top:0;left:0;position:absolute;z-index:200;',
        lat=origin_lat,
        lng=origin_lon,
        zoom='15', )
    return fullmap
    # markers=get_pokemarkers(),

def get_player_position():
    player_position = {
        'lat': out_position[0],
        'lng': out_position[1]
    }

    return player_position

GOOGLEMAPS_KEY = "AIzaSyAZzeHhs-8JZ7i18MjFuM35dJHq70n3Hx4"

webapp = webapp.create_webapp()

@webapp.route('/')
def fullmap():
    return render_template(
        'example_fullmap.html', key=GOOGLEMAPS_KEY, fullmap=get_map(), auto_refresh=0)

@webapp.route('/config')
def config():
    """ Gets the settings for the Google Maps via REST"""
    center = {
        'lat': origin_lat,
        'lng': origin_lon,
        'zoom': 15,
        'identifier': "fullmap"
    }
    return json.dumps(center)


@webapp.route('/getPlayerPosition')
def data():
    """ Gets all the PokeMarkers via REST """
    return json.dumps(get_player_position())

if __name__ == '__main__':
    # main()
    register_background_thread(initial_registration=True)
    webapp.run(debug=True, threaded=True, host="localhost", port=5001)


