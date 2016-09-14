from __future__ import unicode_literals

import os
import time
import json
import requests

from random import uniform
from pokemongo_bot import inventory
from pokemongo_bot.inventory import Pokemon, Pokemons
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.constants import Constants
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.utils import format_dist, format_time, fort_details
from pokemongo_bot.walkers.walker_factory import walker_factory
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker

POKEBALL_ID = 1
GREATBALL_ID = 2
ULTRABALL_ID = 3

class OrderMode():
    IV = 'iv'
    VIP = 'vip'
    MISSING = 'missing'
    THRESHOLD = 'threshold'
    VALUES = [IV, VIP, MISSING, THRESHOLD]
    DEFAULT = [MISSING, IV, THRESHOLD]

class SnipingMode():
    URL = 'url'
    SOCIAL = 'social'
    VALUES = [URL, SOCIAL]
    DEFAULT = SOCIAL

class ResponseMapper():
    ID = 'id'
    IV = 'iv'
    NAME = 'name'
    LATITUDE = 'latitude'
    LONGITUDE = 'longitude'
    ENCOUNTER = 'encounter'
    SPAWNPOINT = 'spawnpoint'

class Sniper(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1
    MIN_SECONDS_ALLOWED_FOR_CELL_CHECK = 10
    CACHE_LIST_MAX_SIZE = 200

    # Constructor (invokes base constructor, which invokes initialize())
    def __init__(self, bot, config):
        super(Sniper, self).__init__(bot, config)

    # Constructor dispatcher
    def initialize(self):
        self.cached_pokemons = []
        self.is_mappings_good = False
        self.is_social = self.bot.config.enable_social
        self.is_debug = self.config.get('debug', False)
        self.url = self.config.get('url', '')
        self.inventory = inventory.items()
        self.pokedex = inventory.pokedex()
        self.last_cell_check_time = time.time()
        self.catch_list = self.config.get('catch', {})
        self.mode = self.config.get('mode', SnipingMode.DEFAULT).lower()
        self.order_by = [order.lower() for order in self.config.get('order_by', OrderMode.DEFAULT)]
        self.altitude = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        self.max_consecutive_catches = self.config.get('max_consecutive_catches', 1)
        self.min_balls_to_teleport_and_catch = self.config.get('min_balls_to_teleport_and_catch', 10)
        self.min_iv_to_ignore_catch_list = self.config.get('min_iv_to_ignore_catch_list', 100)
        self.optional_mappings = ['iv', 'id', 'name', 'encounter', 'spawnpoint']
        self.mappings = {
            ResponseMapper.IV: self.config.get('mappings', {}).get('pokemon_iv', 'iv'),
            ResponseMapper.ID: self.config.get('mappings', {}).get('pokemon_id', 'id'),
            ResponseMapper.NAME: self.config.get('mappings', {}).get('pokemon_name', 'name'),
            ResponseMapper.LATITUDE: self.config.get('mappings', {}).get('latitude', 'latitude'),
            ResponseMapper.LONGITUDE: self.config.get('mappings', {}).get('longitude', 'longitude'),
            ResponseMapper.ENCOUNTER: self.config.get('mappings', {}).get('encounter_id', 'encounter_id'),
            ResponseMapper.SPAWNPOINT: self.config.get('mappings', {}).get('spawnpoint_id', 'spawn_point_id')
        }

        # Validate ordering
        for ordering in self.order_by:
            if ordering not in OrderMode.VALUES:
                raise Exception('Unrecognized ordering: {}'.format(ordering))

        # Validate mode
        if self.mode not in SnipingMode.VALUES:
            raise Exception('Unrecognized mode: {}'.format(self.mode))
        else:
            # Validate url if mode is url
            if self.mode == SnipingMode.URL and not self.url:
                raise Exception('You chose to use URL snipping but you did not specify which (empty)')

            # Validate social flag if mode is social
            if self.mode == SnipingMode.SOCIAL and not self.is_social:
                raise Exception('You chose to use SOCIAL snipping but you did not enable it (enable_social = false)')

    def is_snipeable(self, pokemon):
        pokeballs_count = self.inventory.get(POKEBALL_ID).count
        greatballs_count = self.inventory.get(GREATBALL_ID).count
        ultraballs_count = self.inventory.get(ULTRABALL_ID).count
        all_balls_count = pokeballs_count + greatballs_count + ultraballs_count

        # Skip if already cached
        if self._is_cached(pokemon):
            self._trace('{} was already caught! Skipping...'.format(pokemon['name']))
            return False

        # Skip if not enought balls
        if all_balls_count < self.min_balls_to_teleport_and_catch:
            self._trace('Not enought balls left! Skipping...')
            return False

        # Skip if not in catch list, not a VIP and/or IV sucks (if any)
        if pokemon['name'] not in self.catch_list:
            # If its a VIP, ignore the IV check
            if not pokemon['vip']:
                # If target is not a VIP, check the IV (if any)
                if pokemon['iv'] and pokemon['iv'] < self.min_iv_to_ignore_catch_list:
                    self._trace('{} is not a target, nor a VIP and its IV sucks ({}). Skipping...'.format(pokemon['name'], pokemon['iv']))
                    return False

        return True

    def snipe(self, pokemon):
        # Apply snipping business rules
        if not self.is_snipeable(pokemon):
            self._error('{} is not snipeable! Skipping...'.format(pokemon['name']))
            return WorkerResult.SUCCESS

        # Backup position before anything
        last_position = self.bot.position[0:2]

        # Teleport, so that we can see nearby stuff
        self.bot.hb_locked = True
        self._teleport_to(pokemon)

        # If social is enabled, trust it. If encounter and spawnpoint IDs arent valid, verify them!
        exists = self.is_social
        verify = pokemon.get('encounter_id') and pokemon.get('spawn_point_id')

        # If information verification have to be done, do so
        if verify:
            seconds_since_last_check = time.time() - self.last_cell_check_time

            # Wait a maximum of MIN_SECONDS_ALLOWED_FOR_CELL_CHECK seconds before requesting nearby cells
            if (seconds_since_last_check < self.MIN_SECONDS_ALLOWED_FOR_CELL_CHECK):
                time.sleep(self.MIN_SECONDS_ALLOWED_FOR_CELL_CHECK - seconds_since_last_check)

            nearby_pokemons = []
            nearby_stuff = self.bot.get_meta_cell()
            self.last_cell_check_time = time.time()

            # Retrieve nearby pokemons for validation
            nearby_pokemons.extend(nearby_stuff.get('wild_pokemons', []))
            nearby_pokemons.extend(nearby_stuff.get('catchable_pokemons', []))

            # Make sure the target really/still exists (nearby_pokemon key names are game-bound!)
            for nearby_pokemon in nearby_pokemons:
                nearby_pokemon_id = nearby_pokemon.get('pokemon_data', {}).get('pokemon_id') or nearby_pokemon.get('pokemon_id')

                if int(nearby_pokemon_id) == int(pokemon.get('id')):
                    exists = True

                    # Also, if the IDs arent valid, update them (nearby_pokemon key names are game-bound!)
                    if not pokemon.get('encounter_id') or not pokemon.get('spawn_point_id'):
                        pokemon['encounter_id'] = nearby_pokemon['encounter_id']
                        pokemon['spawn_point_id'] = nearby_pokemon['spawn_point_id']
                    break

        # If target exists, catch it, otherwise ignore
        if exists:
            self._log('Encountered {}!'.format(pokemon['name']))
            self._teleport_back_and_catch(last_position, pokemon)
        else:
            self._error('{} does not exist anymore. Skipping...'.format(pokemon['name']))
            self._teleport_back(last_position)

        # Save target and unlock heartbeat calls
        self._cache(pokemon)
        self.bot.hb_locked = False

        return WorkerResult.SUCCESS

    def work(self):
        targets = []

        # Retrieve the targets
        if self.mode == SnipingMode.SOCIAL:
            targets = self._get_pokemons_from_social()
        elif self.mode == SnipingMode.URL:
            targets = self._get_pokemons_from_url()

        # Order the targets (descending)
        for attr in self.order_by:
            targets.sort(key=lambda pokemon: pokemon[attr], reverse=True)

        # Start sniping the first 'max_consecutive_catches' entries
        for catch_attempt in range(len(targets)):
            if catch_attempt < self.max_consecutive_catches:
                self.snipe(targets[catch_attempt])

                # Wait a bit if were going to snipe again
                if self.max_consecutive_catches is not 1:
                    time.sleep(3)

        return WorkerResult.SUCCESS

    def _validate_mappings(self, dictionary):
        invalid_mappings = []

        # Gather invalid mappings. If one is optional, the correct value can still be retrieved
        for key, value in self.mappings.iteritems():
            if key not in self.optional_mappings and value not in dictionary:
                invalid_mappings.append(value)

        # If mappings are invalid, this would lead to a wrong formatted pokemon object (blank attributes)
        if invalid_mappings:
            raise Exception('Invalid mapping values for {} mode: {}'.format(self.mode, ', '.join(invalid_mappings)))

        # Mappings are good. No need to check again
        self.is_mappings_good = True

    def _parse_pokemons(self, pokemon_dictionary_list):
        pokemons = []

        # If were parsing for the first time, lets validate the mappings (use first item as a dictionary sample)
        if not self.is_mappings_good and pokemon_dictionary_list:
            try:
                self._validate_mappings(pokemon_dictionary_list[0])
            except Exception as exception:
                # If mappings contain errors, log it instead of forwarding the exception
                self._error(exception)
                self._trace('This is the dictionary: {}'.format(pokemon_dictionary_list[0])) # TODO: Remove
                return pokemons

        # Build up the pokemon. Pops are used to destroy random attribute names and keep the known ones!
        for pokemon_dictonary in pokemon_dictionary_list:
            pokemon_dictonary['iv'] = pokemon_dictonary.pop(self.mappings.get(ResponseMapper.IV), 0)
            pokemon_dictonary['id'] = pokemon_dictonary.pop(self.mappings.get(ResponseMapper.ID), None)
            pokemon_dictonary['name'] = pokemon_dictonary.pop(self.mappings.get(ResponseMapper.NAME), None)
            pokemon_dictonary['encounter_id'] = pokemon_dictonary.pop(self.mappings.get(ResponseMapper.ENCOUNTER), None)
            pokemon_dictonary['spawn_point_id'] = pokemon_dictonary.pop(self.mappings.get(ResponseMapper.SPAWNPOINT), None)

            # If ID or name couldnt be retrieved, retrieve ID by name or vice-versa
            if not pokemon_dictonary['name'] or not pokemon_dictonary['id']:
                if not pokemon_dictonary['name'] and pokemon_dictonary['id']:
                    pokemon_dictonary['name'] = Pokemons.name_for(pokemon_dictonary.get('id') - 1)
                elif not pokemon_dictonary['id'] and pokemon_dictonary['name']:
                    pokemon_dictonary['id'] = Pokemons.id_for(pokemon_dictonary.get('name'))
                else:
                    raise Exception('Response does not have both pokemon ID and name')

            # If positions are mapped by the same name, then  we have to split it
            if self.mappings.get(ResponseMapper.LATITUDE) == self.mappings.get(ResponseMapper.LONGITUDE):
                position = pokemon_dictonary.get(self.mappings.get(ResponseMapper.LATITUDE)).replace(' ', '').split(',')
                pokemon_dictonary['latitude'] = float(position[0])
                pokemon_dictonary['longitude'] = float(position[1])
            else:
                pokemon_dictonary['latitude'] = pokemon_dictonary.pop(self.mappings.get('latitude'), .0)
                pokemon_dictonary['longitude'] = pokemon_dictonary.pop(self.mappings.get('longitude'), .0)

            # Some other helpful values
            pokemon_dictonary['vip'] = pokemon_dictonary.get('name') in self.bot.config.vips
            pokemon_dictonary['missing'] = not self.pokedex.captured(pokemon_dictonary.get('id'))
            pokemon_dictonary['threshold'] = self.catch_list.get(pokemon_dictonary.get('name'), 0)

            # Check whether this is a valid target
            if self.is_snipeable(pokemon_dictonary):
                pokemons.append(pokemon_dictonary)

        return pokemons

    def _get_pokemons_from_social(self):
        if not hasattr(self.bot, 'mqtt_pokemon_list') or not self.bot.mqtt_pokemon_list:
            return []

        # Backup mqtt list and clean it for the next cycle
        mqtt_pokemon_list = self.bot.mqtt_pokemon_list
        self.bot.mqtt_pokemon_list = []

        return self._parse_pokemons(mqtt_pokemon_list)

    def _get_pokemons_from_url(self):
        try:
            request = requests.get(self.url)
            response = request.json()
        except requests.exceptions.ConnectionError:
            self._error('Could not get data from {}'.format(self.url))
            return []
        except ValueError:
            self._error('Could not parse the JSON response. It might be related to a bad url or JSON format')
            return []

        # Use some known/possible response 'keywords'
        return self._parse_pokemons(response.get('pokemons') or response.get('results') or [])

    def _is_cached(self, pokemon):
        for entry in self.cached_pokemons:
            # Since IDs might be invalid (null/blank) by this time, compare by approximate location
            same_latitude = "{0:.4f}".format(pokemon['latitude']) == "{0:.4f}".format(entry['latitude'])
            same_longitude = "{0:.4f}".format(pokemon['longitude']) == "{0:.4f}".format(entry['longitude'])

            if same_latitude and same_longitude:
                return True

        return False

    def _cache(self, pokemon):
        # Skip repeated items
        if not self._is_cached(pokemon):
            # Free space if full and store it
            if len(self.cached_pokemons) >= self.CACHE_LIST_MAX_SIZE:
                self.cached_pokemons.pop(0)
            self.cached_pokemons.append(pokemon)

    def _log(self, message):
        self.emit_event('sniper_log', formatted='{message}', data={'message': message})

    def _error(self, message):
        self.emit_event('sniper_error', formatted='{message}', data={'message': message})

    def _trace(self, message):
        if self.is_debug:
            self._log(message)

    def _teleport(self, latitude, longitude, altitude):
        self.bot.api.set_position(latitude, longitude, altitude, True)
        time.sleep(3)

    def _teleport_to(self, pokemon):
        self.emit_event(
            'sniper_teleporting',
            formatted = 'Teleporting to {name} at [{latitude}; {longitude}]...',
            data = { 'name': pokemon['name'], 'latitude': pokemon['latitude'], 'longitude': pokemon['longitude'] }
        )
        self._teleport(pokemon['latitude'], pokemon['longitude'], self.altitude)

    def _teleport_back(self, position_array):
        self.emit_event(
            'sniper_teleporting',
            formatted = 'Teleporting back to ({latitude}; {longitude})...',
            data = { 'latitude': position_array[0], 'longitude': position_array[1] }
        )
        self._teleport(position_array[0], position_array[1], self.altitude)

    def _teleport_back_and_catch(self, position_array, pokemon):
        catch_worker = PokemonCatchWorker(pokemon, self.bot, self.config)
        api_encounter_response = catch_worker.create_encounter_api_call()
        self._teleport_back(position_array)
        catch_worker.work(api_encounter_response)