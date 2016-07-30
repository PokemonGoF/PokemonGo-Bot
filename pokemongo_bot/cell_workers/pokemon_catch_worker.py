# -*- coding: utf-8 -*-

import time

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import (normalized_reticle_size, sleep,
                                           spin_modifier)


class PokemonCatchWorker(object):
    BAG_FULL = 'bag_full'
    NO_POKEBALLS = 'no_pokeballs'
    WANTED_CATCH_RATE = 0.45
    BERRY_ID = 701  # @ TODO: use better berries if possible

    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.item_list = bot.item_list
        self.inventory = bot.inventory
        self.spawn_point_guid = ''
        self.response_key = ''
        self.response_status_key = ''

    def _pick_ball(self, items_stock, catch_rates):
        # use worst ball that has at least WANTED_CATCH_RATE base rate
        # @TODO, use the best ball in stock to catch VIP (Very Important Pokemon: Configurable)
        for i, rate in enumerate(catch_rates):
            pokeball = i + 1
            if items_stock[pokeball] > 0:
                if rate >= self.WANTED_CATCH_RATE:
                    logger.log('Selected {} with {:02f}% rate'.format(
                            self.item_list[str(pokeball)],
                            rate * 100
                        )
                    )
                    return pokeball
                else:
                    logger.log('{} has low catch rate ({:0.2f}%), upgrading if possible...'.format(
                            self.item_list[str(pokeball)],
                            rate * 100
                        )
                    )
        # if we get here, no balls are good enough
        # pick best ball available
        for pokeball in [3, 2, 1]:
            if items_stock[pokeball] > 0:
                return pokeball
            logger.log('No {}s available'.format(self.item_list[str(pokeball)]))
        # out of balls
        return None

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        response_dict = self.create_encounter_api_call()

        if response_dict and 'responses' in response_dict:
            if self.response_key in response_dict['responses']:
                if self.response_status_key in response_dict['responses'][self.response_key]:
                    if response_dict['responses'][self.response_key][self.response_status_key] is 7:
                        if self.config.release_pokemon:
                            raise RuntimeError('Pokemon Bag is full!')

                    if response_dict['responses'][self.response_key][self.response_status_key] is 1:
                        cp = 0
                        if 'wild_pokemon' in response_dict['responses'][self.response_key] or 'pokemon_data' in \
                                response_dict['responses'][self.response_key]:
                            if self.response_key == 'ENCOUNTER':
                                pokemon = response_dict['responses'][self.response_key]['wild_pokemon']
                            else:
                                pokemon = response_dict['responses'][self.response_key]

                            catch_rate = response_dict['responses'][self.response_key]['capture_probability'][
                                'capture_probability']  # 0 = pokeballs, 1 great balls, 3 ultra balls

                            if 'pokemon_data' in pokemon and 'cp' in pokemon['pokemon_data']:
                                pokemon_data = pokemon['pokemon_data']
                                cp = pokemon_data['cp']

                                individual_attack = pokemon_data.get("individual_attack", 0)
                                individual_stamina = pokemon_data.get("individual_stamina", 0)
                                individual_defense = pokemon_data.get("individual_defense", 0)

                                iv_display = '{}/{}/{}'.format(
                                    individual_stamina,
                                    individual_attack,
                                    individual_defense
                                )

                                pokemon_potential = self.pokemon_potential(pokemon_data)
                                pokemon_num = int(pokemon_data['pokemon_id']) - 1
                                pokemon_name = self.pokemon_list[int(pokemon_num)]['Name']
                                logger.log('A Wild {} appeared! [CP {}] [Potential {}]'.format(
                                    pokemon_name, cp, pokemon_potential), 'yellow')

                                logger.log('IV [Stamina/Attack/Defense] = [{}]'.format(iv_display))
                                pokemon_data['name'] = pokemon_name
                                # Simulate app
                                sleep(3)

                        if not self.should_capture_pokemon(pokemon_name, cp, pokemon_potential, response_dict):
                            # logger.log('[x] Rule prevents capture.')
                            return False

                        items_stock = self.bot.current_inventory()
                        while True:
                            pokeball = self._pick_ball(items_stock, catch_rate)
                            if not pokeball:
                                logger.log('Out of pokeballs', 'red')
                                return PokemonCatchWorker.NO_POKEBALLS

                            # if chance is still low and berrys are in stock
                            if catch_rate[pokeball-1] < self.WANTED_CATCH_RATE and items_stock[self.BERRY_ID] > 0:
                                success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                items_stock[self.BERRY_ID] -= 1
                                logger.log(
                                    'Catch Rate with {} is low ({}%). '
                                    'Throwing {}... ({} left!)'.format(
                                        self.item_list[str(pokeball)],
                                        success_percentage,
                                        self.item_list[str(self.BERRY_ID)],
                                        items_stock[self.BERRY_ID]
                                    )
                                )

                                self.api.use_item_capture(
                                    item_id=self.BERRY_ID,
                                    encounter_id=encounter_id,
                                    spawn_point_id=self.spawn_point_guid
                                )
                                # used berry
                                response_dict = self.api.call()
                                if response_dict and response_dict['status_code'] is 1 and 'item_capture_mult' in \
                                        response_dict['responses']['USE_ITEM_CAPTURE']:

                                    for i in range(len(catch_rate)):
                                        if 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                            catch_rate[i] = catch_rate[i] * \
                                                            response_dict['responses']['USE_ITEM_CAPTURE'][
                                                                'item_capture_mult']

                                    success_percentage = '{0:.2f}'.format(catch_rate[pokeball - 1] * 100)
                                    logger.log('Catch Rate with {} has increased to {}%'.format(
                                        self.item_list[str(pokeball)],
                                        success_percentage))
                                else:
                                    if response_dict['status_code'] is 1:
                                        logger.log('Failed to use berry. Seem like you are softbanned.', 'red')
                                        self.bot.softban = True
                                    else:
                                        logger.log(
                                            'Failed to use berry. Status Code: {}'.format(response_dict['status_code']),
                                            'red')

                            # used up ball
                            items_stock[pokeball] -= 1
                            success_percentage = '{0:.2f}'.format(catch_rate[pokeball - 1] * 100)
                            logger.log('Using {} (chance: {}%)... ({} left!)'.format(
                                self.item_list[str(pokeball)],
                                success_percentage,
                                items_stock[pokeball]
                            ))

                            id_list1 = self.count_pokemon_inventory()

                            reticle_size_parameter = normalized_reticle_size(self.config.catch_randomize_reticle_factor)
                            spin_modifier_parameter = spin_modifier(self.config.catch_randomize_spin_factor)

                            self.api.catch_pokemon(encounter_id=encounter_id,
                                                   pokeball=pokeball,
                                                   normalized_reticle_size=reticle_size_parameter,
                                                   spawn_point_id=self.spawn_point_guid,
                                                   hit_pokemon=1,
                                                   spin_modifier=spin_modifier_parameter,
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
                                        '[-] Attempted to capture {} - failed.. trying again!'.format(pokemon_name),
                                        'red')
                                    sleep(2)
                                    continue
                                if status is 3:
                                    logger.log(
                                        'Oh no! {} vanished! :('.format(pokemon_name), 'red')
                                    if success_percentage == 100:
                                        self.softban = True
                                if status is 1:
                                    self.bot.metrics.captured_pokemon(pokemon_name, cp, iv_display, pokemon_potential)

                                    logger.log('Captured {}! [CP {}] [Potential {}] [{}] [+{} exp]'.format(
                                        pokemon_name,
                                        cp,
                                        pokemon_potential,
                                        iv_display,
                                        sum(response_dict['responses']['CATCH_POKEMON']['capture_award']['xp'])
                                    ), 'blue')
                                    self.bot.softban = False

                                    if (self.config.evolve_captured
                                        and (self.config.evolve_captured[0] == 'all'
                                             or pokemon_name in self.config.evolve_captured)):
                                        id_list2 = self.count_pokemon_inventory()
                                        # No need to capture this even for metrics, player stats includes it.
                                        pokemon_to_transfer = list(set(id_list2) - set(id_list1))

                                        # TODO dont throw RuntimeError, do something better
                                        if len(pokemon_to_transfer) == 0:
                                            raise RuntimeError(
                                                'Trying to evolve 0 pokemons!')
                                        self.api.evolve_pokemon(pokemon_id=pokemon_to_transfer[0])
                                        response_dict = self.api.call()
                                        status = response_dict['responses']['EVOLVE_POKEMON']['result']
                                        if status == 1:
                                            logger.log(
                                                '{} has been evolved!'.format(pokemon_name), 'green')
                                        else:
                                            logger.log(
                                                'Failed to evolve {}!'.format(pokemon_name))
                            break
        time.sleep(5)

    def count_pokemon_inventory(self):
        # don't use cached bot.get_inventory() here
        # because we need to have actual information in capture logic
        self.api.get_inventory()
        response_dict = self.api.call()

        id_list = []
        callback = lambda pokemon: id_list.append(pokemon['id'])
        self._foreach_pokemon_in_inventory(response_dict, callback)
        return id_list

    def _foreach_pokemon_in_inventory(self, response_dict, callback):
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
                    if not pokemon.get('is_egg', False):
                        callback(pokemon)

    def pokemon_potential(self, pokemon_data):
        total_iv = 0
        iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']

        for individual_stat in iv_stats:
            try:
                total_iv += pokemon_data[individual_stat]
            except:
                pokemon_data[individual_stat] = 0
                continue

        return round((total_iv / 45.0), 2)

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

        # logger.log(
        #    "Catch config for {}: CP {} {} IV {}".format(
        #        pokemon_name,
        #        catch_cp,
        #        cp_iv_logic,
        #        catch_iv
        #    ), 'yellow'
        # )

        return logic_to_function[cp_iv_logic](*catch_results.values())

    def _get_catch_config_for(self, pokemon):
        catch_config = self.config.catch.get(pokemon)
        if not catch_config:
            catch_config = self.config.catch.get('any')
        return catch_config

    def create_encounter_api_call(self):
        encounter_id = self.pokemon['encounter_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']

        if 'spawn_point_id' in self.pokemon:
            spawn_point_id = self.pokemon['spawn_point_id']
            self.spawn_point_guid = spawn_point_id
            self.response_key = 'ENCOUNTER'
            self.response_status_key = 'status'
            self.api.encounter(encounter_id=encounter_id, spawn_point_id=spawn_point_id,
                               player_latitude=player_latitude, player_longitude=player_longitude)
        else:
            fort_id = self.pokemon['fort_id']
            self.spawn_point_guid = fort_id
            self.response_key = 'DISK_ENCOUNTER'
            self.response_status_key = 'result'
            self.api.disk_encounter(encounter_id=encounter_id, fort_id=fort_id,
                                    player_latitude=player_latitude, player_longitude=player_longitude)

        return self.api.call()
