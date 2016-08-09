# -*- coding: utf-8 -*-

import time
from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import normalized_reticle_size, sleep, spin_modifier
from pokemongo_bot.worker_result import WorkerResult

CATCH_STATUS_SUCCESS = 1
CATCH_STATUS_FAILED = 2
CATCH_STATUS_VANISHED = 3

ENCOUNTER_STATUS_SUCCESS = 1
ENCOUNTER_STATUS_NOT_IN_RANGE = 5
ENCOUNTER_STATUS_POKEMON_INVENTORY_FULL = 7

ITEM_POKEBALL = 1
ITEM_GREATBALL = 2
ITEM_ULTRABALL = 3
ITEM_RAZZBERRY = 701

LOGIC_TO_FUNCTION = {
    'or': lambda x, y: x or y,
    'and': lambda x, y: x and y
}


class Pokemon(object):

    def __init__(self, pokemon_list, pokemon_data):
        self.num = int(pokemon_data['pokemon_id'])
        self.name = pokemon_list[int(self.num) - 1]['Name']
        self.cp = pokemon_data['cp']
        self.attack = pokemon_data.get('individual_attack', 0)
        self.defense = pokemon_data.get('individual_defense', 0)
        self.stamina = pokemon_data.get('individual_stamina', 0)

    @property
    def iv(self):
        return round((self.attack + self.defense + self.stamina) / 45.0, 2)

    @property
    def iv_display(self):
        return '{}/{}/{}'.format(self.attack, self.defense, self.stamina)


class PokemonCatchWorker(BaseTask):

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

    ############################################################################
    # public methods
    ############################################################################

    def work(self, response_dict=None):
        response_dict = response_dict or self.create_encounter_api_call()

        # validate response
        if not response_dict:
<<<<<<< HEAD
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

                                msg = 'A wild {pokemon} appeared! [CP {cp}] [Potential {iv}] [S/A/D {iv_display}]'
                                self.emit_event(
                                    'pokemon_appeared',
                                    formatted=msg,
                                    data={
                                        'pokemon': pokemon_name,
                                        'cp': cp,
                                        'iv': pokemon_potential,
                                        'iv_display': iv_display,
                                    }
                                )

                                pokemon_data['name'] = pokemon_name
                                # Simulate app
                                sleep(3)

                        if not self.should_capture_pokemon(pokemon_name, cp, pokemon_potential, response_dict):
                            return False

                        flag_VIP = False
                        # @TODO, use the best ball in stock to catch VIP (Very Important Pokemon: Configurable)
                        if self.check_vip_pokemon(pokemon_name, cp, pokemon_potential):
                            self.emit_event(
                                'vip_pokemon',
                                formatted='This is a VIP pokemon. Catch!!!'
                            )
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
                                    self.emit_event(
                                        'pokemon_catch_rate',
                                        level='debug',
                                        formatted="Catch rate of {catch_rate} is low. Maybe will throw {berry_name} ({berry_count} left)",
                                        data={
                                            'catch_rate': success_percentage,
                                            'berry_name': self.item_list[str(berry_id)],
                                            'berry_count': berries_count
                                        }
                                    )
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
                                        self.emit_event(
                                            'threw_berry',
                                            formatted="Threw a {berry_name}! Catch rate now: {new_catch_rate}",
                                            data={
                                                "berry_name": self.item_list[str(berry_id)],
                                                "new_catch_rate": success_percentage
                                            }
                                        )
                                    else:
                                        if response_dict['status_code'] is 1:
                                            self.emit_event(
                                                'softban',
                                                level='warning',
                                                formatted='Failed to use berry. You may be softbanned.'
                                            )
                                        else:
                                            self.emit_event(
                                                'threw_berry_failed',
                                                formatted='Unknown response when throwing berry: {status_code}.',
                                                data={
                                                    'status_code': response_dict['status_code']
                                                }
                                            )

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
                                    self.emit_event(
                                        'pokemon_catch_rate',
                                        level='debug',
                                        formatted="Catch rate of {catch_rate} is low. Maybe will throw {berry_name} ({berry_count} left)",
                                        data={
                                            'catch_rate': success_percentage,
                                            'berry_name': self.item_list[str(berry_id)],
                                            'berry_count': berries_count-1
                                        }
                                    )
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
                                        self.emit_event(
                                            'threw_berry',
                                            formatted="Threw a {berry_name}! Catch rate now: {new_catch_rate}",
                                            data={
                                                "berry_name": self.item_list[str(berry_id)],
                                                "new_catch_rate": success_percentage
                                            }
                                        )
                                    else:
                                        if response_dict['status_code'] is 1:
                                            self.emit_event(
                                                'softban',
                                                level='warning',
                                                formatted='Failed to use berry. You may be softbanned.'
                                            )
                                        else:
                                            self.emit_event(
                                                'threw_berry_failed',
                                                formatted='Unknown response when throwing berry: {status_code}.',
                                                data={
                                                    'status_code': response_dict['status_code']
                                                }
                                            )

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
                                    self.emit_event(
                                        'pokemon_catch_rate',
                                        level='debug',
                                        formatted="Catch rate of {catch_rate} is low. Throwing {berry_name} ({berry_count} left)",
                                        data={
                                            'catch_rate': success_percentage,
                                            'berry_name': self.item_list[str(berry_id)],
                                            'berry_count': berries_count-1
                                        }
                                    )
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
                                        self.emit_event(
                                            'threw_berry',
                                            formatted="Threw a {berry_name}! Catch rate now: {new_catch_rate}",
                                            data={
                                                "berry_name": self.item_list[str(berry_id)],
                                                "new_catch_rate": success_percentage
                                            }
                                        )
                                    else:
                                        if response_dict['status_code'] is 1:
                                            self.emit_event(
                                                'softban',
                                                level='warning',
                                                formatted='Failed to use berry. You may be softbanned.'
                                            )
                                        else:
                                            self.emit_event(
                                                'threw_berry_failed',
                                                formatted='Unknown response when throwing berry: {status_code}.',
                                                data={
                                                    'status_code': response_dict['status_code']
                                                }
                                            )

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

                            items_stock[pokeball] -= 1
                            success_percentage = '{0:.2f}'.format(catch_rate[pokeball - 1] * 100)
                            self.emit_event(
                                'threw_pokeball',
                                formatted='Used {pokeball}, with chance {success_percentage} ({count_left} left)',
                                data={
                                    'pokeball': self.item_list[str(pokeball)],
                                    'success_percentage': success_percentage,
                                    'count_left': items_stock[pokeball]
                                }
                            )
                            id_list1 = self.count_pokemon_inventory()

                            reticle_size_parameter = normalized_reticle_size(self.config.catch_randomize_reticle_factor)
                            spin_modifier_parameter = spin_modifier(self.config.catch_randomize_spin_factor)

                            response_dict = self.api.catch_pokemon(
                                encounter_id=encounter_id,
                                pokeball=pokeball,
                                normalized_reticle_size=reticle_size_parameter,
                                spawn_point_id=self.spawn_point_guid,
                                hit_pokemon=1,
                                spin_modifier=spin_modifier_parameter,
                                normalized_hit_position=1
                            )

                            if response_dict and \
                                            'responses' in response_dict and \
                                            'CATCH_POKEMON' in response_dict['responses'] and \
                                            'status' in response_dict['responses']['CATCH_POKEMON']:
                                status = response_dict['responses'][
                                    'CATCH_POKEMON']['status']
                                if status is 2:
                                    self.emit_event(
                                        'pokemon_escaped',
                                        formatted="{pokemon} escaped.",
                                        data={'pokemon': pokemon_name}
                                    )
                                    sleep(2)
                                    continue
                                if status is 3:
                                    self.emit_event(
                                        'pokemon_vanished',
                                        formatted="{pokemon} vanished!",
                                        data={'pokemon': pokemon_name}
                                    )
                                    if success_percentage == 100:
                                        self.softban = True
                                if status is 1:
                                    self.bot.metrics.captured_pokemon(pokemon_name, cp, iv_display, pokemon_potential)

                                    self.emit_event(
                                        'pokemon_caught',
                                        formatted='Captured {pokemon}! [CP {cp}] [Potential {iv}] [{iv_display}] [+{exp} exp]',
                                        data={
                                            'pokemon': pokemon_name,
                                            'cp': cp,
                                            'iv': pokemon_potential,
                                            'iv_display': iv_display,
                                            'exp': sum(response_dict['responses']['CATCH_POKEMON']['capture_award']['xp'])
                                        }
                                    )
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
                                            self.emit_event(
                                                'pokemon_evolved',
                                                formatted="{pokemon} evolved!",
                                                data={'pokemon': pokemon_name}
                                            )
                                        else:
                                            self.emit_event(
                                                'pokemon_evolve_fail',
                                                formatted="Failed to evolve {pokemon}!",
                                                data={'pokemon': pokemon_name}
                                            )
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
=======
            return WorkerResult.ERROR
>>>>>>> update_title_stats_on_terminal
        try:
            responses = response_dict['responses']
            response = responses[self.response_key]
            if response[self.response_status_key] != ENCOUNTER_STATUS_SUCCESS:
                if response[self.response_status_key] == ENCOUNTER_STATUS_NOT_IN_RANGE:
                    self.emit_event('pokemon_not_in_range', formatted='Pokemon went out of range!')
                elif response[self.response_status_key] == ENCOUNTER_STATUS_POKEMON_INVENTORY_FULL:
                    self.emit_event('pokemon_inventory_full', formatted='Your Pokemon inventory is full! Could not catch!')
                return WorkerResult.ERROR
        except KeyError:
            return WorkerResult.ERROR

        # get pokemon data
        pokemon_data = response['wild_pokemon']['pokemon_data'] if 'wild_pokemon' in response else response['pokemon_data']
        pokemon = Pokemon(self.pokemon_list, pokemon_data)

        # skip ignored pokemon
        if not self._should_catch_pokemon(pokemon):
            return WorkerResult.SUCCESS

        # log encounter
        self.emit_event(
            'pokemon_appeared',
            formatted='A wild {pokemon} appeared! [CP {cp}] [Potential {iv}] [A/D/S {iv_display}]',
            data={
                'pokemon': pokemon.name,
                'cp': pokemon.cp,
                'iv': pokemon.iv,
                'iv_display': pokemon.iv_display,
            }
        )

        # simulate app
        sleep(3)

        # check for VIP pokemon
        is_vip = self._is_vip_pokemon(pokemon)
        if is_vip:
            self.emit_event('vip_pokemon', formatted='This is a VIP pokemon. Catch!!!')

        # catch that pokemon!
        encounter_id = self.pokemon['encounter_id']
        catch_rate_by_ball = [0] + response['capture_probability']['capture_probability']  # offset so item ids match indces
        self._do_catch(pokemon, encounter_id, catch_rate_by_ball, is_vip=is_vip)

        # simulate app
        time.sleep(5)

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

    ############################################################################
    # helpers
    ############################################################################

    def _pokemon_matches_config(self, config, pokemon, default_logic='and'):
        pokemon_config = config.get(pokemon.name, config.get('any'))

        if not pokemon_config:
            return False

        catch_results = {
            'cp': False,
            'iv': False,
        }

        if pokemon_config.get('never_catch', False):
            return False

        if pokemon_config.get('always_catch', False):
            return True

        catch_cp = pokemon_config.get('catch_above_cp', 0)
        if pokemon.cp > catch_cp:
            catch_results['cp'] = True

        catch_iv = pokemon_config.get('catch_above_iv', 0)
        if pokemon.iv > catch_iv:
            catch_results['iv'] = True

        return LOGIC_TO_FUNCTION[pokemon_config.get('logic', default_logic)](*catch_results.values())

    def _should_catch_pokemon(self, pokemon):
        return self._pokemon_matches_config(self.config.catch, pokemon)

    def _is_vip_pokemon(self, pokemon):
        # having just a name present in the list makes them vip
        if self.config.vips.get(pokemon.name) == {}:
            return True
        return self._pokemon_matches_config(self.config.vips, pokemon, default_logic='or')

    def _get_current_pokemon_ids(self):
        # don't use cached bot.get_inventory() here because we need to have actual information in capture logic
        response_dict = self.api.get_inventory()

        try:
            inventory_items = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        except KeyError:
            return []  # no items

        id_list = []
        for item in inventory_items:
            try:
                pokemon = item['inventory_item_data']['pokemon_data']
            except KeyError:
                continue

            # ignore eggs
            if pokemon.get('is_egg'):
                continue

            id_list.append(pokemon['id'])

        return id_list

    def _pct(self, rate_by_ball):
        return '{0:.2f}'.format(rate_by_ball * 100)

    def _use_berry(self, berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball):
        new_catch_rate_by_ball = []
        self.emit_event(
            'pokemon_catch_rate',
            level='debug',
            formatted='Catch rate of {catch_rate} with {ball_name} is low. Throwing {berry_name} (have {berry_count})',
            data={
                'catch_rate': self._pct(catch_rate_by_ball[current_ball]),
                'ball_name': self.item_list[str(current_ball)],
                'berry_name': self.item_list[str(berry_id)],
                'berry_count': berry_count
            }
        )

        response_dict = self.api.use_item_capture(
            item_id=berry_id,
            encounter_id=encounter_id,
            spawn_point_id=self.spawn_point_guid
        )
        responses = response_dict['responses']

        if response_dict and response_dict['status_code'] == 1:

            # update catch rates using multiplier
            if 'item_capture_mult' in responses['USE_ITEM_CAPTURE']:
                for rate in catch_rate_by_ball:
                    new_catch_rate_by_ball.append(rate * responses['USE_ITEM_CAPTURE']['item_capture_mult'])
                self.emit_event(
                    'threw_berry',
                    formatted="Threw a {berry_name}! Catch rate with {ball_name} is now: {new_catch_rate}",
                    data={
                        'berry_name': self.item_list[str(berry_id)],
                        'ball_name': self.item_list[str(current_ball)],
                        'new_catch_rate': self._pct(catch_rate_by_ball[current_ball])
                    }
                )

            # softban?
            else:
                new_catch_rate_by_ball = catch_rate_by_ball
                self.emit_event(
                    'softban',
                    level='warning',
                    formatted='Failed to use berry. You may be softbanned.'
                )

        # unknown status code
        else:
            new_catch_rate_by_ball = catch_rate_by_ball
            self.emit_event(
                'threw_berry_failed',
                formatted='Unknown response when throwing berry: {status_code}.',
                data={
                    'status_code': response_dict['status_code']
                }
            )

        return new_catch_rate_by_ball

    def _do_catch(self, pokemon, encounter_id, catch_rate_by_ball, is_vip=False):
        # settings that may be exposed at some point
        berry_id = ITEM_RAZZBERRY
        maximum_ball = ITEM_ULTRABALL if is_vip else ITEM_GREATBALL
        ideal_catch_rate_before_throw = 0.9 if is_vip else 0.35

        berry_count = self.bot.item_inventory_count(berry_id)
        items_stock = self.bot.current_inventory()

        while True:

            # find lowest available ball
            current_ball = ITEM_POKEBALL
            while items_stock[current_ball] == 0 and current_ball < maximum_ball:
                current_ball += 1
            if items_stock[current_ball] == 0:
                self.emit_event('no_pokeballs', formatted='No usable pokeballs found!')
                break

            # check future ball count
            num_next_balls = 0
            next_ball = current_ball
            while next_ball < maximum_ball:
                next_ball += 1
                num_next_balls += items_stock[next_ball]

            # check if we've got berries to spare
            berries_to_spare = berry_count > 0 if is_vip else berry_count > num_next_balls + 30

            # use a berry if we are under our ideal rate and have berries to spare
            used_berry = False
            if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and berries_to_spare:
                catch_rate_by_ball = self._use_berry(berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball)
                berry_count -= 1
                used_berry = True

            # pick the best ball to catch with
            best_ball = current_ball
            while best_ball < maximum_ball:
                best_ball += 1
                if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and items_stock[best_ball] > 0:
                    # if current ball chance to catch is under our ideal rate, and player has better ball - then use it
                    current_ball = best_ball

            # if the rate is still low and we didn't throw a berry before, throw one
            if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and berry_count > 0 and not used_berry:
                catch_rate_by_ball = self._use_berry(berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball)
                berry_count -= 1

            # get current pokemon list before catch
            pokemon_before_catch = self._get_current_pokemon_ids()

            # try to catch pokemon!
            items_stock[current_ball] -= 1
            self.emit_event(
                'threw_pokeball',
                formatted='Used {ball_name}, with chance {success_percentage} ({count_left} left)',
                data={
                    'ball_name': self.item_list[str(current_ball)],
                    'success_percentage': self._pct(catch_rate_by_ball[current_ball]),
                    'count_left': items_stock[current_ball]
                }
            )

            reticle_size_parameter = normalized_reticle_size(self.config.catch_randomize_reticle_factor)
            spin_modifier_parameter = spin_modifier(self.config.catch_randomize_spin_factor)

            response_dict = self.api.catch_pokemon(
                encounter_id=encounter_id,
                pokeball=current_ball,
                normalized_reticle_size=reticle_size_parameter,
                spawn_point_id=self.spawn_point_guid,
                hit_pokemon=1,
                spin_modifier=spin_modifier_parameter,
                normalized_hit_position=1
            )

            try:
                catch_pokemon_status = response_dict['responses']['CATCH_POKEMON']['status']
            except KeyError:
                break

            # retry failed pokemon
            if catch_pokemon_status == CATCH_STATUS_FAILED:
                self.emit_event(
                    'pokemon_capture_failed',
                    formatted='{pokemon} capture failed.. trying again!',
                    data={'pokemon': pokemon.name}
                )
                sleep(2)
                continue

            # abandon if pokemon vanished
            elif catch_pokemon_status == CATCH_STATUS_VANISHED:
                self.emit_event(
                    'pokemon_vanished',
                    formatted='{pokemon} vanished!',
                    data={'pokemon': pokemon.name}
                )
                if self._pct(catch_rate_by_ball[current_ball]) == 100:
                    self.bot.softban = True

            # pokemon caught!
            elif catch_pokemon_status == CATCH_STATUS_SUCCESS:
                self.bot.metrics.captured_pokemon(pokemon.name, pokemon.cp, pokemon.iv_display, pokemon.iv)
                self.emit_event(
                    'pokemon_caught',
                    formatted='Captured {pokemon}! [CP {cp}] [Potential {iv}] [{iv_display}] [+{exp} exp]',
                    data={
                        'pokemon': pokemon.name,
                        'cp': pokemon.cp,
                        'iv': pokemon.iv,
                        'iv_display': pokemon.iv_display,
                        'exp': sum(response_dict['responses']['CATCH_POKEMON']['capture_award']['xp'])
                    }
                )

                # We could refresh here too, but adding 3 saves a inventory request
                candy = inventory.candies().get(pokemon.num)
                candy.add(3)
                self.emit_event(
                    'gained_candy',
                    formatted='You now have {quantity} {type} candy!',
                    data = {
                        'quantity': candy.quantity,
                        'type': candy.type,
                    },
                )

                self.bot.softban = False

                # evolve pokemon if necessary
                if self.config.evolve_captured and (self.config.evolve_captured[0] == 'all' or pokemon.name in self.config.evolve_captured):
                    pokemon_after_catch = self._get_current_pokemon_ids()
                    pokemon_to_evolve = list(set(pokemon_after_catch) - set(pokemon_before_catch))

                    if len(pokemon_to_evolve) == 0:
                        break

                    self._do_evolve(pokemon, pokemon_to_evolve[0])

            break

    def _do_evolve(self, pokemon, new_pokemon_id):
        response_dict = self.api.evolve_pokemon(pokemon_id=new_pokemon_id)
        catch_pokemon_status = response_dict['responses']['EVOLVE_POKEMON']['result']

        if catch_pokemon_status == 1:
            self.emit_event(
                'pokemon_evolved',
                formatted='{pokemon} evolved!',
                data={'pokemon': pokemon.name}
            )
        else:
            self.emit_event(
                'pokemon_evolve_fail',
                formatted='Failed to evolve {pokemon}!',
                data={'pokemon': pokemon.name}
            )
