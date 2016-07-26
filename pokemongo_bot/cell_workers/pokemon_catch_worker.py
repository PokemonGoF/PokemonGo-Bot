# -*- coding: utf-8 -*-

import time
from sets import Set

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep


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
                        if self.config.initial_transfer:
                            logger.log('Pokemon Bag is full!', 'red')
                            return PokemonCatchWorker.BAG_FULL
                        else:
                            raise RuntimeError('Pokemon Bag is full!')

                    if response_dict['responses']['ENCOUNTER']['status'] is 1:
                        cp = 0
                        total_IV = 0
                        if 'wild_pokemon' in response_dict['responses']['ENCOUNTER']:
                            pokemon = response_dict['responses']['ENCOUNTER']['wild_pokemon']
                            catch_rate = response_dict['responses']['ENCOUNTER']['capture_probability']['capture_probability'] # 0 = pokeballs, 1 great balls, 3 ultra balls

                            if 'pokemon_data' in pokemon and 'cp' in pokemon['pokemon_data']:
                                cp = pokemon['pokemon_data']['cp']

                                # make sure we catch any missing iv information
                                if 'individual_stamina' not in pokemon['pokemon_data']:
                                    pokemon['pokemon_data']['individual_stamina'] = 0
                                if 'individual_attack' not in pokemon['pokemon_data']:
                                    pokemon['pokemon_data']['individual_attack'] = 0
                                if 'individual_defense' not in pokemon['pokemon_data']:
                                    pokemon['pokemon_data']['individual_defense'] = 0

                                iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
                                iv_display = '{}/{}/{}'.format(
                                    pokemon['pokemon_data']['individual_stamina'],
                                    pokemon['pokemon_data']['individual_attack'],
                                    pokemon['pokemon_data']['individual_defense']
                                )

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
                                logger.log('A Wild {} appeared! [CP {}] [Potential {}]'.format(
                                    pokemon_name, cp, pokemon_potential), 'yellow')

                                logger.log('IV [Stamina/Attack/Defense] = [{}]'.format(iv_display))
                                pokemon['pokemon_data']['name'] = pokemon_name
                                # Simulate app
                                sleep(3)

                        if not self.should_capture_pokemon(pokemon_name, cp, pokemon_potential, response_dict):
                            #logger.log('[x] Rule prevents capture.')
                            return False

                        balls_stock = self.bot.pokeball_inventory()
                        while(True):

                            ## pick the most simple ball from stock
                            pokeball = 1 # start from 1 - PokeBalls

                            current_type = pokeball
                            while(balls_stock[current_type] is 0 and current_type < 3): # if this type's stock = 0 and not top tier yet
                                current_type = current_type + 1 # progress to next tier
                                if balls_stock[current_type] > 0: # next tier's stock > 0
                                    pokeball = current_type

                            ## re-check stock again
                            if balls_stock[pokeball] is 0:
                                logger.log('Out of pokeballs, switching to farming mode...', 'red')
                                # Begin searching for pokestops.
                                self.config.mode = 'farm'
                                return PokemonCatchWorker.NO_POKEBALLS

                            ## Use berry to increase success chance.
                            berry_id = 701 # @ TODO: use better berries if possible
                            berries_count = self.bot.item_inventory_count(berry_id)
                            if(catch_rate[pokeball-1] < 0.5 and berries_count > 0): # and berry is in stock
                                success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                logger.log('Catch Rate with normal Pokeball is low ({}%). Throwing {}... ({} left!)'.format(success_percentage,self.item_list[str(berry_id)],berries_count-1))

                                if balls_stock[pokeball] is 0:
                                    break

                                self.api.use_item_capture(
                                    item_id=berry_id,
                                    encounter_id = encounter_id,
                                    spawn_point_guid = spawnpoint_id
                                )
                                response_dict = self.api.call()
                                if response_dict and response_dict['status_code'] is 1 and 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:

                                    for i in range(len(catch_rate)):
                                        catch_rate[i] = catch_rate[i] * response_dict['responses']['USE_ITEM_CAPTURE']['item_capture_mult']

                                    success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                    logger.log('Catch Rate with normal Pokeball has increased to {}%'.format(success_percentage))
                                else:
                                    if response_dict['status_code'] is 1:
                                        logger.log('Fail to use berry. Seem like you are softbanned.','red')
                                    else:
                                        logger.log('Fail to use berry. Status Code: {}'.format(response_dict['status_code']),'red')

                            ## change ball to next tier if catch rate is too low
                            current_type = pokeball
                            while(current_type < 3):
                                current_type = current_type+1
                                if catch_rate[pokeball-1] < 0.35 and balls_stock[current_type] > 0:
                                    # if current ball chance to catch is under 35%, and player has better ball - then use it
                                    pokeball = current_type # use better ball

                            # @TODO, use the best ball in stock to catch VIP (Very Important Pokemon: Configurable)

                            balls_stock[pokeball] = balls_stock[pokeball] - 1
                            success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                            logger.log('Using {} (chance: {}%)... ({} left!)'.format(
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
                                        '[-] Attempted to capture {} - failed.. trying again!'.format(pokemon_name), 'red')
                                    sleep(2)
                                    continue
                                if status is 3:
                                    logger.log(
                                        'Oh no! {} vanished! :('.format(pokemon_name), 'red')
                                if status is 1:

                                    id_list2 = self.count_pokemon_inventory()

                                    logger.log('Captured {}! [CP {}] [{}]'.format(
                                        pokemon_name,
                                        cp,
                                        iv_display
                                    ), 'blue')

                                    if self.config.evolve_captured:
                                        pokemon_to_transfer = list(Set(id_list2) - Set(id_list1))
                                        self.api.evolve_pokemon(pokemon_id=pokemon_to_transfer[0])
                                        response_dict = self.api.call()
                                        status = response_dict['responses']['EVOLVE_POKEMON']['result']
                                        if status == 1:
                                            logger.log(
                                                    '{} has been evolved!'.format(pokemon_name), 'green')
                                        else:
                                            logger.log(
                                            'Failed to evolve {}!'.format(pokemon_name))

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
                                            '{} has been exchanged for candy!'.format(pokemon_name), 'green')

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

    def should_capture_pokemon(self, pokemon_name, cp, iv, response_dict):
        catch_config = self._get_catch_config_for(pokemon_name)
        cp_iv_logic = catch_config.get('logic')
        if not cp_iv_logic:
            cp_iv_logic = self._get_catch_config_for('any').get('logic', 'and')

        catch_results = {
            'cp': False,
            'iv': False,
        }

        if catch_config.get('never_catch', False):
            return False

        if catch_config.get('always_catch', False):
            return True

        catch_cp = catch_config.get('catch_above_cp', 0)
        if cp > catch_cp:
            catch_results['cp'] = True

        catch_iv = catch_config.get('catch_above_iv', 0)
        if iv > catch_iv:
            catch_results['iv'] = True

        logic_to_function = {
            'or': lambda x, y: x or y,
            'and': lambda x, y: x and y
        }

        #logger.log(
        #    "Catch config for {}: CP {} {} IV {}".format(
        #        pokemon_name,
        #        catch_cp,
        #        cp_iv_logic,
        #        catch_iv
        #    ), 'yellow'
        #)

        return logic_to_function[cp_iv_logic](*catch_results.values())

    def _get_catch_config_for(self, pokemon):
        catch_config = self.config.catch.get(pokemon)
        if not catch_config:
            catch_config = self.config.catch.get('any')
        if not catch_config:
            catch_config = {}
        return catch_config

    def should_release_pokemon(self, pokemon_name, cp, iv, response_dict):
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
