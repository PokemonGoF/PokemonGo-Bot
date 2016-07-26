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
        self.show_iv(pokemon_groups)
        raw_input("Press Enter to continue...")

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
                        pokemon_id=pokemon_groups[id][group_cp[x]]['id'])
                    response_dict = self.api.call()
                    sleep(2)

        logger.log('[x] Transferring Done.')

    def show_iv(self,pokemon_groups):
        for id in pokemon_groups:
            group_cp = pokemon_groups[id].keys()
            if len(group_cp) > 0:
                group_cp.sort()
                group_cp.reverse()
                for x in range(0, len(group_cp)):
                    res_str = self.pokemon_list[id - 1]['Name'] +"\tCP:"+str(group_cp[x])+"\tIV:"+str(pokemon_groups[id][group_cp[x]]['iv'])+"%"
                    if group_cp[x] <= self.config.initial_transfer:
                        logger.log(res_str, 'red')
                    elif (pokemon_groups[id][group_cp[x]]['iv']>85):
                        logger.log(res_str, 'green')
                    elif (pokemon_groups[id][group_cp[x]]['iv']>70):
                        logger.log(res_str, 'green')
                    elif (pokemon_groups[id][group_cp[x]]['iv']>50):
                        logger.log(res_str, 'yellow')
                    else:
                        logger.log(res_str, 'yellow')


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

            data = pokemon['inventory_item_data']['pokemon_data']

            group_id = data['pokemon_id']
            group_pokemon = data['id']
            group_pokemon_cp = data['cp']
            total_IV = 0
            iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
            for individual_stat in iv_stats:
                try:
                    total_IV += data[individual_stat]
                except:
                    data[individual_stat] = 0
                    continue
            group_iv = (total_IV * 100 / 45)

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = {}

            pokemon_groups[group_id].update({group_pokemon_cp: {'id': group_pokemon, 'iv': group_iv}})
        return pokemon_groups