import json

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class InitialTransferWorker(object):
    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api

    def work(self):
        logger.log('[x] Initial Transfer.')

        logger.log(
        '[x] Preparing to transfer all duplicate Pokemon, keeping the highest CP of each type.')

        logger.log('[x] Will NOT transfer anything above CP {}'.format(
            self.config.initial_transfer))

        pokemon_groups = self._initial_transfer_get_groups()

        for id in pokemon_groups:

            group_cp = pokemon_groups[id].keys()

            if len(group_cp) > 1:
                group_cp.sort()
                group_cp.reverse()


                for x in range(1, len(group_cp)):
                    if self.config.initial_transfer and group_cp[x] > self.config.initial_transfer:
                        continue

                    print('[x] Transferring {} with CP {}'.format(
                        self.pokemon_list[id - 1]['Name'], group_cp[x]))
                    self.api.release_pokemon(
                        pokemon_id=pokemon_groups[id][group_cp[x]])
                    response_dict = self.api.call()
                    sleep(2)

        logger.log('[x] Transferring Done.')

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
