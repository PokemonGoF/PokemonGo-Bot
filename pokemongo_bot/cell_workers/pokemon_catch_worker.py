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
            return WorkerResult.ERROR
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
                'encounter_id': self.pokemon['encounter_id'],
                'latitude': self.pokemon['latitude'],
                'longitude': self.pokemon['longitude'],
                'pokemon_id': pokemon.num
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
                        'new_catch_rate': self._pct(new_catch_rate_by_ball[current_ball])
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
                    data={
                        'pokemon': pokemon.name,
                        'encounter_id': self.pokemon['encounter_id'],
                        'latitude': self.pokemon['latitude'],
                        'longitude': self.pokemon['longitude'],
                        'pokemon_id': pokemon.num
                    }
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
                        'exp': sum(response_dict['responses']['CATCH_POKEMON']['capture_award']['xp']),
                        'encounter_id': self.pokemon['encounter_id'],
                        'latitude': self.pokemon['latitude'],
                        'longitude': self.pokemon['longitude'],
                        'pokemon_id': pokemon.num
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

            break
