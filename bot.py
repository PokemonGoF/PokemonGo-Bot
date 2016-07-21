import logging
import googlemaps
import json
import threading
import time
from pgoapi import PGoApi
from pgoapi.utilities import f2i, h2f
from cell_workers import PokemonCatchWorker, SeenFortWorker
from stepper import Stepper
from geopy.geocoders import GoogleV3
from math import radians, sqrt, sin, cos, atan2

class PokemonGoBot(object):

    def __init__(self, config):
        self.config = config
        self.pokemon_list=json.load(open('pokemon.json'))
        self.item_list=json.load(open('items.json'))

    def start(self):
        self._setup_logging()
        self._setup_api()
        self.stepper = Stepper(self)

    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, position):
        if 'catchable_pokemons' in cell:
            print 'Something rustles nearby!'
            for pokemon in cell['catchable_pokemons']:
                worker = PokemonCatchWorker(pokemon, self)
                worker.work()
        if 'wild_pokemons' in cell:
            for pokemon in cell['wild_pokemons']:
                worker = PokemonCatchWorker(pokemon, self)
                worker.work()
        if self.config.spinstop:
            if 'forts' in cell:
                for fort in cell['forts']:
                    if 'type' in fort:
                        worker = SeenFortWorker(fort, self)
                        hack_chain = worker.work()
                        if hack_chain > 10:
                            print('need a rest')
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
            return

        # chain subrequests (methods) into one RPC call

        # get player profile call
        # ----------------------
        self.api.get_player()

        response_dict = self.api.call()
        #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1="0"
        currency_2="0"
        if 'amount' in response_dict['responses']['GET_PLAYER']['profile']['currency'][0]:
            currency_1=response_dict['responses']['GET_PLAYER']['profile']['currency'][0]['amount']
        if 'amount' in response_dict['responses']['GET_PLAYER']['profile']['currency'][1]:
            currency_2=response_dict['responses']['GET_PLAYER']['profile']['currency'][1]['amount']
        print 'Profile:'
        print '    Username: ' + str(response_dict['responses']['GET_PLAYER']['profile']['username'])
        print '    Bag size: ' + str(response_dict['responses']['GET_PLAYER']['profile']['item_storage'])
        print '    Pokemon Storage Size: ' + str(response_dict['responses']['GET_PLAYER']['profile']['poke_storage'])
        print '    Account Creation: ' + str(response_dict['responses']['GET_PLAYER']['profile']['creation_time'])
        print '    Currency: '
        print '        ' + str(response_dict['responses']['GET_PLAYER']['profile']['currency'][0]['type']) + ': ' + str(currency_1)
        print '        ' + str(response_dict['responses']['GET_PLAYER']['profile']['currency'][1]['type']) + ': ' + str(currency_2)

    def _set_starting_position(self):
        self.position = self._get_pos_by_name(self.config.location)
        self.api.set_position(*self.position)
        print(self.position)
        if self.config.test:
            return

    def _get_pos_by_name(self, location_name):
        geolocator = GoogleV3()
        loc = geolocator.geocode(location_name)

        self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return (loc.latitude, loc.longitude, loc.altitude)
