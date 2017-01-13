# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import time

from pgoapi.utilities import f2i
from pokemongo_bot import inventory

from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from utils import distance, format_time, fort_details

DEPLOY_REQUEST_RESULT_SUCCESS = 1
ERROR_ALREADY_HAS_POKEMON_ON_FORT = 2
ERROR_OPPOSING_TEAM_OWNS_FORT = 3
ERROR_FORT_IS_FULL = 4
ERROR_NOT_IN_RANGE = 5
ERROR_PLAYER_HAS_NO_TEAM = 6
ERROR_POKEMON_NOT_FULL_HP = 7
ERROR_PLAYER_BELOW_MINIMUM_LEVEL = 8


class DropPokemonInGym(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(DropPokemonInGym, self).__init__(bot, config)

    def initialize(self):
        self.order_by = self.config.get('order_by', 'cp')

    def should_run(self):
        if inventory.player.level() < 6:
            return False
        return True

    def work(self):
        gyms = self.get_friendly_gyms_in_range()

        if not self.should_run() or len(gyms) == 0:
            return WorkerResult.SUCCESS

        fort = forts[0]

        lat = fort['latitude']
        lng = fort['longitude']

        details = fort_details(self.bot, fort['id'], lat, lng)
        fort_name = details.get('name', 'Unknown')

        pokemon = self.get_best_pokemon_availible()

        response_dict = self.bot.api.fort_deploy_pokemon(
            fort_id=fort['id'],
            player_latitude=f2i(self.bot.position[0]),
            player_longitude=f2i(self.bot.position[1]),
            pokemon_id=pokemon.unique_id
        )

        if ('responses' in response_dict) and ('FORT_DEPLOY_POKEMON' in response_dict['responses']):
            spin_details = response_dict['responses']['FORT_DEPLOY_POKEMON']
            spin_result = spin_details.get('result', -1)

            if (spin_result == SPIN_REQUEST_RESULT_SUCCESS) or (spin_result == SPIN_REQUEST_RESULT_INVENTORY_FULL):
                self.bot.softban = False
                experience_awarded = spin_details.get('experience_awarded', 0)
                items_awarded = self.get_items_awarded_from_fort_spinned(response_dict)
                egg_awarded = spin_details.get('pokemon_data_egg', None)

                if egg_awarded is not None:
                    items_awarded[u'Egg'] = egg_awarded['egg_km_walked_target']

                if experience_awarded or items_awarded:
                    awards = ', '.join(["{}x {}".format(items_awarded[x], x) for x in items_awarded if x != u'Egg'])
                    if egg_awarded is not None:
                        awards += u', {} Egg'.format(egg_awarded['egg_km_walked_target'])
                    self.emit_event(
                        'spun_pokestop',
                        formatted="Spun pokestop {pokestop}. Experience awarded: {exp}. Items awarded: {items}",
                        data={
                            'pokestop': fort_name,
                            'exp': experience_awarded,
                            'items': awards
                        }
                    )
                else:
                    self.emit_event(
                        'pokestop_empty',
                        formatted='Found nothing in pokestop {pokestop}.',
                        data={'pokestop': fort_name}
                    )
                with self.bot.database as conn:
                    c = conn.cursor()
                    c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='pokestop_log'")
                result = c.fetchone()
                c.execute("SELECT DISTINCT COUNT(pokestop) FROM pokestop_log WHERE dated >= datetime('now','-1 day')")
                if c.fetchone()[0] >= self.config.get('daily_spin_limit', 2000):
                    self.emit_event('spin_limit', formatted='WARNING! You have reached your daily spin limit')
                    sys.exit(2)
                while True:
                    if result[0] == 1:
                        conn.execute('''INSERT INTO pokestop_log (pokestop, exp, items) VALUES (?, ?, ?)''', (fort_name, str(experience_awarded), str(items_awarded)))
                        break
                    else:
                        self.emit_event('pokestop_log',
                                        sender=self,
                                        level='info',
                                        formatted="pokestop_log table not found, skipping log")
                        break
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                self.bot.recent_forts = self.bot.recent_forts[1:] + [fort['id']]
            elif spin_result == SPIN_REQUEST_RESULT_OUT_OF_RANGE:
                self.emit_event(
                    'pokestop_out_of_range',
                    formatted="Pokestop {pokestop} out of range.",
                    data={'pokestop': fort_name}
                )
            elif spin_result == SPIN_REQUEST_RESULT_IN_COOLDOWN_PERIOD:
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    self.bot.fort_timeouts.update({fort["id"]: pokestop_cooldown})
                    seconds_since_epoch = time.time()
                    minutes_left = format_time(
                        (pokestop_cooldown / 1000) - seconds_since_epoch
                    )
                    self.emit_event(
                        'pokestop_on_cooldown',
                        formatted="Pokestop {pokestop} on cooldown. Time left: {minutes_left}.",
                        data={'pokestop': fort_name, 'minutes_left': minutes_left}
                    )
            else:
                self.emit_event(
                    'unknown_spin_result',
                    formatted="Unknown spint result {status_code}",
                    data={'status_code': str(spin_result)}
                )
            

                return WorkerResult.ERROR
        action_delay(self.spin_wait_min, self.spin_wait_max)

        if len(forts) > 1:
            return WorkerResult.RUNNING

        return WorkerResult.SUCCESS

    def get_best_pokemon_availible:
        pokemons = inventory.pokemons().all()
        def get_poke_info(info, pokemon):
            poke_info = {
                'cp': pokemon.cp,
                'iv': pokemon.iv,
                'ivcp': pokemon.ivcp,
                'ncp': pokemon.cp_percent,
                'level': pokemon.level,
                'hp': pokemon.hp,
                'dps': pokemon.moveset.dps
            }
            if info not in poke_info:
                raise ConfigException("order by {}' isn't available".format(self.order_by))
            return poke_info[info]

        pokemons_ordered = sorted(pokemons, key=lambda x: get_poke_info(self.order_by, x), reverse=True)
        return pokemons_ordered[0]

    def get_friendly_gyms_in_range(self):
        my_team = self.bot.player_data.get('team', 0)
        forts = [f for f in self.bot.cell["forts"] if ("latitude" in f) and ("owned_by_team" in f)]
        forts = filter(lambda fort: fort["owned_by_team"] == my_team, forts)

        if self.bot.config.replicate_gps_xy_noise:
            forts = filter(lambda fort: distance(
                self.bot.noised_position[0],
                self.bot.noised_position[1],
                fort['latitude'],
                fort['longitude']
            ) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE, forts)
        else:
            forts = filter(lambda fort: distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            ) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE, forts)

        return forts