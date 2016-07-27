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
from cell_workers import CatchVisiblePokemonWorker, PokemonCatchWorker, SeenFortWorker, MoveToFortWorker, InitialTransferWorker, EvolveAllWorker, RecycleItemsWorker
from cell_workers.utils import distance, get_cellid, encode, i2f
from human_behaviour import sleep
from item_list import Item
from metrics import Metrics
from spiral_navigator import SpiralNavigator
from worker_result import WorkerResult

from services.player_service import PlayerService

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
        self.api = PGoApi()
        self.player_service = PlayerService(self.api)

    def start(self):
        self._setup_logging()
        self._setup_api()
        self.navigator = SpiralNavigator(self)
        random.seed()

    def take_step(self):
        self.process_cells()

    def process_cells(self):
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

        # Have the worker treat the whole area as a single cell.
        self.work_on_cell({"forts": forts, "wild_pokemons": wild_pokemons,
                           "catchable_pokemons": catchable_pokemons}, location)

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
                            fort['gym_details'] = response_gym_details['responses']['GET_GYM_DETAILS']

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

    def work_on_cell(self, cell, position):
        # Check if session token has expired
        self.check_session(position)

        worker = InitialTransferWorker(self)
        if worker.work() == WorkerResult.RUNNING:
            return

        worker = EvolveAllWorker(self)
        if worker.work() == WorkerResult.RUNNING:
            return

        RecycleItemsWorker(self).work()

        worker = CatchVisiblePokemonWorker(self, cell)
        if worker.work() == WorkerResult.RUNNING:
            return


        number_of_things_gained_by_stop = 5

        if ((self.get_inventory_count('item') < self._player['max_item_storage'] - 5) and
            (self.config.mode == "all" or self.config.mode == "farm")):
            if 'forts' in cell:
                # Only include those with a lat/long
                forts = [fort
                         for fort in cell['forts']
                         if 'latitude' in fort and 'type' in fort]
                gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

                # Remove stops that are still on timeout
                forts = filter(lambda x: x["id"] not in self.fort_timeouts, forts)

                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                forts.sort(key=lambda x: distance(self.position[
                           0], self.position[1], x['latitude'], x['longitude']))

                if len(forts) > 0:
                    # Move to and spin the nearest stop.
                    if MoveToFortWorker(forts[0], self).work() == WorkerResult.RUNNING:
                        return
                    if SeenFortWorker(forts[0], self).work() == WorkerResult.RUNNING:
                        return

        self.navigator.take_step()

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
        self.api._auth_token = None
        self.api._auth_provider = None
        self.api._api_endpoint = None
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
        # provide player position on the earth
        self._set_starting_position()

        self.login()

        # chain subrequests (methods) into one RPC call
        self.player_service.print_character_info()
        logger.log('')

        self.inventory = self.player_service.update_inventory()
        # send empty map_cells and then our position
        self.update_web_location()

    def use_lucky_egg(self):
        self.api.use_item_xp_boost(item_id=301)
        inventory_req = self.api.call()
        return inventory_req

    def item_inventory_count(self, id):
        inventory_req = self.player_service.get_inventory()
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
