# -*- coding: utf-8 -*-
import time

from __future__ import unicode_literals

from pokemongo_bot.constants import Constants
from pokemongo_bot.cell_workers.utils import fort_details, distance
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from pokemongo_bot.cell_workers.base_task import BaseTask


class CatchLuredPokemon(BaseTask):
    def work(self, *args, **kwargs):
        lured_pokemon = self.get_lured_pokemon()
        if lured_pokemon:
            self.catch_pokemon(lured_pokemon)

    def get_lured_pokemon(self):
        forts = self.bot.get_forts(order_by_distance=True)

        forts_in_range = []

        for fort in forts:
            distance_to_fort = distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            )

            if distance_to_fort <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
                forts_in_range.append(fort)

        forts_with_lured_pokemons = [fort for fort in forts_in_range if fort.get('lure_info', {}).get('encounter_id', None)]

        for fort in forts_with_lured_pokemons:
            encounter_id = fort.get('lure_info', {}).get('encounter_id', None)

            if encounter_id:
                self.catch_pokemon({
                    'encounter_id': encounter_id,
                    'fort_id': fort['id'],
                    'latitude': fort['latitude'],
                    'longitude': fort['longitude']
                })

            time.sleep(1)

        return False

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot)
        return_value = worker.work()

        return return_value
