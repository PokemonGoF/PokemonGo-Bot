# -*- coding: utf-8 -*-

import json
from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from utils import calc_iv_percent

class PokemonReleaseWorker(object):
    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api

    def work(self):       
        pokemons = self._get_pokemon()
        for id, pokemon in pokemons.iteritems():
            name = self.pokemon_list[pokemon['species'] - 1]['Name']
            if not self.should_release_pokemon(name, pokemon['cp'], pokemon['iv']):
                continue

            logger.log('Releasing {} (CP:{} IV:{}) for candy!'.format(name, pokemon['cp'], pokemon['iv']), 'green')
            self.api.release_pokemon(pokemon_id=id)
            response_dict = self.api.call()
            sleep(2)

    def _get_pokemon(self):
        self.api.get_player().get_inventory()
        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        
        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        pokemon = {}
        for item in inventory_dict:
            try:
                reduce(dict.__getitem__, ["inventory_item_data", "pokemon_data", "pokemon_id"], item)
            except KeyError:
                continue
            
            id = item['inventory_item_data']['pokemon_data']['id']
            pokemon.update({id: {
                'species': item['inventory_item_data']['pokemon_data']['pokemon_id'],
                'cp': item['inventory_item_data']['pokemon_data']['cp'],
                'iv': calc_iv_percent(item['inventory_item_data']['pokemon_data'])
            }})
        
        return pokemon

    def should_release_pokemon(self, pokemon_name, cp, iv):
        release_config = self._get_release_config_for(pokemon_name)
        cp_iv_logic = release_config.get('logic')
        if not cp_iv_logic:
            cp_iv_logic = self._get_release_config_for('any').get('logic', 'and')

        release_results = {
            'cp': False,
            'iv': False,
        }
        
        if release_config.get('never_release', False):
            return False

        if release_config.get('always_release', False):
            return True

        release_cp = release_config.get('release_below_cp', 0)
        if cp < release_cp:
            release_results['cp'] = True

        release_iv = release_config.get('release_below_iv', 0)
        if iv < release_iv:
            release_results['iv'] = True

        logic_to_function = {
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y
        }

        #logger.log(
        #    "Release config for {}: CP {} {} IV {}".format(
        #        pokemon_name,
        #        min_cp,
        #        cp_iv_logic,
        #        min_iv
        #    ), 'yellow'
        #)

        return logic_to_function[cp_iv_logic](*release_results.values())

    def _get_release_config_for(self, pokemon):
        release_config = self.config.release.get(pokemon)
        if not release_config:
            release_config = self.config.release['any']
        return release_config
