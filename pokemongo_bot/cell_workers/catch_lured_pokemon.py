# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.constants import Constants
from pokemongo_bot.cell_workers.utils import fort_details, distance
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker

ENOUGH_POKEBALL_FOR_ALL = 1
ENOUGH_POKEBALL_FOR_VIP = 2
NOT_ENOUGH_POKEBALL = 3

class CatchLuredPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def work(self):
        lured_pokemon = self.get_lured_pokemon()

        enough_pokeball_for = self._check_enough_pokeball()
        if enough_pokeball_for == NOT_ENOUGH_POKEBALL:
            return WorkerResult.SUCCESS
        elif enough_pokeball_for == ENOUGH_POKEBALL_FOR_VIP:
            lured_vip_pokemon = []
            for pokemon in lured_pokemon:
                if(self._is_vip_pokemon(pokemon)):
                    lured_vip_pokemon.append(pokemon)
            lured_pokemon = lured_vip_pokemon

        if len(lured_pokemon) > 0:
            self.catch_pokemon(lured_pokemon[0])

            if len(lured_pokemon) > 1:
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
