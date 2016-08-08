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
from pokemongo_bot.cell_workers.utils import distance, format_dist, format_time
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker


# Update the map if more than N meters away from the center. (AND'd with
# UPDATE_MAP_MIN_TIME_MINUTES)
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

        data_file = 'data/map-caught-{}.json'.format(self.bot.config.username)
        if os.path.isfile(data_file):
            self.caught = json.load(
                open(data_file)
            )

    def get_pokemon_from_map(self):
        try:
            req = requests.get('{}/raw_data?gyms=false&scanned=false'.format(self.config['address']))
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
            except TypeError:
                self._emit_failure('base64 error: {}'.format(pokemon['encounter_id']))
                continue
            pokemon['spawn_point_id'] = pokemon['spawnpoint_id']
            pokemon['disappear_time'] = int(pokemon['disappear_time'] / 1000)
            pokemon['name'] = self.pokemon_data[pokemon['pokemon_id'] - 1]['Name']
            pokemon['is_vip'] = pokemon['name'] in self.bot.config.vips

            if pokemon['name'] not in self.config['catch'] and not pokemon['is_vip']:
                continue

            if pokemon['disappear_time'] < (now + self.config['min_time']):
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
            return log.logger(err, 'red')

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
        catch_worker = PokemonCatchWorker(pokemon, self.bot)
        api_encounter_response = catch_worker.create_encounter_api_call()
        time.sleep(SNIPE_SLEEP_SEC)
        self._teleport_back(last_position)
        self.bot.api.set_position(last_position[0], last_position[1], 0)
        time.sleep(SNIPE_SLEEP_SEC)
        self.bot.heartbeat()
        catch_worker.work(api_encounter_response)
        self.add_caught(pokemon)
        return WorkerResult.SUCCESS

    def dump_caught_pokemon(self):
        user_data_map_caught = 'data/map-caught-{}.json'.format(self.bot.config.username)
        with open(user_data_map_caught, 'w') as outfile:
            json.dump(self.caught, outfile)

    def work(self):
        # check for pokeballs (excluding masterball)
        pokeballs = self.bot.item_inventory_count(1)
        superballs = self.bot.item_inventory_count(2)
        ultraballs = self.bot.item_inventory_count(3)

        if (pokeballs + superballs + ultraballs) < 1:
            return WorkerResult.SUCCESS

        self.update_map_location()
        self.dump_caught_pokemon()

        pokemon_list = self.get_pokemon_from_map()
        pokemon_list.sort(key=lambda x: x['dist'])
        if self.config['mode'] == 'priority':
            pokemon_list.sort(key=lambda x: x['priority'], reverse=True)
        if self.config['prioritize_vips']:
            pokemon_list.sort(key=lambda x: x['is_vip'], reverse=True)

        if len(pokemon_list) < 1:
            return WorkerResult.SUCCESS

        pokemon = pokemon_list[0]

        # if we only have ultraballs and the target is not a vip don't snipe/walk
        if (pokeballs + superballs) < 1 and not pokemon['is_vip']:
            return WorkerResult.SUCCESS

        if self.config['snipe']:
            return self.snipe(pokemon)

        step_walker = self._move_to(pokemon)
        if not step_walker.step():
            return WorkerResult.RUNNING
        self._encountered(pokemon)
        self.add_caught(pokemon)
        return WorkerResult.SUCCESS

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
        self.bot.api.set_position(pokemon['latitude'], pokemon['longitude'], 0)
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
            StepWalker
        """
        now = int(time.time())
        self.emit_event(
            'move_to_map_pokemon_move_towards',
            formatted=('Moving towards {poke_name}, {poke_dist}, left ('
                       '{disappears_in})'),
            data=self._pokemon_event_data(pokemon)
        )
        return StepWalker(
            self.bot,
            self.bot.config.walk,
            pokemon['latitude'],
            pokemon['longitude']
        )
