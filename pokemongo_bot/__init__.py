# -*- coding: utf-8 -*-

import logging
import googlemaps
import json
import random
import threading
import time
import datetime
from pgoapi import PGoApi
from cell_workers import PokemonCatchWorker, SeenFortWorker
from cell_workers.utils import distance
from stepper import Stepper
from geopy.geocoders import GoogleV3
from math import radians, sqrt, sin, cos, atan2

class PokemonGoBot(object):

    def __init__(self, config):
        self.config = config
        self.pokemon_list=json.load(open('data/pokemon.json'))
        self.item_list=json.load(open('data/items.json'))

    def start(self):
        self._setup_logging()
        self._setup_api()
        self.stepper = Stepper(self)
        random.seed()

    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, position, include_fort_on_path):
        if (self.config.mode == "all" or self.config.mode == "poke") and 'catchable_pokemons' in cell:
            print '[#] Something rustles nearby!'
            for pokemon in cell['catchable_pokemons']:
                with open('web/catchable.json', 'w') as outfile:
                    json.dump(pokemon, outfile)
                worker = PokemonCatchWorker(pokemon, self)
                worker.work()
                with open('web/catchable.json', 'w') as outfile:
                    json.dump({}, outfile)
        if (self.config.mode == "all" or self.config.mode == "poke") and 'wild_pokemons' in cell:
            for pokemon in cell['wild_pokemons']:
                worker = PokemonCatchWorker(pokemon, self)
                worker.work()
        if (self.config.mode == "all" or self.config.mode == "farm") and include_fort_on_path:
            if 'forts' in cell:
                # Only include those with a lat/long
                forts = [fort for fort in cell['forts'] if 'latitude' in fort and 'type' in fort]

                # Sort all by distance from current pos- eventually this should build graph & A* it
                forts.sort(key=lambda x: distance(self.position[0], self.position[1], fort['latitude'], fort['longitude']))
                for fort in cell['forts']:
                    worker = SeenFortWorker(fort, self)
                    hack_chain = worker.work()
                    if hack_chain > 10:
                        #print('need a rest')
                        break

    def _setup_logging(self):
        self.log = logging.getLogger(__name__)
        # log settings
        # log format
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

        if self.config.debug:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

    def _setup_api(self):
        # instantiate pgoapi
        self.api = PGoApi()
        # provide player position on the earth

        self._set_starting_position()

        if not self.api.login(self.config.auth_service, str(self.config.username), str(self.config.password)):
            print('Login Error, server busy')
            exit(0)

        # chain subrequests (methods) into one RPC call

        # get player profile call
        # ----------------------
        self.api.get_player()

        response_dict = self.api.call()
        #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1="0"
        currency_2="0"
        import pprint
        pprint.pprint(response_dict)
        player = response_dict['responses']['GET_PLAYER']['profile']

        ### @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(player['creation_time'] / 1e3)

        pokecoins = '0'
        stardust = '0'
        balls_stock = self.pokeball_inventory()

        if 'amount' in player['currency'][0]:
            pokecoins = player['currency'][0]['amount']
        if 'amount' in player['currency'][1]:
            stardust = player['currency'][1]['amount']

        print('[#]')
        print('[#] Username: {username}'.format(**player))
        print('[#] Acccount Creation: {}'.format(creation_date))
        print('[#] Bag Storage: {}/{}'.format(self.get_inventory_count('item'), player['item_storage']))
        print('[#] Pokemon Storage: {}/{}'.format(self.get_inventory_count('pokemon'), player['poke_storage']))
        print('[#] Stardust: {}'.format(stardust))
        print('[#] Pokecoins: {}'.format(pokecoins))
        print('[#] PokeBalls: ' + str(balls_stock[1]))
        print('[#] GreatBalls: ' + str(balls_stock[2]))
        print('[#] UltraBalls: ' + str(balls_stock[3]))
        self.get_player_info()

        if self.config.firsttrans:
            self.first_transfer()

        print('[#]')
        self.update_inventory();

    def first_transfer(self):
        print('[x] First Transfer.')

        pokemon_groups = self._first_transfer_get_groups()

        print('[x] Transfering...')

        for id in pokemon_groups:

            group_cp = pokemon_groups[id].keys()

            if len(group_cp) > 1:
                group_cp.sort()
                group_cp.reverse()

                for x in range(1, len(group_cp)):
                    self.api.release_pokemon(pokemon_id=pokemon_groups[id][group_cp[x]])
                    response_dict = self.api.call()
                    time.sleep(2)

        print('[x] Transfering Done.')

    def _first_transfer_get_groups(self):
        pokemon_groups = {}
        self.api.get_player().get_inventory()
        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        for pokemon in inventory_dict:
            try:
                group_id = pokemon['inventory_item_data']['pokemon_data']['pokemon_id']
                group_pokemon = pokemon['inventory_item_data']['pokemon_data']['id']
                group_pokemon_cp = pokemon['inventory_item_data']['pokemon_data']['cp']

                if group_id not in pokemon_groups:
                    pokemon_groups[group_id] = {}

                pokemon_groups[group_id].update({group_pokemon_cp:group_pokemon})
            except:
                continue
        return pokemon_groups

    def update_inventory(self):
        self.api.get_inventory()
        response = self.api.call()
        self.inventory = list()
        if 'responses' in response:
            if 'GET_INVENTORY' in response['responses']:
                if 'inventory_delta' in response['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response['responses']['GET_INVENTORY']['inventory_delta']:
                        for item in response['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                            if not 'inventory_item_data' in item:
                                continue
                            if not 'item' in item['inventory_item_data']:
                                continue
                            if not 'item_id' in item['inventory_item_data']['item']:
                                continue
                            if not 'count' in item['inventory_item_data']['item']:
                                continue
                            self.inventory.append(item['inventory_item_data']['item'])

    def pokeball_inventory(self):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        # get player balls stock
        # ----------------------
        balls_stock = {1:0,2:0,3:0,4:0}

        for item in inventory_dict:
            try:
                if item['inventory_item_data']['item']['item_id'] == 1:
                    #print('Poke Ball count: ' + str(item['inventory_item_data']['item']['count']))
                    balls_stock[1] = item['inventory_item_data']['item']['count']
                if item['inventory_item_data']['item']['item_id'] == 2:
                    #print('Great Ball count: ' + str(item['inventory_item_data']['item']['count']))
                    balls_stock[2] = item['inventory_item_data']['item']['count']
                if item['inventory_item_data']['item']['item_id'] == 3:
                    #print('Ultra Ball count: ' + str(item['inventory_item_data']['item']['count']))
                    balls_stock[3] = item['inventory_item_data']['item']['count']
            except:
                continue
        return balls_stock

    def _set_starting_position(self):

        if self.config.test:
            return

        if self.config.location_cache:
            try:
                #
                # save location flag used to pull the last known location from the location.json
                with open('location.json') as f:
                    location_json = json.load(f)

                    self.position = (location_json['lat'], location_json['lng'], 0.0)
                    self.api.set_position(*self.position)

                    print('')
                    print('[x] Last location flag used. Overriding passed in location')
                    print('[x] Last in-game location was set as: {}'.format(self.position))
                    print('')

                    return
            except:
                pass

        #
        # this will fail if the location.json isn't there or not valid.
        # Still runs if location is set.
        self.position = self._get_pos_by_name(self.config.location)
        self.api.set_position(*self.position)
        print('')
        print(u'[x] Address found: {}'.format(self.config.location.decode('utf-8')))
        print('[x] Position in-game set as: {}'.format(self.position))
        print('')


    def _get_pos_by_name(self, location_name):
        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name)

        #self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        #self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return (loc.latitude, loc.longitude, loc.altitude)

    def heartbeat(self):
        self.api.get_player()
        self.api.get_hatched_eggs()
        self.api.get_inventory()
        self.api.check_awarded_badges()
        self.api.call()

    def get_inventory_count(self, what):
        self.api.get_inventory()
        response_dict = self.api.call()
        if 'responses' in response_dict:
            if 'GET_INVENTORY' in response_dict['responses']:
                if 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
                        pokecount = 0
                        itemcount = 1
                        for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                            #print('item {}'.format(item))
                            if 'inventory_item_data' in item:
                                if 'pokemon_data' in item['inventory_item_data']:
                                    pokecount = pokecount + 1
                                if 'item' in item['inventory_item_data']:
                                    if 'count' in item['inventory_item_data']['item']:
                                        itemcount = itemcount + item['inventory_item_data']['item']['count']
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
                if 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
                        pokecount = 0
                        itemcount = 1
                        for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                            #print('item {}'.format(item))
                            if 'inventory_item_data' in item:
                                if 'player_stats' in item['inventory_item_data']:
                                    playerdata = item['inventory_item_data']['player_stats']

                                    nextlvlxp = (int(playerdata['next_level_xp']) - int(playerdata['experience']))

                                    if 'level' in playerdata:
                                        print('[#] -- Level: {level}'.format(**playerdata))

                                    if 'experience' in playerdata:
                                        print('[#] -- Experience: {experience}'.format(**playerdata))
                                        print('[#] -- Experience until next level: {}'.format(nextlvlxp))

                                    if 'pokemons_captured' in playerdata:
                                        print('[#] -- Pokemon Captured: {pokemons_captured}'.format(**playerdata))

                                    if 'poke_stop_visits' in playerdata:
                                        print('[#] -- Pokestops Visited: {poke_stop_visits}'.format(**playerdata))
