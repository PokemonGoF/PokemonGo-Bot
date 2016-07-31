from pokemongo_bot import logger
from pokemongo_bot.cell_workers.utils import fort_details
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker


class CatchLuredPokemon(object):
    def __init__(self, bot, config):
        self.bot = bot

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
        fort_name = details.get('name', 'Unknown').encode('utf8', 'replace')

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
