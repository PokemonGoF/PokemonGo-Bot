# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pokemongo_bot.cell_workers.utils import fort_details
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from pokemongo_bot.base_task import BaseTask


class CatchLuredPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def work(self):
        lured_pokemon = self.get_lured_pokemon()
        if lured_pokemon:
            self.catch_pokemon(lured_pokemon)

    def get_lured_pokemon(self):
        forts = self.bot.get_forts(order_by_distance=True)

        if len(forts) == 0:
            return False

        fort = forts[0]
        details = fort_details(self.bot, fort_id=fort['id'],
                              latitude=fort['latitude'],
                              longitude=fort['longitude'])
        fort_name = details.get('name', 'Unknown')

        encounter_id = fort.get('lure_info', {}).get('encounter_id', None)

        if encounter_id:
            result = {
                'encounter_id': encounter_id,
                'fort_id': fort['id'],
                'fort_name': u"{}".format(fort_name),
                'latitude': fort['latitude'],
                'longitude': fort['longitude']
            }

            self.emit_event(
                'lured_pokemon_found',
                formatted='Lured pokemon at fort {fort_name} ({fort_id})',
                data=result
            )
            return result

        return False

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot)
        return_value = worker.work()

        return return_value
