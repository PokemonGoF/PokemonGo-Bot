import json
import time
import pprint

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class InitialTransferWorker(object):
    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api

    def work(self):
        logger.log('Cleaning up Pokemon Bag using release criteria in config.json', 'cyan')

        id_list = self.count_pokemon_inventory()
        for pokemon in id_list:
            if 'cp' not in pokemon:
                continue

            pokemon_num = int(pokemon['pokemon_id']) - 1
            pokemon_name = self.pokemon_list[int(pokemon_num)]['Name']
            cp = pokemon['cp']
            total_IV=0
            iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
            for individual_stat in iv_stats:
                try:
                    total_IV += pokemon[individual_stat]
                except:
                    pokemon[individual_stat] = 0
                    continue
            pokemon_potential = round((total_IV / 45.0), 2)
            
            if self.should_release_pokemon(pokemon_name, cp, pokemon_potential):
                # Transfering Pokemon
                self.transfer_pokemon(pokemon['id'])
                logger.log('{} @ CP: {} with Potential:{} has been exchanged for candy!'.format(pokemon_name, cp, pokemon_potential), 'green')
                time.sleep(1.2)
        
        logger.log('Pokemon Bag has been cleaned up!', 'green')

    def _initial_transfer_get_pokemon(self):
        pokemon_groups = {}
        self.api.get_player().get_inventory()
        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']

        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        for pokemon in inventory_dict:
            try:
                reduce(dict.__getitem__, [
                    "inventory_item_data", "pokemon_data", "pokemon_id"
                ], pokemon)
            except KeyError:
                continue

            group_id = pokemon['inventory_item_data'][
                'pokemon_data']['pokemon_id']
            group_pokemon = pokemon['inventory_item_data'][
                'pokemon_data']['id']
            group_pokemon_cp = pokemon[
                'inventory_item_data']['pokemon_data']['cp']

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = {}

            pokemon_groups[group_id].update({group_pokemon_cp: group_pokemon})
        return inventory_dict

    def _execute_pokemon_transfer(self, value, pokemon):
        if 'cp' in pokemon and pokemon['cp'] < value:
            self.api.release_pokemon(pokemon_id=pokemon['id'])
            response_dict = self.api.call()

    def transfer_pokemon(self, pid):
        self.api.release_pokemon(pokemon_id=pid)
        response_dict = self.api.call()

    def count_pokemon_inventory(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        id_list = []
        return self._counting_pokemon(response_dict, id_list)

    def _counting_pokemon(self, response_dict, id_list):
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
                    id_list.append(pokemon)

        return id_list
      

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

        release_cp = release_config.get('release_under_cp', 0)
        if cp < release_cp:
            release_results['cp'] = True

        release_iv = release_config.get('release_under_iv', 0)
        if iv < release_iv:
            release_results['iv'] = True

        logic_to_function = {
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y
        }

        #logger.log(
        #    "Release config for {}: CP {} {} IV {}".format(
        #        pokemon_name,
        #        release_cp,
        #        cp_iv_logic,
        #        release_iv
        #    ), 'yellow'
        #)

        return logic_to_function[cp_iv_logic](*release_results.values())

    def _get_release_config_for(self, pokemon):
        release_config = self.config.release.get(pokemon)
        if not release_config:
            release_config = self.config.release['any']
        return release_config
