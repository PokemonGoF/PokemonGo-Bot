# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import time
import json
import sys
from collections import OrderedDict

from random import random, randrange, uniform
from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.inventory import Pokemon
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_dir import _base_dir
from datetime import datetime, timedelta
from .utils import getSeconds

CATCH_STATUS_SUCCESS = 1
CATCH_STATUS_FAILED = 2
CATCH_STATUS_VANISHED = 3
CATCH_STATUS_MISSED = 4

ENCOUNTER_STATUS_SUCCESS = 1
ENCOUNTER_STATUS_NOT_IN_RANGE = 5
ENCOUNTER_STATUS_POKEMON_INVENTORY_FULL = 7
INCENSE_ENCOUNTER_AVAILABLE = 1
INCENSE_ENCOUNTER_NOT_AVAILABLE = 2

ITEM_POKEBALL = 1
ITEM_GREATBALL = 2
ITEM_ULTRABALL = 3
ITEM_RAZZBERRY = 701
ITEM_PINAPBERRY = 705

DEFAULT_UNSEEN_AS_VIP = True

LOGIC_TO_FUNCTION = {
    'or': lambda x, y, z: x or y or z,
    'and': lambda x, y, z: x and y and z,
    'orand': lambda x, y, z: x or y and z,
    'andor': lambda x, y, z: x and y or z
}

DEBUG_ON = False

class PokemonCatchWorker(BaseTask):

    def __init__(self, pokemon, bot, config={}):
        self.pokemon = pokemon

        # Load CatchPokemon config if no config supplied
        if not config:
            for value in bot.workers:
                if hasattr(value, 'catch_pokemon'):
                    config = value.config

        self.config = config

        super(PokemonCatchWorker, self).__init__(bot, config)
        if self.config.get('debug', False): DEBUG_ON = True


    def initialize(self):
        self.position = self.bot.position
        self.pokemon_list = self.bot.pokemon_list
        self.inventory = inventory.items()
        self.pokedex = inventory.pokedex()
        self.spawn_point_guid = ''
        self.response_key = ''
        self.response_status_key = ''
        self.rest_completed = False
        self.caught_last_24 = 0

        #Config
        self.min_ultraball_to_keep = self.config.get('min_ultraball_to_keep', 10)
        self.berry_threshold = self.config.get('berry_threshold', 0.35)
        self.vip_berry_threshold = self.config.get('vip_berry_threshold', 0.9)
        self.treat_unseen_as_vip = self.config.get('treat_unseen_as_vip', DEFAULT_UNSEEN_AS_VIP)
        self.daily_catch_limit = self.config.get('daily_catch_limit', 800)
        self.use_pinap_on_vip = self.config.get('use_pinap_on_vip', False)

        self.vanish_settings = self.config.get('vanish_settings', {})
        self.consecutive_vanish_limit = self.vanish_settings.get('consecutive_vanish_limit', 10)
        self.rest_duration_min = getSeconds(self.vanish_settings.get('rest_duration_min', "02:00:00"))
        self.rest_duration_max = getSeconds(self.vanish_settings.get('rest_duration_max', "04:00:00"))

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

        responses = response_dict['responses']
        response = responses[self.response_key]
        if response[self.response_status_key] != ENCOUNTER_STATUS_SUCCESS and response[self.response_status_key] != INCENSE_ENCOUNTER_AVAILABLE:
            if response[self.response_status_key] == ENCOUNTER_STATUS_NOT_IN_RANGE:
                self.emit_event('pokemon_not_in_range', formatted='Pokemon went out of range!')
            elif response[self.response_status_key] == INCENSE_ENCOUNTER_NOT_AVAILABLE:
                self.emit_event('pokemon_not_in_range', formatted='Incensed Pokemon went out of range!')
            elif response[self.response_status_key] == ENCOUNTER_STATUS_POKEMON_INVENTORY_FULL:
                self.emit_event('pokemon_inventory_full', formatted='Your Pokemon inventory is full! Could not catch!')
            return WorkerResult.ERROR

        # get pokemon data
        pokemon_data = response['wild_pokemon']['pokemon_data'] if 'wild_pokemon' in response else response['pokemon_data']
        pokemon = Pokemon(pokemon_data)

        # check if vip pokemon
        is_vip = self._is_vip_pokemon(pokemon)

        # skip ignored pokemon
        if (not self._should_catch_pokemon(pokemon) and not is_vip) or self.bot.catch_disabled:
            if not hasattr(self.bot,'skipped_pokemon'):
                self.bot.skipped_pokemon = []

            # Check if pokemon already skipped and suppress alert if so
            for skipped_pokemon in self.bot.skipped_pokemon:
                if pokemon.pokemon_id == skipped_pokemon.pokemon_id and \
                    pokemon.cp_exact == skipped_pokemon.cp_exact and \
                    pokemon.ivcp == skipped_pokemon.ivcp:
                    return WorkerResult.SUCCESS

            if self.bot.catch_disabled:
                self.logger.info("Not catching {}. All catching tasks are currently disabled until {}.".format(pokemon,self.bot.catch_resume_at.strftime("%H:%M:%S")))
            # Add the encounter_id to the Pokemon
            pokemon.encounter_id = self.pokemon['encounter_id']
            self.bot.skipped_pokemon.append(pokemon)

            self.emit_event(
                'pokemon_appeared',
                formatted='Skip ignored {pokemon}! (CP: {cp} IV: {iv} A/D/S: {iv_display} Shiny: {shiny})',
                data={
                    'pokemon': pokemon.name,
                    'cp': str(int(pokemon.cp)),
                    'iv': str(pokemon.iv),
                    'iv_display': str(pokemon.iv_display),
                    'shiny': pokemon.shiny,
                }
            )
            return WorkerResult.SUCCESS

        if inventory.items().get(ITEM_POKEBALL).count < 1:
            if inventory.items().get(ITEM_GREATBALL).count < 1:
                if inventory.items().get(ITEM_ULTRABALL).count < 1:
                    return WorkerResult.ERROR
                elif (not is_vip) and inventory.items().get(ITEM_ULTRABALL).count <= self.min_ultraball_to_keep:
                    return WorkerResult.ERROR

        # log encounter
        self.emit_event(
            'pokemon_appeared',
            formatted='A wild {} appeared! (CP: {} IV: {} A/D/S: {} NCP: {} Shiny: {})'.format(pokemon.name, pokemon.cp,  pokemon.iv, pokemon.iv_display, round(pokemon.cp_percent, 2),pokemon.shiny, ),
            data={
                'pokemon': pokemon.name,
                'ncp': round(pokemon.cp_percent, 2),
                'cp': pokemon.cp,
                'iv': pokemon.iv,
                'iv_display': pokemon.iv_display,
                'encounter_id': self.pokemon['encounter_id'],
                'latitude': self.pokemon['latitude'],
                'longitude': self.pokemon['longitude'],
                'pokemon_id': pokemon.pokemon_id,
                'shiny': pokemon.shiny,
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


        while True:
            if result[0] < self.daily_catch_limit:
            # catch that pokemon!
                encounter_id = self.pokemon['encounter_id']
                catch_rate_by_ball = [0] + response['capture_probability']['capture_probability']  # offset so item ids match indces
                self._do_catch(pokemon, encounter_id, catch_rate_by_ball, is_vip=is_vip)
                break
            else:
                self.emit_event('catch_limit', formatted='WARNING! You have reached your daily catch limit')
                sys.exit(2)
                break

        # simulate app
        time.sleep(5)

    def create_encounter_api_call(self):
        encounter_id = self.pokemon['encounter_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']

        request = self.bot.api.create_request()
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
        elif 'fort_id' in self.pokemon:
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
        else:
            # This must be a incensed mon
            self.response_key = 'INCENSE_ENCOUNTER'
            self.response_status_key = 'result'
            request.incense_encounter(
                encounter_id=encounter_id,
                encounter_location=self.pokemon['encounter_location']
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
            'fa': True,
            'ca': True
        }

        catch_logic = pokemon_config.get('logic', default_logic)

        candies = inventory.candies().get(pokemon.pokemon_id).quantity
        threshold = pokemon_config.get('candy_threshold', -1)
        if threshold > 0 and candies >= threshold: # Got enough candies
            return False

        if pokemon_config.get('never_catch', False):
            return False

        if pokemon_config.get('always_catch', False):
            return True

        if pokemon_config.get('catch_above_ncp',-1) >= 0:
            if pokemon.cp_percent >= pokemon_config.get('catch_above_ncp'):
                catch_results['ncp'] = True

        if pokemon_config.get('catch_above_cp',-1) >= 0:
            if pokemon.cp >= pokemon_config.get('catch_above_cp'):
                catch_results['cp'] = True

        if pokemon_config.get('catch_below_cp',-1) >= 0:
            if pokemon.cp <= pokemon_config.get('catch_below_cp'):
                catch_results['cp'] = True

        if pokemon_config.get('catch_above_iv',-1) >= 0:
            if pokemon.iv > pokemon_config.get('catch_above_iv', pokemon.iv):
                catch_results['iv'] = True

        catch_results['fa'] = ( len(pokemon_config.get('fast_attack', [])) == 0 or unicode(pokemon.fast_attack) in map(lambda x: unicode(x), pokemon_config.get('fast_attack', [])))
        catch_results['ca'] = ( len(pokemon_config.get('charged_attack', [])) == 0 or unicode(pokemon.charged_attack) in map(lambda x: unicode(x), pokemon_config.get('charged_attack', [])))

        self.bot.logger.debug("Our comparison results: FA: {}, CA: {}, CP: {}, NCP: {}, IV: {}".format(catch_results['fa'], catch_results['ca'], catch_results['cp'],  catch_results['ncp'], catch_results['iv']))

        # check if encountered pokemon is our locked pokemon
        if self.bot.capture_locked and self.bot.capture_locked != pokemon.pokemon_id:
            self.bot.logger.debug("Pokemon locked!")
            return False

        # build catch results
        cr = {
            'ncp': False,
            'cp': False,
            'iv': False
        }
        if catch_logic == 'and':
            cr['ncp'] = True,
            cr['cp'] = True,
            cr['iv'] = True
        elif catch_logic == 'andor':
            cr['ncp'] = True,
            cr['cp'] = True
        elif catch_logic == 'orand':
            cr['cp'] = True,
            cr['iv'] = True

        if pokemon_config.get('catch_above_ncp',-1) >= 0: cr['ncp'] = catch_results['ncp']
        if pokemon_config.get('catch_above_cp',-1) >= 0: cr['cp'] = catch_results['cp']
        if pokemon_config.get('catch_below_cp',-1) >= 0: cr['cp'] = catch_results['cp']
        if pokemon_config.get('catch_above_iv',-1) >= 0: cr['iv'] = catch_results['iv']

        if DEBUG_ON:
            print "Debug information for match rules..."
            print "catch_results ncp = {}".format(catch_results['ncp'])
            print "catch_results cp = {}".format(catch_results['cp'])
            print "catch_results iv = {}".format(catch_results['iv'])
            print "cr = {}".format(cr)
            print "catch_above_ncp = {}".format(pokemon_config.get('catch_above_ncp'))
            print "catch_above_cp iv = {}".format(pokemon_config.get('catch_above_cp'))
            print "catch_below_cp iv = {}".format(pokemon_config.get('catch_below_cp'))
            print "catch_above_iv iv = {}".format(pokemon_config.get('catch_above_iv'))
            print "Pokemon {}".format(pokemon.name)
            print "pokemon ncp = {}".format(pokemon.cp_percent)
            print "pokemon cp = {}".format(pokemon.cp)
            print "pokemon iv = {}".format(pokemon.iv)
            print "catch logic = {}".format(catch_logic)

        if LOGIC_TO_FUNCTION[catch_logic](*cr.values()):
            return catch_results['fa'] and catch_results['ca']
        else:
            return False

    def _should_catch_pokemon(self, pokemon):
        return self._pokemon_matches_config(self.bot.config.catch, pokemon)

    def _is_vip_pokemon(self, pokemon):
        # having just a name present in the list makes them vip
        # Not seen pokemons also will become vip if it's not disabled in config
        if self.bot.config.vips.get(pokemon.name) == {} or (self.treat_unseen_as_vip and not self.pokedex.seen(pokemon.pokemon_id)):
            return True
        # Treat all shiny pokemon as VIP!
        if pokemon.shiny:
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

        response_dict = self.bot.api.use_item_encounter(
            item=berry_id,
            encounter_id=encounter_id,
            spawn_point_guid=self.spawn_point_guid
        )
        responses = response_dict['responses']

        if response_dict['status_code'] == 1:

            # update catch rates using multiplier
            if 'capture_probability' in responses['USE_ITEM_ENCOUNTER']:
                for rate in catch_rate_by_ball:
                    new_catch_rate_by_ball.append(float(responses['USE_ITEM_ENCOUNTER']['capture_probability']['capture_probability'][current_ball-1]))
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

        if self.use_pinap_on_vip and is_vip:
            berry_id = ITEM_PINAPBERRY
        else:
            berry_id = ITEM_RAZZBERRY

        berry_count = self.inventory.get(berry_id).count

        ball_count = {}
        for ball_id in [ITEM_POKEBALL, ITEM_GREATBALL, ITEM_ULTRABALL]:
            ball_count[ball_id] = self.inventory.get(ball_id).count

        # use `min_ultraball_to_keep` from config if is not None
        min_ultraball_to_keep = ball_count[ITEM_ULTRABALL]
        if self.min_ultraball_to_keep is not None and self.min_ultraball_to_keep >= 0:
            min_ultraball_to_keep = self.min_ultraball_to_keep

        maximum_ball = ITEM_GREATBALL if ball_count[ITEM_ULTRABALL] < min_ultraball_to_keep else ITEM_ULTRABALL
        ideal_catch_rate_before_throw = self.vip_berry_threshold if is_vip else self.berry_threshold

        used_berry = False
        original_catch_rate_by_ball = catch_rate_by_ball
        while True:

            # find lowest available ball
            current_ball = ITEM_POKEBALL
            while ball_count[current_ball] == 0 and current_ball < maximum_ball:
                current_ball += 1
            if ball_count[current_ball] == 0:
                self.emit_event('no_pokeballs', formatted='No pokeballs left! Fleeing...')
                return WorkerResult.ERROR

            # check future ball count
            num_next_balls = 0
            next_ball = current_ball
            while next_ball < maximum_ball:
                next_ball += 1
                num_next_balls += ball_count[next_ball]

            # If pinap berry is not enough, use razz berry
            if berry_count == 0 and self.use_pinap_on_vip:
                if berry_id == ITEM_PINAPBERRY:
                    berry_id = ITEM_RAZZBERRY
                    berry_count = self.inventory.get(berry_id).count
                else:
                    berry_id = ITEM_PINAPBERRY
                    berry_count = self.inventory.get(berry_id).count

            # check if we've got berries to spare
            berries_to_spare = berry_count > 0 if is_vip else berry_count > num_next_balls + 30

            changed_ball = False

            # use pinap if config set to true
            if self.use_pinap_on_vip and is_vip and berries_to_spare and not used_berry:
                self._use_berry(berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball)
                self.inventory.get(berry_id).remove(1)
                berry_count -= 1
                used_berry = True

            # use a berry if we are under our ideal rate and have berries to spare
            if catch_rate_by_ball[current_ball] < ideal_catch_rate_before_throw and berries_to_spare and not used_berry:
                new_catch_rate_by_ball = self._use_berry(berry_id, berry_count, encounter_id, catch_rate_by_ball, current_ball)
                if new_catch_rate_by_ball != catch_rate_by_ball:
                    catch_rate_by_ball = new_catch_rate_by_ball
                    self.inventory.get(berry_id).remove(1)
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
                    self.inventory.get(berry_id).remove(1)
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

            response_dict = self.bot.api.catch_pokemon(
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
                catch_rate_by_ball = original_catch_rate_by_ball

                # sleep according to flee_count and flee_duration config settings
                # randomly chooses a number of times to 'show' wobble animation between 1 and flee_count
                # multiplies this by flee_duration to get total sleep
                if self.catchsim_flee_count:
                    sleep((randrange(self.catchsim_flee_count)+1) * self.catchsim_flee_duration)

                continue

            # abandon if pokemon vanished
            elif catch_pokemon_status == CATCH_STATUS_VANISHED:
                #insert into DB
                with self.bot.database as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='vanish_log'")
                result = c.fetchone()

                while True:
                    if result[0] == 1:
                        conn.execute('''INSERT INTO vanish_log (pokemon, cp, iv, encounter_id, pokemon_id) VALUES (?, ?, ?, ?, ?)''', (pokemon.name, pokemon.cp, pokemon.iv, str(encounter_id), pokemon.pokemon_id))
                    break
                else:
                    self.emit_event(
                        'vanish_log',
                        sender=self,
                        level='info',
                        formatted="vanish_log table not found, skipping log"
                    )
                    break

                self.emit_event(
                    'pokemon_vanished',
                    formatted='{} vanished!'.format(pokemon.name),
                    data={
                        'pokemon': pokemon.name,
                        'encounter_id': self.pokemon['encounter_id'],
                        'latitude': self.pokemon['latitude'],
                        'longitude': self.pokemon['longitude'],
                        'pokemon_id': pokemon.pokemon_id
                    }
                )

                with self.bot.database as conn:
                    c = conn.cursor()
                    c.execute("SELECT DISTINCT COUNT(encounter_id) FROM vanish_log WHERE dated > (SELECT dated FROM catch_log WHERE dated IN (SELECT MAX(dated) FROM catch_log))")

                result = c.fetchone()
                self.consecutive_vanishes_so_far = result[0]

                if self.rest_completed == False and self.consecutive_vanishes_so_far >= self.consecutive_vanish_limit:
                    self.start_rest()

                if self._pct(catch_rate_by_ball[current_ball]) == 100:
                    self.bot.softban = True

            # pokemon caught!
            elif catch_pokemon_status == CATCH_STATUS_SUCCESS:
                if self.rest_completed == True:
                    self.rest_completed = False
                pokemon.unique_id = response_dict['responses']['CATCH_POKEMON']['captured_pokemon_id']
                self.bot.metrics.captured_pokemon(pokemon.name, pokemon.cp, pokemon.iv_display, pokemon.iv)

                awards = response_dict['responses']['CATCH_POKEMON']['capture_award']
                exp_gain, candy_gain, stardust_gain = self.extract_award(awards)
                with self.bot.database as conn:
                    c = conn.cursor()
                    c.execute(
                        "SELECT DISTINCT COUNT(encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")

                result = c.fetchone()

                if is_vip:
                    self.emit_event(
                        'pokemon_vip_caught',
                        formatted='Vip Captured {pokemon}! (CP: {cp} IV: {iv} {iv_display} NCP: {ncp} Shiny: {shiny}) Catch Limit: ({caught_last_24_hour}/{daily_catch_limit}) +{exp} exp +{stardust} stardust',
                        data={
                            'pokemon': pokemon.name,
                            'ncp': str(round(pokemon.cp_percent, 2)),
                            'cp': str(int(pokemon.cp)),
                            'iv': str(pokemon.iv),
                            'iv_display': str(pokemon.iv_display),
                            'shiny': pokemon.shiny,
                            'exp': str(exp_gain),
                            'stardust': stardust_gain,
                            'encounter_id': str(self.pokemon['encounter_id']),
                            'latitude': str(self.pokemon['latitude']),
                            'longitude': str(self.pokemon['longitude']),
                            'pokemon_id': str(pokemon.pokemon_id),
                            'caught_last_24_hour': str(result[0]),
                            'daily_catch_limit': str(self.daily_catch_limit)
                        }
                    )

                else:
                    self.emit_event(
                        'pokemon_caught',
                        formatted='Captured {pokemon}! (CP: {cp} IV: {iv} {iv_display} NCP: {ncp} Shiny: {shiny}) Catch Limit: ({caught_last_24_hour}/{daily_catch_limit}) +{exp} exp +{stardust} stardust',
                        data={
                            'pokemon': pokemon.name,
                            'ncp': str(round(pokemon.cp_percent, 2)),
                            'cp': str(int(pokemon.cp)),
                            'iv': str(pokemon.iv),
                            'iv_display': str(pokemon.iv_display),
                            'shiny': pokemon.shiny,
                            'exp': str(exp_gain),
                            'stardust': stardust_gain,
                            'encounter_id': str(self.pokemon['encounter_id']),
                            'latitude': str(self.pokemon['latitude']),
                            'longitude': str(self.pokemon['longitude']),
                            'pokemon_id': str(pokemon.pokemon_id),
                            'caught_last_24_hour': str(result[0]),
                            'daily_catch_limit': str(self.daily_catch_limit)
                        }
                    )


                inventory.pokemons().add(pokemon)
                inventory.player().exp += exp_gain
                self.bot.stardust += stardust_gain
                candy = inventory.candies().get(pokemon.pokemon_id)
                candy.add(candy_gain)

                self.emit_event(
                    'gained_candy',
                    formatted='Candy gained: {gained_candy}. You now have {quantity} {type} candy!',
                    data = {
                        'gained_candy': str(candy_gain),
                        'quantity': candy.quantity,
                        'type': candy.type
                    },
                )

                self.bot.softban = False


                try:
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
                        json.dump(OrderedDict({
                            'datetime': str(datetime.now()),
                            'pokemon': pokemon.name,
                            'cp': pokemon.cp,
                            'iv': pokemon.iv,
                            'encounter_id': self.pokemon['encounter_id'],
                            'pokemon_id': pokemon.pokemon_id,
                            'latitude': self.pokemon['latitude'],
                            'longitude': self.pokemon['longitude']
                        }), outfile)
                        outfile.write('\n')

                    # if it is a new pokemon to our dex, simulate app animation delay
                    if exp_gain >= 500:
                        sleep (randrange(self.catchsim_newtodex_wait_min, self.catchsim_newtodex_wait_max))

                except IOError as e:
                    self.logger.info('[x] Error while opening location file: %s' % e)

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

    def extract_award(self, awards):
        return sum(awards['xp']), sum(awards['candy']), sum(awards['stardust'])

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

    def start_rest(self):
        duration = int(uniform(self.rest_duration_min, self.rest_duration_max))
        resume = datetime.now() + timedelta(seconds=duration)

        self.emit_event(
            'vanish_limit_reached',
            formatted="Vanish limit reached! Taking a rest now for {duration}, will resume at {resume}.",
            data={
                'duration': str(timedelta(seconds=duration)),
                'resume': resume.strftime("%H:%M:%S")
            }
        )

        sleep(duration)
        self.rest_completed = True
        self.bot.login()
