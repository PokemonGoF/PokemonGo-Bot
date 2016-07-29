
import json
from utils import distance, format_dist, i2f
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.cell_workers import PokemonCatchWorker

class CatchVisiblePokemonWorker(object):
    def __init__(self, bot):
        self.bot = bot
        self.cell = bot.cell;
        self.api = bot.api
        self.config = bot.config
        self.position = bot.position

    def work(self):
        if not self.config.catch_pokemon:
            return

        if 'catchable_pokemons' in self.cell and len(self.cell['catchable_pokemons']) > 0:
            logger.log('Something rustles nearby!')
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            self.cell['catchable_pokemons'].sort(
                key=
                lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))

            user_web_catchable = 'web/catchable-%s.json' % (self.config.username)
            for pokemon in self.cell['catchable_pokemons']:
                with open(user_web_catchable, 'w') as outfile:
                    json.dump(pokemon, outfile)

                with open(user_web_catchable, 'w') as outfile:
                    json.dump({}, outfile)

            return self.catch_pokemon(self.cell['catchable_pokemons'][0])

        if 'wild_pokemons' in self.cell and len(self.cell['wild_pokemons']) > 0:
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            self.cell['wild_pokemons'].sort(
                key=
                lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
            return self.catch_pokemon(self.cell['wild_pokemons'][0])

        lured_pokemon = self.get_lured_pokemon()
        if lured_pokemon:
            self.catch_pokemon(lured_pokemon)

    def get_lured_pokemon(self):
        forts = self.bot.get_forts(order_by_distance=True)
        fort = forts[0]

        self.api.fort_details(fort_id=self.fort['id'],
                              latitude=lat,
                              longitude=lng)
        response_dict = self.api.call()
        fort_details = response_dict.get('responses', {}).get('FORT_DETAILS', {})
        fort_name = fort_details.get('name', 'Unknown').encode('utf8', 'replace')

        encounter_id = fort.get('lure_info', {}).get('encounter_id', None)

        pokemon = {
            'encounter_id': encounter_id,
            'fort_id': fort['id'],
            'latitude': fort['latitude'],
            'longitude': fort['longitude']
        }

        return pokmeon

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot)
        return_value = worker.work()

        return return_value
