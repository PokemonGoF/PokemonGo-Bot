import json

from pokemongo_bot import logger
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.cell_workers.pokemon_catch_worker import PokemonCatchWorker
from utils import distance


class CatchVisiblePokemon(BaseTask):
    def work(self):
        if 'catchable_pokemons' in self.bot.cell and len(self.bot.cell['catchable_pokemons']) > 0:
            logger.log('Something rustles nearby!')
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            self.bot.cell['catchable_pokemons'].sort(
                key=
                lambda x: distance(self.bot.position[0], self.bot.position[1], x['latitude'], x['longitude']))

            user_web_catchable = 'web/catchable-%s.json' % self.bot.config.username
            for pokemon in self.bot.cell['catchable_pokemons']:
                with open(user_web_catchable, 'w') as outfile:
                    json.dump(pokemon, outfile)

            return self.catch_pokemon(self.bot.cell['catchable_pokemons'].pop(0))

        if 'wild_pokemons' in self.bot.cell and len(self.bot.cell['wild_pokemons']) > 0:
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            self.bot.cell['wild_pokemons'].sort(
                key=
                lambda x: distance(self.bot.position[0], self.bot.position[1], x['latitude'], x['longitude']))
            return self.catch_pokemon(self.bot.cell['wild_pokemons'].pop(0))

    def catch_pokemon(self, pokemon):
        worker = PokemonCatchWorker(pokemon, self.bot)
        return_value = worker.work()

        return return_value
