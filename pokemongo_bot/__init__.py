# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import googlemaps
import json
import logging
import os
import random
import re
import sys
import time

from geopy.geocoders import GoogleV3
from pgoapi import PGoApi
from pgoapi.utilities import f2i, get_cell_ids

import cell_workers
from api_wrapper import ApiWrapper
from cell_workers.utils import distance
from event_manager import EventManager
from human_behaviour import sleep
from item_list import Item
from metrics import Metrics
from pokemongo_bot.event_handlers import LoggingHandler, SocketIoHandler
from pokemongo_bot.socketio_server.runner import SocketIoRunner
from pokemongo_bot.websocket_remote_control import WebsocketRemoteControl
from worker_result import WorkerResult
from tree_config_builder import ConfigException, TreeConfigBuilder


class PokemonGoBot(object):
    @property
    def position(self):
        return self.api._position_lat, self.api._position_lng, 0

    @position.setter
    def position(self, position_tuple):
        self.api._position_lat, self.api._position_lng, self.api._position_alt = position_tuple

    def __init__(self, config):
        self.config = config
        self.fort_timeouts = dict()
        self.pokemon_list = json.load(
            open(os.path.join('data', 'pokemon.json'))
        )
        self.item_list = json.load(open(os.path.join('data', 'items.json')))
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

        # Make our own copy of the workers for this instance
        self.workers = []

    def start(self):
        self._setup_event_system()
        self._setup_logging()
        self._setup_api()

        self.config.user_journal = os.path.join(
            'data', 'journal-%s.txt' % self.config.username
        )

        if self.config.journal and not os.path.exists(self.config.user_journal):
            with open(self.config.user_journal, 'w') as outfile:
                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                outfile.write('Bot started at %s \n' % st)
		
        random.seed()


    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, position, include_fort_on_path):
        if self.config.evolve_all:
            # Run evolve all once. Flip the bit.
            print('[#] Attempting to evolve all pokemons ...')
            worker = EvolveAllWorker(self)
            worker.work()
            self.config.evolve_all = []

        self._filter_ignored_pokemons(cell)

        if (self.config.mode == "all" or self.config.mode ==
                "poke") and 'catchable_pokemons' in cell and len(cell[
                    'catchable_pokemons']) > 0:
            logger.log('[#] Something rustles nearby!')
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            cell['catchable_pokemons'].sort(
                key=
                lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))

            user_web_catchable = 'web/catchable-%s.json' % (self.config.username)
            for pokemon in cell['catchable_pokemons']:
                with open(user_web_catchable, 'w') as outfile:
                    json.dump(pokemon, outfile)

                if self.catch_pokemon(pokemon) == PokemonCatchWorker.NO_POKEBALLS:
                    break
                with open(user_web_catchable, 'w') as outfile:
                    json.dump({}, outfile)

        if (self.config.mode == "all" or self.config.mode == "poke"
            ) and 'wild_pokemons' in cell and len(cell['wild_pokemons']) > 0:
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            cell['wild_pokemons'].sort(
                key=
                lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
            for pokemon in cell['wild_pokemons']:
                if self.catch_pokemon(pokemon) == PokemonCatchWorker.NO_POKEBALLS:
                    break
        if (self.config.mode == "all" or
                self.config.mode == "farm") and include_fort_on_path:
            if 'forts' in cell:
                # Only include those with a lat/long
                forts = [fort
                         for fort in cell['forts']
                         if 'latitude' in fort and 'type' in fort]
                gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                forts.sort(key=lambda x: distance(self.position[
                           0], self.position[1], x['latitude'], x['longitude']))
                for fort in forts:
                    worker = MoveToFortWorker(fort, self)
                    worker.work()

                    worker = SeenFortWorker(fort, self)
                    hack_chain = worker.work()
                    if hack_chain > 10:
                        #print('need a rest')
                        break

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
                self.logger.info("Session stale, re-logging in", 'yellow')
                position = self.position
                self.api = ApiWrapper()
                self.position = position
                self.login()

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
        self.api.set_position(lat, lng, 0)

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

        self.event_manager.emit(
            'login_successful',
            sender=self,
            level='info',
            formatted="Login successful."
        )

    def _setup_api(self):
        # instantiate pgoapi
        self.api = ApiWrapper()

        # provide player position on the earth
        self._set_starting_position()

        self.login()
        # chain subrequests (methods) into one RPC call

        self._print_character_info()

        self.logger.info('')
        self.update_inventory()
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
        items_stock = self.current_inventory()

        if 'amount' in player['currencies'][0]:
            pokecoins = player['currencies'][0]['amount']
        if 'amount' in player['currencies'][1]:
            stardust = player['currencies'][1]['amount']
        self.logger.info('')
        self.logger.info('--- {username} ---'.format(**player))
        self.get_player_info()
        self.logger.info(
            'Pokemon Bag: {}/{}'.format(
                self.get_inventory_count('pokemon'),
                player['max_pokemon_storage']
            )
        )
        self.logger.info(
            'Items: {}/{}'.format(
                self.get_inventory_count('item'),
                player['max_item_storage']
            )
        )
        self.logger.info(
            'Stardust: {}'.format(stardust) +
            ' | Pokecoins: {}'.format(pokecoins)
        )
        # Items Output
        self.logger.info(
            'PokeBalls: ' + str(items_stock[1]) +
            ' | GreatBalls: ' + str(items_stock[2]) +
            ' | UltraBalls: ' + str(items_stock[3]))

        self.logger.info(
            'RazzBerries: ' + str(items_stock[701]) +
            ' | BlukBerries: ' + str(items_stock[702]) +
            ' | NanabBerries: ' + str(items_stock[703]))

        self.logger.info(
            'LuckyEgg: ' + str(items_stock[301]) +
            ' | Incubator: ' + str(items_stock[902]) +
            ' | TroyDisk: ' + str(items_stock[501]))

        self.logger.info(
            'Potion: ' + str(items_stock[101]) +
            ' | SuperPotion: ' + str(items_stock[102]) +
            ' | HyperPotion: ' + str(items_stock[103]))

        self.logger.info(
            'Incense: ' + str(items_stock[401]) +
            ' | IncenseSpicy: ' + str(items_stock[402]) +
            ' | IncenseCool: ' + str(items_stock[403]))

        self.logger.info(
            'Revive: ' + str(items_stock[201]) +
            ' | MaxRevive: ' + str(items_stock[202]))

        self.logger.info('')

    def use_lucky_egg(self):
        return self.api.use_item_xp_boost(item_id=301)

    def get_inventory(self):
        if self.latest_inventory is None:
            self.latest_inventory = self.api.get_inventory()
        return self.latest_inventory

    def update_inventory(self):
        response = self.get_inventory()
        self.inventory = list()
        inventory_items = response.get('responses', {}).get('GET_INVENTORY', {}).get(
            'inventory_delta', {}).get('inventory_items', {})
        if inventory_items:
            for item in inventory_items:
                item_info = item.get('inventory_item_data', {}).get('item', {})
                if {"item_id", "count"}.issubset(set(item_info.keys())):
                    self.inventory.append(item['inventory_item_data']['item'])

    def current_inventory(self):
        inventory_req = self.get_inventory()
        inventory_dict = inventory_req['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']


        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)

        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        # get player items stock
        # ----------------------
        items_stock = {x.value: 0 for x in list(Item)}

        for item in inventory_dict:
            item_dict = item.get('inventory_item_data', {}).get('item', {})
            item_count = item_dict.get('count')
            item_id = item_dict.get('item_id')

            if item_count and item_id:
                if item_id in items_stock:
                    items_stock[item_id] = item_count
        return items_stock

    def item_inventory_count(self, id):
        inventory_req = self.get_inventory()
        inventory_dict = inventory_req['responses'][
            'GET_INVENTORY']['inventory_delta']['inventory_items']

        if id == 'all':
            return self._all_items_inventory_count(inventory_dict)
        else:
            return self._item_inventory_count_per_id(id, inventory_dict)

    def _item_inventory_count_per_id(self, id, inventory_dict):
        item_count = 0

        for item in inventory_dict:
            item_dict = item.get('inventory_item_data', {}).get('item', {})
            item_id = item_dict.get('item_id', False)
            item_count = item_dict.get('count', False)
            if item_id == int(id) and item_count:
                return item_count
        return 0

    def _all_items_inventory_count(self, inventory_dict):
        item_count_dict = {}

        for item in inventory_dict:
            item_dict = item.get('inventory_item_data', {}).get('item', {})
            item_id = item_dict.get('item_id', False)
            item_count = item_dict.get('count', False)
            if item_id and item_count:
                item_count_dict[item_id] = item_count

        return item_count_dict

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
                with open('data/last-location-%s.json' %
                    self.config.username) as f:
                    location_json = json.load(f)
                location = (
                    location_json['lat'],
                    location_json['lng'],
                    0.0
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
        # Check if the given location is already a coordinate.
        if ',' in location_name:
            possible_coordinates = re.findall(
                "[-]?\d{1,3}[.]\d{3,7}", location_name
            )
            if len(possible_coordinates) == 2:
                # 2 matches, this must be a coordinate. We'll bypass the Google
                # geocode so we keep the exact location.
                self.logger.info(
                    '[x] Coordinates found in passed in location, '
                    'not geocoding.'
                )
                return float(possible_coordinates[0]), float(possible_coordinates[1]), float("0.0")

        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name, timeout=10)

        return float(loc.latitude), float(loc.longitude), float(loc.altitude)

    def heartbeat(self):
        # Remove forts that we can now spin again.
        self.fort_timeouts = {id: timeout for id, timeout
                              in self.fort_timeouts.iteritems()
                              if timeout >= time.time() * 1000}
        request = self.api.create_request()
        request.get_player()
        request.check_awarded_badges()
        request.call()
        self.update_web_location()  # updates every tick

    def get_inventory_count(self, what):
        response_dict = self.get_inventory()
        inventory_items = response_dict.get('responses', {}).get('GET_INVENTORY', {}).get(
            'inventory_delta', {}).get('inventory_items', {})
        if inventory_items:
            pokecount = 0
            itemcount = 1
            for item in inventory_items:
                if 'inventory_item_data' in item:
                    if 'pokemon_data' in item['inventory_item_data']:
                        pokecount += 1
                    itemcount += item['inventory_item_data'].get('item', {}).get('count', 0)
        if 'pokemon' in what:
            return pokecount
        if 'item' in what:
            return itemcount
        return '0'

    def get_player_info(self):
        response_dict = self.get_inventory()
        inventory_items = response_dict.get('responses', {}).get('GET_INVENTORY', {}).get(
            'inventory_delta', {}).get('inventory_items', {})
        if inventory_items:
            pokecount = 0
            itemcount = 1
            for item in inventory_items:
                # print('item {}'.format(item))
                playerdata = item.get('inventory_item_data', {}).get('player_stats')
                if playerdata:
                    nextlvlxp = (int(playerdata.get('next_level_xp', 0)) - int(playerdata.get('experience', 0)))

                    if 'level' in playerdata and 'experience' in playerdata:
                        self.logger.info(
                            'Level: {level}'.format(
                                **playerdata) +
                            ' (Next Level: {} XP)'.format(
                                nextlvlxp) +
                            ' (Total: {experience} XP)'
                            ''.format(**playerdata))

                    if 'pokemons_captured' in playerdata and 'poke_stop_visits' in playerdata:
                        self.logger.info(
                            'Pokemon Captured: '
                            '{pokemons_captured}'.format(
                                **playerdata) +
                            ' | Pokestops Visited: '
                            '{poke_stop_visits}'.format(
                                **playerdata))

    def has_space_for_loot(self):
        number_of_things_gained_by_stop = 5
        enough_space = (
            self.get_inventory_count('item') <
            self._player['max_item_storage'] - number_of_things_gained_by_stop
        )

        return enough_space

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
