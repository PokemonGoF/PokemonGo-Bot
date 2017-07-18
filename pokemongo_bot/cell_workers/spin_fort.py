# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime, timedelta
import sys
import time

from pgoapi.utilities import f2i
from pokemongo_bot import inventory

from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import action_delay
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from .utils import distance, format_time, fort_details

SPIN_REQUEST_RESULT_SUCCESS = 1
SPIN_REQUEST_RESULT_OUT_OF_RANGE = 2
SPIN_REQUEST_RESULT_IN_COOLDOWN_PERIOD = 3
SPIN_REQUEST_RESULT_INVENTORY_FULL = 4
SPIN_REQUEST_RESULT_POI_INACCESSIBLE = 5

LURE_REQUEST_RESULT_SUCCESS = 1
LURE_REQUEST_FORT_ALREADY_HAS_MODIFIER= 2
LURE_REQUEST_TOO_FAR_AWAY = 3
LURE_REQUEST_NO_ITEM_IN_INVENTORY = 4
LURE_REQUEST_POI_INACCESSIBLE = 5

class SpinFort(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(SpinFort, self).__init__(bot, config)

    def initialize(self):
        # 10 seconds from current time
        self.next_update = datetime.now() + timedelta(0, 10)
        self.fort_spins = 0
        self.streak_forts = []

        self.ignore_item_count = self.config.get("ignore_item_count", False)
        self.spin_wait_min = self.config.get("spin_wait_min", 2)
        self.spin_wait_max = self.config.get("spin_wait_max", 3)
        self.min_interval = int(self.config.get('min_interval', 120))
        self.exit_on_limit_reached = self.config.get("exit_on_limit_reached", True)
        self.use_lure = self.config.get("use_lure", False)
        self.try_to_keep_streak = self.config.get("try_to_keep_streak", True)

        # if self.try_to_keep_streak and len(self.bot.recent_forts) is not 10:
        #     self.logger.warn("You enabled the setting for keeping a 10 stop streak, but the number of recent forts is not set to 10! It is set to %s. This will cause the streak to fail!" % len(self.bot.recent_forts))

    def should_run(self):
        has_space_for_loot = inventory.Items.has_space_for_loot()
        if not has_space_for_loot and not self.ignore_item_count:
            self.emit_event(
                'inventory_full',
                formatted="Inventory is full. You might want to change your config to recycle more items if this message appears consistently."
            )
        return self.ignore_item_count or has_space_for_loot


    def work(self):
        forts = self.get_forts_in_range()

        with self.bot.database as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT COUNT(pokestop) FROM pokestop_log WHERE dated >= datetime('now','-1 day')")
        if c.fetchone()[0] >= self.config.get('daily_spin_limit', 2000):
           if self.exit_on_limit_reached:
               self.emit_event('spin_limit', formatted='WARNING! You have reached your daily spin limit')
               sys.exit(2)

           if datetime.now() >= self.next_update:
               self.emit_event('spin_limit', formatted='WARNING! You have reached your daily spin limit')
               self._compute_next_update()
               return WorkerResult.SUCCESS

        if not self.should_run() or len(forts) == 0:
            return WorkerResult.SUCCESS

        fort = forts[0]

        if fort['id'] in self.streak_forts:
            self.fort_spins = 1
            self.streak_forts = [fort['id']]
        elif self.fort_spins >= 10:
            self.fort_spins = 1
            self.streak_forts = [fort['id']]
        else:
            self.fort_spins += 1

        lat = fort['latitude']
        lng = fort['longitude']

        details = fort_details(self.bot, fort['id'], lat, lng)

        fort_name = details.get('name', 'Unknown')
        check_fort_modifier = details.get('modifiers', {})
        if self.use_lure and check_fort_modifier:
            # check_fort_modifier_id = check_fort_modifier[0].get('item_id')
            self.emit_event('lure_info', formatted='A lure is already in fort, skip deploying lure')

        if self.use_lure and not check_fort_modifier:
            # check lures availiblity
            lure_count = inventory.items().get(501).count

            if lure_count > 1: # Only use lures when there's more than one
                request = self.bot.api.create_request()
                request.add_fort_modifier(
                    modifier_type=501,
                    fort_id = fort['id'],
                    player_latitude = f2i(self.bot.position[0]),
                    player_longitude = f2i(self.bot.position[1])
                )
                response_dict = request.call()

                if ('responses' in response_dict) and ('ADD_FORT_MODIFIER' in response_dict['responses']):
                    add_modifier_deatils = response_dict['responses']['ADD_FORT_MODIFIER']
                    add_modifier_result = add_modifier_deatils.get('result', -1)
                    if (add_modifier_result == LURE_REQUEST_RESULT_SUCCESS):
                        self.emit_event('lure_success', formatted='You have successfully placed a lure')
                    if (add_modifier_result == LURE_REQUEST_FORT_ALREADY_HAS_MODIFIER):
                        self.emit_event('lure_failed', formatted='A lure has being placed before you try to do so')
                    if (add_modifier_result == LURE_REQUEST_TOO_FAR_AWAY):
                        self.emit_event('lure_failed', formatted='Pokestop out of range')
                    if (add_modifier_result == LURE_REQUEST_NO_ITEM_IN_INVENTORY):
                        self.emit_event('lure_not_enough', formatted='Not enough lure in inventory')
                    if (add_modifier_result == LURE_REQUEST_POI_INACCESSIBLE):
                        self.emit_event('lure_info', formatted='Unkown Error')
            else:
                self.emit_event('lure_not_enough', formatted='Not enough lure in inventory')

        request = self.bot.api.create_request()
        request.fort_search(
            fort_id=fort['id'],
            fort_latitude=lat,
            fort_longitude=lng,
            player_latitude=f2i(self.bot.position[0]),
            player_longitude=f2i(self.bot.position[1])
        )
        response_dict = request.call()

        if ('responses' in response_dict) and ('FORT_SEARCH' in response_dict['responses']):
            spin_details = response_dict['responses']['FORT_SEARCH']
            spin_result = spin_details.get('result', -1)

            if (spin_result == SPIN_REQUEST_RESULT_SUCCESS) or (spin_result == SPIN_REQUEST_RESULT_INVENTORY_FULL):
                self.bot.softban = False
                experience_awarded = spin_details.get('experience_awarded', 0)
                items_awarded = self.get_items_awarded_from_fort_spinned(response_dict)
                egg_awarded = spin_details.get('pokemon_data_egg', None)
                gym_badge_awarded = spin_details.get('awarded_gym_badge', None)
                chain_hack_sequence_number = spin_details.get('chain_hack_sequence_number', 0)

                if egg_awarded is not None:
                    items_awarded[u'Egg'] = egg_awarded['egg_km_walked_target']

                # if gym_badge_awarded is not None:
                #     self.logger.info("Gained a Gym Badge! %s" % gym_badge_awarded)
                #
                # if chain_hack_sequence_number > 0:
                #     self.logger.info("Chain hack sequence: %s" % chain_hack_sequence_number)

                if experience_awarded or items_awarded:
                    awards = ', '.join(["{}x {}".format(items_awarded[x], x) for x in items_awarded if x != u'Egg'])
                    if egg_awarded is not None:
                        awards += u', {} Egg'.format(egg_awarded['egg_km_walked_target'])
                    self.fort_spins = chain_hack_sequence_number

                    if "type" in fort and fort["type"] == 1:
                        # It's a Pokestop
                        stop_kind = "pokestop"
                    else:
                        # It's a gym
                        stop_kind = "gym"

                    self.emit_event(
                        'spun_pokestop',
                        formatted="Spun {stop_kind} {pokestop} ({spin_amount_now} streak). Experience awarded: {exp}. Items awarded: {items}",
                        data={
                            'stop_kind': stop_kind,
                            'pokestop': fort_name,
                            'exp': experience_awarded,
                            'spin_amount_now': chain_hack_sequence_number,
                            'items': awards
                        }
                    )
                    #time.sleep(10)
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
            elif spin_result == SPIN_REQUEST_RESULT_POI_INACCESSIBLE:
                self.logger.info("Pokestop not accessable at this time.")
                self.bot.fort_timeouts[fort["id"]] = (time.time() + 300) * 1000  # Don't spin for 5m
            else:
                self.emit_event(
                    'unknown_spin_result',
                    formatted="Unknown spint result {status_code}",
                    data={'status_code': str(spin_result)}
                )
            if 'chain_hack_sequence_number' in response_dict['responses'][
                    'FORT_SEARCH']:
                action_delay(self.spin_wait_min, self.spin_wait_max)
                return response_dict['responses']['FORT_SEARCH'][
                    'chain_hack_sequence_number']
            else:
                self.emit_event(
                    'pokestop_searching_too_often',
                    formatted="Possibly searching too often, take a rest."
                )
                if spin_result == 1 and not items_awarded and not experience_awarded and not pokestop_cooldown:
                    self.bot.softban = True
                    self.emit_event(
                        'softban',
                        formatted='Probably got softban.'
                    )
                    with self.bot.database as conn:
                        c = conn.cursor()
                        c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='softban_log'")
                    result = c.fetchone()

                    if result[0] == 1:
                        source = str("SpinFort")
                        status = str("Possible Softban")
                        conn.execute('''INSERT INTO softban_log (status, source) VALUES (?, ?)''', (status, source))
                    else:
                        self.emit_event('softban_log',
                                        sender=self,
                                        level='info',
                                        formatted="softban_log table not found, skipping log")

                self.bot.fort_timeouts[fort["id"]] = (time.time() + 300) * 1000  # Don't spin for 5m

                return WorkerResult.ERROR
        action_delay(self.spin_wait_min, self.spin_wait_max)

        if len(forts) > 1:
            return WorkerResult.RUNNING

        return WorkerResult.SUCCESS

    def get_forts_in_range(self):
        forts = self.bot.get_forts(order_by_distance=True)
        forts = filter(lambda fort: fort["id"] not in self.bot.fort_timeouts, forts)
        if self.bot.camping_forts and self.try_to_keep_streak:
            if datetime.now() >= self.next_update:
                self.logger.info("Camping forts, ignoring 10 stops streak.")
        elif self.try_to_keep_streak:
            if len(self.streak_forts) > 10:
                self.streak_forts.pop()
            # Remove all forts which were spun in the last ticks to keep 10 stops streak
            forts = filter(lambda x: x["id"] not in self.streak_forts, forts)

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

    def get_items_awarded_from_fort_spinned(self, response_dict):
        experience_awarded = response_dict['responses']['FORT_SEARCH'].get('experience_awarded', 0)
        inventory.player().exp += experience_awarded

        items_awarded = response_dict['responses']['FORT_SEARCH'].get('items_awarded', {})
        loot = response_dict['responses']['FORT_SEARCH'].get('loot', {})
        bonus_loot = response_dict['responses']['FORT_SEARCH'].get('bonus_loot', {})
        team_bonus_loot = response_dict['responses']['FORT_SEARCH'].get('team_bonus_loot', {})
        tmp_count_items = {}

        if loot:
            # self.logger.info("Loot: %s" % loot)
            for item_awarded in loot['loot_item']:
                item_awarded_id = item_awarded['item']
                item_awarded_name = inventory.Items.name_for(item_awarded_id)
                item_awarded_count = item_awarded['count']

                if item_awarded_name not in tmp_count_items:
                    tmp_count_items[item_awarded_name] = item_awarded_count
                else:
                    tmp_count_items[item_awarded_name] += item_awarded_count

                self._update_inventory(item_awarded)

        if bonus_loot:
            # self.logger.info("Bonus Loot: %s" % bonus_loot)
            for item_awarded in bonus_loot['loot_item']:
                item_awarded_id = item_awarded['item']
                item_awarded_name = inventory.Items.name_for(item_awarded_id)
                item_awarded_count = item_awarded['count']

                if item_awarded_name not in tmp_count_items:
                    tmp_count_items[item_awarded_name] = item_awarded_count
                else:
                    tmp_count_items[item_awarded_name] += item_awarded_count

                self._update_inventory(item_awarded)

        if team_bonus_loot:
            # self.logger.info("Team Bonus Loot: %s" % team_bonus_loot)
            for item_awarded in team_bonus_loot['loot_item']:
                item_awarded_id = item_awarded['item']
                item_awarded_name = inventory.Items.name_for(item_awarded_id)
                item_awarded_count = item_awarded['count']

                if item_awarded_name not in tmp_count_items:
                    tmp_count_items[item_awarded_name] = item_awarded_count
                else:
                    tmp_count_items[item_awarded_name] += item_awarded_count

                self._update_inventory(item_awarded)

        return tmp_count_items

    # TODO : Refactor this class, hide the inventory update right after the api call
    def _update_inventory(self, item_awarded):
        if 'item_id' in item_awarded:
            inventory.items().get(item_awarded['item_id']).add(item_awarded['item_count'])
        elif 'item' in item_awarded:
            inventory.items().get(item_awarded['item']).add(item_awarded['count'])

    def _compute_next_update(self):
        """
        Computes the next update datetime based on the minimum update interval.
        :return: Nothing.
        :rtype: None
        """
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)
