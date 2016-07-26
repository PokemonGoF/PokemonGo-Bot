import json

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class InitialTransferWorker(object):
    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api

    def work(self):
        if not self.config.initial_transfer:
            return

        logger.log('Cleaning up Pokemon Bag using the release CP config', 'cyan')

        pokemon_groups = self._initial_transfer_get_groups()

        for id in pokemon_groups:

            group_cp = pokemon_groups[id].keys()

            if len(group_cp) > 1:
                group_cp.sort()
                group_cp.reverse()


                for x in range(1, len(group_cp)):
                    pokemon_name = self.pokemon_list[id - 1]['Name']
                    if self.should_release_pokemon(pokemon_name, group_cp[x]):
                        logger.log('Exchanging {} with {} CP'.format(
                            pokemon_name, group_cp[x]))
                        self.api.release_pokemon(
                            pokemon_id=pokemon_groups[id][group_cp[x]])
                        response_dict = self.api.call()
                        sleep(2)

        logger.log('Pokemon Bag has been cleaned up!', 'green')

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

            group_id = pokemon['inventory_item_data'][
                'pokemon_data']['pokemon_id']
            group_pokemon = pokemon['inventory_item_data'][
                'pokemon_data']['id']
            group_pokemon_cp = pokemon[
                'inventory_item_data']['pokemon_data']['cp']

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = {}

            pokemon_groups[group_id].update({group_pokemon_cp: group_pokemon})
        return pokemon_groups

    def should_release_pokemon(self, pokemon_name, cp):
        release_config = self._get_release_config_for(pokemon_name)

        if release_config.get('never_release', False):
            return False

        if release_config.get('always_release', False):
            return True

        release_cp = release_config.get('release_below_cp', 0)
        return cp < release_cp

    def _get_release_config_for(self, pokemon):
        release_config = self.config.release.get(pokemon)
        if not release_config:
            release_config = self.config.release.get('any')
        if not release_config:
            release_config = {}
        return release_config
