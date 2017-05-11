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
from __future__ import unicode_literals

import argparse
import codecs
import json
import logging
import os
import six
import ssl
import sys
import time
import signal
import string
import subprocess

from logging import Formatter
from random import randint

codecs.register(lambda name: codecs.lookup("utf-8") if name == "cp65001" else None)

from getpass import getpass
from pgoapi.exceptions import NotLoggedInException, ServerSideRequestThrottlingException, ServerBusyOrOfflineException, NoPlayerPositionSetException
from geopy.exc import GeocoderQuotaExceeded

from pokemongo_bot import PokemonGoBot, TreeConfigBuilder
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.health_record import BotEvent
from pokemongo_bot.plugin_loader import PluginLoader
from pokemongo_bot.api_wrapper import PermaBannedException

try:
    from demjson import jsonlint
except ImportError:
    # Run `pip install -r requirements.txt` to fix this
    jsonlint = None

if sys.version_info >= (2, 7, 9):
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    import pkg_resources
    pgoapi_version = pkg_resources.get_distribution("pgoapi").version
    if pgoapi_version != '1.2.0':
        print "Run following command to get latest update: `pip install -r requirements.txt --upgrade`"
        sys.exit(1)
except pkg_resources.DistributionNotFound:
    print 'Seems you forgot to install python modules.'
    print 'Run: `pip install -r requirements.txt`'
    sys.exit(1)
except ImportError as e:
    print e
    pass


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)10s] [%(levelname)s] %(message)s')
logger = logging.getLogger('cli')
logger.setLevel(logging.INFO)


class SIGINTRecieved(Exception):
    pass


def main():
    bot = False

    def handle_sigint(*args):
        raise SIGINTRecieved
    signal.signal(signal.SIGINT, handle_sigint)

    def initialize_task(bot, config):
        tree = TreeConfigBuilder(bot, config.raw_tasks).build()
        bot.workers = tree

    def initialize(config):
        from pokemongo_bot.datastore import Datastore

        ds = Datastore(conn_str='/data/{}.db'.format(config.username))
        for directory in ['pokemongo_bot', 'pokemongo_bot/cell_workers']:
            ds.migrate(directory + '/migrations')

        bot = PokemonGoBot(ds.get_connection(), config)

        return bot

    def setup_logging(config):
        log_level = logging.ERROR

        if config.debug:
            log_level = logging.DEBUG

        logging.getLogger("requests").setLevel(log_level)
        logging.getLogger("websocket").setLevel(log_level)
        logging.getLogger("socketio").setLevel(log_level)
        logging.getLogger("engineio").setLevel(log_level)
        logging.getLogger("socketIO-client").setLevel(log_level)
        logging.getLogger("pgoapi").setLevel(log_level)
        logging.getLogger("rpc_api").setLevel(log_level)

        if config.logging:
            logging_format = '%(message)s'
            logging_format_options = ''

            if ('show_log_level' not in config.logging) or config.logging['show_log_level']:
                logging_format = '[%(levelname)s] ' + logging_format
            if ('show_process_name' not in config.logging) or config.logging['show_process_name']:
                logging_format = '[%(name)10s] ' + logging_format
            if ('show_thread_name' not in config.logging) or config.logging['show_thread_name']:
                logging_format = '[%(threadName)s] ' + logging_format
            if ('show_datetime' not in config.logging) or config.logging['show_datetime']:
                logging_format = '[%(asctime)s] ' + logging_format
                logging_format_options = '%Y-%m-%d %H:%M:%S'

            formatter = Formatter(logging_format,logging_format_options)
            for handler in logging.root.handlers[:]:
                handler.setFormatter(formatter)

    def start_bot(bot, config):
        bot.start()
        initialize_task(bot, config)
        bot.metrics.capture_stats()
        bot.health_record = BotEvent(config)
        return bot

    def get_commit_hash():
        try:
            hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                           stderr=subprocess.STDOUT)
            if all(c in string.hexdigits for c in hash[:-1]):
                with open('version', 'w') as f:
                    f.write(hash)
        except:
            pass

        if not os.path.exists('version'):
            return 'unknown'

        with open('version') as f:
            return f.read()[:8]

    try:
        if six.PY2:
            sys.stdout = codecs.getwriter('utf8')(sys.stdout)
            sys.stderr = codecs.getwriter('utf8')(sys.stderr)

        logger.info('PokemonGO Bot v1.0')
        logger.info('commit: ' + get_commit_hash())

        config, config_file = init_config()
        if not config:
            return

        logger.info('Configuration initialized')
        health_record = BotEvent(config)
        health_record.login_success()

        setup_logging(config)

        finished = False

        while not finished:
            min_wait_time = int(config.reconnecting_timeout * 0.8 * 60)
            max_wait_time = int(config.reconnecting_timeout *  1.2 * 60)
            wait_time = randint(min_wait_time, max_wait_time)
            try:
                bot = initialize(config)
                bot = start_bot(bot, config)
                config_changed = check_mod(config_file)

                bot.event_manager.emit(
                    'bot_start',
                    sender=bot,
                    level='info',
                    formatted='Starting bot...'
                )

                while True:
                    bot.tick()
                    if config.live_config_update_enabled and config_changed():
                        logger.info('Config changed! Applying new config.')
                        config, _ = init_config()

                        if config.live_config_update_tasks_only:
                            initialize_task(bot, config)
                        else:
                            bot = initialize(config)
                            bot = start_bot(bot, config)

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
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='Not logged in, reconnecting in {:d} seconds'.format(wait_time)
                )
                time.sleep(wait_time)
            except ServerBusyOrOfflineException:
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='Server busy or offline, reconnecting in {:d} seconds'.format(wait_time)
                )
                time.sleep(wait_time)
            except ServerSideRequestThrottlingException:
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='Server is throttling, reconnecting in {:d} seconds'.format(wait_time)
                )
                time.sleep(wait_time)
            except PermaBannedException:
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='Probably permabanned, Game Over ! Play again at https://club.pokemon.com/us/pokemon-trainer-club/sign-up/'
                )
                time.sleep(36000)
            except NoPlayerPositionSetException:
                bot.event_manager.emit(
                    'api_error',
                    sender=bot,
                    level='info',
                    formatted='No player position set, reconnecting in {:d} seconds'.format(wait_time)
                )
                time.sleep(wait_time)

    except GeocoderQuotaExceeded:
        raise Exception("Google Maps API key over requests limit.")
    except SIGINTRecieved:
        if bot:
            bot.event_manager.emit(
                'bot_interrupted',
                sender=bot,
                level='info',
                formatted='Bot caught SIGINT. Shutting down.'
            )
            report_summary(bot)

    except Exception as e:
        # always report session summary and then raise exception
        if bot:
            report_summary(bot)

        raise
    finally:
        # Cache here on SIGTERM, or Exception.  Check data is available and worth caching.
        if bot:
            if len(bot.recent_forts) > 0 and bot.recent_forts[-1] is not None and bot.config.forts_cache_recent_forts:
                cached_forts_path = os.path.join(
                    _base_dir, 'data', 'recent-forts-%s.json' % bot.config.username
                )
                try:
                    with open(cached_forts_path, 'w') as outfile:
                        json.dump(bot.recent_forts, outfile)
                    bot.event_manager.emit(
                        'cached_fort',
                        sender=bot,
                        level='debug',
                        formatted='Forts cached.'
                    )
                except IOError as e:
                    bot.event_manager.emit(
                        'error_caching_forts',
                        sender=bot,
                        level='debug',
                        formatted='Error caching forts for {path}',
                        data={'path': cached_forts_path}
                        )


def check_mod(config_file):
    check_mod.mtime = os.path.getmtime(config_file)

    def compare_mtime():
        mdate = os.path.getmtime(config_file)
        if check_mod.mtime == mdate:  # mtime didnt change
            return False
        else:
            check_mod.mtime = mdate
            return True

    return compare_mtime


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
    logger.info('Encountered {} pokemon, {} caught, {} released, {} evolved, {} never seen before ({})'
                .format(metrics.num_encounters(), metrics.num_captures(), metrics.releases,
                        metrics.num_evolutions(), metrics.num_new_mons(), metrics.uniq_caught()))
    logger.info('Threw {} pokeball{}'.format(metrics.num_throws(), '' if metrics.num_throws() == 1 else 's'))
    logger.info('Earned {} Stardust'.format(metrics.earned_dust()))
    logger.info('Hatched eggs {}'.format(metrics.hatched_eggs(0)))
    if (metrics.next_hatching_km(0)):
        logger.info('Next egg hatches in {:.2f} km'.format(metrics.next_hatching_km(0)))
    logger.info('')
    if metrics.highest_cp is not None:
        logger.info('Highest CP Pokemon: {}'.format(metrics.highest_cp['desc']))
    if metrics.most_perfect is not None:
        logger.info('Most Perfect Pokemon: {}'.format(metrics.most_perfect['desc']))


def init_config():
    parser = argparse.ArgumentParser()
    config_file = os.path.join(_base_dir, 'configs', 'config.json')
    web_dir = "web"

    # If config file exists, load variables from json
    load = {}

    def _json_loader(filename):
        try:
            with open(filename, 'rb') as data:
                load.update(json.load(data))
        except ValueError:
            if jsonlint:
                with open(filename, 'rb') as data:
                    lint = jsonlint()
                    rc = lint.main(['-v', filename])

            logger.critical('Error with configuration file')
            sys.exit(-1)

    # Select a config file code
    parser.add_argument("-cf", "--config", help="Config File to use")
    parser.add_argument("-af", "--auth", help="Auth File to use")

    for _config in ['auth', 'config']:
        config_file = os.path.join(_base_dir, 'configs', _config + '.json')
        config_arg = parser.parse_known_args() and parser.parse_known_args()[0].__dict__[_config] or None

        if config_arg and os.path.isfile(config_arg):
            _json_loader(config_arg)
            config_file = config_arg
        elif os.path.isfile(config_file):
            logger.info('No ' + _config + ' argument specified, checking for ' + config_file)
            _json_loader(config_file)
        else:
            logger.info('Error: No /configs/' + _config + '.json')

    # Read passed in Arguments
    required = lambda x: x not in load
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
        short_flag="-capi",
        long_flag="--check_niantic_api",
        help="Enable killswitch on API Change",
        type=bool,
        default=True
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
        help="Enable remote control through websocket (requires websocket server url)",
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
        short_flag="-wmax",
        long_flag="--walk_max",
        help="Walk instead of teleport with given speed",
        type=float,
        default=2.5
    )
    add_config(
        parser,
        load,
        short_flag="-wmin",
        long_flag="--walk_min",
        help="Walk instead of teleport with given speed",
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
        short_flag="-hk",
        long_flag="--hashkey",
        help="Set Bossland hashing key",
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
        short_flag="-crf",
        long_flag="--forts.cache_recent_forts",
        help="Caches recent forts used by max_circle_size",
        type=bool,
        default=True,
    )
    add_config(
        parser,
        load,
        long_flag="--map_object_cache_time",
        help="Amount of seconds to keep the map object in cache (bypass Niantic throttling)",
        type=float,
        default=5.0
    )
    add_config(
        parser,
        load,
        long_flag="--logging.color",
        help="If logging_color is set to true, colorized logging handler will be used",
        type=bool,
        default=True
    )
    add_config(
        parser,
        load,
        long_flag="--logging.clean",
        help="If clean_logging is set to true, meta data will be stripped from the log messages",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--heartbeat_threshold",
        help="A threshold between each heartbeat sending to server",
        type=int,
        default=10
    )
    add_config(
        parser,
        load,
        long_flag="--pokemon_bag.show_at_start",
        help="Logs all pokemon in the bag at bot start",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--pokemon_bag.show_count",
        help="Shows the amount of which pokemon (minimum 1)",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--pokemon_bag.show_candies",
        help="Shows the amount of candies for each pokemon",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--pokemon_bag.pokemon_info",
        help="List with the info to show for each pokemon",
        type=bool,
        default=[]
    )
    add_config(
        parser,
        load,
        long_flag="--alt_min",
        help="Minimum random altitude",
        type=float,
        default=500
    )
    add_config(
        parser,
        load,
        long_flag="--alt_max",
        help="Maximum random altitude",
        type=float,
        default=1000
    )
    add_config(
        parser,
        load,
        long_flag="--replicate_gps_xy_noise",
        help="Add noise to current position",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--replicate_gps_z_noise",
        help="Add noise to current position",
        type=bool,
        default=False
    )
    add_config(
        parser,
        load,
        long_flag="--gps_xy_noise_range",
        help="Intensity of gps noise (unit is lat and lng,) high values may cause issues (default=0.000125)",
        type=float,
        default=0.000125
    )
    add_config(
        parser,
        load,
        long_flag="--gps_z_noise_range",
        help="Intensity of gps noise (unit is in meter, default=12.5)",
        type=float,
        default=12.5
    )
    add_config(
        parser,
        load,
        long_flag="--gps_default_altitude",
        help="Initial altitude (default=8.0)",
        type=float,
        default=8.0
    )
    add_config(
         parser,
         load,
         long_flag="--enable_social",
         help="Enable social event exchange between bot",
         type=bool,
         default=True
    )

    add_config(
         parser,
         load,
         long_flag="--walker_limit_output",
         help="Limit output from walker functions (move_to_fort, position_update, etc)",
         type=bool,
         default=False
    )

    # Start to parse other attrs
    config = parser.parse_args()
    if not config.username and 'username' not in load:
        config.username = raw_input("Username: ")
    if not config.password and 'password' not in load:
        config.password = getpass("Password: ")

    config.favorite_locations = load.get('favorite_locations', [])
    config.encrypt_location = load.get('encrypt_location', '')
    config.telegram_token = load.get('telegram_token', '')
    config.discord_token = load.get('discord_token', '')
    config.catch = load.get('catch', {})
    config.release = load.get('release', {})
    config.plugins = load.get('plugins', [])
    config.raw_tasks = load.get('tasks', [])
    config.vips = load.get('vips', {})
    config.sleep_schedule = load.get('sleep_schedule', {})
    config.live_config_update = load.get('live_config_update', {})
    config.live_config_update_enabled = config.live_config_update.get('enabled', False)
    config.live_config_update_tasks_only = config.live_config_update.get('tasks_only', False)
    config.logging = load.get('logging', {})

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
                 'longer_eggs_first', 'evolve_speed', 'use_lucky_egg', 'item_filter', 'evolve_all', 'evolve_cp_min',
                 'max_steps', 'catch_throw_parameters.excellent_rate', 'catch_throw_parameters.great_rate',
                 'catch_throw_parameters.nice_rate', 'catch_throw_parameters.normal_rate',
                 'catch_throw_parameters.spin_success_rate']
    for flag in old_flags:
        if flag in load:
            task_configuration_error(flag)
            return None

    nested_old_flags = [('forts', 'spin'), ('forts', 'move_to_spin'), ('navigator', 'path_mode'), ('navigator', 'path_file'), ('navigator', 'type')]
    for outer, inner in nested_old_flags:
        if load.get(outer, {}).get(inner, None):
            task_configuration_error('{}.{}'.format(outer, inner))
            return None

    if "evolve_captured" in load:
        logger.warning('The evolve_captured argument is no longer supported. Please use the EvolvePokemon task instead')

    if "walk" in load:
        logger.warning('The walk argument is no longer supported. Please use the walk_max and walk_min variables instead')

    if "daily_catch_limit" in load:
        logger.warning('The daily_catch_limit argument has been moved into the CatchPokemon Task')

    if "logging_color" in load:
        logger.warning('The logging_color argument has been moved into the logging config section')

    if config.walk_min < 1:
        parser.error("--walk_min is out of range! (should be >= 1.0)")
        return None

    if config.alt_min < -413.0:
        parser.error("--alt_min is out of range! (should be >= -413.0)")
        return None

    if not (config.location or config.location_cache):
        parser.error("Needs either --use-location-cache or --location.")
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

    fix_nested_config(config)
    return config, config_file


def add_config(parser, json_config, short_flag=None, long_flag=None, **kwargs):
    if not long_flag:
        raise Exception('add_config calls requires long_flag parameter!')

    full_attribute_path = long_flag.split('--')[1]
    attribute_name = full_attribute_path.split('.')[-1]

    if '.' in full_attribute_path:  # embedded config!
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
    except (UnicodeEncodeError, UnicodeDecodeError):
        return string

if __name__ == '__main__':
    main()
