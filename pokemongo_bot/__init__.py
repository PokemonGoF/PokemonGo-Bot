# -*- coding: utf-8 -*-

import datetime
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
import logger
from api_wrapper import ApiWrapper
from cell_workers.utils import distance
from event_manager import EventManager
from human_behaviour import sleep
from item_list import Item
from metrics import Metrics
from pokemongo_bot.event_handlers import LoggingHandler, SocketIoHandler
from pokemongo_bot.socketio_server.runner import SocketIoRunner
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

        # Make our own copy of the workers for this instance
        self.workers = []

    def start(self):
        self._setup_logging()
        self._setup_api()

        random.seed()

    def _setup_event_system(self):
        handlers = [LoggingHandler()]
        if self.config.websocket_server:
            websocket_handler = SocketIoHandler(self.config.websocket_server_url)
            handlers.append(websocket_handler)

            if self.config.websocket_start_embedded_server:
                self.sio_runner = SocketIoRunner(self.config.websocket_server_url)
                self.sio_runner.start_listening_async()

        self.event_manager = EventManager(*handlers)

        # Registering event:
        # self.event_manager.register_event("location", parameters=['lat', 'lng'])
        #
        # Emitting event should be enough to add logging and send websocket
        # message: :
        # self.event_manager.emit('location', 'level'='info', data={'lat': 1, 'lng':1}),

    def tick(self):
        self.cell = self.get_meta_cell()
        self.tick_count += 1

        # Check if session token has expired
        self.check_session(self.position[0:2])

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
            alt = 0

        if cells == []:
            location = self.position[0:2]
            cells = self.find_close_cells(*location)

            # insert detail info about gym to fort
            for cell in cells:
                if 'forts' in cell:
                    for fort in cell['forts']:
                        if fort.get('type') != 1:
                            response_gym_details = self.api.get_gym_details(
                                gym_id=fort.get('id'),
                                player_latitude=lng,
                                player_longitude=lat,
                                gym_latitude=fort.get('latitude'),
                                gym_longitude=fort.get('longitude')
                            )
                            fort['gym_details'] = response_gym_details.get(
                                'responses', {}
                            ).get('GET_GYM_DETAILS', None)

        user_data_cells = "data/cells-%s.json" % self.config.username
        with open(user_data_cells, 'w') as outfile:
            json.dump(cells, outfile)

        user_web_location = os.path.join(
            'web', 'location-%s.json' % self.config.username
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
            logger.log('[x] Error while opening location file: %s' % e, 'red')

        user_data_lastlocation = os.path.join(
            'data', 'last-location-%s.json' % self.config.username
        )
        try:
            with open(user_data_lastlocation, 'w') as outfile:
                json.dump({'lat': lat, 'lng': lng, 'start_position': self.start_position}, outfile)
        except IOError as e:
            logger.log('[x] Error while opening location file: %s' % e, 'red')

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
        self.log = logging.getLogger(__name__)
        # log settings
        # log format
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(name)10s] [%(levelname)5s] %(message)s')

        if self.config.debug:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("websocket").setLevel(logging.DEBUG)
            logging.getLogger("socketio").setLevel(logging.DEBUG)
            logging.getLogger("engineio").setLevel(logging.DEBUG)
            logging.getLogger("socketIO-client").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("websocket").setLevel(logging.ERROR)
            logging.getLogger("socketio").setLevel(logging.ERROR)
            logging.getLogger("engineio").setLevel(logging.ERROR)
            logging.getLogger("socketIO-client").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

    def check_session(self, position):
        # Check session expiry
        if self.api._auth_provider and self.api._auth_provider._ticket_expire:

            # prevent crash if return not numeric value
            if not self.is_numeric(self.api._auth_provider._ticket_expire):
                logger.log("Ticket expired value is not numeric", 'yellow')
                return

            remaining_time = \
                self.api._auth_provider._ticket_expire / 1000 - time.time()

            if remaining_time < 60:
                logger.log("Session stale, re-logging in", 'yellow')
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
        logger.log('Attempting login to Pokemon Go.', 'white')
        lat, lng = self.position[0:2]
        self.api.set_position(lat, lng, 0)

        while not self.api.login(
            self.config.auth_service,
            str(self.config.username),
            str(self.config.password)):

            logger.log('[X] Login Error, server busy', 'red')
            logger.log('[X] Waiting 10 seconds to try again', 'red')
            time.sleep(10)

        logger.log('Login to Pokemon Go successful.', 'green')

    def _setup_api(self):
        # instantiate pgoapi
        self.api = ApiWrapper()

        # provide player position on the earth
        self._set_starting_position()

        self.login()

        # chain subrequests (methods) into one RPC call

        self._print_character_info()

        logger.log('')
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
            logger.log(
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
        logger.log('')
        logger.log('--- {username} ---'.format(**player), 'cyan')
        self.get_player_info()
        logger.log(
            'Pokemon Bag: {}/{}'.format(
                self.get_inventory_count('pokemon'),
                player['max_pokemon_storage']
            ), 'cyan'
        )
        logger.log(
            'Items: {}/{}'.format(
                self.get_inventory_count('item'),
                player['max_item_storage']
            ), 'cyan'
        )
        logger.log(
            'Stardust: {}'.format(stardust) +
            ' | Pokecoins: {}'.format(pokecoins), 'cyan'
        )
        # Items Output
        logger.log(
            'PokeBalls: ' + str(items_stock[1]) +
            ' | GreatBalls: ' + str(items_stock[2]) +
            ' | UltraBalls: ' + str(items_stock[3]), 'cyan')

        logger.log(
            'RazzBerries: ' + str(items_stock[701]) +
            ' | BlukBerries: ' + str(items_stock[702]) +
            ' | NanabBerries: ' + str(items_stock[703]), 'cyan')

        logger.log(
            'LuckyEgg: ' + str(items_stock[301]) +
            ' | Incubator: ' + str(items_stock[902]) +
            ' | TroyDisk: ' + str(items_stock[501]), 'cyan')

        logger.log(
            'Potion: ' + str(items_stock[101]) +
            ' | SuperPotion: ' + str(items_stock[102]) +
            ' | HyperPotion: ' + str(items_stock[103]), 'cyan')

        logger.log(
            'Incense: ' + str(items_stock[401]) +
            ' | IncenseSpicy: ' + str(items_stock[402]) +
            ' | IncenseCool: ' + str(items_stock[403]), 'cyan')

        logger.log(
            'Revive: ' + str(items_stock[201]) +
            ' | MaxRevive: ' + str(items_stock[202]), 'cyan')

        logger.log('')

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

        user_web_inventory = 'web/inventory-%s.json' % self.config.username

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

        has_position = False

        if self.config.test:
            # TODO: Add unit tests
            return

        if self.config.location:
            location_str = self.config.location.encode('utf-8')
            location = (self.get_pos_by_name(location_str.replace(" ", "")))
            self.api.set_position(*location)
            self.start_position = self.position
            logger.log('')
            logger.log('Location Found: {}'.format(location_str))
            logger.log('GeoPosition: {}'.format(self.position))
            logger.log('')
            has_position = True

        if self.config.location_cache:
            try:
                # save location flag used to pull the last known location from
                # the location.json
                logger.log('[x] Parsing cached location...')
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
                        logger.log('[x] Last location flag used but with a stale starting location', 'yellow')
                        logger.log('[x] Using new starting location, {}'.format(self.position))
                        return

                self.api.set_position(*location)

                logger.log('')
                logger.log(
                    '[x] Last location flag used. Overriding passed in location'
                )
                logger.log(
                    '[x] Last in-game location was set as: {}'.format(
                        self.position
                    )
                )
                logger.log('')

                has_position = True
            except Exception:
                if has_position is False:
                    sys.exit(
                        "No cached Location. Please specify initial location."
                    )
                logger.log(
                    '[x] Parsing cached location failed, try to use the '
                    'initial location...'
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
                logger.log(
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
                        logger.log(
                            'Level: {level}'.format(
                                **playerdata) +
                            ' (Next Level: {} XP)'.format(
                                nextlvlxp) +
                            ' (Total: {experience} XP)'
                            ''.format(**playerdata), 'cyan')

                    if 'pokemons_captured' in playerdata and 'poke_stop_visits' in playerdata:
                        logger.log(
                            'Pokemon Captured: '
                            '{pokemons_captured}'.format(
                                **playerdata) +
                            ' | Pokestops Visited: '
                            '{poke_stop_visits}'.format(
                                **playerdata), 'cyan')

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
