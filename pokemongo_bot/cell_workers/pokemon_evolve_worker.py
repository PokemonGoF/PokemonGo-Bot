# -*- coding: utf-8 -*-

from sets import Set
from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from utils import calc_iv_percent

class PokemonEvolveWorker(object):
    def __init__(self, bot):
        self.api = bot.api
        self.config = bot.config
        self.bot = bot

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
            evolve_list = self._sort_by_cp(response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items'])
            if self.config.evolve_all[0] != 'all':
                # filter out non-listed pokemons
                evolve_list = [x for x in evolve_list if str(x[1]) in self.config.evolve_all]
            
            ## enable to limit number of pokemons to evolve. Useful for testing.
            # nn = 1
            # if len(evolve_list) > nn:
            #     evolve_list = evolve_list[:nn]
            ##

            id_list1 = self.count_pokemon_inventory()
            for pokemon in evolve_list:
                try:
                    self._execute_pokemon_evolve(pokemon, cache)
                except:
                    pass
            id_list2 = self.count_pokemon_inventory()
            release_cand_list_ids = list(Set(id_list2) - Set(id_list1))

            if release_cand_list_ids:
                print('[#] Evolved {} pokemons! Checking if any of them needs to be released ...'.format(
                    len(release_cand_list_ids)
                ))

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
                        pokemon['cp'],
                        calc_iv_percent(pokemon)
                        ])
                except:
                    pass

        pokemons.sort(key=lambda x: x[2], reverse=True)
        return pokemons

    def _execute_pokemon_evolve(self, pokemon, cache):
        pokemon_id = pokemon[0]
        pokemon_name = pokemon[1]
        pokemon_cp = pokemon[2]

        if pokemon_name in cache:
            return

        self.api.evolve_pokemon(pokemon_id=pokemon_id)
        response_dict = self.api.call()
        status = response_dict['responses']['EVOLVE_POKEMON']['result']
        if status == 1:
            print('[#] Successfully evolved {} with {} cp!'.format(
                pokemon_name, pokemon_cp
            ))
        else:
            # cache pokemons we can't evolve. Less server calls
            cache[pokemon_name] = 1
        sleep(5.7)

    def count_pokemon_inventory(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        id_list = []
        return self.counting_pokemon(response_dict, id_list)

    def counting_pokemon(self, response_dict, id_list):
        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                           "inventory_item_data", "pokemon_data"], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon_data']
                    if pokemon.get('is_egg', False):
                        continue
                    id_list.append(pokemon['id'])

        return id_list
