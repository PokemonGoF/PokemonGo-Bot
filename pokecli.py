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
from pgoapi.exceptions import NotLoggedInException, ServerSideRequestThrottlingException, ServerBusyOrOfflineException
from geopy.exc import GeocoderQuotaExceeded

from pokemongo_bot import PokemonGoBot, TreeConfigBuilder
from pokemongo_bot.health_record import BotEvent
from pokemongo_bot.plugin_loader import PluginLoader

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)10s] [%(levelname)s] %(message)s')
logger = logging.getLogger('cli')
logger.setLevel(logging.INFO)

def main():
    bot = False
    
    try:
        logger.info('PokemonGO Bot v1.0')
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

        config = init_config()
        if not config:
            return

        logger.info('Configuration initialized')
        health_record = BotEvent(config)
        health_record.login_success()

        finished = False

        while not finished:
            try:
                bot = PokemonGoBot(config)
                bot.start()
                tree = TreeConfigBuilder(bot, config.raw_tasks).build()
                bot.workers = tree
                bot.metrics.capture_stats()
                bot.health_record = health_record

                bot.event_manager.emit(
                    'bot_start',
                    sender=bot,
                    level='info',
                    formatted='Starting bot...'
                )

                while True:
                    bot.tick()

            except KeyboardInterrupt:
                bot.event_manager.emit(
                    'bot_exit',
                    sender=bot,
                    level='info',
                    formatted='Exiting bot.'
                )
                finished = True
                report_summary(bot)

            except NotLoggedInException:
                wait_time = config.reconnecting_timeout * 60
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formmated='Log logged in, reconnecting in {:s}'.format(wait_time)
                )
                time.sleep(wait_time)
            except ServerBusyOrOfflineException:
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='Server busy or offline'
                )
            except ServerSideRequestThrottlingException:
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='Server is throttling, reconnecting in 30 seconds'
                )
                time.sleep(30)

    except GeocoderQuotaExceeded:
        raise Exception("Google Maps API key over requests limit.")
    except Exception as e:
        # always report session summary and then raise exception
        if bot:
            report_summary(bot)

        raise e

def report_summary(bot):
    if bot.metrics.start_time is None:
        return  # Bot didn't actually start, no metrics to show.

    metrics = bot.metrics
    metrics.capture_stats()
    logger.info('')
    logger.info('Ran for {}'.format(metrics.runtime()))
    logger.info('Total XP Earned: {}  Average: {:.2f}/h'.format(metrics.xp_earned(), metrics.xp_per_hour()))
    logger.info('Travelled {:.2f}km'.format(metrics.distance_travelled()))
    logger.info('Visited {} stops'.format(metrics.visits['latest'] - metrics.visits['start']))
    logger.info('Encountered {} pokemon, {} caught, {} released, {} evolved, {} never seen before'
                .format(metrics.num_encounters(), metrics.num_captures(), metrics.releases,
                        metrics.num_evolutions(), metrics.num_new_mons()))
    logger.info('Threw {} pokeball{}'.format(metrics.num_throws(), '' if metrics.num_throws() == 1 else 's'))
    logger.info('Earned {} Stardust'.format(metrics.earned_dust()))
    logger.info('')
    if metrics.highest_cp is not None:
        logger.info('Highest CP Pokemon: {}'.format(metrics.highest_cp['desc']))
    if metrics.most_perfect is not None:
        logger.info('Most Perfect Pokemon: {}'.format(metrics.most_perfect['desc']))

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
        logger.info('No config argument specified, checking for /configs/config.json')
        with open(config_file) as data:
            load.update(json.load(data))
    else:
        logger.info('Error: No /configs/config.json or specified config')

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
        long_flag="--websocket.server_url",
        help="Connect to websocket server at given url",
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-wss",
        long_flag="--websocket.start_embedded_server",
        help="Start embedded websocket server",
        default=False
    )
    add_config(
        parser,
        load,
        short_flag="-wsr",
        long_flag="--websocket.remote_control",
        help="Enable remote control through websocket (requires websocekt server url)",
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
        short_flag="-e",
        long_flag="--show_events",
        help="Show events",
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
        short_flag="-ec",
        long_flag="--evolve_captured",
        help="(Ad-hoc mode) Pass \"all\" or a list of pokemon to evolve (e.g., \"Pidgey,Weedle,Caterpie\"). Bot will attempt to evolve all the pokemon captured!",
        type=str,
        default=[]
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
    add_config(
        parser,
        load,
        long_flag="--catch_randomize_reticle_factor",
        help="Randomize factor for pokeball throwing accuracy (DEFAULT 1.0 means no randomize: always 'Excellent' throw. 0.0 randomizes between normal and 'Excellent' throw)",
        type=float,
        default=1.0
    )
    add_config(
        parser,
        load,
        long_flag="--catch_randomize_spin_factor",
        help="Randomize factor for pokeball curve throwing (DEFAULT 1.0 means no randomize: always perfect 'Super Spin' curve ball. 0.0 randomizes between normal and 'Super Spin' curve ball)",
        type=float,
        default=1.0
    )
    add_config(
        parser,
        load,
        long_flag="--map_object_cache_time",
        help="Amount of seconds to keep the map object in cache (bypass Niantic throttling)",
        type=float,
        default=5.0
    )

    # Start to parse other attrs
    config = parser.parse_args()
    if not config.username and 'username' not in load:
        config.username = raw_input("Username: ")
    if not config.password and 'password' not in load:
        config.password = getpass("Password: ")

    config.catch = load.get('catch', {})
    config.release = load.get('release', {})
    config.action_wait_max = load.get('action_wait_max', 4)
    config.action_wait_min = load.get('action_wait_min', 1)
    config.plugins = load.get('plugins', [])
    config.raw_tasks = load.get('tasks', [])

    config.vips = load.get('vips', {})

    if config.map_object_cache_time < 0.0:
        parser.error("--map_object_cache_time is out of range! (should be >= 0.0)")
        return None

    if len(config.raw_tasks) == 0:
        logging.error("No tasks are configured. Did you mean to configure some behaviors? Read https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Configuration-files#configuring-tasks for more information")
        return None

    if config.auth_service not in ['ptc', 'google']:
        logging.error("Invalid Auth service specified! ('ptc' or 'google')")
        return None

    def task_configuration_error(flag_name):
        parser.error("""
            \"{}\" was removed from the configuration options.
            You can now change the behavior of the bot by modifying the \"tasks\" key.
            Read https://github.com/PokemonGoF/PokemonGo-Bot/wiki/Configuration-files#configuring-tasks for more information.
            """.format(flag_name))

    old_flags = ['mode', 'catch_pokemon', 'spin_forts', 'forts_spin', 'hatch_eggs', 'release_pokemon', 'softban_fix',
                'longer_eggs_first', 'evolve_speed', 'use_lucky_egg', 'item_filter', 'evolve_all', 'evolve_cp_min', 'max_steps']
    for flag in old_flags:
        if flag in load:
            task_configuration_error(flag)
            return None

    nested_old_flags = [('forts', 'spin'), ('forts', 'move_to_spin'), ('navigator', 'path_mode'), ('navigator', 'path_file'), ('navigator', 'type')]
    for outer, inner in nested_old_flags:
        if load.get(outer, {}).get(inner, None):
            task_configuration_error('{}.{}'.format(outer, inner))
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

    if config.catch_randomize_reticle_factor < 0 or 1 < config.catch_randomize_reticle_factor:
        parser.error("--catch_randomize_reticle_factor is out of range! (should be 0 <= catch_randomize_reticle_factor <= 1)")
        return None

    if config.catch_randomize_spin_factor < 0 or 1 < config.catch_randomize_spin_factor:
        parser.error("--catch_randomize_spin_factor is out of range! (should be 0 <= catch_randomize_spin_factor <= 1)")
        return None

    plugin_loader = PluginLoader()
    for plugin in config.plugins:
        plugin_loader.load_plugin(plugin)

    # create web dir if not exists
    try:
        os.makedirs(web_dir)
    except OSError:
        if not os.path.isdir(web_dir):
            raise

    if config.evolve_captured and isinstance(config.evolve_captured, str):
        config.evolve_captured = [str(pokemon_name).strip() for pokemon_name in config.evolve_captured.split(',')]

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
