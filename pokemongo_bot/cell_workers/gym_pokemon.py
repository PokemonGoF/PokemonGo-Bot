# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime, timedelta
import sys
import time
import random
from random import uniform
from collections import Counter

from pgoapi.utilities import f2i
from pokemongo_bot import inventory
from pokemongo_bot.inventory import player

from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import action_delay, sleep
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot import inventory
from .utils import distance, format_time, fort_details, format_dist
from pokemongo_bot.tree_config_builder import ConfigException
from pokemongo_bot.walkers.walker_factory import walker_factory
from pokemongo_bot.inventory import Pokemons

from sys import stdout

GYM_DETAIL_RESULT_SUCCESS = 1
GYM_DETAIL_RESULT_OUT_OF_RANGE = 2
GYM_DETAIL_RESULT_UNSET = 0

TEAM_NOT_SET = 0
TEAM_BLUE = 1
TEAM_RED = 2
TEAM_YELLOW = 3

TEAMS = {
    0: "Not Set",
    1: "Mystic",
    2: "Valor",
    3: "Instinct"
}

ITEM_RAZZBERRY = 701
ITEM_NANABBERRY = 703
ITEM_PINAPBERRY = 705



class GymPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(GymPokemon, self).__init__(bot, config)

    def initialize(self):
        # 10 seconds from current time
        self.next_update = datetime.now() + timedelta(0, 10)
        self.order_by = self.config.get('order_by', 'cp')
        self.enabled = self.config.get('enabled', False)
        self.min_interval = self.config.get('min_interval', 360)
        self.min_recheck = self.config.get('min_recheck', 30)
        self.max_recheck = self.config.get('max_recheck', 120)
        
        self.take_at_most = self.config.get('take_at_most', 20)
        if self.take_at_most > 20:
            self.logger.warning("We can take more than 20 gyms!")
            self.take_at_most = 20
        self.leave_at_least_spots = self.config.get('leave_at_least_spots', 0)
        if self.leave_at_least_spots > 4:
            self.logger.warning("There are only 6 spots in a gym, when we drop a Pokemon in that would leave 5 spots! Setting leave open spots to 4!")
            self.leave_at_least_spots = 4
        self.chain_fill_gyms = self.config.get('chain_fill_gyms', True)
        self.ignore_max_cp_pokemon = self.config.get('allow_above_cp', ["Blissey"])
        self.never_place = self.config.get('never_place', [])

        self.pick_random_pokemon = self.config.get('pick_random_pokemon', True)
        
        self.can_be_disabled_by_catch_limter = self.config.get("can_be_disabled_by_catch_limter", False)

        self.recheck = datetime.now()
        self.walker = self.config.get('walker', 'StepWalker')
        self.destination = None
        self.recent_gyms = []
        self.pokemons = []
        self.fort_pokemons = []
        self.expire_recent = 10
        self.next_expire = None
        self.dropped_gyms = []
        self.blacklist= []
        self.check_interval = 0
        self.gyms = []
        self.raid_gyms = dict()

        self.bot.event_manager.register_event('gym_error')
        self.bot.event_manager.register_event('fed_pokemon')
        self.bot.event_manager.register_event('gym_full')
        self.bot.event_manager.register_event('deployed_pokemon')
        
        #self.logger.info("player_date %s." % self.bot.player_data)

        try:
            self.team = self.bot.player_data['team']
        except KeyError:
            self.team = TEAM_NOT_SET
            if self.enabled:
                self.emit_event(
                    'gym_error',
                    formatted="You have no team selected, so the module GymPokemon should be disabled"
                )

    def should_run(self):
        # Check if we have any Pokemons and are level > 5 and have selected a team
        return player()._level >= 5 and len(self.pokemons) > 0 and self.team > TEAM_NOT_SET

    def display_fort_pokemon(self):
        if len(self.fort_pokemons) == 0:
            return
        self.logger.info("We currently have %s Pokemon in Gym(s):" % len(self.fort_pokemons) )
        for pokemon in self.fort_pokemons:
            lat = self.bot.position[0:2][0]
            lng = self.bot.position[0:2][1]
            self.logger.info("%s (%s CP)" % (pokemon.name, pokemon.cp))

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        if self.bot.catch_disabled and self.can_be_disabled_by_catch_limter:
            # When catching is disabled, drop the target.
            if self.destination is not None:
                self.destination = None

            if not hasattr(self.bot, "gym_pokemon_disabled_global_warning") or \
                        (hasattr(self.bot, "gym_pokemon_disabled_global_warning") and not self.bot.gym_pokemon_disabled_global_warning):
                self.logger.info("All gym tasks are currently disabled until {}. Gym function will resume when catching tasks are re-enabled".format(self.bot.catch_resume_at.strftime("%H:%M:%S")))
            self.bot.gym_pokemon_disabled_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.gym_pokemon_disabled_global_warning = False
            
        self.pokemons = inventory.pokemons().all()
        self.fort_pokemons = [p for p in self.pokemons if p.in_fort]
        self.pokemons = [p for p in self.pokemons if not p.in_fort]

        self.dropped_gyms = []
        for pokemon in self.fort_pokemons:
            self.dropped_gyms.append(pokemon.fort_id)

        if self._should_print():
            self.display_fort_pokemon()
            self._compute_next_update()
        # Do display the stats about Pokemon in Gym and collection time [please]
        if not self.enabled:
            return WorkerResult.SUCCESS
        if self.bot.softban:
            return WorkerResult.SUCCESS

        if len(self.fort_pokemons) >= self.take_at_most:
            if self._should_print():
                self.logger.info("We have a max of %s Pokemon in gyms." % self.take_at_most)
            return WorkerResult.SUCCESS

        if not self.should_run():
            return WorkerResult.SUCCESS
            
        if self.destination is None:
            self.check_close_gym()

        if self.destination is None:
            self.determin_new_destination()

        if self.destination is not None:
            result = self.move_to_destination()
            # Can return RUNNING to move to a gym
            return result

        if hasattr(self.bot, "hunter_locked_target") and self.bot.hunter_locked_target is not None:
            # Don't move to a gym when hunting for a Pokemon
            return WorkerResult.SUCCESS

        return WorkerResult.SUCCESS

    def check_close_gym(self):
        # Check if we are walking past a gym
        close_gyms = self.get_gyms_in_range()
        # Filter active raids from the gyms
        close_gyms = filter(lambda gym: gym["id"] not in self.raid_gyms, close_gyms)

        if len(close_gyms) > 0:
            # self.logger.info("Walking past a gym!")
            for gym in close_gyms:
                if gym["id"] in self.dropped_gyms:
                    continue

                gym_details = self.get_gym_details(gym)
                if gym_details:
                    pokes = self._get_pokemons_in_gym(gym_details)
                    if len(pokes) == 6:
                        continue
                    if 'enabled' in gym:
                        if not gym['enabled']:
                            continue
                    if 'owned_by_team' in gym:
                        if gym["owned_by_team"] == self.team:
                            if 'gym_display' in gym:
                                display = gym['gym_display']
                                if 'slots_available' in display:
                                    self.logger.info("Gym has %s open spots!" % display['slots_available'])
                                    if display['slots_available'] > 0 and gym["id"] not in self.dropped_gyms:
                                        self.logger.info("Dropping pokemon in %s" % gym_details["name"])
                                        self.drop_pokemon_in_gym(gym, pokes)
                                        if self.destination is not None and gym["id"] == self.destination["id"]:
                                            self.destination = None
                                        return WorkerResult.SUCCESS
                    else:
                        self.logger.info("Neutral gym? %s" % gym)
                        self.logger.info("Dropping pokemon in %s" % gym_details["name"])
                        self.drop_pokemon_in_gym(gym, [])
                        if self.destination is not None and gym["id"] == self.destination["id"]:
                            self.destination = None
                        return WorkerResult.SUCCESS

    def determin_new_destination(self):
        gyms = self.get_gyms()
        if len(gyms) == 0:
            if len(self.recent_gyms) == 0 and self._should_print():
                self.logger.info("No Gyms in range to scan!")
            return WorkerResult.SUCCESS

        self.logger.info("Inspecting %s gyms." % len(gyms))
        self.logger.info("Recent gyms: %s" % len(self.recent_gyms))
        self.logger.info("Active raid gyms: %s" % len(self.raid_gyms))
        teams = []
        for gym in gyms:
            # Ignore after done for 5 mins
            self.recent_gyms.append(gym["id"])

            if 'enabled' in gym:
                # Gym can be closed for a raid or something, skipp to the next
                if not gym['enabled']:
                    continue

            if 'owned_by_team' in gym:
                if gym["owned_by_team"] == 1:
                    teams.append("Mystic")
                elif gym["owned_by_team"] == 2:
                    teams.append("Valor")
                elif gym["owned_by_team"] == 3:
                    teams.append("Instinct")
                # else:
                #     self.logger.info("Unknown team? %s" % gym)

                if gym["owned_by_team"] == self.team:
                    if 'gym_display' in gym:
                        display = gym['gym_display']
                        if 'slots_available' in display:
                            if self.leave_at_least_spots > 0:
                                if display['slots_available'] > self.leave_at_least_spots:
                                    self.logger.info("Gym has %s open spots!" % display['slots_available'])
                                    self.destination = gym
                                    break
                                else:
                                    self.logger.info("Gym has %s open spots, but we don't drop Pokemon in it because that would leave less than %s open spots" % (display['slots_available'], self.leave_at_least_spots))
                            else:
                                self.logger.info("Gym has %s open spots!" % display['slots_available'])
                                self.destination = gym
                                break
            else:
                # self.logger.info("Found a Neutral gym?")
                # self.logger.info("Info: %s" % gym)
                self.destination = gym
                break
        if len(teams) > 0:
            count_teams = Counter(teams)
            self.logger.info("Gym Teams %s", ", ".join('{}({})'.format(key, val) for key, val in count_teams.items()))

    def move_to_destination(self):
        if self.check_interval >= 4:
            self.check_interval = 0
            gyms = self.get_gyms()
            for g in gyms:
                if g["id"] == self.destination["id"]:
                    # self.logger.info("Inspecting target: %s" % g)
                    if "owned_by_team" in g and g["owned_by_team"] is not self.team:
                        self.logger.info("Damn! Team %s took gym before we arrived!" % TEAMS[g["owned_by_team"]])
                        self.destination = None
                        return WorkerResult.SUCCESS
                    break
        else:
            self.check_interval += 1

        # Moving to a gym to deploy Pokemon
        unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance
        lat = self.destination["latitude"]
        lng = self.destination["longitude"]
        details = fort_details(self.bot, self.destination["id"], lat, lng)
        gym_name = details.get('name', 'Unknown')

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            lat,
            lng
        )
        noised_dist = distance(
            self.bot.noised_position[0],
            self.bot.noised_position[1],
            lat,
            lng
        )

        moving = noised_dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE if self.bot.config.replicate_gps_xy_noise else dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE

        if moving:
            fort_event_data = {
                'fort_name': u"{}".format(gym_name),
                'distance': format_dist(dist, unit),
            }
            self.emit_event(
                'moving_to_fort',
                formatted="Moving towards open Gym {fort_name} - {distance}",
                data=fort_event_data
            )

            step_walker = walker_factory(self.walker, self.bot, lat, lng)

            if not step_walker.step():
                return WorkerResult.RUNNING
            else:
                #Running fails. Let's stop moving to the gym
                return WorkerResult.SUCCESS
        else:
            self.emit_event(
                'arrived_at_fort',
                formatted=("Arrived at Gym %s." % gym_name)
            )
            gym_details = self.get_gym_details(self.destination)
            current_pokemons = self._get_pokemons_in_gym(gym_details)
            self.drop_pokemon_in_gym(self.destination, current_pokemons)
            self.destination = None
            if len(self.fort_pokemons) >= self.take_at_most:
                self.logger.info("We have a max of %s Pokemon in gyms." % self.take_at_most)
                return WorkerResult.SUCCESS
            elif self.chain_fill_gyms:
                # Look around if there are more gyms to fill
                self.determin_new_destination()
                # If there is none, we're done, else we go to the next!
                if self.destination is None:
                    return WorkerResult.SUCCESS
                else:
                    return WorkerResult.RUNNING
            else:
                return WorkerResult.SUCCESS
    
    def get_gym_details(self, gym):
        lat = gym['latitude']
        lng = gym['longitude']

        in_reach = False

        if self.bot.config.replicate_gps_xy_noise:
            if distance(self.bot.noised_position[0], self.bot.noised_position[1], gym['latitude'], gym['longitude']) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
                in_reach = True
        else:
            if distance(self.bot.position[0], self.bot.position[1], gym['latitude'], gym['longitude']) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
                in_reach = True

        if in_reach:
            request = self.bot.api.create_request()
            request.gym_get_info(gym_id=gym['id'], gym_lat_degrees=lat, gym_lng_degrees=lng, player_lat_degrees=self.bot.position[0],player_lng_degrees=self.bot.position[1])
            response_dict = request.call()

            if ('responses' in response_dict) and ('GYM_GET_INFO' in response_dict['responses']):
                details = response_dict['responses']['GYM_GET_INFO']
                return details
        else:
            return False
        # details = fort_details(self.bot, , lat, lng)
        # fort_name = details.get('name', 'Unknown')
        # self.logger.info("Checking Gym: %s (%s pts)" % (fort_name, gym['gym_points']))

    def _get_pokemons_in_gym(self, gym_details):
        pokemon_names = []
        gym_info = gym_details.get('gym_status_and_defenders', None)
        if gym_info:
            defenders = gym_info.get('gym_defender', [])
            for defender in defenders:
                motivated_pokemon = defender.get('motivated_pokemon')
                pokemon_info = motivated_pokemon.get('pokemon')
                pokemon_id = pokemon_info.get('pokemon_id')
                pokemon_names.append(Pokemons.name_for(pokemon_id))

        return pokemon_names
       
    def drop_pokemon_in_gym(self, gym, current_pokemons):
        self.pokemons = inventory.pokemons().all()
        self.fort_pokemons = [p for p in self.pokemons if p.in_fort]
        self.pokemons = [p for p in self.pokemons if not p.in_fort]
        close_gyms = self.get_gyms_in_range()

        empty_gym = False

        for pokemon in self.fort_pokemons:
            if pokemon.fort_id == gym["id"]:
                self.logger.info("We are already in this gym!")
                if pokemon.fort_id not in self.dropped_gyms:
                    self.dropped_gyms.append(pokemon.fort_id)
                self.recent_gyms.append(gym["id"])
                return WorkerResult.SUCCESS
    
        for g in close_gyms:
            if g["id"] == gym["id"]:
                if 'owned_by_team' in g:
                    self.logger.info("Expecting team: %s it is: %s" % (self.bot.player_data['team'], g["owned_by_team"]) )
                    if g["owned_by_team"] is not self.team:
                        self.logger.info("Can't drop in a enemy gym!")
                        self.recent_gyms.append(gym["id"])
                        return WorkerResult.SUCCESS
                else:
                    #self.logger.info("Empty gym?? %s" % g)
                    gym_details = self.get_gym_details(gym)
                    #self.logger.info("Details: %s" % gym_details)
                    empty_gym = True
                    if not gym_details or gym_details == {}:
                        self.logger.info("No details for this Gym? Blacklisting!")
                        self.blacklist.append(gym["id"])
                        return WorkerResult.SUCCESS

        # Check for raid
        if 'raid_info' in gym:
            raid_info = gym["raid_info"]
            raid_starts = datetime.fromtimestamp(int(raid_info["raid_battle_ms"]) / 1e3)
            raid_ends = datetime.fromtimestamp(int(raid_info["raid_end_ms"]) / 1e3)
            self.logger.info("Raid starts: %s" % raid_starts.strftime('%Y-%m-%d %H:%M:%S.%f'))
            self.logger.info("Raid ends: %s" % raid_ends.strftime('%Y-%m-%d %H:%M:%S.%f'))
            t = datetime.today()

            if raid_starts < datetime.now():
                self.logger.info("Active raid?")
                if raid_ends < datetime.now():
                    self.logger.info("No need to wait.")
                elif (raid_ends-t).seconds > 600:
                    self.logger.info("Need to wait long than 10 minutes, skipping")
                    self.destination = None
                    self.recent_gyms.append(gym["id"])
                    self.raid_gyms[gym["id"]] = raid_ends
                    return WorkerResult.SUCCESS
                else:
                    first_time = False
                    while raid_ends > datetime.now():
                        raid_ending = (raid_ends-datetime.today()).seconds
                        sleep_m, sleep_s = divmod(raid_ending, 60)
                        sleep_h, sleep_m = divmod(sleep_m, 60)
                        sleep_hms = '%02d:%02d:%02d' % (sleep_h, sleep_m, sleep_s)
                        if not first_time:
                            # Clear the last log line!
                            stdout.write("\033[1A\033[0K\r")
                            stdout.flush()
                        first_time = True
                        self.logger.info("Waiting for %s for raid to end..." % sleep_hms)
                        if raid_ending > 20:
                            sleep(20)
                        else:
                            sleep(raid_ending)
                            break
            else:
                self.logger.info("Raid has not begun yet!")

        if 'same_team_deploy_lockout_end_ms' in gym:
            # self.logger.info("%f" % gym["same_team_deploy_lockout_end_ms"])
            org_time = int(gym["same_team_deploy_lockout_end_ms"]) / 1e3
            lockout_time = datetime.fromtimestamp(org_time)
            t = datetime.today()

            if lockout_time > datetime.now():
                self.logger.info("Lockout time: %s" % lockout_time.strftime('%Y-%m-%d %H:%M:%S.%f'))
                first_time = False
                while lockout_time > datetime.now():
                    lockout_ending = (lockout_time-datetime.today()).seconds
                    sleep_m, sleep_s = divmod(lockout_ending, 60)
                    sleep_h, sleep_m = divmod(sleep_m, 60)
                    sleep_hms = '%02d:%02d:%02d' % (sleep_h, sleep_m, sleep_s)
                    if not first_time:
                        # Clear the last log line!
                        stdout.write("\033[1A\033[0K\r")
                        stdout.flush()
                    first_time = True
                    self.logger.info("Waiting for %s deployment lockout to end..." % sleep_hms)
                    if lockout_ending > 40:
                        sleep(40)
                        break
                    else:
                        sleep(lockout_ending)
                        break

        #FortDeployPokemon
        # self.logger.info("Trying to deploy Pokemon in gym: %s" % gym)
        gym_details = self.get_gym_details(gym)
        # self.logger.info("Gym details: %s" % gym_details)
        fort_pokemon = self._get_best_pokemon(current_pokemons)
        pokemon_id = fort_pokemon.unique_id
        # self.logger.info("Trying to deploy %s (%s)" % (fort_pokemon, pokemon_id))
        # self.logger.info("Gym in control by %s. I am on team %s" % (gym["owned_by_team"], self.bot.player_data['team']))

        request = self.bot.api.create_request()
        request.gym_deploy(
            fort_id=gym["id"],
            pokemon_id=pokemon_id,
            player_lat_degrees=f2i(self.bot.position[0]),
            player_lng_degrees=f2i(self.bot.position[1])
        )
        # self.logger.info("Req: %s" % request)
        response_dict = request.call()
        # self.logger.info("Called deploy pokemon: %s" % response_dict)

        if ('responses' in response_dict) and ('GYM_DEPLOY' in response_dict['responses']):
            deploy = response_dict['responses']['GYM_DEPLOY']
            result = response_dict.get('status_code', -1)
            self.recent_gyms.append(gym["id"])
            # self.logger.info("Status: %s" % result)
            if result == 1:
                self.dropped_gyms.append(gym["id"])
                self.fort_pokemons.append(fort_pokemon)
                gym_details = self.get_gym_details(gym)
                # SUCCES
                #self.logger.info("We deployed %s (%s CP) in the gym! We now have %s Pokemon in gyms!" % (fort_pokemon.name, fort_pokemon.cp, len(self.dropped_gyms)))
                self.emit_event(
                    'deployed_pokemon',
                    formatted=("We deployed %s (%s CP) in the gym %s!!" % (fort_pokemon.name, fort_pokemon.cp, gym_details["name"])),
                    data={'gym_id': gym['id'], 'pokemon_id': pokemon_id}
                )
                return WorkerResult.SUCCESS
            elif result == 2:
                #ERROR_ALREADY_HAS_POKEMON_ON_FORT
                self.logger.info('ERROR_ALREADY_HAS_POKEMON_ON_FORT')
                self.dropped_gyms.append(gym["id"])
                return WorkerResult.ERROR
            elif result == 3:
                #ERROR_OPPOSING_TEAM_OWNS_FORT
                self.logger.info('ERROR_OPPOSING_TEAM_OWNS_FORT')
                return WorkerResult.ERROR
            elif result == 4:
                #ERROR_FORT_IS_FULL
                self.logger.info('ERROR_FORT_IS_FULL')
                return WorkerResult.ERROR
            elif result == 5:
                #ERROR_NOT_IN_RANGE
                self.logger.info('ERROR_NOT_IN_RANGE')
                return WorkerResult.ERROR
            elif result == 6:
                #ERROR_PLAYER_HAS_NO_TEAM
                self.logger.info('ERROR_PLAYER_HAS_NO_TEAM')
                return WorkerResult.ERROR
            elif result == 7:
                #ERROR_POKEMON_NOT_FULL_HP
                self.logger.info('ERROR_POKEMON_NOT_FULL_HP')
                return WorkerResult.ERROR
            elif result == 8:
                #ERROR_PLAYER_BELOW_MINIMUM_LEVEL
                self.logger.info('ERROR_PLAYER_BELOW_MINIMUM_LEVEL')
                return WorkerResult.ERROR
            elif result == 8:
                #ERROR_POKEMON_IS_BUDDY
                self.logger.info('ERROR_POKEMON_IS_BUDDY')
                return WorkerResult.ERROR

    def get_gyms(self, skip_recent_filter=False):
        if len(self.gyms) == 0:
            self.gyms = self.bot.get_gyms(order_by_distance=True)

        if self._should_recheck():
            self.gyms = self.bot.get_gyms(order_by_distance=True)
            self._compute_next_recheck()

        if self._should_expire():
            self.recent_gyms = []
            self._compute_next_expire()
        # Check raid gyms for raids that ended
        for gym_id in list(self.raid_gyms.keys()):
            if self.raid_gyms[gym_id] < datetime.now():
                self.logger.info("Raid at %s ended (%s)" % (gym_id, self.raid_gyms[gym_id]))
                del(self.raid_gyms[gym_id])

        gyms = []
        # if not skip_recent_filter:
        gyms = filter(lambda gym: gym["id"] not in self.recent_gyms, self.gyms)
        # Filter blacklisted gyms
        gyms = filter(lambda gym: gym["id"] not in self.blacklist, gyms)
        # Filter out gyms we already in
        gyms = filter(lambda gym: gym["id"] not in self.dropped_gyms, gyms)
        # Filter ongoing raids
        gyms = filter(lambda gym: gym["id"] not in self.raid_gyms, gyms)
        # filter fake gyms
        # self.gyms = filter(lambda gym: "type" not in gym or gym["type"] != 1, self.gyms)
        # sort by current distance
        gyms.sort(key=lambda x: distance(
                self.bot.position[0],
                self.bot.position[1],
                x['latitude'],
                x['longitude']
            ))

        return gyms

    def get_gyms_in_range(self):
        gyms = self.get_gyms()

        if self.bot.config.replicate_gps_xy_noise:
            gyms = filter(lambda fort: distance(
                self.bot.noised_position[0],
                self.bot.noised_position[1],
                fort['latitude'],
                fort['longitude']
            ) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE, self.gyms)
        else:
            gyms = filter(lambda fort: distance(
                self.bot.position[0],
                self.bot.position[1],
                fort['latitude'],
                fort['longitude']
            ) <= Constants.MAX_DISTANCE_FORT_IS_REACHABLE, self.gyms)

        return gyms

    def _should_print(self):
        return self.next_update is None or datetime.now() >= self.next_update

    def _should_expire(self):
        return self.next_expire is None or datetime.now() >= self.next_expire

    def _compute_next_expire(self):
        self.next_expire = datetime.now() + timedelta(seconds=300)

    def _compute_next_recheck(self):
        wait = uniform(self.min_recheck, self.max_recheck)
        self.recheck = datetime.now() + timedelta(seconds=wait)

    def _should_recheck(self):
        return self.recheck is None or datetime.now() >= self.recheck

    def _compute_next_update(self):
        """
        Computes the next update datetime based on the minimum update interval.
        :return: Nothing.
        :rtype: None
        """
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def _get_best_pokemon(self, current_pokemons):
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
        # Don't place a Pokemon which is already in the gym (prevent ALL Blissey etc)
        possible_pokemons = [p for p in self.pokemons if not p.name in current_pokemons]
        # Don't put in Pokemon above 3000 cp (morale drops too fast)
        possible_pokemons = [p for p in possible_pokemons if p.cp < 3000 and p.name not in self.ignore_max_cp_pokemon]
        # Filter out "bad" Pokemon
        possible_pokemons = [p for p in possible_pokemons if not p.is_bad]
        # Filter out "never place" Pokemon
        possible_pokemons = [p for p in possible_pokemons if p.name not in self.never_place]
        # HP Must be max
        possible_pokemons = [p for p in possible_pokemons if p.hp == p.hp_max]
        possible_pokemons = [p for p in possible_pokemons if not p.in_fort]
        # Sort them
        pokemons_ordered = sorted(possible_pokemons, key=lambda x: get_poke_info(self.order_by, x), reverse=True)
        # Top 20 picks
        pokemons_ordered = pokemons_ordered[0:20]
        if self.pick_random_pokemon:
            # Pick a random one!
            random.shuffle(pokemons_ordered)
        return pokemons_ordered[0]
