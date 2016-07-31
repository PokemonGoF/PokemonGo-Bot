# -*- coding: utf-8 -*-

import json
import time
import requests
import base64
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.utils import distance, i2f, format_dist, format_time
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemon_catch_worker import PokemonCatchWorker


class MoveToMapPokemon(BaseTask):
    def initialize(self):
        self.last_map_update = 0
        self.pokemon_data = self.bot.pokemon_list
        self.caught = []
        self.unit = self.bot.config.distance_unit

    def get_pokemon_from_map(self):
        try:
            r = requests.get('{}/raw_data?gyms=false&scanned=false'.format(self.config['address']))
        except:
            logger.log('Could not reach PokemonGo-Map Server', color='red')
            return []

        raw_data = r.json()

        pokemon_list = []
        now = int(time.time())

        for pokemon in raw_data['pokemons']:
            pokemon['encounter_id'] = long(base64.b64decode(pokemon['encounter_id']))
            pokemon['spawn_point_id'] = pokemon['spawnpoint_id']
            pokemon['disappear_time'] = int(pokemon['disappear_time'] / 1000)
            pokemon['name'] = self.pokemon_data[pokemon['pokemon_id'] - 1]['Name']
            pokemon['is_vip'] = pokemon['name'] in self.bot.config.vips

            if (pokemon['name'] not in self.config['catch']):
                continue

            if pokemon['disappear_time'] < (now + self.config['min_time']):
                continue

            if pokemon['encounter_id'] in self.caught:
                continue

            pokemon['priority'] = self.config['catch'][pokemon['name']]

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

    def addCaught(self, pokemon):
        if len(self.caught) >= 200:
            self.caught.pop(0)
        self.caught.append(pokemon['encounter_id'])

    def update_map_location(self):
        try:
            r = requests.get('{}/loc'.format(self.config['address']))
        except:
            logger.log('Could not reach PokemonGo-Map Server', color='red')
            return
        j = r.json()

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            j['lat'],
            j['lng']
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
        catchWorker = PokemonCatchWorker(pokemon, self.bot)
        apiEncounterResponse = catchWorker.create_encounter_api_call()

        time.sleep(2)
        logger.log('Teleport back to previous location..', 'green')
        self.bot.api.set_position(last_position[0], last_position[1], 0)
        time.sleep(2)
        self.bot.heartbeat()

        catchWorker.work(apiEncounterResponse)
        self.addCaught(pokemon)

        return WorkerResult.SUCCESS


    def work(self):
        self.update_map_location()

        pokemon_list = self.get_pokemon_from_map()
        pokemon_list.sort(key=lambda x: x['dist'])
        if self.config['mode'] == 'priority':
            pokemon_list.sort(key=lambda x: x['priority'], reverse=True)
        if self.config['prioritize_vips'] == 'priority':
            pokemon_list.sort(key=lambda x: x['is_vip'])

        if (len(pokemon_list) < 1):
            return WorkerResult.SUCCESS

        pokemon = pokemon_list[0]

        if 'catchable_pokemons' in self.bot.cell and len(self.bot.cell['catchable_pokemons']) > 0:
            for catchable_pokemon in self.bot.cell['catchable_pokemons']:
                if pokemon['encounter_id'] == catchable_pokemon['encounter_id']:
                    self.addCaught(pokemon)
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
        self.addCaught(pokemon)
        return WorkerResult.SUCCESS