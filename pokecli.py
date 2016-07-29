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

import argparse
import codecs
import json
import logging
import os
import ssl
import sys
import time
from datetime import timedelta
from getpass import getpass
from pgoapi.exceptions import NotLoggedInException

from pokemongo_bot import PokemonGoBot
from pokemongo_bot import logger

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context


def main():
    logger.log('PokemonGO Bot v1.0', 'green')
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    config = init_config()
    if not config:
        return
    logger.log('Configuration initialized', 'yellow')

    finished = False

    while not finished:
        try:
            bot = PokemonGoBot(config)
            bot.start()
            bot.metrics.capture_stats()

            logger.log('Starting PokemonGo Bot....', 'green')

            while True:
                bot.tick()

        except KeyboardInterrupt:
            logger.log('Exiting PokemonGo Bot', 'red')
            finished = True
            if bot.metrics.start_time is None:
                return  # Bot didn't actually start, no metrics to show.

            metrics = bot.metrics
            metrics.capture_stats()
            logger.log('')
            logger.log('Ran for {}'.format(metrics.runtime()), 'cyan')
            logger.log('Total XP Earned: {}  Average: {:.2f}/h'.format(metrics.xp_earned(), metrics.xp_per_hour()), 'cyan')
            logger.log('Travelled {:.2f}km'.format(metrics.distance_travelled()), 'cyan')
            logger.log('Visited {} stops'.format(metrics.visits['latest'] - metrics.visits['start']), 'cyan')
            logger.log('Encountered {} pokemon, {} caught, {} released, {} evolved, {} never seen before'
                       .format(metrics.num_encounters(), metrics.num_captures(), metrics.releases,
                               metrics.num_evolutions(), metrics.num_new_mons()), 'cyan')
            logger.log('Threw {} pokeball{}'.format(metrics.num_throws(), '' if metrics.num_throws() == 1 else 's'),
                       'cyan')
            logger.log('Earned {} Stardust'.format(metrics.earned_dust()), 'cyan')
            logger.log('')
            if metrics.highest_cp is not None:
                logger.log('Highest CP Pokemon: {}'.format(metrics.highest_cp['desc']), 'cyan')
            if metrics.most_perfect is not None:
                logger.log('Most Perfect Pokemon: {}'.format(metrics.most_perfect['desc']), 'cyan')


        except NotLoggedInException:
            logger.log('[x] Error while connecting to the server, please wait %s minutes' % config.reconnecting_timeout, 'red')
            time.sleep(config.reconnecting_timeout * 60)

def init_config():
    parser = argparse.ArgumentParser()
    config_file = "configs/config.json"
    web_dir = "web"

    # If config file exists, load variables from json
    load = {}

    # Select a config file code
    parser.add_argument("-cf", "--config", help="Config File to use")
    config_arg = parser.parse_known_args() and parser.parse_known_args()[0].config or None
    if config_arg and os.path.isfile(config_arg):
        with open(config_arg) as data:
            load.update(json.load(data))
    elif os.path.isfile(config_file):
        logger.log('No config argument specified, checking for /configs/config.json', 'yellow')
        with open(config_file) as data:
            load.update(json.load(data))
    else:
        logger.log('Error: No /configs/config.json or specified config', 'red')

    # Read passed in Arguments
    required = lambda x: not x in load
    add_config(
        parser,
        load,
        short_flag="-a",
        long_flag="--auth_service",
        help="Auth Service ('ptc' or 'google')",
        required=required("auth_service"),
        default=None
    )
    add_config(
        parser,
        load,
        short_flag="-u",
        long_flag="--username",
        help="Username",
        default=None
    )
    add_config(
        parser,
        load,
        short_flag="-ws",
        long_flag="--websocket_server",
        help="Start websocket server (format 'host:port')",
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-p",
        long_flag="--password",
        help="Password",
        default=None
    )
    add_config(
        parser,
        load,
        short_flag="-l",
        long_flag="--location",
        help="Location",
        type=parse_unicode_str,
        default=''
    )
    add_config(
        parser,
        load,
        short_flag="-lc",
        long_flag="--location_cache",
        help="Bot will start at last known location",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--catch_pokemon",
        help="Enable catching pokemon",
        type=bool,
        default=True
    )
    add_config(
        parser,
        load,
        long_flag="--forts.spin",
        help="Enable Spinning Pokestops",
        type=bool,
        default=True,
    )
    add_config(
        parser,
        load,
        short_flag="-w",
        long_flag="--walk",
        help=
        "Walk instead of teleport with given speed (meters per second, e.g. 2.5)",
        type=float,
        default=2.5
    )
    add_config(
        parser,
        load,
        short_flag="-k",
        long_flag="--gmapkey",
        help="Set Google Maps API KEY",
        type=str,
        default=None
    )
    add_config(
        parser,
        load,
        short_flag="-ms",
        long_flag="--max_steps",
        help=
        "Set the steps around your initial location(DEFAULT 5 mean 25 cells around your location)",
        type=int,
        default=50
    )
    add_config(
        parser,
        load,
        short_flag="-rp",
        long_flag="--release_pokemon",
        help="Allow transfer pokemon to professor based on release configuration. Default is false",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-d",
        long_flag="--debug",
        help="Debug Mode",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-t",
        long_flag="--test",
        help="Only parse the specified location",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-du",
        long_flag="--distance_unit",
        help="Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)",
        type=str,
        default='km'
    )
    add_config(
        parser,
        load,
        short_flag="-ev",
        long_flag="--evolve_all",
        help="(Batch mode) Pass \"all\" or a list of pokemon to evolve (e.g., \"Pidgey,Weedle,Caterpie\"). Bot will start by attempting to evolve all pokemon. Great after popping a lucky egg!",
        type=str,
        default=[]
    )
    add_config(
        parser,
        load,
        short_flag="-ecm",
        long_flag="--evolve_cp_min",
        help="Minimum CP for evolve all. Bot will attempt to first evolve highest IV pokemon with CP larger than this.",
        type=int,
        default=300
    )
    add_config(
        parser,
        load,
        short_flag="-ec",
        long_flag="--evolve_captured",
        help="(Ad-hoc mode) Pass \"all\" or a list of pokemon to evolve (e.g., \"Pidgey,Weedle,Caterpie\"). Bot will attempt to evolve all the pokemon captured!",
        type=str,
        default=[]
    )
    add_config(
        parser,
        load,
        short_flag="-le",
        long_flag="--use_lucky_egg",
        help="Uses lucky egg when using evolve_all",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-rt",
        long_flag="--reconnecting_timeout",
        help="Timeout between reconnecting if error occured (in minutes, e.g. 15)",
        type=float,
        default=15.0
    )
    add_config(
        parser,
        load,
        short_flag="-hr",
        long_flag="--health_record",
        help="Send anonymous bot event to GA for bot health record. Set \"health_record\":false if you need disable it.",
        type=bool,
        default=True
    )
    add_config(
        parser,
        load,
        short_flag="-ac",
        long_flag="--forts.avoid_circles",
        help="Avoids circles (pokestops) of the max size set in max_circle_size flag",
        type=bool,
        default=False,
    )
    add_config(
        parser,
        load,
        short_flag="-mcs",
        long_flag="--forts.max_circle_size",
        help="If avoid_circles flag is set, this flag specifies the maximum size of circles (pokestops) avoided",
        type=int,
        default=10,
    )

    # Start to parse other attrs
    config = parser.parse_args()
    if not config.username and 'username' not in load:
        config.username = raw_input("Username: ")
    if not config.password and 'password' not in load:
        config.password = getpass("Password: ")

    config.catch = load.get('catch', {})
    config.release = load.get('release', {})
    config.item_filter = load.get('item_filter', {})
    config.action_wait_max = load.get('action_wait_max', 4)
    config.action_wait_min = load.get('action_wait_min', 1)

    config.hatch_eggs = load.get("hatch_eggs", True)
    config.longer_eggs_first = load.get("longer_eggs_first", True)

    if config.auth_service not in ['ptc', 'google']:
        logging.error("Invalid Auth service specified! ('ptc' or 'google')")
        return None

    if 'mode' in load or 'mode' in config:
        parser.error('"mode" has been removed and replaced with two new flags: "catch_pokemon" and "spin_forts". ' +
            ' Set these to true or false and remove "mode" from your configuration')
        return None

    if (config.evolve_captured
        and (not isinstance(config.evolve_captured, str)
             or str(config.evolve_captured).lower() in ["true", "false"])):
        parser.error('"evolve_captured" should be list of pokemons: use "all" or "none" to match all ' +
                     'or none of the pokemons, or use a comma separated list such as "Pidgey,Weedle,Caterpie"')
        return None

    if not (config.location or config.location_cache):
        parser.error("Needs either --use-location-cache or --location.")
        return None

    # create web dir if not exists
    try:
        os.makedirs(web_dir)
    except OSError:
        if not os.path.isdir(web_dir):
            raise

    if config.evolve_all and isinstance(config.evolve_all, str):
        config.evolve_all = [str(pokemon_name) for pokemon_name in config.evolve_all.split(',')]
    if config.evolve_captured and isinstance(config.evolve_captured, str):
        config.evolve_captured = [str(pokemon_name) for pokemon_name in config.evolve_captured.split(',')]

    fix_nested_config(config)
    return config

def add_config(parser, json_config, short_flag=None, long_flag=None, **kwargs):
    if not long_flag:
        raise Exception('add_config calls requires long_flag parameter!')

    full_attribute_path = long_flag.split('--')[1]
    attribute_name = full_attribute_path.split('.')[-1]

    if '.' in full_attribute_path: # embedded config!
        embedded_in = full_attribute_path.split('.')[0: -1]
        for level in embedded_in:
            json_config = json_config.get(level, {})

    if 'default' in kwargs:
        kwargs['default'] = json_config.get(attribute_name, kwargs['default'])
    if short_flag:
        args = (short_flag, long_flag)
    else:
        args = (long_flag,)
    parser.add_argument(*args, **kwargs)


def fix_nested_config(config):
    config_dict = config.__dict__

    for key, value in config_dict.iteritems():
        if '.' in key:
            new_key = key.replace('.', '_')
            config_dict[new_key] = value
            del config_dict[key]

def parse_unicode_str(string):
    try:
        return string.decode('utf8')
    except UnicodeEncodeError:
        return string


if __name__ == '__main__':
    main()
