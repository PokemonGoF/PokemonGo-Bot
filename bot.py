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
        self.log = logging.getLogger(__name__)

    def start(self):
        self._setup_logging()
        self._setup_api()
        self.stepper = Stepper(self)

    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, position):
        if 'catchable_pokemons' in cell:
            self.log.debug('Something rustles nearby!')
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
                            self.log.info('need a rest')
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
        player_profile = response_dict['responses']['GET_PLAYER']['profile']

        for currency in player_profile.get('currency', []):
            player_profile[currency['type']] = currency.get('amount', 0)

        self.log.info('#' * 30)
        self.log.info('Profile:')
        self.log.info('Username: {username}'.format(**player_profile))
        self.log.info('Bag Size: {item_storage}'.format(**player_profile))
        self.log.info('Pokemon Storage: {poke_storage}'.format(**player_profile))
        self.log.info('Account Creation: {creation_time}'.format(**player_profile))
        self.log.info('Pokecoin: {POKECOIN}'.format(**player_profile))
        self.log.info('Stardust: {STARDUST}'.format(**player_profile))
        self.log.info('#' * 30)
        self.log.info("log configuration:")
        for l in ['pokecli', 'requests', 'pgoapi', 'rpc_api', 'bot', 'stepper', 'seen_fort_worker']:
            self.log.info('%s: %s', l, logging.getLevelName(logging.getLogger(l).level))
        self.log.info('#' * 30)



    def _set_starting_position(self):
        self.position = self._get_pos_by_name(self.config.location)
        self.api.set_position(*self.position)
        if self.config.test:
            return

    def _get_pos_by_name(self, location_name):
        geolocator = GoogleV3()
        loc = geolocator.geocode(location_name)

        self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return (loc.latitude, loc.longitude, loc.altitude)
