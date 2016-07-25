# -*- coding: utf-8 -*-

import time
from sets import Set
from utils import distance
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class PokemonCatchWorker(object):
    BAG_FULL = 'bag_full'
    NO_POKEBALLS = 'no_pokeballs'

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
        self.api.encounter(encounter_id=encounter_id, spawnpoint_id=spawnpoint_id,
                           player_latitude=player_latitude, player_longitude=player_longitude)
        response_dict = self.api.call()

        if response_dict and 'responses' in response_dict:
            if 'ENCOUNTER' in response_dict['responses']:
                if 'status' in response_dict['responses']['ENCOUNTER']:
                    if response_dict['responses']['ENCOUNTER']['status'] is 7:
                        logger.log('[x] Pokemon Bag is full!', 'red')
                        return PokemonCatchWorker.BAG_FULL

                    if response_dict['responses']['ENCOUNTER']['status'] is 1:
                        cp = 0
                        total_IV = 0
                        if 'wild_pokemon' in response_dict['responses']['ENCOUNTER']:
                            pokemon = response_dict['responses']['ENCOUNTER']['wild_pokemon']
                            catch_rate = response_dict['responses']['ENCOUNTER']['capture_probability']['capture_probability'] # 0 = pokeballs, 1 great balls, 3 ultra balls

                            if 'pokemon_data' in pokemon and 'cp' in pokemon['pokemon_data']:
                                cp = pokemon['pokemon_data']['cp']
                                iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']

                                for individual_stat in iv_stats:
                                    try:
                                        total_IV += pokemon['pokemon_data'][individual_stat]
                                    except:
                                        pokemon['pokemon_data'][individual_stat] = 0
                                        continue

                                pokemon_potential = round((total_IV / 45.0), 2)
                                pokemon_num = int(pokemon['pokemon_data'][
                                                  'pokemon_id']) - 1
                                pokemon_name = self.pokemon_list[
                                    int(pokemon_num)]['Name']
                                logger.log('[#] A Wild {} appeared! [CP {}] [Potential {}]'.format(
                                    pokemon_name, cp, pokemon_potential), 'yellow')

                                logger.log('[#] IV [Stamina/Attack/Defense] = [{}/{}/{}]'.format(
                                    pokemon['pokemon_data']['individual_stamina'],
                                    pokemon['pokemon_data']['individual_attack'],
                                    pokemon['pokemon_data']['individual_defense']
                                ))
                                pokemon['pokemon_data']['name'] = pokemon_name
                                # Simulate app
                                sleep(3)

                        balls_stock = self.bot.pokeball_inventory()
                        while(True):

                            pokeball = 1 # default:poke ball

                            if balls_stock[1] <= 0: # if poke ball are out of stock
                                if balls_stock[2] > 0: # and player has great balls in stock...
                                    pokeball = 2 # then use great balls
                                elif balls_stock[3] > 0: # or if great balls are out of stock too, and player has ultra balls...
                                    pokeball = 3 # then use ultra balls
                                else:
                                    pokeball = 0 # player doesn't have any of pokeballs, great balls or ultra balls

                            while(pokeball < 3):
                                if catch_rate[pokeball-1] < 0.35 and balls_stock[pokeball+1] > 0:
                                    # if current ball chance to catch is under 35%, and player has better ball - then use it
                                    pokeball = pokeball+1 # use better ball
                                else:
                                    break

                            # @TODO, use the best ball in stock to catch VIP (Very Important Pokemon: Configurable)

                            if pokeball is 0:
                                logger.log(
                                    '[x] Out of pokeballs, switching to farming mode...', 'red')
                                # Begin searching for pokestops.
                                self.config.mode = 'farm'
                                return PokemonCatchWorker.NO_POKEBALLS

                            balls_stock[pokeball] = balls_stock[pokeball] - 1
                            success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                            logger.log('[x] Using {} (chance: {}%)... ({} left!)'.format(
                                self.item_list[str(pokeball)], 
                                success_percentage, 
                                balls_stock[pokeball]
                            ))

                            id_list1 = self.count_pokemon_inventory()
                            self.api.catch_pokemon(encounter_id=encounter_id,
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
                                        '[-] Attempted to capture {}- failed.. trying again!'.format(pokemon_name), 'red')
                                    sleep(2)
                                    continue
                                if status is 3:
                                    logger.log(
                                        '[x] Oh no! {} vanished! :('.format(pokemon_name), 'red')
                                if status is 1:
                                    logger.log(
                                        '[x] Captured {}! [CP {}] [IV {}]'.format(
                                            pokemon_name,
                                            cp,
                                            pokemon_potential
                                        ), 'green'
                                    )

                                    id_list2 = self.count_pokemon_inventory()

                                    if self.config.evolve_captured:
                                        pokemon_to_transfer = list(Set(id_list2) - Set(id_list1))
                                        self.api.evolve_pokemon(pokemon_id=pokemon_to_transfer[0])
                                        response_dict = self.api.call()
                                        status = response_dict['responses']['EVOLVE_POKEMON']['result']
                                        if status == 1:
                                            logger.log(
                                                    '[#] {} has been evolved!'.format(pokemon_name), 'green')
                                        else:
                                            logger.log(
                                            '[x] Failed to evolve {}!'.format(pokemon_name))

                                    if self.should_release_pokemon(pokemon_name, cp, pokemon_potential, response_dict):
                                        # Transfering Pokemon
                                        pokemon_to_transfer = list(
                                            Set(id_list2) - Set(id_list1))
                                        if len(pokemon_to_transfer) == 0:
                                            raise RuntimeError(
                                                'Trying to transfer 0 pokemons!')
                                        self.transfer_pokemon(
                                            pokemon_to_transfer[0])
                                        logger.log(
                                            '[#] {} has been exchanged for candy!'.format(pokemon_name), 'green')
                                    else:
                                        logger.log(
                                        '[x] Captured {}! [CP {}]'.format(pokemon_name, cp), 'green')
                            break
        time.sleep(5)

    def _transfer_low_cp_pokemon(self, value):
        self.api.get_inventory()
        response_dict = self.api.call()
        self._transfer_all_low_cp_pokemon(value, response_dict)

    def _transfer_all_low_cp_pokemon(self, value, response_dict):
        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                           "inventory_item_data", "pokemon"], item)
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

    def should_release_pokemon(self, pokemon_name, cp, iv, response_dict):
        if self._check_always_capture_exception_for(pokemon_name):
            return False
        else:
            release_config = self._get_release_config_for(pokemon_name)
            cp_iv_logic = release_config.get('cp_iv_logic')
            if not cp_iv_logic:
                cp_iv_logic = self._get_release_config_for('any').get('cp_iv_logic', 'and')

            release_results = {
                'cp':               False,
                'iv':               False,
            }

            if 'release_under_cp' in release_config:
                min_cp = release_config['release_under_cp']
                if cp < min_cp:
                    release_results['cp'] = True

            if 'release_under_iv' in release_config:
                min_iv = release_config['release_under_iv']
                if iv < min_iv:
                    release_results['iv'] = True

            if release_config.get('always_release'):
                return True

            logic_to_function = {
                'or': lambda x, y: x or y,
                'and': lambda x, y: x and y
            }

            #logger.log(
            #    "[x] Release config for {}: CP {} {} IV {}".format(
            #        pokemon_name,
            #        min_cp,
            #        cp_iv_logic,
            #        min_iv
            #    ), 'yellow'
            #)

            return logic_to_function[cp_iv_logic](*release_results.values())

    def _get_release_config_for(self, pokemon):
        release_config = self.config.release_config.get(pokemon)
        if not release_config:
            release_config = self.config.release_config['any']
        return release_config

    def _get_exceptions(self):
        exceptions = self.config.release_config.get('exceptions')
        if not exceptions:
            return None
        return exceptions

    def _get_always_capture_list(self):
        exceptions = self._get_exceptions()
        if not exceptions:
            return []
        always_capture_list = exceptions['always_capture']
        if not always_capture_list:
            return []
        return always_capture_list

    def _check_always_capture_exception_for(self, pokemon_name):
        always_capture_list = self._get_always_capture_list()
        if not always_capture_list:
            return False
        else:
            for pokemon in always_capture_list:
                if pokemon_name == str(pokemon):
                    return True
        return False
