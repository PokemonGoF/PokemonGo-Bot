# -*- coding: utf-8 -*-

from pokemongo_bot import logger

class PlayerService():
    def __init__(self, api):
        self.api = api
        self.latest_inventory = None

    def update_inventory(self):
        response = self.get_inventory()
        inventory = list()

        if not 'responses' in response:
            return

        if not 'GET_INVENTORY' in response['responses']:
            return

        if not 'inventory_delta' in response['responses']['GET_INVENTORY']:
            return

        if not 'inventory_items' in response['responses']['GET_INVENTORY']['inventory_delta']:
            return

        r = response['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        for item in r:
            if not 'inventory_item_data' in item:
                continue
            if not 'item' in item['inventory_item_data']:
                continue
            if not 'item_id' in item['inventory_item_data'][
                    'item']:
                continue
            if not 'count' in item['inventory_item_data'][
                    'item']:
                continue

            inventory.append(item['inventory_item_data']['item'])

        return inventory

    def get_inventory(self):
        if self.latest_inventory is None:
            self.api.get_inventory()
            response = self.api.call()
            self.latest_inventory = response

        return self.latest_inventory

    def current_inventory(self):
        inventory_req = self.get_inventory()
        inventory_dict = inventory_req['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']

        user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        with open(user_web_inventory, 'w') as outfile:
            json.dump(inventory_dict, outfile)

        # get player items stock
        items_stock = {x.value:0 for x in list(Item)}

        for item in inventory_dict:
            try:
                # print(item['inventory_item_data']['item'])
                item_id = item['inventory_item_data']['item']['item_id']
                item_count = item['inventory_item_data']['item']['count']

                if item_id in items_stock:
                    items_stock[item_id] = item_count
            except:
                continue

        return items_stock

    def print_character_info(self):
        # get player profile call
        # ----------------------
        self.api.get_player()
        response_dict = self.api.call()
        #print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1 = "0"
        currency_2 = "0"

        if response_dict:
            self._player = response_dict['responses']['GET_PLAYER']['player_data']
            player = self._player
        else:
            logger.log("The API didn't return player info, servers are unstable - retrying.", 'red')
            sleep(5)
            self.print_character_info()

        # @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(
            player['creation_timestamp_ms'] / 1e3)
        creation_date = creation_date.strftime("%Y/%m/%d %H:%M:%S")

        pokecoins = '0'
        stardust = '0'
        items_stock = self.current_inventory()

        if 'amount' in player['currencies'][0]:
            pokecoins = player['currencies'][0]['amount']
        if 'amount' in player['currencies'][1]:
            stardust = player['currencies'][1]['amount']

        logger.log('')
        logger.log('--- {username} ---'.format(**player), 'cyan')
        self.get_player_info()

        logger.log('Pokemon Bag: {}/{}'.format(self.get_inventory_count('pokemon'), player['max_pokemon_storage']), 'cyan')
        logger.log('Items: {}/{}'.format(self.get_inventory_count('item'), player['max_item_storage']), 'cyan')
        logger.log('Stardust: {}'.format(stardust) + ' | Pokecoins: {}'.format(pokecoins), 'cyan')

        # Items Output
        logger.log('PokeBalls: ' + str(items_stock[1]) +
            ' | GreatBalls: ' + str(items_stock[2]) +
            ' | UltraBalls: ' + str(items_stock[3]), 'cyan')
        logger.log('RazzBerries: ' + str(items_stock[701]) +
            ' | BlukBerries: ' + str(items_stock[702]) +
            ' | NanabBerries: ' + str(items_stock[703]), 'cyan')
        logger.log('LuckyEgg: ' + str(items_stock[301]) +
            ' | Incubator: ' + str(items_stock[902]) +
            ' | TroyDisk: ' + str(items_stock[501]), 'cyan')
        logger.log('Potion: ' + str(items_stock[101]) +
            ' | SuperPotion: ' + str(items_stock[102]) +
            ' | HyperPotion: ' + str(items_stock[103]), 'cyan')
        logger.log('Incense: ' + str(items_stock[401]) +
            ' | IncenseSpicy: ' + str(items_stock[402]) +
            ' | IncenseCool: ' + str(items_stock[403]), 'cyan')
        logger.log('Revive: ' + str(items_stock[201]) +
            ' | MaxRevive: ' + str(items_stock[202]), 'cyan')

        logger.log('')

    def get_inventory_count(self, what):
        response_dict = self.get_inventory()

        if not 'responses' in response_dict:
            return

        if not 'GET_INVENTORY' in response_dict['responses']:
            return

        if not 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
            return

        if not 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
            return

        pokecount = 0
        itemcount = 1
        r = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        for item in r:
            #print('item {}'.format(item))
            if not 'inventory_item_data' in item:
                continue

            if 'pokemon_data' in item['inventory_item_data']:
                    pokecount = pokecount + 1

            if not 'item' in item['inventory_item_data']:
                continue

            if 'count' in item['inventory_item_data']['item']:
                itemcount = itemcount + \
                    item['inventory_item_data'][
                        'item']['count']

        if 'pokemon' in what:
            return pokecount
        if 'item' in what:
            return itemcount

        return '0'

    def get_player_info(self, response_dict):
        response_dict = self.get_inventory()

        if not 'responses' in response_dict:
            return

        if not 'GET_INVENTORY' in response_dict['responses']:
            return

        if not 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
            return

        if not 'inventory_items' in response_dict['responses']['GET_INVENTORY']['inventory_delta']:
            return

        pokecount = 0
        itemcount = 1
        r = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        for item in r:
            #print('item {}'.format(item))
            if not 'inventory_item_data' in item:
                continue

            if not 'player_stats' in item['inventory_item_data']:
                continue

            playerdata = item['inventory_item_data']['player_stats']

            nextlvlxp = (
                int(playerdata.get('next_level_xp', 0)) -
                int(playerdata.get('experience', 0)))

            if 'level' in playerdata:
                if 'experience' in playerdata:
                    logger.log('Level: {level}'.format(**playerdata) +
                        ' (Next Level: {} XP)'.format(nextlvlxp) +
                         ' (Total: {experience} XP)'.format(**playerdata), 'cyan')

            if 'pokemons_captured' in playerdata:
                if 'poke_stop_visits' in playerdata:
                    logger.log(
                        'Pokemon Captured: {pokemons_captured}'.format(**playerdata) +
                        ' | Pokestops Visited: {poke_stop_visits}'.format(**playerdata), 'cyan')
