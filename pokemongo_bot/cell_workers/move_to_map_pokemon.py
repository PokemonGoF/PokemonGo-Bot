# -*- coding: utf-8 -*-

import time
import base64
import requests
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.utils import distance, format_dist, format_time
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker


class MoveToMapPokemon(BaseTask):
    def initialize(self):
        self.last_map_update = 0
        self.pokemon_data = self.bot.pokemon_list
        self.caught = []
        self.seen = []
        self.unit = self.bot.config.distance_unit

    def get_pokemon_from_map(self):
        try:
            req = requests.get('{}/raw_data?gyms=false&scanned=false'.format(self.config['address']))
        except requests.exceptions.ConnectionError:
            logger.log('Could not reach PokemonGo-Map Server', color='red')
            return []

        raw_data = req.json()

        pokemon_list = []
        now = int(time.time())

        for pokemon in raw_data['pokemons']:
            pokemon['encounter_id'] = long(base64.b64decode(pokemon['encounter_id']))
            pokemon['spawn_point_id'] = pokemon['spawnpoint_id']
            pokemon['disappear_time'] = int(pokemon['disappear_time'] / 1000)
            pokemon['name'] = self.pokemon_data[pokemon['pokemon_id'] - 1]['Name']
            pokemon['is_vip'] = pokemon['name'] in self.bot.config.vips

            if pokemon['name'] not in self.config['catch'] and pokemon['name'] not in self.bot.config.vips:
                continue

            if pokemon['disappear_time'] < (now + self.config['min_time']):
                continue

            if self.was_caught(pokemon):
                continue

            if pokemon['name'] in self.config['catch']:
                pokemon['priority'] = self.config['catch'][pokemon['name']]
            else:
                pokemon['priority'] = 0

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

    def add_seen(self, pokemon):
        for seen_pokemon in self.seen:
            if seen_pokemon['encounter_id'] == pokemon['encounter_id']:
                return
        if len(self.seen) >= 200:
            self.seen.pop(0)
        self.seen.append(pokemon)

    def remove_seen(self, pokemon):
        for idx in xrange(len(self.seen)):
            if self.seen[idx]['encounter_id'] == pokemon['encounter_id']:
                del self.seen[idx]
                return

    def update_map_location(self):
        if not self.config['update_map']:
            return
        try:
            req = requests.get('{}/loc'.format(self.config['address']))
        except requests.exceptions.ConnectionError:
            logger.log('Could not reach PokemonGo-Map Server', color='red')
            return
        loc_json = req.json()

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
        self.bot.check_session(last_position)
        self.bot.heartbeat()

        logger.log('Teleporting to {} ({})'.format(pokemon['name'], format_dist(pokemon['dist'], self.unit)), 'green')
        self.bot.api.set_position(pokemon['latitude'], pokemon['longitude'], 0)

        logger.log('Encounter pokemon', 'green')
        catch_worker = PokemonCatchWorker(pokemon, self.bot)
        api_encounter_response = catch_worker.create_encounter_api_call()

        time.sleep(2)
        logger.log('Teleport back to previous location..', 'green')
        self.bot.api.set_position(last_position[0], last_position[1], 0)
        time.sleep(2)
        self.bot.heartbeat()

        catch_worker.work(api_encounter_response)
        self.add_caught(pokemon)

        return WorkerResult.SUCCESS


    def work(self):
        self.update_map_location()

        # remove caught pokemon from candidates
        if not self.config['snipe']:
            cell = self.bot.get_meta_cell()
            for catchable_pokemon in cell['catchable_pokemons']:
                self.add_seen(catchable_pokemon)

            for seen_pokemon in self.seen:
                caught = True
                for catchable_pokemon in self.bot.cell['catchable_pokemons']:
                    if catchable_pokemon['encounter_id'] == seen_pokemon['encounter_id']:
                        caught = False
                        break
                if caught:
                    self.remove_seen(seen_pokemon)
                    self.add_caught(seen_pokemon)

        pokemon_list = self.get_pokemon_from_map()
        pokemon_list.sort(key=lambda x: x['dist'])
        if self.config['mode'] == 'priority':
            pokemon_list.sort(key=lambda x: x['priority'], reverse=True)
        if self.config['prioritize_vips'] == 'priority':
            pokemon_list.sort(key=lambda x: x['is_vip'])

        if len(pokemon_list) < 1:
            return WorkerResult.SUCCESS

        pokemon = pokemon_list[0]

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
