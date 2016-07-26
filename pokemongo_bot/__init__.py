# -*- coding: utf-8 -*-

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
from cell_workers import PokemonCatchWorker, SeenFortWorker, MoveToFortWorker, InitialTransferWorker, EvolveAllWorker
from cell_workers.utils import distance, get_cellid, encode, i2f
from human_behaviour import sleep
from item_list import Item
from spiral_navigator import SpiralNavigator


class PokemonGoBot(object):
    def __init__(self, config):
        self.config = config
        self.pokemon_list = json.load(open('data/pokemon.json'))
        self.item_list = json.load(open('data/items.json'))

    def start(self):
        self._setup_logging()
        self._setup_api()
        self.navigator = SpiralNavigator(self)
        random.seed()

    def take_step(self):
        location = self.navigator.take_step()
        cells = self.find_close_cells(*location[0:2])

        for cell in cells:
            self.work_on_cell(cell, location)

    def update_web_location(self, cells=[], lat=None, lng=None, alt=None):
        # we can call the function with no arguments and still get the position and map_cells
        if lat == None:
            lat = i2f(self.api._position_lat)
        if lng == None:
            lng = i2f(self.api._position_lng)
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

        user_web_location = 'web/location-%s.json' % (self.config.username)
        # should check if file exists first but os is not imported here
        # alt is unused atm but makes using *location easier
        with open(user_web_location,'w') as outfile:
            json.dump(
                {'lat': lat,
                'lng': lng,
                'alt': alt,
                'cells': cells
                }, outfile)

        user_data_lastlocation = 'data/last-location-%s.json' % (self.config.username)
        with open(user_data_lastlocation, 'w') as outfile:
            outfile.truncate()
            json.dump({'lat': lat, 'lng': lng}, outfile)

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
        self.update_web_location(map_cells)
        return map_cells

    def work_on_cell(self, cell, position):
        # Check if session token has expired
        self.check_session(position)

        if self.config.evolve_all:
            # Will skip evolving if user wants to use an egg and there is none
            skip_evolves = False

            # Pop lucky egg before evolving to maximize xp gain
            use_lucky_egg = self.config.use_lucky_egg
            lucky_egg_count = self.item_inventory_count(Item.ITEM_LUCKY_EGG.value)

            if  use_lucky_egg and lucky_egg_count > 0:
                logger.log('Using lucky egg ... you have {}'
                           .format(lucky_egg_count))
                response_dict_lucky_egg = self.use_lucky_egg()
                if response_dict_lucky_egg and 'responses' in response_dict_lucky_egg and \
                    'USE_ITEM_XP_BOOST' in response_dict_lucky_egg['responses'] and \
                    'result' in response_dict_lucky_egg['responses']['USE_ITEM_XP_BOOST']:
                    result = response_dict_lucky_egg['responses']['USE_ITEM_XP_BOOST']['result']
                    if result is 1: # Request success
                        logger.log('Successfully used lucky egg... ({} left!)'
                                   .format(lucky_egg_count-1), 'green')
                    else:
                        logger.log('Failed to use lucky egg!', 'red')
                        skip_evolves = True
            elif use_lucky_egg: #lucky_egg_count is 0
                # Skipping evolve so they aren't wasted
                logger.log('No lucky eggs... skipping evolve!', 'yellow')
                skip_evolves = True

            if not skip_evolves:
                # Run evolve all once.
                logger.log('Attempting to evolve all pokemons ...', 'cyan')
                worker = EvolveAllWorker(self)
                worker.work()

            # Flip the bit.
            self.config.evolve_all = []

        if (self.config.mode == "all" or self.config.mode ==
                "poke") and 'catchable_pokemons' in cell and len(cell[
                    'catchable_pokemons']) > 0:
            logger.log('Something rustles nearby!')
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
                self.config.mode == "farm"):
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
                    if self.config.mode == "poke":
                        break

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
                self.position = [i2f(self.api._position_lat), i2f(self.api._position_lng), 0]
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
        # instantiate pgoapi
        self.api = PGoApi()

        # provide player position on the earth
        self._set_starting_position()

        self.login()

        # chain subrequests (methods) into one RPC call

        self._print_character_info()

        if self.config.initial_transfer:
            worker = InitialTransferWorker(self)
            worker.work()

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

        player = response_dict['responses']['GET_PLAYER']['player_data']

        # @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(
            player['creation_timestamp_ms'] / 1e3)
        creation_date = creation_date.strftime("%Y/%m/%d %H:%M:%S")

        pokecoins = '0'
        stardust = '0'
        balls_stock = self.pokeball_inventory()

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
        # Pokeball Output
        logger.log('PokeBalls: ' + str(balls_stock[1]) +
            ' | GreatBalls: ' + str(balls_stock[2]) +
            ' | UltraBalls: ' + str(balls_stock[3]), 'cyan')
        logger.log('Razz Berries: ' + str(self.item_inventory_count(701)), 'cyan')

        logger.log('')

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self)
        return_value = worker.work()

        if return_value == PokemonCatchWorker.BAG_FULL:
            worker = InitialTransferWorker(self)
            worker.work()

        return return_value

    def drop_item(self, item_id, count):
        self.api.recycle_inventory_item(item_id=item_id, count=count)
        inventory_req = self.api.call()

        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return inventory_req

    def use_lucky_egg(self):
        self.api.use_item_xp_boost(item_id=301)
        inventory_req = self.api.call()
        return inventory_req

    def update_inventory(self):
        self.api.get_inventory()
        response = self.api.call()
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

    def pokeball_inventory(self):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']

        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        # get player balls stock
        # ----------------------
        balls_stock = {1: 0, 2: 0, 3: 0, 4: 0}

        for item in inventory_dict:
            try:
                # print(item['inventory_item_data']['item'])
                item_id = item['inventory_item_data']['item']['item_id']
                item_count = item['inventory_item_data']['item']['count']

                if item_id == Item.ITEM_POKE_BALL.value:
                    # print('Poke Ball count: ' + str(item_count))
                    balls_stock[1] = item_count
                if item_id == Item.ITEM_GREAT_BALL.value:
                    # print('Great Ball count: ' + str(item_count))
                    balls_stock[2] = item_count
                if item_id == Item.ITEM_ULTRA_BALL.value:
                    # print('Ultra Ball count: ' + str(item_count))
                    balls_stock[3] = item_count
            except:
                continue
        return balls_stock

    def item_inventory_count(self, id):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses'][
            'GET_INVENTORY']['inventory_delta']['inventory_items']

        item_count = 0

        for item in inventory_dict:
            try:
                if item['inventory_item_data']['item']['item_id'] == int(id):
                    item_count = item[
                        'inventory_item_data']['item']['count']
            except:
                continue
        return item_count

    def _set_starting_position(self):

        has_position = False

        if self.config.test:
            # TODO: Add unit tests
            return

        if self.config.location:
            try:
                location_str = str(self.config.location)
                location = (self._get_pos_by_name(location_str.replace(" ", "")))
                self.position = location
                self.api.set_position(*self.position)
                logger.log('')
                logger.log(u'Location Found: {}'.format(self.config.location.decode(
                    'utf-8')))
                logger.log('GeoPosition: {}'.format(self.position))
                logger.log('')
                has_position = True
                return
            except:
                logger.log('[x] The location given using -l could not be parsed. Checking for a cached location.')
                pass

        if self.config.location_cache and not has_position:
            try:
                #
                # save location flag used to pull the last known location from
                # the location.json
                logger.log('[x] Parsing cached location...')
                with open('data/last-location-%s.json' %
                          (self.config.username)) as f:
                    location_json = json.load(f)

                    self.position = (location_json['lat'],
                                     location_json['lng'], 0.0)
                    print(self.position)
                    self.api.set_position(*self.position)

                    logger.log('')
                    logger.log(
                        '[x] Last location flag used. Overriding passed in location')
                    logger.log(
                        '[x] Last in-game location was set as: {}'.format(
                            self.position))
                    logger.log('')

                    has_position = True
                    return
            except:
                sys.exit(
                    "No cached Location. Please specify initial location.")

    def _get_pos_by_name(self, location_name):
        # Check if the given location is already a coordinate.
        if ',' in location_name:
            possibleCoordinates = re.findall("[-]?\d{1,3}[.]\d{6,7}", location_name)
            if len(possibleCoordinates) == 2:
                # 2 matches, this must be a coordinate. We'll bypass the Google geocode so we keep the exact location.
                logger.log(
                    '[x] Coordinates found in passed in location, not geocoding.')
                return (float(possibleCoordinates[0]), float(possibleCoordinates[1]), float("0.0"))

        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name, timeout=10)

        #self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        #self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return (loc.latitude, loc.longitude, loc.altitude)

    def heartbeat(self):
        self.api.get_player()
        self.api.get_hatched_eggs()
        self.api.get_inventory()
        self.api.check_awarded_badges()
        self.api.call()
        self.update_web_location() # updates every tick

    def get_inventory_count(self, what):
        self.api.get_inventory()
        response_dict = self.api.call()
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
        self.api.get_inventory()
        response_dict = self.api.call()
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
