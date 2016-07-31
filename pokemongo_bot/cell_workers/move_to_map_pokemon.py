# -*- coding: utf-8 -*-

import json
import time
import sqlite3
import requests
import base64
from pokemongo_bot import logger
from pokemongo_bot.cell_workers.utils import distance, i2f, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemon_catch_worker import PokemonCatchWorker


class MoveToMapPokemon(object):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.last_map_update = 0
        self.db = self.load_db()
        self.pokemon_data = bot.pokemon_list
        self.caught = []
        self.unit = self.bot.config.distance_unit

    def load_db(self):
        if self.config['db_file'] == None:
            raise RuntimeError('You need to specify a db file (sqlite)')

        try:
            conn = sqlite3.connect(self.config['db_file'])
        except:
            raise RuntimeError('Could not open db file "{}"'.format(self.config['db_file']))
        return conn

    def get_pokemon_from_map(self):
        cursor = self.db.cursor()

        pokemon_list = []

        now = int(time.time() + self.config['min_time'])
        for row in cursor.execute('SELECT * FROM pokemon WHERE datetime(disappear_time) > datetime(?, "unixepoch");', (now, )):
            encounter_id = long(base64.b64decode(row[0]))
            spawn_point_id = row[1]
            pokemon_id = row[2]
            lat = row[3]
            lon = row[4]

            dist = distance(
                self.bot.position[0],
                self.bot.position[1],
                lat,
                lon
            )

            if dist > self.config['max_distance'] and self.config['mode'] != 'snipe':
                continue

            if encounter_id in self.caught:
                continue

            pokemon_list.append({
                'encounter_id': encounter_id,
                'spawn_point_id': spawn_point_id,
                'pokemon_id': pokemon_id,
                'lat': lat,
                'lon': lon,
                'dist': dist
            })

        cursor.close()
        return pokemon_list

    def get_name_from_id(self, pokemon_id):
        return self.pokemon_data[pokemon_id - 1]['Name']

    def is_vip(self, pokemon_id):
        return self.get_name_from_id(pokemon_id) in self.bot.config.vips

    def get_config_priority(self, pokemon_id):
        if (self.get_name_from_id(pokemon_id) in self.config['priority']):
            return self.config['priority'][self.get_name_from_id(pokemon_id)]
        else:
            return 0

    def addCaught(self, pokemon):
        if len(self.caught) >= 200:
            self.caught.pop(0)
        self.caught.append(pokemon['encounter_id'])

    def score_pokemon(self, pokemon_list):
        new_list = []
        has_vips = False
        for pokemon in pokemon_list:
            if self.config['prioritize_vips'] and self.is_vip(pokemon['pokemon_id']):
                has_vips = True
                break

        for pokemon in pokemon_list:
            score = 0
            if self.is_vip(pokemon['pokemon_id']):
                score += 10000
            if self.config['mode'] == 'distance':
                score -= pokemon['dist']
            elif self.config['mode'] == 'priority':
                score += self.get_config_priority(pokemon['pokemon_id'])
            elif self.config['mode'] == 'hybrid':
                score += self.get_config_priority(pokemon['pokemon_id'])
                score -= pokemon['dist']

            pokemon['name'] = self.get_name_from_id(pokemon['pokemon_id'])
            pokemon['score'] = score

            if self.config['mode'] == 'priority' and pokemon['score'] < 1:
                continue

            if pokemon['name'] in self.config['ignore']:
                continue

            if has_vips:
                if not self.is_vip(pokemon['pokemon_id']):
                    pokemon['score'] = 0

            new_list.append(pokemon)
        return new_list

    def update_map_location(self):
        r = requests.get('{}/loc'.format(self.config['address']))
        if r.status_code != 200:
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
        self.bot.api.set_position(pokemon['lat'], pokemon['lon'], 0)
        cell = self.bot.get_meta_cell()

        logger.log('Encounter pokemon', 'green')
        pokemon['latitude'] = pokemon['lat']
        pokemon['longitude'] = pokemon['lon']
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

        if 'catched_pokemon' in self.bot.passon:
            self.addCaught(self.bot.passon['catched_pokemon'])
            del self.bot.passon['catched_pokemon']
            return WorkerResult.SUCCESS

        pokemon_on_map = self.get_pokemon_from_map()
        pokemon_on_map = self.score_pokemon(pokemon_on_map)
        pokemon_on_map.sort(key=lambda x: x['score'], reverse=True)

        if (len(pokemon_on_map) < 1):
            return

        pokemon = pokemon_on_map[0]
        now = int(time.time())

        if self.bot.config.walk <= 0 or self.config['snipe']:
            return self.snipe(pokemon)

        logger.log('Moving towards {}, {} left'.format(pokemon['name'], format_dist(pokemon['dist'], self.unit)))
        step_walker = StepWalker(
            self.bot,
            self.bot.config.walk,
            pokemon['lat'],
            pokemon['lon']
        )

        if not step_walker.step():
            return WorkerResult.RUNNING

        logger.log('Arrived at {}'.format(pokemon['name']))
        self.addCaught(pokemon)
        return WorkerResult.SUCCESS