import logging
import googlemaps
import json
import random
import threading
import time
import datetime
from pgoapi import PGoApi
from pgoapi.utilities import f2i, h2f, distance
from cell_workers import PokemonCatchWorker, SeenFortWorker
from stepper import Stepper
from geopy.geocoders import GoogleV3
from math import radians, sqrt, sin, cos, atan2
import os

class PokemonGoBot(object):

    def __init__(self, config):
        self.config = config
        self.pokemon_list=json.load(open(os.path.dirname(__file__) + '/pokemon.json'))
        self.item_list=json.load(open(os.path.dirname(__file__)    + '/items.json'))
        self.noballs = False

    def start(self):
        self._setup_logging()
        self._setup_api()
        if self.config.stats:
            ## exit early and just show stats
            print '[ stats mode, exiting ... ]'
            exit()
        self.stepper = Stepper(self)
        random.seed()
    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, position):
        if 'catchable_pokemons' in cell:
            print '[#] Something rustles nearby!'
            for pokemon in cell['catchable_pokemons']:
                worker = PokemonCatchWorker(pokemon, self)
                worker.work()
        if 'wild_pokemons' in cell:
            for pokemon in cell['wild_pokemons']:
                worker = PokemonCatchWorker(pokemon, self)
                worker.work()

        # After [self.noballs = True] and first spining, check if 50 pokeballs was gathered, if so stop spining
        if self.noballs and self.ballstock[1] >= 50:
            print ('[#] Gathered 50/50 pokeballs, continue catching!')
            self.noballs = False
        elif self.noballs and self.ballstock[1] < 50:
            print ('[#] Gathered ' + str(self.ballstock[1]) + '/50 pokeballs, continue farming...')

        if self.config.spinstop or self.noballs:
            if 'forts' in cell:
                # Only include those with a lat/long
                forts = [fort for fort in cell['forts'] if 'latitude' in fort and 'type' in fort]

                # Sort all by distance from current pos- eventually this should build graph & A* it
                forts.sort(key=lambda x: distance(self.position[0], self.position[1], fort['latitude'], fort['longitude']))
                for fort in cell['forts']:
                    worker = SeenFortWorker(fort, self)
                    hack_chain = worker.work()
                    if hack_chain > 10:
                        print('[-] Anti-ban resting....')
                        break

    def _setup_logging(self):
        self.log = logging.getLogger(__name__)
        # log settings
        # log format
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
        # log level for http request class
        logging.getLogger("requests").setLevel(logging.WARNING)
        # log level for main pgoapi class
        logging.getLogger("pgoapi").setLevel(logging.INFO)
        # log level for internal pgoapi class
        logging.getLogger("rpc_api").setLevel(logging.INFO)

    def _setup_api(self):
        # instantiate pgoapi
        self.api = PGoApi()
        # provide player position on the earth

        self._set_starting_position()

        if not self.api.login(self.config.auth_service, self.config.username, self.config.password):
            print('Login Error, server busy')
            exit(0)

        # chain subrequests (methods) into one RPC call

        # get player inventory call
        # ----------------------
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()

        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        # get player balls stock
        # ----------------------
        balls_stock = {1:0,2:0,3:0,4:0}

        for item in inventory_dict:
            try:
                if item['inventory_item_data']['item']['item'] == 1:
                    #print('Poke Ball count: ' + str(item['inventory_item_data']['item']['count']))
                    balls_stock[1] = item['inventory_item_data']['item']['count']
                if item['inventory_item_data']['item']['item'] == 2:
                    #print('Great Ball count: ' + str(item['inventory_item_data']['item']['count']))
                    balls_stock[2] = item['inventory_item_data']['item']['count']
                if item['inventory_item_data']['item']['item'] == 3:
                    #print('Ultra Ball count: ' + str(item['inventory_item_data']['item']['count']))
                    balls_stock[3] = item['inventory_item_data']['item']['count']
            except:
                continue

        self.ballstock = balls_stock

        # get player pokemon[id] group by pokemon[pokemon_id]
        # ----------------------
        pokemon_stock = {}

        for pokemon in inventory_dict:
            try:
                id1 = pokemon['inventory_item_data']['pokemon']['pokemon_id']
                id2 = pokemon['inventory_item_data']['pokemon']['id']
                id3 = pokemon['inventory_item_data']['pokemon']['cp']
                #DEBUG - Hide
                #print(str(id1))
                if id1 not in pokemon_stock:
                    pokemon_stock[id1] = {}
                #DEBUG - Hide
                #print(str(id2))
                pokemon_stock[id1].update({id3:id2})
            except:
                continue

        #DEBUG - Hide
        #print pokemon_stock

        for id in pokemon_stock:
            #DEBUG - Hide
            #print id
            sorted_cp = pokemon_stock[id].keys()
            if len(sorted_cp) > 1:
                sorted_cp.sort()
                sorted_cp.reverse()
                #DEBUG - Hide
                #print sorted_cp

                #Hide for now. If Unhide transfer all poke duplicates exept most CP.
                #for x in range(1, len(sorted_cp)):
                    #DEBUG - Hide
                    #print x
                    #print pokemon_stock[id][sorted_cp[x]]
                    #self.api.release_pokemon(pokemon_id=pokemon_stock[id][sorted_cp[x]])
                    #response_dict = self.api.call()

        # get player profile call
        # ----------------------
        self.api.get_player()

        response_dict = self.api.call()
        # print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1="0"
        currency_2="0"

        player = response_dict['responses']['GET_PLAYER']['profile']

        ### @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(player['creation_time'] / 1e3)

        pokecoins = '0'
        stardust = '0'

        if 'amount' in player['currency'][0]:
            pokecoins = player['currency'][0]['amount']
        if 'amount' in player['currency'][1]:
            stardust = player['currency'][1]['amount']

        try:
            print('[#]')
            print('[#] Username: ' + str(player['username']))
            print('[#] Acccount Creation: ' + str(creation_date))
            print('[#] Bag Storage: ' + str(self.getInventoryCount('item')) + '/' + str(player['item_storage']))
            print('[#] Pokemon Storage: ' + str(self.getInventoryCount('pokemon')) + '/' + str(player['poke_storage']))
            print('[#] Stardust: ' + str(stardust))
            print('[#] Pokecoins: ' + str(pokecoins))
            print('[#] PokeBalls: ' + str(self.ballstock[1]))
            print('[#] GreatBalls: ' + str(self.ballstock[2]))
            print('[#] UltraBalls: ' + str(self.ballstock[3]))
            self.getPlayerInfo()
            print('[#]')
        except:
             print('Exception during print player profile')
        self.update_inventory();

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
                            if not 'item' in item['inventory_item_data']['item']:
                                continue
                            if not 'count' in item['inventory_item_data']['item']:
                                continue
                            self.inventory.append(item['inventory_item_data']['item'])

    def _set_starting_position(self):
        self.position = self._get_pos_by_name(self.config.location)
        self.api.set_position(*self.position)

        print('[x] Address found: ' + self.config.location.decode('utf-8'))
        print('[x] Position in-game set as: ' + str(self.position))

        if self.config.test:
            return

    def _get_pos_by_name(self, location_name):
        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name)

        print

        #self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        #self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return (loc.latitude, loc.longitude, loc.altitude)


    ###########################################
    ## @eggins pretty print functions
    ###########################################

    ## - Get count of inventory items and return the output for each
    def getInventoryCount(self, what):
        # Get contents of inventory
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
                                if 'pokemon' in item['inventory_item_data']:
                                    pokecount = pokecount + 1
                                if 'item' in item['inventory_item_data']:
                                    if 'count' in item['inventory_item_data']['item']:
                                        itemcount = itemcount + item['inventory_item_data']['item']['count']
        if 'pokemon' in what:
            return pokecount
        if 'item' in what:
            return itemcount
        return '0'

    ## - Get more player information
    def getPlayerInfo(self):
        # Get contents of inventory
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
                                        print('[#] -- Level: ' + str(playerdata['level']))

                                    if 'experience' in playerdata:
                                        print('[#] -- Experience: ' + str(playerdata['experience']))
                                        print('[#] -- Experience until next level: ' + str(nextlvlxp))

                                    if 'pokemons_captured' in playerdata:
                                        print('[#] -- Pokemon Captured: ' + str(playerdata['pokemons_captured']))

                                    if 'poke_stop_visits' in playerdata:
                                        print('[#] -- Pokestops Visited: ' + str(playerdata['poke_stop_visits']))
