# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.constants import Constants
from pokemongo_bot.cell_workers.utils import fort_details, distance
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker


class CatchLuredPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.encountered = [None] * 10

    def add_encountered(self, pokemon):
        self.encountered = self.encountered[1:] + [pokemon['encounter_id']]

    def was_encountered(self, pokemon):
        if pokemon['encounter_id'] in self.encountered:
            return True
        return False

    def work(self):
        lured_pokemon = self.get_lured_pokemon()
        if len(lured_pokemon) > 0:
            for pokemon in lured_pokemon:
                if not self.was_encountered(pokemon):
                    self.catch_pokemon(pokemon)
                    self.add_encountered(pokemon)
                    return WorkerResult.RUNNING

        return WorkerResult.SUCCESS

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
