# -*- coding: utf-8 -*-

import os
import time
import json
import base64
import requests
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.utils import distance, format_dist, format_time
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker


class MoveToMapPokemon(BaseTask):
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
            logger.log('Could not reach PokemonGo-Map Server', 'red')
            return []

        try:
            raw_data = req.json()
        except ValueError:
            logger.log('Map data was not valid', 'red')
            return []

        pokemon_list = []
        now = int(time.time())

        for pokemon in raw_data['pokemons']:
            try:
                pokemon['encounter_id'] = long(base64.b64decode(pokemon['encounter_id']))
            except TypeError:
                log.logger('base64 error: {}'.format(pokemon['encounter_id']), 'red')
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
            logger.log('Could not reach PokemonGo-Map Server', 'red')
            return

        try:
            loc_json = req.json()
        except ValueError:
            return log.logger('Map location data was not valid', 'red')


        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            loc_json['lat'],
            loc_json['lng']
        )

        # update map when 500m away from center and last update longer than 2 minutes away
        now = int(time.time())
        if dist > 500 and now - self.last_map_update > 2 * 60:
            requests.post('{}/next_loc?lat={}&lon={}'.format(self.config['address'], self.bot.position[0], self.bot.position[1]))
            logger.log('Updated PokemonGo-Map position')
            self.last_map_update = now

    def snipe(self, pokemon):
        last_position = self.bot.position[0:2]

        self.bot.heartbeat()

        logger.log('Teleporting to {} ({})'.format(pokemon['name'], format_dist(pokemon['dist'], self.unit)), 'green')
        self.bot.api.set_position(pokemon['latitude'], pokemon['longitude'], 0)

        logger.log('Encounter pokemon', 'green')
        catch_worker = PokemonCatchWorker(pokemon, self.bot)
        api_encounter_response = catch_worker.create_encounter_api_call()

        time.sleep(2)
        logger.log('Teleporting back to previous location..', 'green')
        self.bot.api.set_position(last_position[0], last_position[1], 0)
        time.sleep(2)
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

        now = int(time.time())
        logger.log('Moving towards {}, {} left ({})'.format(pokemon['name'], format_dist(pokemon['dist'], self.unit), format_time(pokemon['disappear_time'] - now)))
        step_walker = StepWalker(
            self.bot,
            self.bot.config.walk,
            pokemon['latitude'],
            pokemon['longitude']
        )

        if not step_walker.step():
            return WorkerResult.RUNNING

        logger.log('Arrived at {}'.format(pokemon['name']))
        self.add_caught(pokemon)
        return WorkerResult.SUCCESS
