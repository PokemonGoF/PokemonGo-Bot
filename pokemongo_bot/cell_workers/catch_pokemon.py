# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import random

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.item_list import Item
from pokemongo_bot import inventory
from utils import fort_details, distance
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.constants import Constants
from pokemongo_bot.inventory import Pokemons, Pokemon, Attack


class CatchPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.pokemon = []

    def work(self):
        # make sure we have SOME balls
        if sum([inventory.items().get(ball.value).count for ball in 
            [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]]) <= 0:
            return WorkerResult.ERROR

        # check if we have already loaded a list
        if len(self.pokemon) <= 0:
            # load available pokemon by config settings
            if self.config.get('catch_visible_pokemon', True):
                self.get_visible_pokemon()
            if self.config.get('catch_lured_pokemon', True):
                self.get_lured_pokemon()

            random.shuffle(self.pokemon)

        num_pokemon = len(self.pokemon)
        if num_pokemon > 0:
            # try catching
            if self.catch_pokemon(self.pokemon.pop()) == WorkerResult.ERROR:
                # give up incase something went wrong in our catch worker (ran out of balls, etc)
                return WorkerResult.ERROR
            elif num_pokemon > 1:
                # we have more pokemon to catch
                return WorkerResult.RUNNING

        # all pokemon have been processed
        return WorkerResult.SUCCESS

    def get_visible_pokemon(self):
        pokemon_to_catch = []
        if 'catchable_pokemons' in self.bot.cell:
            pokemon_to_catch = self.bot.cell['catchable_pokemons']

            if len(pokemon_to_catch) > 0:
    		user_web_catchable = os.path.join(_base_dir, 'web', 'catchable-{}.json'.format(self.bot.config.username))
    		for pokemon in pokemon_to_catch:

    	            # Update web UI
    		    with open(user_web_catchable, 'w') as outfile:
    		        json.dump(pokemon, outfile)

    		    self.emit_event(
    		        'catchable_pokemon',
    		        level='debug',
    		        data={
    		            'pokemon_id': pokemon['pokemon_id'],
    		            'spawn_point_id': pokemon['spawn_point_id'],
    		            'encounter_id': pokemon['encounter_id'],
    		            'latitude': pokemon['latitude'],
    		            'longitude': pokemon['longitude'],
    		            'expiration_timestamp_ms': pokemon['expiration_timestamp_ms'],
    		            'pokemon_name': Pokemons.name_for(pokemon['pokemon_id']),
    		        }
    		    )

                    self.add_pokemon(pokemon)

        if 'wild_pokemons' in self.bot.cell:
            for pokemon in self.bot.cell['wild_pokemons']:
                self.add_pokemon(pokemon)

    def get_lured_pokemon(self):
        forts_in_range = []
        forts = self.bot.get_forts(order_by_distance=False)

        if len(forts) == 0:
            return []

        for fort in forts:
            distance_to_fort = distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            )

            # See if we have an encounter at this fort
            encounter_id = fort.get('lure_info', {}).get('encounter_id', None)
            if distance_to_fort < Constants.MAX_DISTANCE_FORT_IS_REACHABLE and encounter_id:
                forts_in_range.append(fort)


        for fort in forts_in_range:
            details = fort_details(self.bot, fort_id=fort['id'],
                                  latitude=fort['latitude'],
                                  longitude=fort['longitude'])
            fort_name = details.get('name', 'Unknown')
            encounter_id = fort['lure_info']['encounter_id']

            pokemon = {
                'encounter_id': encounter_id,
                'fort_id': fort['id'],
                'fort_name': u"{}".format(fort_name),
                'latitude': fort['latitude'],
                'longitude': fort['longitude']
            }

            self.emit_event(
                'lured_pokemon_found',
                level='info',
                formatted='Lured pokemon at fort {fort_name} ({fort_id})',
                data=pokemon
            )

            self.add_pokemon(pokemon)

    def add_pokemon(self, pokemon):
        if pokemon['encounter_id'] not in self.pokemon:
            self.pokemon.append(pokemon)

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot, self.config)
        return_value = worker.work()

        return return_value
