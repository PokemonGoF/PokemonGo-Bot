# -*- coding: utf-8 -*-

import os
import time
import json
import logging
import time
from random import random, randrange
from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.inventory import Pokemon
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.datastore import Datastore
from pokemongo_bot.base_dir import _base_dir
from datetime import datetime, timedelta

CATCH_STATUS_SUCCESS = 1
CATCH_STATUS_FAILED = 2
CATCH_STATUS_VANISHED = 3
CATCH_STATUS_MISSED = 4

ENCOUNTER_STATUS_SUCCESS = 1
ENCOUNTER_STATUS_NOT_IN_RANGE = 5
ENCOUNTER_STATUS_POKEMON_INVENTORY_FULL = 7

ITEM_POKEBALL = 1
ITEM_GREATBALL = 2
ITEM_ULTRABALL = 3
ITEM_RAZZBERRY = 701

DEFAULT_UNSEEN_AS_VIP = True

LOGIC_TO_FUNCTION = {
    'or': lambda x, y, z: x or y or z,
    'and': lambda x, y, z: x and y and z,
    'orand': lambda x, y, z: x or y and z,
    'andor': lambda x, y, z: x and y or z
}


class PokemonCatchWorker(Datastore, BaseTask):

    def __init__(self, pokemon, bot, config):
        self.pokemon = pokemon
        super(PokemonCatchWorker, self).__init__(bot, config)

    def initialize(self):
        self.api = self.bot.api
        self.position = self.bot.position
        self.pokemon_list = self.bot.pokemon_list
        self.inventory = inventory.items()
        self.pokedex = inventory.pokedex()
        self.spawn_point_guid = ''
        self.response_key = ''
        self.response_status_key = ''

        #Config
        self.min_ultraball_to_keep = self.config.get('min_ultraball_to_keep', 10)
        self.berry_threshold = self.config.get('berry_threshold', 0.35)
        self.vip_berry_threshold = self.config.get('vip_berry_threshold', 0.9)
        self.treat_unseen_as_vip = self.config.get('treat_unseen_as_vip', DEFAULT_UNSEEN_AS_VIP)
        self.daily_catch_limit = self.config.get('daily_catch_limit', 800)

        self.catch_throw_parameters = self.config.get('catch_throw_parameters', {})
        self.catch_throw_parameters_spin_success_rate = self.catch_throw_parameters.get('spin_success_rate', 0.6)
        self.catch_throw_parameters_excellent_rate = self.catch_throw_parameters.get('excellent_rate', 0.1)
        self.catch_throw_parameters_great_rate = self.catch_throw_parameters.get('great_rate', 0.5)
        self.catch_throw_parameters_nice_rate = self.catch_throw_parameters.get('nice_rate', 0.3)
        self.catch_throw_parameters_normal_rate = self.catch_throw_parameters.get('normal_rate', 0.1)
        self.catch_throw_parameters_hit_rate = self.catch_throw_parameters.get('hit_rate', 0.8)

        self.catchsim_config = self.config.get('catch_simulation', {})
        self.catchsim_catch_wait_min = self.catchsim_config.get('catch_wait_min', 2)
        self.catchsim_catch_wait_max = self.catchsim_config.get('catch_wait_max', 6)
        self.catchsim_flee_count = int(self.catchsim_config.get('flee_count', 3))
        self.catchsim_flee_duration = self.catchsim_config.get('flee_duration', 2)
        self.catchsim_berry_wait_min = self.catchsim_config.get('berry_wait_min', 2)
        self.catchsim_berry_wait_max = self.catchsim_config.get('berry_wait_max', 3)
        self.catchsim_changeball_wait_min = self.catchsim_config.get('changeball_wait_min', 2)
        self.catchsim_changeball_wait_max = self.catchsim_config.get('changeball_wait_max', 3)
        self.catchsim_newtodex_wait_min = self.catchsim_config.get('newtodex_wait_min', 20)
        self.catchsim_newtodex_wait_max = self.catchsim_config.get('newtodex_wait_max', 30)


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
        pokemon = Pokemon(pokemon_data)

        # skip ignored pokemon
        if not self._should_catch_pokemon(pokemon):
            self.emit_event(
                'pokemon_appeared',
                formatted='Skip ignored {pokemon}! [CP {cp}] [Potential {iv}] [A/D/S {iv_display}]',
                data={
                    'pokemon': pokemon.name,
                    'cp': pokemon.cp,
                    'iv': pokemon.iv,
                    'iv_display': pokemon.iv_display,
                }
            )
            return WorkerResult.SUCCESS

        is_vip = self._is_vip_pokemon(pokemon)
        if inventory.items().get(ITEM_POKEBALL).count < 1:
            if inventory.items().get(ITEM_GREATBALL).count < 1:
                if inventory.items().get(ITEM_ULTRABALL).count < 1:
                    return WorkerResult.ERROR
                elif (not is_vip) and inventory.items().get(ITEM_ULTRABALL).count <= self.min_ultraball_to_keep:
                    return WorkerResult.ERROR

        # log encounter
        self.emit_event(
            'pokemon_appeared',
            formatted='A wild {pokemon} appeared! [CP {cp}] [NCP {ncp}] [Potential {iv}] [A/D/S {iv_display}]',
            data={
                'pokemon': pokemon.name,
                'ncp': round(pokemon.cp_percent, 2),
                'cp': pokemon.cp,
                'iv': pokemon.iv,
                'iv_display': pokemon.iv_display,
                'encounter_id': self.pokemon['encounter_id'],
                'latitude': self.pokemon['latitude'],
                'longitude': self.pokemon['longitude'],
                'pokemon_id': pokemon.pokemon_id
            }
        )

        # simulate app
        time.sleep(3)

        # check for VIP pokemon
        if is_vip:
            self.emit_event('vip_pokemon', formatted='This is a VIP pokemon. Catch!!!')

        # check catch limits before catch
        with self.bot.database as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT COUNT(encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")

        result = c.fetchone()
        self.caught_last_24_hour = result[0]

        while True:
            if self.caught_last_24_hour < self.daily_catch_limit:
            # catch that pokemon!
                encounter_id = self.pokemon['encounter_id']
                catch_rate_by_ball = [0] + response['capture_probability']['capture_probability']  # offset so item ids match indces
                self._do_catch(pokemon, encounter_id, catch_rate_by_ball, is_vip=is_vip)
                break
            else:
                self.emit_event('catch_limit', formatted='WARNING! You have reached your daily catch limit')
                break

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
            'ncp': False,
            'cp': False,
            'iv': False,
        }

        candies = inventory.candies().get(pokemon.pokemon_id).quantity
        threshold = pokemon_config.get('candy_threshold', -1 )
        if( threshold > 0 and candies >= threshold  ):
            self.emit_event(
                'ignore_candy_above_thresold',
                level='info',
                formatted='Amount of candies for {name} is {amount}, greater than threshold {threshold}',
                data={
                    'name': pokemon.name,
                    'amount': candies ,
                    'threshold' : threshold
                }
            )
            return False



        if pokemon_config.get('never_catch', False):
            return False

        if pokemon_config.get('always_catch', False):
            return True

        catch_ncp = pokemon_config.get('catch_above_ncp', 0.8)
        if pokemon.cp_percent > catch_ncp:
            catch_results['ncp'] = True

        catch_cp = pokemon_config.get('catch_above_cp', 1200)
        if pokemon.cp > catch_cp:
            catch_results['cp'] = True

        catch_iv = pokemon_config.get('catch_above_iv', 0.8)
        if pokemon.iv > catch_iv:
            catch_results['iv'] = True

        return LOGIC_TO_FUNCTION[pokemon_config.get('logic', default_logic)](*catch_results.values())

    def _should_catch_pokemon(self, pokemon):
        return self._pokemon_matches_config(self.bot.config.catch, pokemon)

    def _is_vip_pokemon(self, pokemon):
        # having just a name present in the list makes them vip
        # Not seen pokemons also will become vip if it's not disabled in config
        if self.bot.config.vips.get(pokemon.name) == {} or (self.treat_unseen_as_vip and not self.pokedex.seen(pokemon.pokemon_id)):
            return True
        return self._pokemon_matches_config(self.bot.config.vips, pokemon, default_logic='or')

    def _pct(self, rate_by_ball):
        return '{0:.2f}'.format(rate_by_ball * 100)

    def _use_berry(self, berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball):
        # Delay to simulate selecting berry
        action_delay(self.catchsim_berry_wait_min, self.catchsim_berry_wait_max)
        new_catch_rate_by_ball = []
        self.emit_event(
            'pokemon_catch_rate',
            level='debug',
            formatted='Catch rate of {catch_rate} with {ball_name} is low. Throwing {berry_name} (have {berry_count})',
            data={
                'catch_rate': self._pct(catch_rate_by_ball[current_ball]),
                'ball_name': self.inventory.get(current_ball).name,
                'berry_name': self.inventory.get(berry_id).name,
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
                        'berry_name': self.inventory.get(berry_id).name,
                        'ball_name': self.inventory.get(current_ball).name,
                        'new_catch_rate': self._pct(new_catch_rate_by_ball[current_ball])
                    }
                )

            # softban?
            else:
                new_catch_rate_by_ball = catch_rate_by_ball
                self.bot.softban = True
                self.emit_event(
                    'softban',
                    level='warning',
                    formatted='Failed to use berry. You may be softbanned.'
                )
                with self.bot.database as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='softban_log'")
                result = c.fetchone()

                while True:
                    if result[0] == 1:
                        source = str("PokemonCatchWorker")
                        status = str("Possible Softban")
                        conn.execute('''INSERT INTO softban_log (status, source) VALUES (?, ?)''', (status, source))
                    break
                else:
                    self.emit_event(
                        'softban_log',
                        sender=self,
                        level='info',
                        formatted="softban_log table not found, skipping log"
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
        """

        :type pokemon: Pokemon
        """
        berry_id = ITEM_RAZZBERRY
        maximum_ball = ITEM_ULTRABALL if is_vip else ITEM_GREATBALL
        ideal_catch_rate_before_throw = self.vip_berry_threshold if is_vip else self.berry_threshold

        berry_count = self.inventory.get(ITEM_RAZZBERRY).count
        ball_count = {}
        for ball_id in [ITEM_POKEBALL, ITEM_GREATBALL, ITEM_ULTRABALL]:
            ball_count[ball_id] = self.inventory.get(ball_id).count

        # use `min_ultraball_to_keep` from config if is not None
        min_ultraball_to_keep = ball_count[ITEM_ULTRABALL]
        if self.min_ultraball_to_keep is not None:
            if self.min_ultraball_to_keep >= 0 and self.min_ultraball_to_keep < min_ultraball_to_keep:
                min_ultraball_to_keep = self.min_ultraball_to_keep

        used_berry = False
        while True:

            # find lowest available ball
            current_ball = ITEM_POKEBALL
            while ball_count[current_ball] == 0 and current_ball < maximum_ball:
                current_ball += 1
            if ball_count[current_ball] == 0:
                # use untraball if there is no other balls with constraint to `min_ultraball_to_keep`
                if maximum_ball != ITEM_ULTRABALL and ball_count[ITEM_ULTRABALL] > min_ultraball_to_keep:
                    maximum_ball = ITEM_ULTRABALL
                    self.emit_event('enough_ultraballs', formatted='No regular balls left! Trying ultraball.')
                    continue
                else:
                    self.emit_event('no_pokeballs', formatted='No pokeballs left! Fleeing...')
                    return WorkerResult.ERROR

            # check future ball count
            num_next_balls = 0
            next_ball = current_ball
            while next_ball < maximum_ball:
                next_ball += 1
                num_next_balls += ball_count[next_ball]

            # check if we've got berries to spare
            berries_to_spare = berry_count > 0 if is_vip else berry_count > num_next_balls + 30

            # use a berry if we are under our ideal rate and have berries to spare
            changed_ball = False
            if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and berries_to_spare and not used_berry:
                new_catch_rate_by_ball = self._use_berry(berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball)
                if new_catch_rate_by_ball != catch_rate_by_ball:
                    catch_rate_by_ball = new_catch_rate_by_ball
                    self.inventory.get(ITEM_RAZZBERRY).remove(1)
                    berry_count -= 1
                    used_berry = True

            # pick the best ball to catch with
            best_ball = current_ball
            while best_ball < maximum_ball:
                best_ball += 1
                if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and ball_count[best_ball] > 0:
                    # if current ball chance to catch is under our ideal rate, and player has better ball - then use it
                    current_ball = best_ball
                    changed_ball = True

            # if the rate is still low and we didn't throw a berry before, throw one
            if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and berry_count > 0 and not used_berry:
                new_catch_rate_by_ball = self._use_berry(berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball)
                if new_catch_rate_by_ball != catch_rate_by_ball:
                    catch_rate_by_ball = new_catch_rate_by_ball
                    self.inventory.get(ITEM_RAZZBERRY).remove(1)
                    berry_count -= 1
                    used_berry = True

            # If we change ball then wait to simulate user selecting it
            if changed_ball:
                action_delay(self.catchsim_changeball_wait_min, self.catchsim_changeball_wait_max)

            # Randomize the quality of the throw
            # Default structure
            throw_parameters = {'normalized_reticle_size': 1.950,
                                'spin_modifier': 1.0,
                                'normalized_hit_position': 1.0,
                                'throw_type_label': 'Excellent'}
            self.generate_spin_parameter(throw_parameters)
            self.generate_throw_quality_parameters(throw_parameters)

            # try to catch pokemon!
            ball_count[current_ball] -= 1
            self.inventory.get(current_ball).remove(1)
            # Take some time to throw the ball from config options
            action_delay(self.catchsim_catch_wait_min, self.catchsim_catch_wait_max)
            self.emit_event(
                'threw_pokeball',
                formatted='{throw_type}{spin_label} throw! Used {ball_name}, with chance {success_percentage} ({count_left} left)',
                data={
                    'throw_type': throw_parameters['throw_type_label'],
                    'spin_label': throw_parameters['spin_label'],
                    'ball_name': self.inventory.get(current_ball).name,
                    'success_percentage': self._pct(catch_rate_by_ball[current_ball]),
                    'count_left': ball_count[current_ball]
                }
            )

            hit_pokemon = 1
            if random() >= self.catch_throw_parameters_hit_rate and not is_vip:
                hit_pokemon = 0

            response_dict = self.api.catch_pokemon(
                encounter_id=encounter_id,
                pokeball=current_ball,
                normalized_reticle_size=throw_parameters['normalized_reticle_size'],
                spawn_point_id=self.spawn_point_guid,
                hit_pokemon=hit_pokemon,
                spin_modifier=throw_parameters['spin_modifier'],
                normalized_hit_position=throw_parameters['normalized_hit_position']
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
                used_berry = False

                # sleep according to flee_count and flee_duration config settings
                # randomly chooses a number of times to 'show' wobble animation between 1 and flee_count
                # multiplies this by flee_duration to get total sleep
                if self.catchsim_flee_count:
                    sleep((randrange(self.catchsim_flee_count)+1) * self.catchsim_flee_duration)

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
                        'pokemon_id': pokemon.pokemon_id
                    }
                )
                if self._pct(catch_rate_by_ball[current_ball]) == 100:
                    self.bot.softban = True

            # pokemon caught!
            elif catch_pokemon_status == CATCH_STATUS_SUCCESS:
                pokemon.unique_id = response_dict['responses']['CATCH_POKEMON']['captured_pokemon_id']
                self.bot.metrics.captured_pokemon(pokemon.name, pokemon.cp, pokemon.iv_display, pokemon.iv)

                try:
                    inventory.pokemons().add(pokemon)
                    exp_gain = sum(response_dict['responses']['CATCH_POKEMON']['capture_award']['xp'])
                    
                    self.emit_event(
                        'pokemon_caught',
                        formatted='Captured {pokemon}! [CP {cp}] [NCP {ncp}] [Potential {iv}] [{iv_display}] ({caught_last_24_hour}/{daily_catch_limit}) [+{exp} exp]',
                        data={
                            'pokemon': pokemon.name,
                            'ncp': round(pokemon.cp_percent, 2),
                            'cp': pokemon.cp,
                            'iv': pokemon.iv,
                            'iv_display': pokemon.iv_display,
                            'exp': exp_gain,
                            'encounter_id': self.pokemon['encounter_id'],
                            'latitude': self.pokemon['latitude'],
                            'longitude': self.pokemon['longitude'],
                            'pokemon_id': pokemon.pokemon_id,
                            'caught_last_24_hour': self.caught_last_24_hour + 1,
                            'daily_catch_limit': self.daily_catch_limit
                        }

                    )
                    with self.bot.database as conn:
                        c = conn.cursor()
                        c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='catch_log'")
                    result = c.fetchone()

                    while True:
                        if result[0] == 1:
                            conn.execute('''INSERT INTO catch_log (pokemon, cp, iv, encounter_id, pokemon_id) VALUES (?, ?, ?, ?, ?)''', (pokemon.name, pokemon.cp, pokemon.iv, str(encounter_id), pokemon.pokemon_id))
                        break
                    else:
                        self.emit_event(
                            'catch_log',
                            sender=self,
                            level='info',
                            formatted="catch_log table not found, skipping log"
                        )
                        break
                    user_data_caught = os.path.join(_base_dir, 'data', 'caught-%s.json' % self.bot.config.username)
                    with open(user_data_caught, 'ab') as outfile:
                        outfile.write(str(datetime.now()))
                        json.dump({
                            'pokemon': pokemon.name,
                            'cp': pokemon.cp,
                            'iv': pokemon.iv,
                            'encounter_id': self.pokemon['encounter_id'],
                            'pokemon_id': pokemon.pokemon_id
                        }, outfile)
                        outfile.write('\n')

                    # if it is a new pokemon to our dex, simulate app animation delay
                    if exp_gain >= 500:
                        sleep (randrange(self.catchsim_newtodex_wait_min, self.catchsim_newtodex_wait_max))

                except IOError as e:
                    self.logger.info('[x] Error while opening location file: %s' % e)

                candy = inventory.candies().get(pokemon.pokemon_id)
                candy.add(self.get_candy_gained_count(response_dict))

                self.emit_event(
                    'gained_candy',
                    formatted='You now have {quantity} {type} candy!',
                    data = {
                        'quantity': candy.quantity,
                        'type': candy.type,
                    },
                )

                self.bot.softban = False

            elif catch_pokemon_status == CATCH_STATUS_MISSED:
                self.emit_event(
                    'pokemon_capture_failed',
                    formatted='Pokeball thrown to {pokemon} missed.. trying again!',
                    data={'pokemon': pokemon.name}
                )
                # Take some time to throw the ball from config options
                action_delay(self.catchsim_catch_wait_min, self.catchsim_catch_wait_max)
                continue

            break

    def get_candy_gained_count(self, response_dict):
        total_candy_gained = 0
        for candy_gained in response_dict['responses']['CATCH_POKEMON']['capture_award']['candy']:
            total_candy_gained += candy_gained
        return total_candy_gained

    def generate_spin_parameter(self, throw_parameters):
        spin_success_rate = self.catch_throw_parameters_spin_success_rate
        if random() <= spin_success_rate:
            throw_parameters['spin_modifier'] = 0.5 + 0.5 * random()
            throw_parameters['spin_label'] = ' Curveball'
        else:
            throw_parameters['spin_modifier'] = 0.499 * random()
            throw_parameters['spin_label'] = ''

    def generate_throw_quality_parameters(self, throw_parameters):
        throw_excellent_chance = self.catch_throw_parameters_excellent_rate
        throw_great_chance = self.catch_throw_parameters_great_rate
        throw_nice_chance = self.catch_throw_parameters_nice_rate
        throw_normal_throw_chance = self.catch_throw_parameters_normal_rate

        # Total every chance types, pick a random number in the range and check what type of throw we got
        total_chances = throw_excellent_chance + throw_great_chance \
                        + throw_nice_chance + throw_normal_throw_chance

        random_throw = random() * total_chances

        if random_throw <= throw_excellent_chance:
            throw_parameters['normalized_reticle_size'] = 1.70 + 0.25 * random()
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
        throw_parameters['throw_type_label'] = 'OK'
