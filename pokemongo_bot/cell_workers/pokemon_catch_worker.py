# -*- coding: utf-8 -*-

import time
from sets import Set
from utils import distance, print_green, print_yellow, print_red
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger


class PokemonCatchWorker(object):
    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.item_list = bot.item_list
        self.inventory = bot.inventory

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        spawnpoint_id = self.pokemon['spawnpoint_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']
        self.api.encounter(encounter_id=encounter_id,
                           spawnpoint_id=spawnpoint_id,
                           player_latitude=player_latitude,
                           player_longitude=player_longitude)
        response_dict = self.api.call()

        if response_dict and 'responses' in response_dict:
            if 'ENCOUNTER' in response_dict['responses']:
                if 'status' in response_dict['responses']['ENCOUNTER']:
                    if response_dict['responses']['ENCOUNTER']['status'] is 7:
                        logger.log('[x] Pokemon Bag is full!', 'red')
                        self.bot.initial_transfer()
                    if response_dict['responses']['ENCOUNTER']['status'] is 1:
                        cp = 0
                        total_IV = 0
                        if 'wild_pokemon' in response_dict['responses'][
                                'ENCOUNTER']:
                            pokemon = response_dict['responses'][
                                'ENCOUNTER']['wild_pokemon']
                            if 'pokemon_data' in pokemon and 'cp' in pokemon[
                                    'pokemon_data']:
                                cp = pokemon['pokemon_data']['cp']
                                iv_stats = [
                                    'individual_attack', 'individual_defense',
                                    'individual_stamina'
                                ]
                                for individual_stat in iv_stats:
                                    try:
                                        total_IV += pokemon[
                                            'pokemon_data'][individual_stat]
                                    except:
                                        continue
                                print total_IV
                                pokemon_potential = round((total_IV / 45.0), 2)
                                pokemon_num = int(pokemon['pokemon_data'][
                                    'pokemon_id']) - 1
                                pokemon_name = self.pokemon_list[
                                    int(pokemon_num)]['Name']
                                logger.log(
                                    '[#] A Wild {} appeared! [CP {}] [Potential {}]'.format(
                                        pokemon_name, cp, pokemon_potential),
                                    'yellow')
                                # Simulate app
                                sleep(3)

                        balls_stock = self.bot.pokeball_inventory()
                        while (True):
                            pokeball = 0

                            if balls_stock[1] > 0:
                                # print 'use Poke Ball'
                                pokeball = 1

                            if balls_stock[2] > 0:
                                if pokeball is 0 and cp <= 300 and balls_stock[2] < 10:
                                    print('Great Ball stock is low... saving for pokemon with cp greater than 300')
                                elif cp > 300 or pokeball is 0:
                                    #print 'use Great Ball'
                                    pokeball = 2

                            if balls_stock[3] > 0:
                                if pokeball is 0 and cp <= 700 and balls_stock[3] < 10:
                                    print('Ultra Ball stock is low... saving for pokemon with cp greater than 700')
                                elif cp > 700 or pokeball is 0:
                                    #print 'use Utra Ball'
                                    pokeball = 3

                            if pokeball is 0:
                                logger.log(
                                    '[x] Out of pokeballs, switching to farming mode...',
                                    'red')
                                # Begin searching for pokestops.
                                self.config.mode = 'farm'
                                return -1

                            logger.log('[x] Using {}... ({} left!)'.format(
                                self.item_list[str(pokeball)], balls_stock[pokeball]-1))

                            balls_stock[pokeball] = balls_stock[pokeball] - 1
                            id_list1 = self.count_pokemon_inventory()
                            self.api.catch_pokemon(
                                encounter_id=encounter_id,
                                pokeball=pokeball,
                                normalized_reticle_size=1.950,
                                spawn_point_guid=spawnpoint_id,
                                hit_pokemon=1,
                                spin_modifier=1,
                                NormalizedHitPosition=1)
                            response_dict = self.api.call()

                            if response_dict and \
                                'responses' in response_dict and \
                                'CATCH_POKEMON' in response_dict['responses'] and \
                                    'status' in response_dict['responses']['CATCH_POKEMON']:
                                status = response_dict['responses'][
                                    'CATCH_POKEMON']['status']
                                if status is 2:
                                    logger.log(
                                        '[-] Attempted to capture {} - failed.. trying again!'.format(
                                            pokemon_name), 'red')
                                    sleep(2)
                                    continue
                                if status is 3:
                                    logger.log(
                                        '[x] Oh no! {} vanished! :('.format(
                                            pokemon_name), 'red')
                                if status is 1:
                                    if cp < self.config.cp or pokemon_potential < self.config.pokemon_potential:
                                        logger.log(
                                            '[x] Captured {}! [CP {}] [IV {}] - exchanging for candy'.format(
                                                pokemon_name, cp,
                                                pokemon_potential), 'green')
                                        id_list2 = self.count_pokemon_inventory(
                                        )
                                        # Transfering Pokemon
                                        pokemon_to_transfer = list(Set(
                                            id_list2) - Set(id_list1))
                                        if len(pokemon_to_transfer) == 0:
                                            raise RuntimeError(
                                                'Trying to transfer 0 pokemons!')
                                        self.transfer_pokemon(
                                            pokemon_to_transfer[0])
                                        logger.log(
                                            '[#] {} has been exchanged for candy!'.format(
                                                pokemon_name), 'green')
                                    else:
                                        logger.log(
                                            '[x] Captured {}! [CP {}]'.format(
                                                pokemon_name, cp), 'green')
                            break
        time.sleep(5)

    def _transfer_low_cp_pokemon(self, value):
        self.api.get_inventory()
        response_dict = self.api.call()
        self._transfer_all_low_cp_pokemon(value, response_dict)

    def _transfer_all_low_cp_pokemon(self, value, response_dict):
        try:
            reduce(dict.__getitem__, [
                "responses", "GET_INVENTORY", "inventory_delta",
                "inventory_items"
            ], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY'][
                    'inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                        "inventory_item_data", "pokemon"
                    ], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon']
                    self._execute_pokemon_transfer(value, pokemon)
                    time.sleep(1.2)

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
        return self.counting_pokemon(response_dict, id_list)

    def counting_pokemon(self, response_dict, id_list):
        try:
            reduce(dict.__getitem__, [
                "responses", "GET_INVENTORY", "inventory_delta",
                "inventory_items"
            ], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY'][
                    'inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                        "inventory_item_data", "pokemon_data"
                    ], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon_data']
                    if pokemon.get('is_egg', False):
                        continue
                    id_list.append(pokemon['id'])

        return id_list
