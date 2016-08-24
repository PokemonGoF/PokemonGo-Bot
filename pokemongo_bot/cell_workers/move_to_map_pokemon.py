# -*- coding: utf-8 -*-
"""
Moves a trainer to a Pokemon.

Events:
    move_to_map_pokemon_fail
        When the worker fails.
        Returns:
            message: Failure message.

    move_to_map_pokemon_updated_map
        When worker updates the PokemonGo-Map.
        Returns:
            lat: Latitude
            lon: Longitude

    move_to_map_pokemon_teleport_to
        When trainer is teleported to a Pokemon.
        Returns:
            poke_name: Pokemon's name
            poke_dist: Distance from the trainer
            poke_lat: Latitude of the Pokemon
            poke_lon: Longitude of the Pokemon
            disappears_in: Number of seconds before the Pokemon disappears

    move_to_map_pokemon_encounter
        When a trainer encounters a Pokemon by teleporting or walking.
        Returns:
            poke_name: Pokemon's name
            poke_dist: Distance from the trainer
            poke_lat: Latitude of the Pokemon
            poke_lon: Longitude of the Pokemon
            disappears_in: Number of seconds before the Pokemon disappears

    move_to_map_pokemon_move_towards
        When a trainer moves toward a Pokemon.
        Returns:
            poke_name: Pokemon's name
            poke_dist: Distance from the trainer
            poke_lat: Latitude of the Pokemon
            poke_lon: Longitude of the Pokemon
            disappears_in: Number of seconds before the Pokemon disappears

    move_to_map_pokemon_teleport_back
        When a trainer teleports back to thier previous location.
        Returns:
            last_lat: Trainer's last known latitude
            last_lon: Trainer's last known longitude

"""

import os
import time
import json
import base64
import requests

from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.cell_workers.utils import distance, format_dist, format_time, fort_details
from pokemongo_bot.walkers.walker_factory import walker_factory
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from random import uniform
from pokemongo_bot.constants import Constants

# Update the map if more than N meters away from the center. (AND'd with
# UPDATE_MAP_MIN_TIME_MINUTES)
ULTRABALL_ID = 3
GREATBALL_ID = 2
POKEBALL_ID = 1
UPDATE_MAP_MIN_DISTANCE_METERS = 500

# Update the map if it hasn't been updated in n seconds. (AND'd with
# UPDATE_MAP_MIN_DISTANCE_METERS)
UPDATE_MAP_MIN_TIME_SEC = 120

# Number of seconds to sleep between teleporting to a snipped Pokemon.
SNIPE_SLEEP_SEC = 2


class MoveToMapPokemon(BaseTask):
    """Task for moving a trainer to a Pokemon."""
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.last_map_update = 0
        self.pokemon_data = self.bot.pokemon_list
        self.unit = self.bot.config.distance_unit
        self.caught = []
        self.min_ball = self.config.get('min_ball', 1)
        self.map_path = self.config.get('map_path', 'raw_data')
        self.walker = self.config.get('walker', 'StepWalker')
        self.snipe_high_prio_only = self.config.get('snipe_high_prio_only', False)
        self.snipe_high_prio_threshold = self.config.get('snipe_high_prio_threshold', 400)

        data_file = os.path.join(_base_dir, 'map-caught-{}.json'.format(self.bot.config.username))
        if os.path.isfile(data_file):
            self.caught = json.load(
                open(data_file)
            )
        self.alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
    def get_pokemon_from_social(self):
    	if not hasattr(self.bot, 'mqtt_pokemon_list'):
            return []
        if not self.bot.mqtt_pokemon_list or len(self.bot.mqtt_pokemon_list) <= 0:
            return []

        pokemon_list = []
        now = int(time.time())

        for pokemon in self.bot.mqtt_pokemon_list:
            pokemon['encounter_id'] = pokemon['encounter_id']
            pokemon['spawn_point_id'] = pokemon['spawn_point_id']
            pokemon['disappear_time'] = int(pokemon['expiration_timestamp_ms'] / 1000)
            pokemon['name'] = self.pokemon_data[pokemon['pokemon_id'] - 1]['Name']
            pokemon['is_vip'] = pokemon['name'] in self.bot.config.vips

            if pokemon['name'] not in self.config['catch']:
                continue

            if self.was_caught(pokemon):
                continue

            pokemon['priority'] = self.config['catch'].get(pokemon['name'], 0)

            pokemon['dist'] = distance(
                self.bot.position[0],
                self.bot.position[1],
                pokemon['latitude'],
                pokemon['longitude'],
            )

            if pokemon['dist'] > self.config['max_distance'] and not self.config['snipe']:
                continue

            # pokemon not reachable with mean walking speed (by config)
            mean_walk_speed = (self.bot.config.walk_max + self.bot.config.walk_min) / 2
            if pokemon['dist'] > ((pokemon['disappear_time'] - now) * mean_walk_speed) and not self.config['snipe']:
                continue
            pokemon_list.append(pokemon)
        self.bot.mqtt_pokemon_list = []
        return pokemon_list
    def get_pokemon_from_map(self):
        try:
            req = requests.get('{}/{}?gyms=false&scanned=false'.format(self.config['address'], self.map_path))
        except requests.exceptions.ConnectionError:
            self._emit_failure('Could not get Pokemon data from PokemonGo-Map: '
                               '{}. Is it running?'.format(
                                   self.config['address']))
            return []

        try:
            raw_data = req.json()
        except ValueError:
            self._emit_failure('Map data was not valid')
            return []

        pokemon_list = []
        now = int(time.time())

        for pokemon in raw_data['pokemons']:
            try:
                pokemon['encounter_id'] = long(base64.b64decode(pokemon['encounter_id']))
            except:
                self._emit_failure('base64 error: {}'.format(pokemon['encounter_id']))
                continue
            pokemon['spawn_point_id'] = pokemon['spawnpoint_id']
            pokemon['disappear_time'] = int(pokemon['disappear_time'] / 1000)
            pokemon['name'] = self.pokemon_data[pokemon['pokemon_id'] - 1]['Name']
            pokemon['is_vip'] = pokemon['name'] in self.bot.config.vips

            if pokemon['name'] not in self.config['catch'] and not pokemon['is_vip']:
                continue

            if self.was_caught(pokemon):
                continue

            pokemon['priority'] = self.config['catch'].get(pokemon['name'], 0)

            pokemon['dist'] = distance(
                self.bot.position[0],
                self.bot.position[1],
                pokemon['latitude'],
                pokemon['longitude'],
            )

            if pokemon['dist'] > self.config['max_distance'] and not self.config['snipe']:
                continue

            # pokemon not reachable with mean walking speed (by config)
            mean_walk_speed = (self.bot.config.walk_max + self.bot.config.walk_min) / 2
            if pokemon['dist'] > ((pokemon['disappear_time'] - now) * mean_walk_speed) and not self.config['snipe']:
                continue

            pokemon_list.append(pokemon)

        return pokemon_list

    def add_caught(self, pokemon):
        for caught_pokemon in self.caught:
            if caught_pokemon['encounter_id'] == pokemon['encounter_id']:
                return
        if len(self.caught) >= 200:
            self.caught.pop(0)
        self.caught.append(pokemon)

    def was_caught(self, pokemon):
        for caught_pokemon in self.caught:
            if pokemon['encounter_id'] == caught_pokemon['encounter_id']:
                return True
        return False

    def update_map_location(self):
        if not self.config['update_map']:
            return
        try:
            req = requests.get('{}/loc'.format(self.config['address']))
        except requests.exceptions.ConnectionError:
            self._emit_failure('Could not update trainer location '
                               'PokemonGo-Map: {}. Is it running?'.format(
                                   self.config['address']))
            return

        try:
            loc_json = req.json()
        except ValueError:
            err = 'Map location data was not valid'
            self._emit_failure(err)
            return

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            loc_json['lat'],
            loc_json['lng']
        )

        # update map when 500m away from center and last update longer than 2 minutes away
        now = int(time.time())
        if (dist > UPDATE_MAP_MIN_DISTANCE_METERS and
            now - self.last_map_update > UPDATE_MAP_MIN_TIME_SEC):
            requests.post(
                '{}/next_loc?lat={}&lon={}'.format(self.config['address'],
                                                   self.bot.position[0],
                                                   self.bot.position[1]))
            self.emit_event(
                'move_to_map_pokemon_updated_map',
                formatted='Updated PokemonGo-Map to {lat}, {lon}',
                data={
                    'lat': self.bot.position[0],
                    'lon': self.bot.position[1]
                }
            )
            self.last_map_update = now

    def snipe(self, pokemon):
        """Snipe a Pokemon by teleporting.

        Args:
            pokemon: Pokemon to snipe.
        """
        last_position = self.bot.position[0:2]
        self.bot.heartbeat()
        self._teleport_to(pokemon)
        catch_worker = PokemonCatchWorker(pokemon, self.bot, self.config)
        api_encounter_response = catch_worker.create_encounter_api_call()
        time.sleep(SNIPE_SLEEP_SEC)
        self._teleport_back(last_position)
        self.bot.api.set_position(last_position[0], last_position[1], self.alt, False)
        time.sleep(SNIPE_SLEEP_SEC)
        self.bot.heartbeat()
        catch_worker.work(api_encounter_response)
        self.add_caught(pokemon)
        return WorkerResult.SUCCESS

    def dump_caught_pokemon(self):
        user_data_map_caught = os.path.join(_base_dir, 'data', 'map-caught-{}.json'.format(self.bot.config.username))
        with open(user_data_map_caught, 'w') as outfile:
            json.dump(self.caught, outfile)

    def work(self):
        # check for pokeballs (excluding masterball)
        pokeballs_quantity = inventory.items().get(POKEBALL_ID).count
        superballs_quantity = inventory.items().get(GREATBALL_ID).count
        ultraballs_quantity = inventory.items().get(ULTRABALL_ID).count

        if (pokeballs_quantity + superballs_quantity + ultraballs_quantity) < self.min_ball:
            return WorkerResult.SUCCESS

        self.update_map_location()
        self.dump_caught_pokemon()
        pokemon_list = self.get_pokemon_from_social()
        #Temp works as it, need add more configuration
        #pokemon_list = self.get_pokemon_from_map()
        pokemon_list.sort(key=lambda x: x['dist'])
        if self.config['mode'] == 'priority':
            pokemon_list.sort(key=lambda x: x['priority'], reverse=True)
        if self.config['prioritize_vips']:
            pokemon_list.sort(key=lambda x: x['is_vip'], reverse=True)

        if len(pokemon_list) < 1:
            return WorkerResult.SUCCESS

        pokemon = pokemon_list[0]

        if self.config['snipe']:
            if self.snipe_high_prio_only:
                if self.snipe_high_prio_threshold < pokemon['priority']:
                    self.snipe(pokemon)
            else:
                return self.snipe(pokemon)

        # check for pokeballs (excluding masterball)
        # checking again as we may have lost some if we sniped
        pokeballs_quantity = inventory.items().get(POKEBALL_ID).count
        superballs_quantity = inventory.items().get(GREATBALL_ID).count
        ultraballs_quantity = inventory.items().get(ULTRABALL_ID).count

        if pokeballs_quantity + superballs_quantity + ultraballs_quantity < self.min_ball:
            return WorkerResult.SUCCESS

        nearest_fort = self.get_nearest_fort_on_the_way(pokemon)

        if nearest_fort is None :
            step_walker = self._move_to(pokemon)
            if not step_walker.step():

                if pokemon['dist'] < Constants.MAX_DISTANCE_POKEMON_IS_REACHABLE:
                    self._encountered(pokemon)
                    self.add_caught(pokemon)
                    return WorkerResult.SUCCESS
                else :
                    return WorkerResult.RUNNING

        else :
            step_walker = self._move_to_pokemon_througt_fort(nearest_fort, pokemon)
            if not step_walker or not step_walker.step():
                return WorkerResult.RUNNING

    def _emit_failure(self, msg):
        """Emits failure to event log.

        Args:
            msg: Message to emit
        """
        self.emit_event(
            'move_to_map_pokemon_fail',
            formatted='Failure! {message}',
            data={'message': msg}
        )

    def _emit_log(self, msg):
        """Emits log to event log.

        Args:
            msg: Message to emit
        """
        self.emit_event(
            'move_to_map_pokemon',
            formatted='{message}',
            data={'message': msg}
        )

    def _pokemon_event_data(self, pokemon):
        """Generates parameters used for the Bot's event manager.

        Args:
            pokemon: Pokemon object

        Returns:
            Dictionary with Pokemon's info.
        """
        now = int(time.time())
        return {
            'poke_name': pokemon['name'],
            'poke_dist': (format_dist(pokemon['dist'], self.unit)),
            'poke_lat': pokemon['latitude'],
            'poke_lon': pokemon['longitude'],
            'disappears_in': (format_time(pokemon['disappear_time'] - now))
        }

    def _teleport_to(self, pokemon):
        """Teleports trainer to a Pokemon.

        Args:
            pokemon: Pokemon to teleport to.
        """
        self.emit_event(
            'move_to_map_pokemon_teleport_to',
            formatted='Teleporting to {poke_name}. ({poke_dist})',
            data=self._pokemon_event_data(pokemon)
        )
        self.bot.api.set_position(pokemon['latitude'], pokemon['longitude'], self.alt, True)
        self._encountered(pokemon)

    def _encountered(self, pokemon):
        """Emit event when trainer encounters a Pokemon.

        Args:
            pokemon: Pokemon encountered.
        """
        self.emit_event(
            'move_to_map_pokemon_encounter',
            formatted='Encountered Pokemon: {poke_name}',
            data=self._pokemon_event_data(pokemon)
        )

    def _teleport_back(self, last_position):
        """Teleports trainer back to their last position."""
        self.emit_event(
            'move_to_map_pokemon_teleport_back',
            formatted=('Teleporting back to previous location ({last_lat}, '
                       '{last_lon})'),
            data={'last_lat': last_position[0], 'last_lon': last_position[1]}
        )

    def _move_to(self, pokemon):
        """Moves trainer towards a Pokemon.

        Args:
            pokemon: Pokemon to move to.

        Returns:
            Walker
        """
        now = int(time.time())
        self.emit_event(
            'move_to_map_pokemon_move_towards',
            formatted=('Moving towards {poke_name}, {poke_dist}, left ('
                       '{disappears_in})'),
            data=self._pokemon_event_data(pokemon)
        )
        return walker_factory(self.walker,
            self.bot,
            pokemon['latitude'],
            pokemon['longitude']
        )
    def _move_to_pokemon_througt_fort(self, fort, pokemon):
        """Moves trainer towards a fort before a Pokemon.

        Args:
            fort

        Returns:
            StepWalker
        """

        nearest_fort = fort

        lat = nearest_fort['latitude']
        lng = nearest_fort['longitude']
        fortID = nearest_fort['id']
        details = fort_details(self.bot, fortID, lat, lng)
        fort_name = details.get('name', 'Unknown')

        unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            lat,
            lng
        )

        if dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            pokemon_throught_fort_event_data = {
                'fort_name': u"{}".format(fort_name),
                'distance': format_dist(dist, unit),
                'poke_name': pokemon['name'],
                'poke_dist': (format_dist(pokemon['dist'], self.unit))
            }

            self.emit_event(
                'moving_to_pokemon_throught_fort',
                formatted="Moving towards {poke_name} - {poke_dist}  through pokestop  {fort_name} - {distance}",
                data= pokemon_throught_fort_event_data
            )
        else:
            self.emit_event(
                'arrived_at_fort',
                formatted='Arrived at fort.'
            )

	return walker_factory(self.walker,
            self.bot,
            lat,
            lng
        )

    def get_nearest_fort_on_the_way(self, pokemon):
        forts = self.bot.get_forts(order_by_distance=True)

        # Remove stops that are still on timeout
        forts = filter(lambda x: x["id"] not in self.bot.fort_timeouts, forts)
        i=0
        while i < len(forts) :
            ratio = float(self.config.get('max_extra_dist_fort', 20))
            dist_self_to_fort = distance (self.bot.position[0], self.bot.position[1], forts[i]['latitude'], forts [i]['longitude'])
            dist_fort_to_pokemon = distance (pokemon['latitude'], pokemon['longitude'], forts[i]['latitude'], forts [i]['longitude'])
            total_dist = dist_self_to_fort + dist_fort_to_pokemon
            dist_self_to_pokemon = distance (self.bot.position[0], self.bot.position[1], pokemon['latitude'], pokemon['longitude'])
            if total_dist < (1 + (ratio / 100))* dist_self_to_pokemon:
                i = i + 1
            else :
                del forts[i]
		#Return nearest fort if there are remaining
        if len(forts)> 0 :
            return forts[0]
        else :
            return None
