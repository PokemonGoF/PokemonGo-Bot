# -*- coding: utf-8 -*-

import time
from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import (normalized_reticle_size, sleep,
                                           spin_modifier)
from random import random


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
        self.spawn_point_guid = ''
        self.response_key = ''
        self.response_status_key = ''

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        response_dict = self.create_encounter_api_call()

        if response_dict and 'responses' in response_dict:
            if self.response_key in response_dict['responses']:
                if self.response_status_key in response_dict['responses'][self.response_key]:
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
                                    individual_attack,
                                    individual_defense,
                                    individual_stamina
                                )

                                pokemon_potential = self.pokemon_potential(pokemon_data)
                                pokemon_num = int(pokemon_data['pokemon_id']) - 1
                                pokemon_name = self.pokemon_list[int(pokemon_num)]['Name']
                                logger.log('A Wild {} appeared! [CP {}] [Potential {}]'.format(
                                    pokemon_name, cp, pokemon_potential), 'yellow')

                                logger.log('IV [Attack/Defense/Stamina] = [{}]'.format(iv_display))
                                pokemon_data['name'] = pokemon_name
                                # Simulate app
                                sleep(3)

                        if not self.should_capture_pokemon(pokemon_name, cp, pokemon_potential, response_dict):
                            # logger.log('[x] Rule prevents capture.')
                            return False

                        flag_VIP = False
                        # @TODO, use the best ball in stock to catch VIP (Very Important Pokemon: Configurable)
                        if self.check_vip_pokemon(pokemon_name, cp, pokemon_potential):
                            logger.log('[-] {} is a VIP Pokemon! [CP {}] [Potential {}] Nice! Try our best to catch it!'.format(pokemon_name, cp, pokemon_potential),'red')
                            flag_VIP=True

                        items_stock = self.bot.current_inventory()
                        berry_id = 701  # @ TODO: use better berries if possible
                        berries_count = self.bot.item_inventory_count(berry_id)
                        while True:
                            # pick the most simple ball from stock
                            pokeball = 1  # start from 1 - PokeBalls
                            berry_used = False

                            if flag_VIP:
                                if(berries_count>0 and catch_rate[pokeball-1] < 0.9):
                                    success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                    logger.log('Catch Rate with normal Pokeball is low ({}%). Thinking to throw a {}... ({} left!)'.format(success_percentage,self.item_list[str(berry_id)],berries_count-1))
                                    # Out of all pokeballs! Let's don't waste berry.
                                    if items_stock[1] == 0 and items_stock[2] == 0 and items_stock[3] == 0:
                                        break

                                    # Use the berry to catch
                                    response_dict = self.api.use_item_capture(
                                        item_id=berry_id,
                                        encounter_id=encounter_id,
                                        spawn_point_id=self.spawn_point_guid
                                    )
                                    if response_dict and response_dict['status_code'] is 1 and 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                        for i in range(len(catch_rate)):
                                            if 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                                catch_rate[i] = catch_rate[i] * response_dict['responses']['USE_ITEM_CAPTURE']['item_capture_mult']
                                        success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                        berries_count = berries_count -1
                                        berry_used = True
                                        logger.log('Threw a berry! Catch Rate with normal Pokeball has increased to {}%'.format(success_percentage))
                                    else:
                                        if response_dict['status_code'] is 1:
                                            logger.log('Fail to use berry. Seem like you are softbanned.', 'red')
                                        else:
                                            logger.log('Fail to use berry. Status Code: {}'.format(response_dict['status_code']),'red')

                                #use the best ball to catch
                                current_type = pokeball
                                #debug use normal ball
                                while current_type < 3:
                                    current_type += 1
                                    if catch_rate[pokeball-1] < 0.9 and items_stock[current_type] > 0:
                                        # if current ball chance to catch is under 90%, and player has better ball - then use it
                                        pokeball = current_type # use better ball
                            else:
                                # If we have a lot of berries (than the great ball), we prefer use a berry first!
                                if catch_rate[pokeball-1] < 0.42 and items_stock[pokeball+1]+30 < berries_count:
                                    # If it's not the VIP type, we don't want to waste our ultra ball if no balls left.
                                    if items_stock[1] == 0 and items_stock[2] == 0:
                                        break

                                    success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                    logger.log('Catch Rate with normal Pokeball is low ({}%). Thinking to throw a {}... ({} left!)'.format(success_percentage,self.item_list[str(berry_id)],berries_count-1))
                                    response_dict = self.api.use_item_capture(item_id=berry_id,
                                        encounter_id=encounter_id,
                                        spawn_point_id=self.spawn_point_guid
                                    )
                                    if response_dict and response_dict['status_code'] is 1 and 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                        for i in range(len(catch_rate)):
                                            if 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                                catch_rate[i] = catch_rate[i] * response_dict['responses']['USE_ITEM_CAPTURE']['item_capture_mult']
                                        success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                        berries_count = berries_count -1
                                        berry_used = True
                                        logger.log('Threw a berry! Catch Rate with normal Pokeball has increased to {}%'.format(success_percentage))
                                    else:
                                        if response_dict['status_code'] is 1:
                                            logger.log('Fail to use berry. Seem like you are softbanned.', 'red')
                                        else:
                                            logger.log('Fail to use berry. Status Code: {}'.format(response_dict['status_code']),'red')

                                else:
                                    #We don't have many berry to waste, pick a good ball first. Save some berry for future VIP pokemon
                                    current_type = pokeball
                                    while current_type < 2:
                                        current_type += 1
                                        if catch_rate[pokeball-1] < 0.35 and items_stock[current_type] > 0:
                                            # if current ball chance to catch is under 35%, and player has better ball - then use it
                                            pokeball = current_type # use better ball

                                #if the rate is still low and we didn't throw a berry before use berry
                                if catch_rate[pokeball-1] < 0.35 and berries_count > 0 and berry_used == False:
                                    # If it's not the VIP type, we don't want to waste our ultra ball if no balls left.
                                    if items_stock[1] == 0 and items_stock[2] == 0:
                                        break

                                    success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                    logger.log('Catch Rate with normal Pokeball is low ({}%). Thinking to throw a {}... ({} left!)'.format(success_percentage,self.item_list[str(berry_id)],berries_count-1))
                                    response_dict = self.api.use_item_capture(item_id=berry_id,
                                        encounter_id=encounter_id,
                                        spawn_point_id=self.spawn_point_guid
                                    )
                                    if response_dict and response_dict['status_code'] is 1 and 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                        for i in range(len(catch_rate)):
                                            if 'item_capture_mult' in response_dict['responses']['USE_ITEM_CAPTURE']:
                                                catch_rate[i] = catch_rate[i] * response_dict['responses']['USE_ITEM_CAPTURE']['item_capture_mult']
                                        success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                                        berries_count = berries_count -1
                                        berry_used = True
                                        logger.log('Threw a berry! Catch Rate with normal Pokeball has increased to {}%'.format(success_percentage))
                                    else:
                                        if response_dict['status_code'] is 1:
                                            logger.log('Fail to use berry. Seem like you are softbanned.', 'red')
                                        else:
                                            logger.log('Fail to use berry. Status Code: {}'.format(response_dict['status_code']),'red')

                                # Re-check if berry is used, find a ball for a good capture rate
                                current_type=pokeball
                                while current_type < 2:
                                    current_type += 1
                                    if catch_rate[pokeball-1] < 0.35 and items_stock[current_type] > 0:
                                        pokeball = current_type # use better ball

                                # This is to avoid rare case that a berry has ben throwed <0.42
                                # and still picking normal pokeball (out of stock) -> error
                                if items_stock[1] == 0 and items_stock[2] > 0:
                                    pokeball = 2

                                # Add this logic to avoid Pokeball = 0, Great Ball = 0, Ultra Ball = X
                                # And this logic saves Ultra Balls if it's a weak trash pokemon
                                if catch_rate[pokeball-1]<0.30 and items_stock[3]>0:
                                    pokeball = 3

                            # Randomize the quality of the throw
                            # Example of the structure
                            throw_parameters = {'normalized_reticle_size': 1.950,
                                                'spin_modifier': 1.0,
                                                'normalized_hit_position': 1.0,
                                                'throw_type_label' : 'Excellent'}
                            self.generate_random_throw_parameters_if_necessary(throw_parameters)

                            items_stock[pokeball] -= 1
                            success_percentage = '{0:.2f}'.format(catch_rate[pokeball - 1] * 100)
                            logger.log('Using {} ({}), (chance: {}%)... ({} left!)'.format(
                                self.item_list[str(pokeball)],
                                throw_parameters.get('throw_type_label'),
                                success_percentage,
                                items_stock[pokeball]
                            ))

                            id_list1 = self.count_pokemon_inventory()

                            response_dict = self.api.catch_pokemon(
                                encounter_id=encounter_id,
                                pokeball=pokeball,
                                normalized_reticle_size=throw_parameters['normalized_reticle_size'],
                                spawn_point_id=self.spawn_point_guid,
                                hit_pokemon=1,
                                spin_modifier=throw_parameters['spin_modifier'],
                                normalized_hit_position=throw_parameters['normalized_hit_position']
                            )

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
                                        response_dict = self.api.evolve_pokemon(pokemon_id=pokemon_to_transfer[0])
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
        response_dict = self.api.get_inventory()

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

        request = self.api.create_request()
        if 'spawn_point_id' in self.pokemon:
            spawn_point_id = self.pokemon['spawn_point_id']
            self.spawn_point_guid = spawn_point_id
            self.response_key = 'ENCOUNTER'
            self.response_status_key = 'status'
            request.encounter(
                encounter_id=encounter_id,
                spawn_point_id=spawn_point_id,
                player_latitude=player_latitude,
                player_longitude=player_longitude
            )
        else:
            fort_id = self.pokemon['fort_id']
            self.spawn_point_guid = fort_id
            self.response_key = 'DISK_ENCOUNTER'
            self.response_status_key = 'result'
            request.disk_encounter(
                encounter_id=encounter_id,
                fort_id=fort_id,
                player_latitude=player_latitude,
                player_longitude=player_longitude
            )
        return request.call()

    def check_vip_pokemon(self,pokemon, cp, iv):

        vip_name = self.config.vips.get(pokemon)
        if vip_name == {}:
            return True
        else:
            catch_config = self.config.vips.get("any")
            if not catch_config:
                return False
            cp_iv_logic = catch_config.get('logic', 'or')
        catch_results = {
            'cp': False,
            'iv': False,
        }

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
        return logic_to_function[cp_iv_logic](*catch_results.values())

    def generate_random_throw_parameters_if_necessary(self, throw_parameters):

        # First, randomize spin
        spin_success_rate = self.config.catch_throw_parameters.get('spin_success_rate', 1)

        if random() <= spin_success_rate:
            throw_parameters['spin_modifier'] = 0.5 + 0.5 * random()
        else:
            throw_parameters['spin_modifier'] = 0.499 * random()

        # Then, randomize the throw quality
        throw_excellent_chance = self.config.catch_throw_parameters.get('excellent_rate', 0)
        throw_great_chance = self.config.catch_throw_parameters.get('great_rate', 0)
        throw_nice_chance = self.config.catch_throw_parameters.get('nice_rate', 0)
        throw_normal_throw_chance = self.config.catch_throw_parameters.get('normal_rate', 0)

        # Total every chance types, pick a random number in the range and check what type of throw we got
        total_chances = throw_excellent_chance + throw_great_chance \
                        + throw_nice_chance + throw_normal_throw_chance

        random_throw = random() * total_chances

        if random_throw <= throw_excellent_chance:
            throw_parameters['normalized_reticle_size'] = 1.70 + 0.25*random()
            throw_parameters['normalized_hit_position'] = 1.0
            throw_parameters['throw_type_label'] = 'Excellent'
            return

        random_throw -= throw_excellent_chance
        if random_throw <= throw_great_chance:
            throw_parameters['normalized_reticle_size'] = 1.30 + 0.399 * random()
            throw_parameters['normalized_hit_position'] = 1.0
            throw_parameters['throw_type_label'] = 'Great'
            return

        random_throw -= throw_great_chance
        if random_throw <= throw_nice_chance:
            throw_parameters['normalized_reticle_size'] = 1.00 + 0.299 * random()
            throw_parameters['normalized_hit_position'] = 1.0
            throw_parameters['throw_type_label'] = 'Nice'
            return

        # Not a any kind of special throw, let's throw a normal one
        # Here the reticle size doesn't matter, we scored out of it
        throw_parameters['normalized_reticle_size'] = 1.25 + 0.70 * random()
        throw_parameters['normalized_hit_position'] = 0.0
        throw_parameters['throw_type_label'] = 'Normal'

