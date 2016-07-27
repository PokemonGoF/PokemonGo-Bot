import json

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class PokemonTransferWorker(object):
    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api
        self.metrics = bot.metrics

    def work(self):
        if not self.config.initial_transfer:
            return

        pokemon_groups = self._initial_transfer_get_groups()

        for id in pokemon_groups:

            group_cp = pokemon_groups[id].keys()

            if len(group_cp) > 1:
                group_cp.sort()
                group_cp.reverse()

                for x in range(1, len(group_cp)):
                    pokemon_name = self.pokemon_list[id - 1]['Name']
                    pokemon_cp = group_cp[x]
                    pokemon_data = pokemon_groups[id][pokemon_cp]
                    pokemon_potential = self.get_pokemon_potential(pokemon_data)
                    if self.should_release_pokemon(pokemon_name, pokemon_cp, pokemon_potential):
                        logger.log('Exchanging {} [CP {}] [Potential {}] for candy!'.format(
                            pokemon_name, pokemon_cp, pokemon_potential))
                        self.transfer_pokemon(pokemon_data['id'])
                        sleep(2)

    def release_catched_pokemon(self, pokemon_name, pokemon_to_transfer, cp, iv):
        # Transfering Pokemon
        self.transfer_pokemon(pokemon_to_transfer)
        self.metrics.released_pokemon()
        logger.log(
            '{} has been exchanged for candy!'.format(pokemon_name), 'green')
        
    def transfer_pokemon(self, pid):
         self.api.release_pokemon(pokemon_id=pid)
         response_dict = self.api.call()
         
    def _initial_transfer_get_groups(self):
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

            pokemon_data = pokemon['inventory_item_data']['pokemon_data']
            group_id = pokemon_data['pokemon_id']
            group_pokemon_cp = pokemon_data['cp']

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = {}

            pokemon_groups[group_id].update({group_pokemon_cp: pokemon_data})
        return pokemon_groups

    def get_pokemon_potential(self, pokemon_data):
        total_iv = 0
        iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
        for individual_stat in iv_stats:
            try:
                total_iv += pokemon_data[individual_stat]
            except:
                continue
        return round((total_iv / 45.0), 2)

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
            release_config = self.config.release.get('any')
        if not release_config:
            release_config = {}
        return release_config
