# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
import logging
import os
import random
import re
import sys
import time
import Queue
import threading
import shelve
import uuid

from geopy.geocoders import GoogleV3
from pgoapi import PGoApi
from pgoapi.utilities import f2i, get_cell_ids

import cell_workers
from base_task import BaseTask
from plugin_loader import PluginLoader
from api_wrapper import ApiWrapper
from cell_workers.utils import distance
from event_manager import EventManager
from human_behaviour import sleep
from item_list import Item
from metrics import Metrics
from sleep_schedule import SleepSchedule
from pokemongo_bot.event_handlers import LoggingHandler, SocketIoHandler, ColoredLoggingHandler, SocialHandler
from pokemongo_bot.socketio_server.runner import SocketIoRunner
from pokemongo_bot.websocket_remote_control import WebsocketRemoteControl
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.datastore import _init_database, Datastore
from worker_result import WorkerResult
from tree_config_builder import ConfigException, MismatchTaskApiVersion, TreeConfigBuilder
from inventory import init_inventory
from sys import platform as _platform
from pgoapi.protos.POGOProtos.Enums import BadgeType_pb2
import struct

class PokemonGoBot(Datastore):
    @property
    def position(self):
        return self.api.actual_lat, self.api.actual_lng, self.api.actual_alt

    @property
    def noised_position(self):
        return self.api.noised_lat, self.api.noised_lng, self.api.noised_alt

    #@position.setter # these should be called through api now that gps replication is there...
    #def position(self, position_tuple):
    #    self.api._position_lat, self.api._position_lng, self.api._position_alt = position_tuple

    @property
    def player_data(self):
        """
        Returns the player data as received from the API.
        :return: The player data.
        :rtype: dict
        """
        return self._player

    def __init__(self, config):

        # Database connection MUST be setup before migrations will work
        self.database = _init_database('/data/{}.db'.format(config.username))

        self.config = config
        super(PokemonGoBot, self).__init__()

        self.fort_timeouts = dict()
        self.pokemon_list = json.load(
            open(os.path.join(_base_dir, 'data', 'pokemon.json'))
        )
        self.item_list = json.load(open(os.path.join(_base_dir, 'data', 'items.json')))
        # @var Metrics
        self.metrics = Metrics(self)
        self.latest_inventory = None
        self.cell = None
        self.recent_forts = [None] * config.forts_max_circle_size
        self.tick_count = 0
        self.softban = False
        self.start_position = None
        self.last_map_object = None
        self.last_time_map_object = 0
        self.logger = logging.getLogger(type(self).__name__)
        self.alt = self.config.gps_default_altitude

        # Make our own copy of the workers for this instance
        self.workers = []

        # Theading setup for file writing
        self.web_update_queue = Queue.Queue(maxsize=1)
        self.web_update_thread = threading.Thread(target=self.update_web_location_worker)
        self.web_update_thread.start()

        # Heartbeat limiting
        self.heartbeat_threshold = self.config.heartbeat_threshold
        self.heartbeat_counter = 0
        self.last_heartbeat = time.time()

        self.capture_locked = False  # lock catching while moving to VIP pokemon

        client_id_file_path = os.path.join(_base_dir, 'data', 'mqtt_client_id')
        saved_info = shelve.open(client_id_file_path)
        key = 'client_id'.encode('utf-8')
        if key in saved_info:
            self.config.client_id = saved_info[key]
        else:
            self.config.client_id = str(uuid.uuid4())
            saved_info[key] = self.config.client_id
        saved_info.close()

    def start(self):
        self._setup_event_system()
        self._setup_logging()
        self.sleep_schedule = SleepSchedule(self, self.config.sleep_schedule) if self.config.sleep_schedule else None
        if self.sleep_schedule: self.sleep_schedule.work()
        self._setup_api()
        self._load_recent_forts()
        init_inventory(self)
        self.display_player_info()
        self._print_character_info()
        if self.config.pokemon_bag_show_at_start and self.config.pokemon_bag_pokemon_info:
            self._print_list_pokemon()

        random.seed()

    def _setup_event_system(self):
        handlers = []
        if self.config.logging_color:
            handlers.append(ColoredLoggingHandler())
        else:
            handlers.append(LoggingHandler())
        if self.config.enable_social:
            handlers.append(SocialHandler(self))
        if self.config.websocket_server_url:
            if self.config.websocket_start_embedded_server:
                self.sio_runner = SocketIoRunner(self.config.websocket_server_url)
                self.sio_runner.start_listening_async()

            websocket_handler = SocketIoHandler(
                self,
                self.config.websocket_server_url
            )
            handlers.append(websocket_handler)

            if self.config.websocket_remote_control:
                remote_control = WebsocketRemoteControl(self).start()

        # @var EventManager
        self.event_manager = EventManager(self.config.walker_limit_output, *handlers)
        self._register_events()
        if self.config.show_events:
            self.event_manager.event_report()
            sys.exit(1)

            # Registering event:
            # self.event_manager.register_event("location", parameters=['lat', 'lng'])
            #
            # Emitting event should be enough to add logging and send websocket
            # message: :
            # self.event_manager.emit('location', 'level'='info', data={'lat': 1, 'lng':1}),

    def _register_events(self):
        self.event_manager.register_event(
            'location_found',
            parameters=('position', 'location')
        )
        self.event_manager.register_event('api_error')
        self.event_manager.register_event('config_error')

        self.event_manager.register_event('login_started')
        self.event_manager.register_event('login_failed')
        self.event_manager.register_event('login_successful')

        self.event_manager.register_event('set_start_location')
        self.event_manager.register_event('load_cached_location')
        self.event_manager.register_event('location_cache_ignored')

        #  ignore candy above threshold
        self.event_manager.register_event(
            'ignore_candy_above_thresold',
            parameters=(
                'name',
                'amount',
                'threshold'
            )
        )





        self.event_manager.register_event(
            'position_update',
            parameters=(
                'current_position',
                'last_position',
                'distance', # optional
                'distance_unit' # optional
            )
        )
        self.event_manager.register_event(
            'path_lap_update',
            parameters=(
                'number_lap',
                'number_lap_max'
            )
        )
        self.event_manager.register_event(
            'path_lap_end',
            parameters=(
                'duration',
                'resume'
            )
        )


        self.event_manager.register_event('location_cache_error')

        self.event_manager.register_event('bot_start')
        self.event_manager.register_event('bot_exit')
        self.event_manager.register_event('bot_interrupted')

        # sleep stuff
        self.event_manager.register_event(
            'next_sleep',
            parameters=('time',)
        )
        self.event_manager.register_event(
            'bot_sleep',
            parameters=(
                'time_hms',
                'wake'
            )
        )

        # random pause
        self.event_manager.register_event(
            'next_random_pause',
            parameters=(
                'time',
                'duration'
            )
        )
        self.event_manager.register_event(
            'bot_random_pause',
            parameters=(
                'time_hms',
                'resume'
            )
        )

        # recycle stuff
        self.event_manager.register_event(
            'next_force_recycle',
            parameters=(
                'time'
            )
        )
        self.event_manager.register_event('force_recycle')

        # random alive pause
        self.event_manager.register_event(
            'next_random_alive_pause',
            parameters=(
                'time',
                'duration'
            )
        )
        self.event_manager.register_event(
            'bot_random_alive_pause',
            parameters=(
                'time_hms',
                'resume'
            )
        )

        # fort stuff
        self.event_manager.register_event(
            'spun_fort',
            parameters=(
                'fort_id',
                'latitude',
                'longitude'
            )
        )
        self.event_manager.register_event(
            'lured_pokemon_found',
            parameters=(
                'fort_id',
                'fort_name',
                'encounter_id',
                'latitude',
                'longitude'
            )
        )
        self.event_manager.register_event(
            'moving_to_fort',
            parameters=(
                'fort_name',
                'distance'
            )
        )
        self.event_manager.register_event(
            'moving_to_lured_fort',
            parameters=(
                'fort_name',
                'distance',
                'lure_distance'
            )
        )
        self.event_manager.register_event(
            'spun_pokestop',
            parameters=(
                'pokestop', 'exp', 'items'
            )
        )
        self.event_manager.register_event(
            'pokestop_empty',
            parameters=('pokestop',)
        )
        self.event_manager.register_event(
            'pokestop_out_of_range',
            parameters=('pokestop',)
        )
        self.event_manager.register_event(
            'pokestop_on_cooldown',
            parameters=('pokestop', 'minutes_left')
        )
        self.event_manager.register_event(
            'unknown_spin_result',
            parameters=('status_code',)
        )
        self.event_manager.register_event('pokestop_searching_too_often')
        self.event_manager.register_event('arrived_at_fort')

        # pokemon stuff
        self.event_manager.register_event(
            'catchable_pokemon',
            parameters=(
                'pokemon_id',
                'spawn_point_id',
                'encounter_id',
                'latitude',
                'longitude',
                'expiration_timestamp_ms',
                'pokemon_name'
            )
        )
        self.event_manager.register_event(
            'pokemon_appeared',
            parameters=(
                'pokemon',
                'ncp',
                'cp',
                'iv',
                'iv_display',
                'encounter_id',
                'latitude',
                'longitude',
                'pokemon_id'
            )
        )
        self.event_manager.register_event('no_pokeballs')
        self.event_manager.register_event('enough_ultraballs')
        self.event_manager.register_event(
            'pokemon_catch_rate',
            parameters=(
                'catch_rate',
                'ball_name',
                'berry_name',
                'berry_count'
            )
        )
        self.event_manager.register_event(
            'threw_berry',
            parameters=(
                'berry_name',
                'ball_name',
                'new_catch_rate'
            )
        )
        self.event_manager.register_event(
            'threw_pokeball',
            parameters=(
                'throw_type',
                'spin_label',
                'ball_name',
                'success_percentage',
                'count_left'
            )
        )
        self.event_manager.register_event(
            'pokemon_capture_failed',
            parameters=('pokemon',)
        )
        self.event_manager.register_event(
            'pokemon_vanished',
            parameters=(
                'pokemon',
                'encounter_id',
                'latitude',
                'longitude',
                'pokemon_id'
            )
        )
        self.event_manager.register_event('pokemon_not_in_range')
        self.event_manager.register_event('pokemon_inventory_full')
        self.event_manager.register_event(
            'pokemon_caught',
            parameters=(
                'pokemon',
                'ncp', 'cp', 'iv', 'iv_display', 'exp',
                'encounter_id',
                'latitude',
                'longitude',
                'pokemon_id',
                'daily_catch_limit',
                'caught_last_24_hour',
            )
        )
        self.event_manager.register_event(
            'pokemon_evolved',
            parameters=('pokemon', 'iv', 'cp', 'xp', 'candy')
        )
        self.event_manager.register_event('skip_evolve')
        self.event_manager.register_event('threw_berry_failed', parameters=('status_code',))
        self.event_manager.register_event('vip_pokemon')
        self.event_manager.register_event('gained_candy', parameters=('quantity', 'type'))
        self.event_manager.register_event('catch_limit')
        self.event_manager.register_event('show_best_pokemon', parameters=('pokemons'))

        # level up stuff
        self.event_manager.register_event(
            'level_up',
            parameters=(
                'previous_level',
                'current_level'
            )
        )
        self.event_manager.register_event(
            'level_up_reward',
            parameters=('items',)
        )

        # lucky egg
        self.event_manager.register_event(
            'used_lucky_egg',
            parameters=('amount_left',)
        )
        self.event_manager.register_event('lucky_egg_error')

        # softban
        self.event_manager.register_event('softban')
        self.event_manager.register_event('softban_fix')
        self.event_manager.register_event('softban_fix_done')

        # egg incubating
        self.event_manager.register_event(
            'incubate_try',
            parameters=(
                'incubator_id',
                'egg_id'
            )
        )
        self.event_manager.register_event(
            'incubate',
            parameters=('distance_in_km',)
        )
        self.event_manager.register_event(
            'next_egg_incubates',
            parameters=('eggs_left', 'eggs_inc', 'eggs')
        )
        self.event_manager.register_event('incubator_already_used')
        self.event_manager.register_event('egg_already_incubating')
        self.event_manager.register_event(
            'egg_hatched',
            parameters=(
                'pokemon',
                'cp', 'iv', 'exp', 'stardust', 'candy'
            )
        )

        # discard item
        self.event_manager.register_event(
            'item_discarded',
            parameters=(
                'amount', 'item', 'maximum'
            )
        )
        self.event_manager.register_event(
            'item_discard_skipped',
            parameters=('space',)
        )
        self.event_manager.register_event(
            'item_discard_fail',
            parameters=('item',)
        )

        # inventory
        self.event_manager.register_event('inventory_full')

        # release
        self.event_manager.register_event(
            'keep_best_release',
            parameters=(
                'amount', 'pokemon', 'criteria'
            )
        )
        self.event_manager.register_event(
            'future_pokemon_release',
            parameters=(
                'pokemon', 'cp', 'iv', 'below_iv', 'below_cp', 'cp_iv_logic'
            )
        )
        self.event_manager.register_event(
            'pokemon_release',
            parameters=('pokemon', 'iv', 'cp', 'candy')
        )

        # polyline walker
        self.event_manager.register_event(
            'polyline_request',
            parameters=('url',)
        )

        # cluster
        self.event_manager.register_event(
            'found_cluster',
            parameters=(
                'num_points', 'forts', 'radius', 'distance'
            )
        )
        self.event_manager.register_event(
            'arrived_at_cluster',
            parameters=(
                'num_points', 'forts', 'radius'
            )
        )

        # rename
        self.event_manager.register_event(
            'rename_pokemon',
            parameters=('old_name', 'current_name',)
        )
        self.event_manager.register_event(
            'pokemon_nickname_invalid',
            parameters=('nickname',)
        )
        self.event_manager.register_event(
            'unset_pokemon_nickname',
            parameters=('old_name',)
        )

        # Move To map pokemon
        self.event_manager.register_event(
            'move_to_map_pokemon_fail',
            parameters=('message',)
        )
        self.event_manager.register_event(
            'move_to_map_pokemon_updated_map',
            parameters=('lat', 'lon')
        )
        self.event_manager.register_event(
            'move_to_map_pokemon_teleport_to',
            parameters=('poke_name', 'poke_dist', 'poke_lat', 'poke_lon',
                        'disappears_in')
        )
        self.event_manager.register_event(
            'move_to_map_pokemon_encounter',
            parameters=('poke_name', 'poke_dist', 'poke_lat', 'poke_lon',
                        'disappears_in')
        )
        self.event_manager.register_event(
            'move_to_map_pokemon_move_towards',
            parameters=('poke_name', 'poke_dist', 'poke_lat', 'poke_lon',
                        'disappears_in')
        )
        self.event_manager.register_event(
            'move_to_map_pokemon_teleport_back',
            parameters=('last_lat', 'last_lon')
        )
        self.event_manager.register_event(
            'moving_to_pokemon_throught_fort',
            parameters=('fort_name', 'distance','poke_name','poke_dist')
        )

        # cached recent_forts
        self.event_manager.register_event('loaded_cached_forts')
        self.event_manager.register_event('cached_fort')
        self.event_manager.register_event(
            'no_cached_forts',
            parameters=('path', )
        )
        self.event_manager.register_event(
            'error_caching_forts',
            parameters=('path', )
        )
        # database shit
        self.event_manager.register_event('catch_log')
        self.event_manager.register_event('evolve_log')
        self.event_manager.register_event('login_log')
        self.event_manager.register_event('transfer_log')
        self.event_manager.register_event('pokestop_log')
        self.event_manager.register_event('softban_log')

        self.event_manager.register_event(
            'badges',
            parameters=('badge', 'level')
        )
        self.event_manager.register_event(
            'player_data',
            parameters=('player_data', )
        )

    def tick(self):
        self.health_record.heartbeat()
        self.cell = self.get_meta_cell()

        if self.sleep_schedule: self.sleep_schedule.work()

        now = time.time() * 1000

        for fort in self.cell["forts"]:
            timeout = fort.get("cooldown_complete_timestamp_ms", 0)

            if timeout >= now:
                self.fort_timeouts[fort["id"]] = timeout

        self.tick_count += 1

        # Check if session token has expired
        self.check_session(self.position)

        for worker in self.workers:
            if worker.work() == WorkerResult.RUNNING:
                return

    def get_meta_cell(self):
        location = self.position[0:2]
        cells = self.find_close_cells(*location)

        # Combine all cells into a single dict of the items we care about.
        forts = []
        wild_pokemons = []
        catchable_pokemons = []
        for cell in cells:
            if "forts" in cell and len(cell["forts"]):
                forts += cell["forts"]
            if "wild_pokemons" in cell and len(cell["wild_pokemons"]):
                wild_pokemons += cell["wild_pokemons"]
            if "catchable_pokemons" in cell and len(cell["catchable_pokemons"]):
                catchable_pokemons += cell["catchable_pokemons"]

        # If there are forts present in the cells sent from the server or we don't yet have any cell data, return all data retrieved
        if len(forts) > 1 or not self.cell:
            return {
                "forts": forts,
                "wild_pokemons": wild_pokemons,
                "catchable_pokemons": catchable_pokemons
            }
        # If there are no forts present in the data from the server, keep our existing fort data and only update the pokemon cells.
        else:
            return {
                "forts": self.cell["forts"],
                "wild_pokemons": wild_pokemons,
                "catchable_pokemons": catchable_pokemons
            }

    def update_web_location(self, cells=[], lat=None, lng=None, alt=None):
        # we can call the function with no arguments and still get the position
        # and map_cells
        if lat is None:
            lat = self.api._position_lat
        if lng is None:
            lng = self.api._position_lng
        if alt is None:
            alt = self.api._position_alt

        # dont cache when teleport_to
        if self.api.teleporting:
            return

        if cells == []:
            location = self.position[0:2]
            cells = self.find_close_cells(*location)

        user_data_cells = os.path.join(_base_dir, 'data', 'cells-%s.json' % self.config.username)
        try:
            with open(user_data_cells, 'w') as outfile:
                json.dump(cells, outfile)
        except IOError as e:
            self.logger.info('[x] Error while opening location file: %s' % e)

        user_web_location = os.path.join(
            _base_dir, 'web', 'location-%s.json' % self.config.username
        )
        # alt is unused atm but makes using *location easier
        try:
            with open(user_web_location, 'w') as outfile:
                json.dump({
                    'lat': lat,
                    'lng': lng,
                    'alt': alt,
                    'cells': cells
                }, outfile)
        except IOError as e:
            self.logger.info('[x] Error while opening location file: %s' % e)

        user_data_lastlocation = os.path.join(
            _base_dir, 'data', 'last-location-%s.json' % self.config.username
        )
        try:
            with open(user_data_lastlocation, 'w') as outfile:
                json.dump({'lat': lat, 'lng': lng, 'alt': alt, 'start_position': self.start_position}, outfile)
        except IOError as e:
            self.logger.info('[x] Error while opening location file: %s' % e)

    def find_close_cells(self, lat, lng):
        cellid = get_cell_ids(lat, lng)
        timestamp = [0, ] * len(cellid)
        response_dict = self.get_map_objects(lat, lng, timestamp, cellid)
        map_objects = response_dict.get(
            'responses', {}
        ).get('GET_MAP_OBJECTS', {})
        status = map_objects.get('status', None)

        map_cells = []
        if status and status == 1:
            map_cells = map_objects['map_cells']
            position = (lat, lng, 0)
            map_cells.sort(
                key=lambda x: distance(
                    lat,
                    lng,
                    x['forts'][0]['latitude'],
                    x['forts'][0]['longitude']) if x.get('forts', []) else 1e6
            )
        return map_cells

    def _setup_logging(self):
        # log settings
        # log format

        if self.config.debug:
            log_level = logging.DEBUG
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("websocket").setLevel(logging.DEBUG)
            logging.getLogger("socketio").setLevel(logging.DEBUG)
            logging.getLogger("engineio").setLevel(logging.DEBUG)
            logging.getLogger("socketIO-client").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            log_level = logging.ERROR
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("websocket").setLevel(logging.ERROR)
            logging.getLogger("socketio").setLevel(logging.ERROR)
            logging.getLogger("engineio").setLevel(logging.ERROR)
            logging.getLogger("socketIO-client").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(name)10s] [%(levelname)s] %(message)s'
        )
    def check_session(self, position):

        # Check session expiry
        if self.api._auth_provider and self.api._auth_provider._ticket_expire:

            # prevent crash if return not numeric value
            if not self.is_numeric(self.api._auth_provider._ticket_expire):
                self.logger.info("Ticket expired value is not numeric", 'yellow')
                return

            remaining_time = \
                self.api._auth_provider._ticket_expire / 1000 - time.time()

            if remaining_time < 60:
                self.event_manager.emit(
                    'api_error',
                    sender=self,
                    level='info',
                    formatted='Session stale, re-logging in.'
                )
                self.api = ApiWrapper(config=self.config)
                self.api.set_position(*position)
                self.login()
                self.api.activate_signature(self.get_encryption_lib())

    @staticmethod
    def is_numeric(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def login(self):
        self.event_manager.emit(
            'login_started',
            sender=self,
            level='info',
            formatted="Login procedure started."
        )
        lat, lng = self.position[0:2]
        self.api.set_position(lat, lng, self.alt) # or should the alt kept to zero?

        while not self.api.login(
            self.config.auth_service,
            str(self.config.username),
            str(self.config.password)):

            self.event_manager.emit(
                'login_failed',
                sender=self,
                level='info',
                formatted="Login error, server busy. Waiting 10 seconds to try again."
            )
            time.sleep(10)

        with self.database as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='login'")

        result = c.fetchone()

        while True:
            if result[0] == 1:
                conn.execute('''INSERT INTO login (timestamp, message) VALUES (?, ?)''', (time.time(), 'LOGIN_SUCCESS'))
                break
            else:
                self.event_manager.emit(
                    'login_failed',
                    sender=self,
                    level='info',
                    formatted="Login table not founded, skipping log"
                )
                break

        self.event_manager.emit(
            'login_successful',
            sender=self,
            level='info',
            formatted="Login successful."
        )

    def get_encryption_lib(self):
        if _platform == "Windows" or _platform == "win32":
            # Check if we are on 32 or 64 bit
            if sys.maxsize > 2**32:
                file_name = 'encrypt_64.dll'
            else:
                file_name = 'encrypt.dll'
        else:
            file_name = 'encrypt.so'

        if self.config.encrypt_location == '':
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        else:
            path = self.config.encrypt_location

        full_path = path + '/'+ file_name
        if not os.path.isfile(full_path):
            self.logger.error(file_name + ' is not found! Please place it in the bots root directory or set encrypt_location in config.')
            self.logger.info('Platform: '+ _platform + ' ' + file_name + ' directory: '+ path)
            sys.exit(1)
        else:
            self.logger.info('Found '+ file_name +'! Platform: ' + _platform + ' ' + file_name + ' directory: ' + path)

        return full_path

    def _setup_api(self):
        # instantiate pgoapi @var ApiWrapper
        self.api = ApiWrapper(config=self.config)

        # provide player position on the earth
        self._set_starting_position()

        self.login()
        # chain subrequests (methods) into one RPC call

        self.api.activate_signature(self.get_encryption_lib())
        self.logger.info('')
        # send empty map_cells and then our position
        self.update_web_location()

    def _print_character_info(self):
        # get player profile call
        # ----------------------
        response_dict = self.api.get_player()
        # print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1 = "0"
        currency_2 = "0"

        if response_dict:
            self._player = response_dict['responses']['GET_PLAYER']['player_data']
            player = self._player
        else:
            self.logger.info(
                "The API didn't return player info, servers are unstable - "
                "retrying.", 'red'
            )
            sleep(5)
            self._print_character_info()

        # @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(
            player['creation_timestamp_ms'] / 1e3)
        creation_date = creation_date.strftime("%Y/%m/%d %H:%M:%S")

        pokecoins = '0'
        stardust = '0'
        items_inventory = inventory.items()

        if 'amount' in player['currencies'][0]:
            pokecoins = player['currencies'][0]['amount']
        if 'amount' in player['currencies'][1]:
            stardust = player['currencies'][1]['amount']
        self.logger.info('')
        self.logger.info('--- {username} ---'.format(**player))

        self.logger.info(
            'Pokemon Bag: {}/{}'.format(
                inventory.Pokemons.get_space_used(),
                inventory.get_pokemon_inventory_size()
            )
        )
        self.logger.info(
            'Items: {}/{}'.format(
                inventory.Items.get_space_used(),
                inventory.get_item_inventory_size()
            )
        )
        self.logger.info(
            'Stardust: {}'.format(stardust) +
            ' | Pokecoins: {}'.format(pokecoins)
        )
        # Items Output
        self.logger.info(
            'PokeBalls: ' + str(items_inventory.get(1).count) +
            ' | GreatBalls: ' + str(items_inventory.get(2).count) +
            ' | UltraBalls: ' + str(items_inventory.get(3).count) +
            ' | MasterBalls: ' + str(items_inventory.get(4).count))

        self.logger.info(
            'RazzBerries: ' + str(items_inventory.get(701).count) +
            ' | BlukBerries: ' + str(items_inventory.get(702).count) +
            ' | NanabBerries: ' + str(items_inventory.get(703).count))

        self.logger.info(
            'LuckyEgg: ' + str(items_inventory.get(301).count) +
            ' | Incubator: ' + str(items_inventory.get(902).count) +
            ' | TroyDisk: ' + str(items_inventory.get(501).count))

        self.logger.info(
            'Potion: ' + str(items_inventory.get(101).count) +
            ' | SuperPotion: ' + str(items_inventory.get(102).count) +
            ' | HyperPotion: ' + str(items_inventory.get(103).count) +
            ' | MaxPotion: ' + str(items_inventory.get(104).count))

        self.logger.info(
            'Incense: ' + str(items_inventory.get(401).count) +
            ' | IncenseSpicy: ' + str(items_inventory.get(402).count) +
            ' | IncenseCool: ' + str(items_inventory.get(403).count))

        self.logger.info(
            'Revive: ' + str(items_inventory.get(201).count) +
            ' | MaxRevive: ' + str(items_inventory.get(202).count))

        self.logger.info('')

    def _print_list_pokemon(self):
        # get pokemon list
        bag = inventory.pokemons().all()
        id_list =list(set(map(lambda x: x.pokemon_id, bag)))
        id_list.sort()
        pokemon_list = [filter(lambda x: x.pokemon_id == y, bag) for y in id_list]

        show_count = self.config.pokemon_bag_show_count
        show_candies = self.config.pokemon_bag_show_candies
        poke_info_displayed = self.config.pokemon_bag_pokemon_info

        def get_poke_info(info, pokemon):
            poke_info = {
                'cp': 'CP {}'.format(pokemon.cp),
                'iv_ads': 'A/D/S {}/{}/{}'.format(pokemon.iv_attack, pokemon.iv_defense, pokemon.iv_stamina),
                'iv_pct': 'IV {}'.format(pokemon.iv),
                'ivcp': 'IVCP {}'.format(round(pokemon.ivcp,2)),
                'ncp': 'NCP {}'.format(round(pokemon.cp_percent,2)),
                'level': "Level {}".format(pokemon.level),
                'hp': 'HP {}/{}'.format(pokemon.hp, pokemon.hp_max),
                'moveset': 'Moves: {}'.format(pokemon.moveset),
                'dps': 'DPS {}'.format(round(pokemon.moveset.dps, 2))
            }
            if info not in poke_info:
                raise ConfigException("info '{}' isn't available for displaying".format(info))
            return poke_info[info]

        self.logger.info('Pokemon:')

        for pokes in pokemon_list:
            line_p = '#{} {}'.format(pokes[0].pokemon_id, pokes[0].name)
            if show_count:
                line_p += '[{}]'.format(len(pokes))
            if show_candies:
                line_p += '[{} candies]'.format(pokes[0].candy_quantity)
            line_p += ': '

            poke_info = ['({})'.format(', '.join([get_poke_info(x, p) for x in poke_info_displayed])) for p in pokes]
            self.logger.info(line_p + ' | '.join(poke_info))

        self.logger.info('')

    def use_lucky_egg(self):
        return self.api.use_item_xp_boost(item_id=301)

    def _set_starting_position(self):

        self.event_manager.emit(
            'set_start_location',
            sender=self,
            level='info',
            formatted='Setting start location.'
        )

        has_position = False

        if self.config.test:
            # TODO: Add unit tests
            return

        if self.config.location:
            location_str = self.config.location
            location = self.get_pos_by_name(location_str.replace(" ", ""))
            msg = "Location found: {location} {position}"
            self.event_manager.emit(
                'location_found',
                sender=self,
                level='info',
                formatted=msg,
                data={
                    'location': location_str,
                    'position': location
                }
            )

            self.api.set_position(*location)

            self.event_manager.emit(
                'position_update',
                sender=self,
                level='info',
                formatted="Now at {current_position}",
                data={
                    'current_position': self.position,
                    'last_position': '',
                    'distance': '',
                    'distance_unit': ''
                }
            )

            self.start_position = self.position

            has_position = True

        if self.config.location_cache:
            try:
                # save location flag used to pull the last known location from
                # the location.json
                self.event_manager.emit(
                    'load_cached_location',
                    sender=self,
                    level='debug',
                    formatted='Loading cached location...'
                )
                with open(os.path.join(_base_dir, 'data', 'last-location-%s.json' %
                    self.config.username)) as f:
                    location_json = json.load(f)
                location = (
                    location_json['lat'],
                    location_json['lng'],
                    location_json['alt'],
                )

                # If location has been set in config, only use cache if starting position has not differed
                if has_position and 'start_position' in location_json:
                    last_start_position = tuple(location_json.get('start_position', []))

                    # Start position has to have been set on a previous run to do this check
                    if last_start_position and last_start_position != self.start_position:
                        msg = 'Going to a new place, ignoring cached location.'
                        self.event_manager.emit(
                            'location_cache_ignored',
                            sender=self,
                            level='debug',
                            formatted=msg
                        )
                        return

                self.api.set_position(*location)
                self.event_manager.emit(
                    'position_update',
                    sender=self,
                    level='debug',
                    formatted='Loaded location {current_position} from cache',
                    data={
                        'current_position': location,
                        'last_position': '',
                        'distance': '',
                        'distance_unit': ''
                    }
                )

                has_position = True
            except Exception:
                if has_position is False:
                    sys.exit(
                        "No cached Location. Please specify initial location."
                    )
                self.event_manager.emit(
                    'location_cache_error',
                    sender=self,
                    level='debug',
                    formatted='Parsing cached location failed.'
                )

    def get_pos_by_name(self, location_name):
        # Check if given location name, belongs to favorite_locations
        favorite_location_coords = self._get_pos_by_fav_location(location_name)

        if favorite_location_coords is not None:
            return favorite_location_coords

        # Check if the given location is already a coordinate.
        if ',' in location_name:
            possible_coordinates = re.findall(
                "[-]?\d{1,3}[.]\d{3,7}", location_name
            )
            if len(possible_coordinates) >= 2:
                # 2 matches, this must be a coordinate. We'll bypass the Google
                # geocode so we keep the exact location.
                self.logger.info(
                    '[x] Coordinates found in passed in location, '
                    'not geocoding.'
                )
                return float(possible_coordinates[0]), float(possible_coordinates[1]), (float(possible_coordinates[2]) if len(possible_coordinates) == 3 else self.alt)

        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name, timeout=10)

        return float(loc.latitude), float(loc.longitude), float(loc.altitude)

    def _get_pos_by_fav_location(self, location_name):

        location_name = location_name.lower()
        coords = None

        for location in self.config.favorite_locations:
            if location.get('name').lower() == location_name:
                coords = re.findall(
                    "[-]?\d{1,3}[.]\d{3,7}", location.get('coords').strip()
                )
                if len(coords) >= 2:
                    self.logger.info('Favorite location found: {} ({})'.format(location_name, coords))
                break

        #TODO: This is real bad
        if coords is None:
            return coords
        else:
            return float(coords[0]), float(coords[1]), (float(coords[2]) if len(coords) == 3 else self.alt)

    def heartbeat(self):
        # Remove forts that we can now spin again.
        now = time.time()
        self.fort_timeouts = {id: timeout for id, timeout
                              in self.fort_timeouts.iteritems()
                              if timeout >= now * 1000}

        if now - self.last_heartbeat >= self.heartbeat_threshold:
            self.last_heartbeat = now
            request = self.api.create_request()
            request.get_player()
            request.check_awarded_badges()
            responses = request.call()

            if responses['responses']['GET_PLAYER']['success'] == True:
                #we get the player_data anyway, might as well store it
                self._player = responses['responses']['GET_PLAYER']['player_data']
                self.event_manager.emit(
                    'player_data',
                    sender=self,
                    level='debug',
                    formatted='player_data: {player_data}',
                    data={'player_data': self._player}
                )
            if responses['responses']['CHECK_AWARDED_BADGES']['success'] == True:
                #store awarded_badges reponse to be used in a task or part of heartbeat
                self._awarded_badges = responses['responses']['CHECK_AWARDED_BADGES']

            if self._awarded_badges.has_key('awarded_badges'):
                i = 0
                for badge in self._awarded_badges['awarded_badges']:
                    badgelevel = self._awarded_badges['awarded_badge_levels'][i]
                    badgename = BadgeType_pb2._BADGETYPE.values_by_number[badge].name
                    i += 1
                    self.event_manager.emit(
                        'badges',
                        sender=self,
                        level='info',
                        formatted='awarded badge: {badge}, lvl {level}',
                        data={'badge': badgename,
                              'level' : badgelevel }
                    )

                    #todo move equip badge into its own task once working
                    #should work but gives errors :'(s
                    #response = self.api.equip_badge(badge_type=badge)
                    response = {'responses': "awaiting further testing on api call to equip_badge"}
                    self.event_manager.emit(
                        'badges',
                        sender=self,
                        level='info',
                        formatted='equiped badge: {badge}',
                        data={'badge': response['responses']}
                    )
                    human_behaviour.action_delay(3,10)


        try:
            self.web_update_queue.put_nowait(True)  # do this outside of thread every tick
        except Queue.Full:
            pass

    def update_web_location_worker(self):
        while True:
            self.web_update_queue.get()
            self.update_web_location()

    def display_player_info(self):
            inventory_items = self.api.get_inventory()
            inventory_items = inventory_items['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
            player_stats = next((x["inventory_item_data"]["player_stats"]
                     for x in inventory_items
                     if x.get("inventory_item_data", {}).get("player_stats", {})),
                    None)

            if player_stats:

                nextlvlxp = (int(player_stats.get('next_level_xp', 0)) - int(player_stats.get('experience', 0)))

                if 'level' in player_stats and 'experience' in player_stats:
                    self.logger.info(
                        'Level: {level}'.format(
                            **player_stats) +
                        ' (Next Level: {} XP)'.format(
                            nextlvlxp) +
                        ' (Total: {experience} XP)'
                        ''.format(**player_stats))

                if 'pokemons_captured' in player_stats and 'poke_stop_visits' in player_stats:
                    self.logger.info(
                        'Pokemon Captured: '
                        '{pokemons_captured}'.format(
                            **player_stats) +
                        ' | Pokestops Visited: '
                        '{poke_stop_visits}'.format(
                            **player_stats))

    def get_forts(self, order_by_distance=False):
        forts = [fort
                 for fort in self.cell['forts']
                 if 'latitude' in fort and 'type' in fort]

        if order_by_distance:
            forts.sort(key=lambda x: distance(
                self.position[0],
                self.position[1],
                x['latitude'],
                x['longitude']
            ))

        return forts

    def get_map_objects(self, lat, lng, timestamp, cellid):
        if time.time() - self.last_time_map_object < self.config.map_object_cache_time:
            return self.last_map_object

        self.last_map_object = self.api.get_map_objects(
            latitude=f2i(lat),
            longitude=f2i(lng),
            since_timestamp_ms=timestamp,
            cell_id=cellid
        )
        self.last_time_map_object = time.time()

        return self.last_map_object

    def _load_recent_forts(self):
        if not self.config.forts_cache_recent_forts:
            return


        cached_forts_path = os.path.join(_base_dir, 'data', 'recent-forts-%s.json' % self.config.username)
        try:
            # load the cached recent forts
            with open(cached_forts_path) as f:
                cached_recent_forts = json.load(f)

            num_cached_recent_forts = len(cached_recent_forts)
            num_recent_forts = len(self.recent_forts)

            # Handles changes in max_circle_size
            if not num_recent_forts:
                self.recent_forts = []
            elif num_recent_forts > num_cached_recent_forts:
                self.recent_forts[-num_cached_recent_forts:] = cached_recent_forts
            elif num_recent_forts < num_cached_recent_forts:
                self.recent_forts = cached_recent_forts[-num_recent_forts:]
            else:
                self.recent_forts = cached_recent_forts

            self.event_manager.emit(
                'loaded_cached_forts',
                sender=self,
                level='debug',
                formatted='Loaded cached forts...'
            )
        except IOError:
            self.event_manager.emit(
                'no_cached_forts',
                sender=self,
                level='debug',
                formatted='Starting new cached forts for {path}',
                data={'path': cached_forts_path}
            )
