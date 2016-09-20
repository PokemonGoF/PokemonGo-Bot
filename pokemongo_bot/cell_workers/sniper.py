from __future__ import unicode_literals

import time
import json
import requests
import calendar

from random import uniform
from datetime import datetime, timedelta
from pokemongo_bot import inventory
from pokemongo_bot.item_list import Item
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.inventory import Pokemons
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker

# Represents a URL source and its mappings
class SniperSource(object):
    def __init__(self, data):
        self.url = data.get('url', '')
        self.key = data.get('key', '')
        self.time_mask = data.get('time_mask', '%Y-%m-%d %H:%M:%S')
        self.mappings = SniperSourceMapping(data.get('mappings', {}))

    def __str__(self):
        return self.url

    def fetch_raw(self, timeoutz):
        some_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/52.0.2743.116 Safari/537.36'
        response = requests.get(self.url, headers={'User-Agent': some_agent}, timeout=timeoutz)
        results = response.json()

        # If the results is a dict, retrieve the list from it by the given key. This will return a list afterall.
        return results.get(self.key, []) if isinstance(results, dict) else results

    def fetch(self, timeout):
        pokemons = []

        try:
            results = self.fetch_raw(timeout)

            # Parse results
            for result in results:
                iv = result.get(self.mappings.iv.param)
                id = result.get(self.mappings.id.param)
                name = result.get(self.mappings.name.param)
                latitude = result.get(self.mappings.latitude.param)
                longitude = result.get(self.mappings.longitude.param)
                expiration = result.get(self.mappings.expiration.param)
                encounter = result.get(self.mappings.encounter.param)
                spawnpoint = result.get(self.mappings.spawnpoint.param)

                # If this is a composite param, split it ("coords": "-31.415553, -64.190480")
                if self.mappings.latitude.param == self.mappings.longitude.param:
                    position = result.get(self.mappings.latitude.param).replace(" ", "").split(",")
                    latitude = position[0]
                    longitude = position[1]

                # Format the time accordingly. Pokemon times are in milliseconds!
                if self.mappings.expiration.exists and expiration:
                    if self.mappings.expiration.format == SniperSourceMappingTimeFormat.SECONDS:
                        expiration = expiration * 1000
                    elif self.mappings.expiration.format == SniperSourceMappingTimeFormat.UTC:
                        utc_date = datetime.strptime(expiration.replace("T", " ")[:19], self.time_mask)
                        timestamp = calendar.timegm(utc_date.timetuple())
                        local_date = datetime.fromtimestamp(timestamp)
                        local_date = local_date.replace(microsecond=utc_date.microsecond)
                        expiration = time.mktime(local_date.timetuple()) * 1000

                # If either name or ID are invalid, fix it using each other
                if not name or not id:
                    if not name and id:
                        name = Pokemons.name_for(id - 1)
                    if not id and name:
                        id = Pokemons.id_for(name)

                # Some type castings were specified for a better readability
                pokemons.append({
                    'iv': int(iv or 0),
                    'pokemon_id': int(id or 0),
                    'pokemon_name': str(name or ''),
                    'latitude': float(latitude or .0),
                    'longitude': float(longitude or .0),
                    'expiration_timestamp_ms': long(expiration or 0),
                    'last_modified_timestamp_ms': long(expiration or 0),
                    'encounter_id': long(encounter or 0),
                    'spawn_point_id': str(spawnpoint or '')
                })
        except requests.exceptions.Timeout:
            raise Exception("Fetching has timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Source not available")
        except:
            raise

        return pokemons

    def validate(self):
        try:
            errors = []
            data = self.fetch_raw(7)

            # Check whether the params really exist if they have been specified like so
            if data:
                if self.mappings.iv.exists and self.mappings.iv.param not in data[0]:
                   errors.append(self.mappings.iv.param)
                if self.mappings.id.exists and self.mappings.id.param not in data[0]:
                    errors.append(self.mappings.id.param)
                if self.mappings.name.exists and self.mappings.name.param not in data[0]:
                    errors.append(self.mappings.name.param)
                if self.mappings.latitude.exists and self.mappings.latitude.param not in data[0]:
                    errors.append(self.mappings.latitude.param)
                if self.mappings.longitude.exists and self.mappings.longitude.param not in data[0]:
                    errors.append(self.mappings.longitude.param)
                if self.mappings.expiration.exists and self.mappings.expiration.param not in data[0]:
                    errors.append(self.mappings.expiration.param)
                if self.mappings.encounter.exists and self.mappings.encounter.param not in data[0]:
                    errors.append(self.mappings.encounter.param)
                if self.mappings.spawnpoint.exists and self.mappings.spawnpoint.param not in data[0]:
                    errors.append(self.mappings.spawnpoint.param)

                # All wrong mappings were gathered at once for a better usability (instead of raising multiple exceptions)
                if errors:
                    raise LookupError("The following params dont exist: {}".format(", ".join(errors)))
            else:
                raise ValueError("Empty reply")
        except requests.exceptions.Timeout:
            raise ValueError("Fetching has timed out")
        except requests.exceptions.ConnectionError:
            raise ValueError("Source not available")
        except:
            raise

# Represents the JSON params mappings
class SniperSourceMapping(object):
    def __init__(self, mapping):
        self.iv = SniperSourceMappingValues(False, mapping.get('iv', {}))
        self.id = SniperSourceMappingValues(True, mapping.get('id', {}))
        self.name = SniperSourceMappingValues(True, mapping.get('name', {}))
        self.latitude = SniperSourceMappingValues(True, mapping.get('latitude', {}))
        self.longitude = SniperSourceMappingValues(True, mapping.get('longitude', {}))
        self.expiration = SniperSourceMappingValues(False, mapping.get('expiration', {}))
        self.encounter = SniperSourceMappingValues(False, mapping.get('encounter', {}))
        self.spawnpoint = SniperSourceMappingValues(False, mapping.get('spawnpoint', {}))

# Represents the JSON params mappings values
class SniperSourceMappingValues(object):
    def __init__(self, required, values):
        self.required = required
        self.param = values.get('param', '')
        self.format = values.get('format', SniperSourceMappingTimeFormat.DEFAULT)
        self.exists = values != {} and values.get('param') != None

        # Validate formats
        if self.format not in vars(SniperSourceMappingTimeFormat).values():
            raise ValueError('Unrecognized format: {}'.format(self.format))

# Represents the JSON time param formatting type
class SniperSourceMappingTimeFormat(object):
    NONE = ''
    UTC = 'utc'
    SECONDS = 'seconds'
    MILLISECONDS = 'milliseconds'
    DEFAULT = NONE

# Represents the information ordering types
class SniperOrderMode(object):
    IV = 'iv'
    VIP = 'vip'
    MISSING = 'missing'
    PRIORITY = 'priority'
    EXPIRATION = 'expiration_timestamp_ms'
    DEFAULT = [MISSING, VIP, PRIORITY]

# Represents the snipping type
class SniperMode(object):
    URL = 'url'
    SOCIAL = 'social'
    DEFAULT = SOCIAL

# Teleports the player to a target gotten from either social or a single/multiple URL sources
class Sniper(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1
    MIN_SECONDS_ALLOWED_FOR_CELL_CHECK = 10
    MIN_SECONDS_ALLOWED_FOR_REQUESTING_DATA = 5
    MIN_BALLS_FOR_CATCHING = 10
    CACHE_LIST_MAX_SIZE = 200

    def __init__(self, bot, config):
        super(Sniper, self).__init__(bot, config)

    def initialize(self):
        self.cache = []
        self.disabled = False
        self.last_cell_check_time = time.time()
        self.last_data_request_time = time.time()
        self.inventory = inventory.items()
        self.pokedex = inventory.pokedex()
        self.debug = self.config.get('debug', False)
        self.special_iv = self.config.get('special_iv', 100)
        self.bullets = self.config.get('bullets', 1)
        self.homing_shots = self.config.get('homing_shots', True)
        self.mode = self.config.get('mode', SniperMode.DEFAULT)
        self.order = self.config.get('order', SniperOrderMode.DEFAULT)
        self.catch_list = self.config.get('catch', {})
        self.altitude = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        self.sources = [SniperSource(data) for data in self.config.get('sources', [])]

        # Validate ordering
        for ordering in self.order:
            if ordering not in vars(SniperOrderMode).values():
                raise ValueError("Unrecognized ordering: '{}'".format(ordering))

        # Validate mode and sources
        if self.mode not in vars(SniperMode).values():
            raise ValueError("Unrecognized mode: '{}'".format(self.mode))
        else:
            # Selected mode is valid. Validate sources if mode is URL
            if self.mode == SniperMode.URL:
                self._log("Validating sources: {}...".format(", ".join([source.url for source in self.sources])))

                # Create a copy of the list so we can iterate and remove elements at the same time
                for source in list(self.sources):
                    try:
                        source.validate()
                        self._log("Source '{}' is good!".format(source.url))
                    # TODO: On ValueError, remember source and validate later (pending validation)
                    except (LookupError, ValueError) as exception:
                        self._error("Source '{}' contains errors. Details: {}. Removing from sources list...".format(source.url, exception))
                        self.sources.remove(source)

                # Notify user if all sources are invalid and cant proceed
                if not self.sources:
                    self._error("There is no source available. Disabling Sniper...")
                    self.disabled = True

    def is_snipeable(self, pokemon):
        pokeballs_count = self.inventory.get(Item.ITEM_POKE_BALL.value).count
        greatballs_count = self.inventory.get(Item.ITEM_GREAT_BALL.value).count
        ultraballs_count = self.inventory.get(Item.ITEM_ULTRA_BALL.value).count
        all_balls_count = pokeballs_count + greatballs_count + ultraballs_count

        # Skip if expired (cast milliseconds to seconds for comparision)
        if (pokemon.get('expiration_timestamp_ms', 0) or pokemon.get('last_modified_timestamp_ms', 0)) / 1000 < time.time():
            self._trace('{} is expired! Skipping...'.format(pokemon.get('pokemon_name')))
            return False

        # Skip if already cached
        if self._is_cached(pokemon):
            self._trace('{} was already handled! Skipping...'.format(pokemon.get('pokemon_name', '')))
            return False

        # Skip if not enought balls. Sniping wastes a lot of balls. Theres no point to let user decide this amount
        if all_balls_count < self.MIN_BALLS_FOR_CATCHING:
            self._trace('Not enought balls left! Skipping...')
            return False

        # Skip if not in catch list, not a VIP and/or IV sucks (if any)
        if pokemon.get('pokemon_name', '') not in self.catch_list:
            # This is not in the catch list. Lets see if its a VIP one
            if not pokemon.get('pokemon_name') in self.bot.config.vips:
                # It is not a VIP either. Lets see if its IV is good (if any)
                if pokemon.get('iv', 0) < self.special_iv:
                    self._trace('{} is not listed to catch, nor a VIP and its IV sucks. Skipping...'.format(pokemon.get('pokemon_name')))
                    return False
        #         else:
        #             self._trace('{} has a decent IV ({}), therefore a valid target'.format(pokemon.get('pokemon_name'), pokemon.get('iv')))
        #     else:
        #         self._trace('{} is a VIP, therefore a valid target'.format(pokemon.get('pokemon_name')))
        # else:
        #     self._trace('{} is in the catch list, therefore a valid target'.format(pokemon.get('pokemon_name')))

        return True

    # Snipe a target. This function admits that if a target really exists, it will be 'caught'.
    def snipe(self, pokemon):
        success = False

        # Apply snipping business rules and snipe if its good
        if not self.is_snipeable(pokemon):
            self._error('{} is not snipeable! Skipping...'.format(pokemon['pokemon_name']))
        else:
            # Backup position before anything
            last_position = self.bot.position[0:2]

            # Teleport, so that we can see nearby stuff
            self.bot.hb_locked = True
            self._teleport_to(pokemon)

            # If social is enabled and if no verification is needed, trust it. Otherwise, update IDs!
            verify = not pokemon.get('encounter_id') or not pokemon.get('spawn_point_id')
            exists = not verify and self.mode == SniperMode.SOCIAL

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

                    # If we found the target, it exists and will very likely be encountered/caught (success)
                    if nearby_pokemon_id == pokemon.get('pokemon_id', 0):
                        exists = True
                        success = True

                        # Also, if the IDs arent valid, override them (nearby_pokemon key names are game-bound!) with game values
                        if not pokemon.get('encounter_id') or not pokemon.get('spawn_point_id'):
                            pokemon['encounter_id'] = nearby_pokemon['encounter_id']
                            pokemon['spawn_point_id'] = nearby_pokemon['spawn_point_id']
                        break

            # If target exists, catch it, otherwise ignore
            if exists:
                self._log('Yay! There really is a wild {} nearby!'.format(pokemon.get('pokemon_name')))
                self._teleport_back_and_catch(last_position, pokemon)
            else:
                self._error('Damn! Its not here. Reasons: too far, caught, expired or fake data. Skipping...')
                self._teleport_back(last_position)

            # Save target and unlock heartbeat calls
            self._cache(pokemon)
            self.bot.hb_locked = False

        return success

    def work(self):
        # Do nothing if this task was invalidated
        if self.disabled:
            self._error("Sniper was disabled for some reason. Scroll up to find out.")
        else:
            targets = []

            # Retrieve the targets
            if self.mode == SniperMode.SOCIAL:
                targets = self._get_pokemons_from_social()
            elif self.mode == SniperMode.URL:
                targets = self._get_pokemons_from_url()

            if targets:
                # Order the targets (descending)
                for attr in self.order:
                    targets.sort(key=lambda pokemon: pokemon[attr], reverse=True)

                shots = 0

                # For as long as there are targets available, try to snipe untill we run out of bullets
                for index, target in enumerate(targets):
                    if shots < self.bullets:
                        success = self.snipe(target)
                        shots += 1

                        # Homing shots are supposed to hit the target (capture). Rollback
                        if self.homing_shots and not success:
                            shots -= 1

                        # Wait a bit if were going to snipe again (bullets and targets left)
                        if shots < self.bullets and index < len(targets):
                            self._trace('Waiting a few seconds to teleport again to another target...')
                            time.sleep(3)

        return WorkerResult.SUCCESS

    def _parse_pokemons(self, pokemon_dictionary_list):
        result = []

        # Build up the pokemon. Pops are used to destroy random attribute names and keep the known ones!
        for pokemon in pokemon_dictionary_list:
            # Even thought the dict might have the name in it, use ID instead for safety (social vs url)
            pokemon_name = Pokemons.name_for(pokemon.get('pokemon_id') - 1)

            # TODO: See below
            # The plan is to only keep valid data in the broker, so if it hasnt ever been verified, we'll verify it and
            # send the information back to the broker. Untill then, dont trust it.
            # Sniper should send back to the broker whether it really exists or not. Use this in the snipe() function.
            pokemon['verified'] = pokemon.get('verified', False)
            pokemon['iv'] = pokemon.get('iv', 0)
            pokemon['vip'] = pokemon_name in self.bot.config.vips
            pokemon['missing'] = not self.pokedex.captured(pokemon.get('pokemon_id'))
            pokemon['priority'] = self.catch_list.get(pokemon_name, 0)

            # Check whether this is a valid target
            if self.is_snipeable(pokemon):
                result.append(pokemon)

        return result

    def _get_pokemons_from_social(self):
        if not hasattr(self.bot, 'mqtt_pokemon_list') or not self.bot.mqtt_pokemon_list:
            return []

        self._trace('Social has returned {} pokemon(s)'.format(len(self.bot.mqtt_pokemon_list)))

        return self._parse_pokemons(self.bot.mqtt_pokemon_list)

    def _get_pokemons_from_url(self):
        results_hash_map = {}
        seconds_since_last_valid_request = time.time() - self.last_data_request_time

        # If something is requesting this info too fast, skip it, otherwise lets merge the results!
        if (seconds_since_last_valid_request > self.MIN_SECONDS_ALLOWED_FOR_REQUESTING_DATA):
            self.last_data_request_time = time.time()

            self._trace("Fetching pokemons from the sources...")
            for source in self.sources:
                try:
                    source_pokemons = source.fetch(3)
                    self._trace("Source '{}' returned {} results".format(source.url, len(source_pokemons)))

                    # Merge lists, making sure to exclude repeated data. Use location as the hash key
                    for source_pokemon in source_pokemons:
                        hash_key = self._hash(source_pokemon)

                        # Add if new
                        if not results_hash_map.has_key(hash_key):
                            results_hash_map[hash_key] = source_pokemon
                except Exception as exception:
                    self._error("Could not fetch data from '{}'. Details: {}. Skipping...".format(source.url, exception))
                    continue

            self._trace("After merging, we've got {} results".format(len(results_hash_map.values())))
        else:
            self._trace("Not ready yet to retrieve data...")

        return self._parse_pokemons(results_hash_map.values())

    def _hash(self, pokemon):
        # Use approximate location instead, because some IDs might be wrong. The first 4 decimal places is enough for this
        return "{0:.4f};{1:.4f}".format(pokemon.get('latitude'), pokemon.get('longitude'))

    def _equals(self, pokemon_1, pokemon_2):
        return self._hash(pokemon_1) == self._hash(pokemon_2)

    def _is_cached(self, pokemon):
        for cached_pokemon in self.cache:
            if self._equals(pokemon, cached_pokemon):
                return True

        return False

    def _cache(self, pokemon):
        # Skip repeated items
        if not self._is_cached(pokemon):
            # Free space if full and store it
            if len(self.cache) >= self.CACHE_LIST_MAX_SIZE:
                self.cache.pop(0)
            self.cache.append(pokemon)

    def _log(self, message):
        self.emit_event('sniper_log', formatted='{message}', data={'message': message})

    def _error(self, message):
        self.emit_event('sniper_error', formatted='{message}', data={'message': message})

    def _trace(self, message):
        if self.debug:
            self._log(message)

    def _teleport(self, latitude, longitude, altitude):
        self.bot.api.set_position(latitude, longitude, altitude, True)
        time.sleep(3)

    def _teleport_to(self, pokemon):
        self.emit_event(
            'sniper_teleporting',
            formatted = 'Teleporting to meet {name} ({latitude}; {longitude})...',
            data = { 'name': pokemon['pokemon_name'], 'latitude': pokemon['latitude'], 'longitude': pokemon['longitude'] }
        )
        self._teleport(pokemon['latitude'], pokemon['longitude'], self.altitude)

    def _teleport_back(self, position_array):
        self.emit_event(
            'sniper_teleporting',
            formatted = 'Teleporting back to the old position ({latitude}; {longitude})...',
            data = { 'latitude': position_array[0], 'longitude': position_array[1] }
        )
        self._teleport(position_array[0], position_array[1], self.altitude)

    def _teleport_back_and_catch(self, position_array, pokemon):
        catch_worker = PokemonCatchWorker(pokemon, self.bot, self.config)
        api_encounter_response = catch_worker.create_encounter_api_call()
        self._teleport_back(position_array)
        catch_worker.work(api_encounter_response)