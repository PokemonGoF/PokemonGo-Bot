# -*- coding: utf-8 -*-

import os
import datetime
import json
import logging
import random
import re
import sys
import time

from geopy.geocoders import GoogleV3
from pgoapi import PGoApi
from pgoapi.utilities import f2i

import logger
from cell_workers import SpinNearestFortWorker, CatchVisiblePokemonWorker, PokemonCatchWorker, SeenFortWorker, MoveToFortWorker, PokemonTransferWorker, EvolveAllWorker, RecycleItemsWorker, IncubateEggsWorker
from cell_workers.utils import distance, get_cellid, encode, i2f
from human_behaviour import sleep
from item_list import Item
from metrics import Metrics
from spiral_navigator import SpiralNavigator
from worker_result import WorkerResult
from api_wrapper import ApiWrapper


class PokemonGoBot(object):

    @property
    def position(self):
        return self.api._position_lat, self.api._position_lng, 0

    def __init__(self, config):
        self.config = config
        self.fort_timeouts = dict()
        self.pokemon_list = json.load(open(os.path.join('data', 'pokemon.json')))
        self.item_list = json.load(open(os.path.join('data', 'items.json')))
        self.metrics = Metrics(self)
        self.latest_inventory = None
        self.cell = None

    def start(self):
        self._setup_logging()
        self._setup_api()
        self.navigator = SpiralNavigator(self)
        random.seed()

    def tick(self):
        self.cell = self.get_meta_cell()

        # Check if session token has expired
        self.check_session(self.position[0:2])

        workers = [
            IncubateEggsWorker,
            PokemonTransferWorker,
            EvolveAllWorker,
            RecycleItemsWorker,
            CatchVisiblePokemonWorker,
            SpinNearestFortWorker
        ]

        for worker in workers:
            if worker(self).work() == WorkerResult.RUNNING:
                return

        self.navigator.take_step()

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

        return {
            "forts": forts,
            "wild_pokemons": wild_pokemons,
            "catchable_pokemons": catchable_pokemons
        }

    def update_web_location(self, cells=[], lat=None, lng=None, alt=None):
        # we can call the function with no arguments and still get the position and map_cells
        if lat == None:
            lat = self.api._position_lat
        if lng == None:
            lng = self.api._position_lng
        if alt == None:
            alt = 0

        if cells == []:
            cellid = get_cellid(lat, lng)
            timestamp = [0, ] * len(cellid)
            self.api.get_map_objects(
                latitude=f2i(lat),
                longitude=f2i(lng),
                since_timestamp_ms=timestamp,
                cell_id=cellid
            )
            response_dict = self.api.call()
            map_objects = response_dict.get('responses', {}).get('GET_MAP_OBJECTS', {})
            status = map_objects.get('status', None)
            cells = map_objects['map_cells']

            #insert detail info about gym to fort
            for cell in cells:
                if 'forts' in cell:
                    for fort in cell['forts']:
                        if fort.get('type') != 1:
                            self.api.get_gym_details(gym_id=fort.get('id'),
                                                     player_latitude=lng,
                                                     player_longitude=lat,
                                                     gym_latitude=fort.get('latitude'),
                                                     gym_longitude=fort.get('longitude'))
                            response_gym_details = self.api.call()
                            fort['gym_details'] = response_gym_details.get('responses', {}).get('GET_GYM_DETAILS', None)

        user_data_cells = "data/cells-%s.json" % (self.config.username)
        with open(user_data_cells, 'w') as outfile:
            outfile.truncate()
            json.dump(cells, outfile)

        user_web_location = os.path.join('web', 'location-%s.json' % (self.config.username))
        # alt is unused atm but makes using *location easier
        try:
            with open(user_web_location,'w') as outfile:
                json.dump(
                    {'lat': lat,
                    'lng': lng,
                    'alt': alt,
                    'cells': cells
                    }, outfile)
        except IOError as e:
            logger.log('[x] Error while opening location file: %s' % e, 'red')

        user_data_lastlocation = os.path.join('data', 'last-location-%s.json' % (self.config.username))
        try:
            with open(user_data_lastlocation, 'w') as outfile:
                outfile.truncate()
                json.dump({'lat': lat, 'lng': lng}, outfile)
        except IOError as e:
            logger.log('[x] Error while opening location file: %s' % e, 'red')


    def find_close_cells(self, lat, lng):
        cellid = get_cellid(lat, lng)
        timestamp = [0, ] * len(cellid)

        self.api.get_map_objects(
            latitude=f2i(lat),
            longitude=f2i(lng),
            since_timestamp_ms=timestamp,
            cell_id=cellid
        )
        response_dict = self.api.call()
        map_objects = response_dict.get('responses', {}).get('GET_MAP_OBJECTS', {})
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
            format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

        if self.config.debug:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

    def check_session(self, position):
        # Check session expiry
        if self.api._auth_provider and self.api._auth_provider._ticket_expire:
            remaining_time = self.api._auth_provider._ticket_expire/1000 - time.time()

            if remaining_time < 60:
                logger.log("Session stale, re-logging in", 'yellow')
                self.login()

    def login(self):
        logger.log('Attempting login to Pokemon Go.', 'white')
        self.api.reset_auth()
        lat, lng = self.position[0:2]
        self.api.set_position(lat, lng, 0)

        while not self.api.login(self.config.auth_service,
                               str(self.config.username),
                               str(self.config.password)):

            logger.log('[X] Login Error, server busy', 'red')
            logger.log('[X] Waiting 10 seconds to try again', 'red')
            time.sleep(10)

        logger.log('Login to Pokemon Go successful.', 'green')

    def _setup_api(self):
        # instantiate pgoapi
        self.api = ApiWrapper(PGoApi())

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
        self.api.get_player()
        response_dict = self.api.call()
        #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1 = "0"
        currency_2 = "0"

        if response_dict:
            self._player = response_dict['responses']['GET_PLAYER']['player_data']
            player = self._player
        else:
            logger.log("The API didn't return player info, servers are unstable - retrying.", 'red')
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
        logger.log('Pokemon Bag: {}/{}'.format(self.get_inventory_count('pokemon'), player['max_pokemon_storage']), 'cyan')
        logger.log('Items: {}/{}'.format(self.get_inventory_count('item'), player['max_item_storage']), 'cyan')
        logger.log('Stardust: {}'.format(stardust) + ' | Pokecoins: {}'.format(pokecoins), 'cyan')
        # Items Output
        logger.log('PokeBalls: ' + str(items_stock[1]) +
            ' | GreatBalls: ' + str(items_stock[2]) +
            ' | UltraBalls: ' + str(items_stock[3]), 'cyan')
        logger.log('RazzBerries: ' + str(items_stock[701]) +
            ' | BlukBerries: ' + str(items_stock[702]) +
            ' | NanabBerries: ' + str(items_stock[703]), 'cyan')
        logger.log('LuckyEgg: ' + str(items_stock[301]) +
            ' | Incubator: ' + str(items_stock[902]) +
            ' | TroyDisk: ' + str(items_stock[501]), 'cyan')
        logger.log('Potion: ' + str(items_stock[101]) +
            ' | SuperPotion: ' + str(items_stock[102]) +
            ' | HyperPotion: ' + str(items_stock[103]), 'cyan')
        logger.log('Incense: ' + str(items_stock[401]) +
            ' | IncenseSpicy: ' + str(items_stock[402]) +
            ' | IncenseCool: ' + str(items_stock[403]), 'cyan')
        logger.log('Revive: ' + str(items_stock[201]) +
            ' | MaxRevive: ' + str(items_stock[202]), 'cyan')

        logger.log('')

    def use_lucky_egg(self):
        self.api.use_item_xp_boost(item_id=301)
        inventory_req = self.api.call()
        return inventory_req

    def get_inventory(self):
        if self.latest_inventory is None:
            self.api.get_inventory()
            response = self.api.call()
            self.latest_inventory = response
        return self.latest_inventory

    def update_inventory(self):
        response = self.get_inventory()
        self.inventory = list()
        if 'responses' in response:
            if 'GET_INVENTORY' in response['responses']:
                if 'inventory_delta' in response['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response['responses'][
                            'GET_INVENTORY']['inventory_delta']:
                        for item in response['responses']['GET_INVENTORY'][
                                'inventory_delta']['inventory_items']:
                            if not 'inventory_item_data' in item:
                                continue
                            if not 'item' in item['inventory_item_data']:
                                continue
                            if not 'item_id' in item['inventory_item_data'][
                                    'item']:
                                continue
                            if not 'count' in item['inventory_item_data'][
                                    'item']:
                                continue
                            self.inventory.append(item['inventory_item_data'][
                                'item'])

    def current_inventory(self):
        inventory_req = self.get_inventory()
        inventory_dict = inventory_req['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']

        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        # get player items stock
        # ----------------------
        items_stock = {x.value:0 for x in list(Item)}

        for item in inventory_dict:
            try:
                # print(item['inventory_item_data']['item'])
                item_id = item['inventory_item_data']['item']['item_id']
                item_count = item['inventory_item_data']['item']['count']

                if item_id in items_stock:
                    items_stock[item_id] = item_count
            except Exception:
                continue
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
            if  item_id == int(id) and item_count:
                return item_count

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
            try:
                location_str = self.config.location.encode('utf-8')
                location = (self._get_pos_by_name(location_str.replace(" ", "")))
                self.api.set_position(*location)
                logger.log('')
                logger.log(u'Location Found: {}'.format(self.config.location))
                logger.log('GeoPosition: {}'.format(self.position))
                logger.log('')
                has_position = True
            except Exception:
                logger.log('[x] The location given in the config could not be parsed. Checking for a cached location.')
                pass

        if self.config.location_cache:
            try:
                #
                # save location flag used to pull the last known location from
                # the location.json
                logger.log('[x] Parsing cached location...')
                with open('data/last-location-%s.json' %
                          (self.config.username)) as f:
                    location_json = json.load(f)
                    location = (location_json['lat'],
                                     location_json['lng'], 0.0)
                    #print(location)
                    self.api.set_position(*location)

                    logger.log('')
                    logger.log(
                        '[x] Last location flag used. Overriding passed in location')
                    logger.log(
                        '[x] Last in-game location was set as: {}'.format(
                            self.position))
                    logger.log('')

                    has_position = True
                    return
            except Exception:
                if(has_position == False):
                    sys.exit(
                        "No cached Location. Please specify initial location.")
                logger.log('[x] Parsing cached location failed, try to use the initial location...')

    def _get_pos_by_name(self, location_name):
        # Check if the given location is already a coordinate.
        if ',' in location_name:
            possible_coordinates = re.findall("[-]?\d{1,3}[.]\d{6,7}", location_name)
            if len(possible_coordinates) == 2:
                # 2 matches, this must be a coordinate. We'll bypass the Google geocode so we keep the exact location.
                logger.log(
                    '[x] Coordinates found in passed in location, not geocoding.')
                return float(possible_coordinates[0]), float(possible_coordinates[1]), float("0.0")

        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name, timeout=10)

        return float(loc.latitude), float(loc.longitude), float(loc.altitude)

    def heartbeat(self):
        # Remove forts that we can now spin again.
        self.fort_timeouts = {id: timeout for id ,timeout
                              in self.fort_timeouts.iteritems()
                              if timeout >= time.time() * 1000}
        self.api.get_player()
        self.api.get_hatched_eggs()
        self.api.check_awarded_badges()
        self.api.call()
        self.update_web_location() # updates every tick

    def get_inventory_count(self, what):
        response_dict = self.get_inventory()
        if 'responses' in response_dict:
            if 'GET_INVENTORY' in response_dict['responses']:
                if 'inventory_delta' in response_dict['responses'][
                        'GET_INVENTORY']:
                    if 'inventory_items' in response_dict['responses'][
                            'GET_INVENTORY']['inventory_delta']:
                        pokecount = 0
                        itemcount = 1
                        for item in response_dict['responses'][
                                'GET_INVENTORY']['inventory_delta'][
                                    'inventory_items']:
                            #print('item {}'.format(item))
                            if 'inventory_item_data' in item:
                                if 'pokemon_data' in item[
                                        'inventory_item_data']:
                                    pokecount = pokecount + 1
                                if 'item' in item['inventory_item_data']:
                                    if 'count' in item['inventory_item_data'][
                                            'item']:
                                        itemcount = itemcount + \
                                            item['inventory_item_data'][
                                                'item']['count']
        if 'pokemon' in what:
            return pokecount
        if 'item' in what:
            return itemcount
        return '0'

    def get_player_info(self):
        response_dict = self.get_inventory()
        if 'responses' in response_dict:
            if 'GET_INVENTORY' in response_dict['responses']:
                if 'inventory_delta' in response_dict['responses'][
                        'GET_INVENTORY']:
                    if 'inventory_items' in response_dict['responses'][
                            'GET_INVENTORY']['inventory_delta']:
                        pokecount = 0
                        itemcount = 1
                        for item in response_dict['responses'][
                                'GET_INVENTORY']['inventory_delta'][
                                    'inventory_items']:
                            #print('item {}'.format(item))
                            if 'inventory_item_data' in item:
                                if 'player_stats' in item[
                                        'inventory_item_data']:
                                    playerdata = item['inventory_item_data'][
                                        'player_stats']

                                    nextlvlxp = (
                                        int(playerdata.get('next_level_xp', 0)) -
                                        int(playerdata.get('experience', 0)))

                                    if 'level' in playerdata:
                                        if 'experience' in playerdata:
                                            logger.log('Level: {level}'.format(**playerdata) +
                                                ' (Next Level: {} XP)'.format(nextlvlxp) +
                                                 ' (Total: {experience} XP)'.format(**playerdata), 'cyan')


                                    if 'pokemons_captured' in playerdata:
                                        if 'poke_stop_visits' in playerdata:
                                            logger.log(
                                                'Pokemon Captured: {pokemons_captured}'.format(**playerdata) +
                                                ' | Pokestops Visited: {poke_stop_visits}'.format(**playerdata), 'cyan')
