# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.item_list import Item
from pokemongo_bot import inventory
from utils import fort_details, distance
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.constants import Constants


class CatchPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def work(self):
        if sum([inventory.items().get(ball.value).count for ball in 
            [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]]) <= 0:
            return WorkerResult.ERROR

        pokemon = []
        if self.config.get('catch_visible_pokemon', True):
            pokemon = self.get_visible_pokemon()
        if self.config.get('catch_lured_pokemon', True):
            pokemon += self.get_lured_pokemon()

        num_pokemon = len(pokemon)
        if num_pokemon > 0:
            pokemon = self.sort_pokemon(pokemon)
            
            if self.catch_pokemon(pokemon[0]) == WorkerResult.ERROR:
                return WorkerResult.ERROR
            elif num_pokemon > 1:
                return WorkerResult.RUNNING

        return WorkerResult.SUCCESS

    def get_visible_pokemon(self):
        pokemon_to_catch = []
        if 'catchable_pokemons' in self.bot.cell:
            pokemon_to_catch = self.bot.cell['catchable_pokemons']

            if len(pokemon_to_catch) > 0:
    		    # Update web UI
    		    user_web_catchable = os.path.join(_base_dir, 'web', 'catchable-{}.json'.format(self.bot.config.username))
    		    for pokemon in pokemon_to_catch:
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
    		            }
    		        )

        if 'wild_pokemons' in self.bot.cell:
            pokemon_to_catch += self.bot.cell['wild_pokemons']

        return pokemon_to_catch

    def get_lured_pokemon(self):
        forts_in_range = []
        pokemon_to_catch = []
        forts = self.bot.get_forts(order_by_distance=True)

        if len(forts) == 0:
            return []

        for fort in forts:
            distance_to_fort = distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            )

            encounter_id = fort.get('lure_info', {}).get('encounter_id', None)
            if distance_to_fort < Constants.MAX_DISTANCE_FORT_IS_REACHABLE and encounter_id:
                forts_in_range.append(fort)


        for fort in forts_in_range:
            details = fort_details(self.bot, fort_id=fort['id'],
                                  latitude=fort['latitude'],
                                  longitude=fort['longitude'])
            fort_name = details.get('name', 'Unknown')
            encounter_id = fort['lure_info']['encounter_id']

            result = {
                'encounter_id': encounter_id,
                'fort_id': fort['id'],
                'fort_name': u"{}".format(fort_name),
                'latitude': fort['latitude'],
                'longitude': fort['longitude']
            }
            pokemon_to_catch.append(result)

            self.emit_event(
                'lured_pokemon_found',
                level='info',
                formatted='Lured pokemon at fort {fort_name} ({fort_id})',
                data=result
            )
        return pokemon_to_catch

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot, self.config)
        return_value = worker.work()

        return return_value
        
    def sort_pokemon(self, pokemon_list):
        # Sort all by distance from current pos- eventually this should
        # build graph & A* it
        pokemon_list.sort(
            key=
            lambda x: distance(self.bot.position[0], self.bot.position[1], x['latitude'], x['longitude'])
        )
        
        return pokemon_list
