
import json
from utils import distance, format_dist, i2f
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.cell_workers import PokemonCatchWorker


class CatchLuredPokemonWorker(object):
    def __init__(self, bot):
        self.bot = bot
        self.cell = bot.cell;
        self.api = bot.api
        self.config = bot.config
        self.position = bot.position

    def work(self):
        if not self.config.catch_pokemon:
            return

        lured_pokemon = self.get_lured_pokemon()
        if lured_pokemon:
            self.catch_pokemon(lured_pokemon)

    def get_lured_pokemon(self):
        forts = self.bot.get_forts(order_by_distance=True)

        if len(forts) == 0:
            return False

        fort = forts[0]

        self.api.fort_details(fort_id=fort['id'],
                              latitude=fort['latitude'],
                              longitude=fort['longitude'])

        response_dict = self.api.call()
        fort_details = response_dict.get('responses', {}).get('FORT_DETAILS', {})
        fort_name = fort_details.get('name', 'Unknown').encode('utf8', 'replace')

        encounter_id = fort.get('lure_info', {}).get('encounter_id', None)

        if encounter_id:
            logger.log('Lured pokemon at fort {}'.format(fort['id']))
            return {
                'encounter_id': encounter_id,
                'fort_id': fort['id'],
                'latitude': fort['latitude'],
                'longitude': fort['longitude']
            }

        return False

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot)
        return_value = worker.work()

        return return_value
