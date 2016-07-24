from utils import distance, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class EvolveAllWorker(object):
    def __init__(self, bot):
        self.api = bot.api
        self.config = bot.config
        # self.stepper = bot.stepper
        # self.position = bot.position

    def work(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        cache = {}

        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            self._sort_by_cp(response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items'])
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                           "inventory_item_data", "pokemon_data"], item)
                except KeyError:
                    pass
                else:
                    try:
                        pokemon = item['inventory_item_data']['pokemon_data']
                        # TODO: reenable
                        # self._execute_pokemon_evolve(pokemon, cache)
                        # sleep(1.2)
                    except:
                        pass

    def _sort_by_cp(self, inventory_items):
        pokemons = []
        for item in inventory_items:
            try:
                reduce(dict.__getitem__, [
                       "inventory_item_data", "pokemon_data"], item)
            except KeyError:
                pass
            else:
                try:
                    pokemon = item['inventory_item_data']['pokemon_data']
                    pokemon_num = int(pokemon['pokemon_id']) - 1
                    pokemon_name = self.bot.pokemon_list[int(pokemon_num)]['Name']
                    pokemons.append([
                        pokemon['id'],
                        pokemon_name,
                        pokemon['cp']
                        ])
                except:
                    pass

        pokemons.sort(key=lambda x: x[2], reverse=True)
        ## TODO: remove temp
        print
        print
        for p in pokemons:
            print p
        print
        print
        ##
        return pokemons



    def _execute_pokemon_evolve(self, pokemon, cache):
        pokemon_num = int(pokemon['pokemon_id']) - 1
        pokemon_name = self.bot.pokemon_list[
            int(pokemon_num)]['Name']
        if pokemon_name in cache:
            return

        self.api.evolve_pokemon(pokemon_id=pokemon['id'])
        response_dict = self.api.call()
        status = response_dict['responses']['EVOLVE_POKEMON']['result']
        if status == 1:
            print('[#] Successfully evolved {}!'.format(
                pokemon_name
            ))
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon_name] = 1
