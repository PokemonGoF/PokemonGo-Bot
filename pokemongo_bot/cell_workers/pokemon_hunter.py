# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time
from datetime import datetime, timedelta
from collections import Counter

from geopy.distance import great_circle
from s2sphere import Cell, CellId, LatLng

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.item_list import Item
from pokemongo_bot.walkers.polyline_walker import PolylineWalker
from pokemongo_bot.walkers.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from .utils import fort_details

import random
from random import uniform

class PokemonHunter(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(PokemonHunter, self).__init__(bot, config)

    def initialize(self):
        self.max_pokemon_storage = inventory.get_pokemon_inventory_size()
        self.notified_second_gen = []
        self.destination = None
        self.walker = None
        self.search_cell_id = None
        self.search_points = []
        self.lost_counter = 0
        self.no_log_until = 0
        self.distance_to_target = 0
        self.distance_counter = 0
        self.recent_tries = []
        self.no_hunt_until = None
        self.hunt_started_at = None

        self.config_max_distance = self.config.get("max_distance", 2000)
        self.config_hunt_all = self.config.get("hunt_all", False)
        self.config_hunt_vip = self.config.get("hunt_vip", True)
        self.config_hunt_pokedex = self.config.get("hunt_pokedex", True)
        self.config_enable_cooldown = self.config.get("enable_cooldown", True)
        # closest first?
        self.config_hunt_closest_first = self.config.get("hunt_closest_first", False)
        # Lock on Target; ignore all other Pokémon until we found our target.
        self.config_lock_on_target = self.config.get("lock_on_target", False)
        # Lock only VIP Pokemon (unseen / VIP)
        self.config_lock_vip_only = self.config.get("lock_vip_only", True)
        # If we are camping forts, disable hunting (see CampFort)
        self.config_disabled_while_camping = self.config.get("disabled_while_camping", True)
        # Hunt unseens as VIP?
        self.config_treat_unseen_as_vip = self.config.get("treat_unseen_as_vip", True)
        self.config_target_family_of_vip = self.config.get("target_family_of_vip", True)
        self.config_treat_family_of_vip_as_vip = self.config.get("treat_family_of_vip_as_vip", False)
        self.bot.hunter_locked_target = None
        # Hunt for trash when bags are almost full
        self.config_hunt_for_trash = self.config.get("hunt_for_trash_to_fill_bag", False)
        self.config_trash_hunt_open_slots = self.config.get("trash_hunt_open_slots", 25)
        self.hunting_trash = False

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        if self.bot.catch_disabled:
            # When catching is disabled, drop the target.
            if self.destination is not None:
                self.destination = None
                self.last_cell_id = None

            if not hasattr(self.bot, "hunter_disabled_global_warning") or \
                        (hasattr(self.bot, "hunter_disabled_global_warning") and not self.bot.hunter_disabled_global_warning):
                self.logger.info("All catching tasks are currently disabled until {}. Pokemon Hunter will resume when catching tasks are re-enabled".format(self.bot.catch_resume_at.strftime("%H:%M:%S")))
            self.bot.hunter_disabled_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.hunter_disabled_global_warning = False

        if self.bot.softban:
            # At softban, drop target
            if self.destination is not None:
                self.destination = None
                self.last_cell_id = None
                self.hunting_trash = False

            if not hasattr(self.bot, "softban_global_warning") or \
                        (hasattr(self.bot, "softban_global_warning") and not self.bot.softban_global_warning):
                self.logger.info("Possible softban! Not trying to catch Pokemon.")
            self.bot.softban_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.softban_global_warning = False

        if self.config_disabled_while_camping and hasattr(self.bot, 'camping_forts') and self.bot.camping_forts:
            return WorkerResult.SUCCESS

        if not self.config_lock_on_target:
            self.bot.hunter_locked_target = None

        if self.no_hunt_until != None and self.no_hunt_until > time.time():
            # No hunting now, cooling down
            return WorkerResult.SUCCESS
        else:
            # Resume hunting
            self.no_hunt_until = None

        if self.get_pokeball_count() <= 0:
            self.destination = None
            self.last_cell_id = None
            self.hunting_trash = False
            return WorkerResult.SUCCESS

        if self.destination is not None:
            if self.destination_caught():
                self.logger.info("We found a %(name)s while hunting.", self.destination)
                self.recent_tries.append(self.destination['pokemon_id'])
                self.destination = None
                self.hunting_trash = False
                if self.config_enable_cooldown:
                    wait = uniform(120, 600)
                    self.no_hunt_until = time.time() + wait
                    self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
                    return WorkerResult.SUCCESS
                else:
                    self.logger.info("Electing new target....")

            if self.destination_vanished():
                self.logger.info("Darn, target got away!")
                self.recent_tries.append(self.destination['pokemon_id'])
                self.destination = None
                self.hunting_trash = False
                if self.config_enable_cooldown:
                    wait = uniform(120, 600)
                    self.no_hunt_until = time.time() + wait
                    self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
                    return WorkerResult.SUCCESS
                else:
                    self.logger.info("Electing new target....")

        now = time.time()
        pokemons = self.get_nearby_pokemons()
        pokemons = filter(lambda x: x["pokemon_id"] not in self.recent_tries, pokemons)

        if self.config_hunt_for_trash and self.hunting_trash is False and (self.destination is None or self._is_vip_pokemon(self.destination) is False ):
            # Okay, we should hunt for trash if the bag is almost full
            trash_mons = ["Caterpie", "Weedle", "Pidgey", "Pidgeotto", "Pidgeot", "Kakuna", "Beedrill", "Metapod", "Butterfree"]
            if self.pokemon_slots_left() <= self.config_trash_hunt_open_slots:
                if self.no_log_until < now:
                    self.logger.info("Less than %s slots left to fill, starting hunt for trash" % elf.config_trash_hunt_open_slots)
                for pokemon in pokemons:
                    if pokemon["name"] in trash_mons:
                        self.hunting_trash = True
                        self.destination = pokemon
                        self.lost_counter = 0
                        self.hunt_started_at = datetime.now()
                        self.logger.info("Hunting for trash at %(distance).2f meters: %(name)s", self.destination)
                        self.set_target()
                        # We have a target
                        return WorkerResult.SUCCESS

        if self.config_hunt_for_trash and self.hunting_trash:
            if self.pokemon_slots_left() > 20:
                self.logger.info("No longer trying to fill the bag. Electing new target....")
                self.hunting_trash = False
                self.destination = None

        if self.destination is None:
            worth_pokemons = self.get_worth_pokemons(pokemons, self.config_hunt_closest_first)

            if len(worth_pokemons) > 0:
                # Pick a random target from the list
                # random.shuffle(worth_pokemons)
                # Priotize closer pokemon
                worth_pokemons.sort(key=lambda p: p["distance"])
                # Prevents the bot from looping the same Pokemon
                self.destination = worth_pokemons[0]
                self.set_target()
                self.lost_counter = 0
                self.hunt_started_at = datetime.now()

                self.logger.info("New destination at %(distance).2f meters: %(name)s", self.destination)
                if self._is_vip_pokemon(self.destination):
                    self.logger.info("This is a VIP Pokemon! Starting hunt.")
                    if self.config_lock_on_target:
                        self.bot.hunter_locked_target = self.destination
                elif self._is_needed_pokedex(self.destination):
                    self.logger.info("I need a %(name)s to complete the Pokedex! I have %(candies)s candies.", self.destination)
                    if self.config_lock_on_target and not self.config_lock_vip_only:
                        self.bot.hunter_locked_target = self.destination
                    else:
                        self.bot.hunter_locked_target = None

                self.no_log_until = now + 60
                # We have a target
                return WorkerResult.SUCCESS
            else:
                if self.no_log_until < now:
                    # Show like "Pidgey (12), Zubat(2)"
                    names = Counter((p["name"] for p in pokemons))
                    sorted(names) # unicode object, no lower? , key=str.lower)

                    self.logger.info("There is no nearby pokemon worth hunting down [%s]", ", ".join('{}({})'.format(key, val) for key, val in names.items()))
                    self.no_log_until = now + 120
                    self.destination = None
                    if self.config_enable_cooldown:
                        wait = uniform(120, 360)
                        self.no_hunt_until = now + wait
                        self.logger.info("Will look again around {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))

                self.last_cell_id = None

                return WorkerResult.SUCCESS

        # Make sure a VIP is treated that way
        if self.config_lock_on_target and self.destination is not None:
            if self._is_vip_pokemon(self.destination) and self.bot.hunter_locked_target is None:
                self.bot.hunter_locked_target = self.destination

        # Check if there is a VIP around to hunt
        if (self.destination is not None and
                self.config_lock_on_target and
                self.config_lock_vip_only and
                self.bot.hunter_locked_target is None):
            worth_pokemons = self.get_worth_pokemons(pokemons)
            # We have a none VIP target set, check for VIP targets!
            if len(worth_pokemons) > 0:
                for pokemon in worth_pokemons:
                    if self._is_vip_pokemon(pokemon):
                        self.hunting_trash = False
                        self.destination = pokemon
                        self.lost_counter = 0
                        self.hunt_started_at = datetime.now()
                        self.set_target()
                        if self.config_lock_on_target:
                            self.bot.hunter_locked_target = self.destination
                        self.logger.info("Found a VIP Pokemon! Looking for a %(name)s at %(distance).2f.", self.destination)
                        return WorkerResult.SUCCESS
            pass

        if self.destination is None:
            if self.no_log_until < now:
                self.logger.info("Nothing to hunt.")
            return WorkerResult.SUCCESS

        if self.config_lock_on_target and not self.config_lock_vip_only:
            if self.bot.hunter_locked_target == None:
                self.logger.info("We found a %(name)s while hunting. Aborting the current search.", self.destination)
                self.destination = None
                self.hunting_trash = False
                if self.config_enable_cooldown:
                    wait = uniform(120, 600)
                    self.no_hunt_until = time.time() + wait
                    self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
                return WorkerResult.SUCCESS

        if any(self.destination["encounter_id"] == p["encounter_id"] for p in self.bot.cell["catchable_pokemons"] + self.bot.cell["wild_pokemons"]):
            self.destination = None
            self.hunting_trash = False
        elif self.walker.step():
            if not any(self.destination["encounter_id"] == p["encounter_id"] for p in pokemons):
                self.lost_counter += 1
            else:
                self.lost_counter = 0

            if self.lost_counter >= 3:
                self.logger.info("I haven't found %(name)s", self.destination)
                self.bot.hunter_locked_target = None
                self.destination = None
                self.hunting_trash = False
                if self.config_enable_cooldown:
                    wait = uniform(120, 600)
                    self.no_hunt_until = time.time() + wait
                    self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
            else:
                self.logger.info("Now searching for %(name)s", self.destination)

                self.walker = StepWalker(self.bot, self.search_points[0][0], self.search_points[0][1])
                self.search_points = self.search_points[1:] + self.search_points[:1]
        elif self.no_log_until < now:
            distance = great_circle(self.bot.position, (self.walker.dest_lat, self.walker.dest_lng)).meters
            if round(distance, 2) == self.distance_to_target:
                # Hmm, not moved toward the Pokemon?
                self.distance_counter += 1
            else:
                self.distance_counter = 0

            if self.distance_counter >= 3:
                # Ignore last 3
                if len(self.recent_tries) > 3:
                    self.recent_tries.pop()

                self.recent_tries.append(self.destination['pokemon_id'])
                self.logger.info("I cant move toward %(name)s! Aborting search.", self.destination)
                self.hunting_trash = False
                self.bot.hunter_locked_target = None
                self.destination = None
                if self.config_enable_cooldown:
                    wait = uniform(120, 600)
                    self.no_hunt_until = time.time() + wait
                    self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
                return WorkerResult.ERROR
            else:
                self.logger.info("Moving to destination at %s meters: %s", round(distance, 2), self.destination["name"])
                # record the new distance...
                self.distance_to_target = round(distance, 2)
                if self.config_lock_on_target and not self.config_lock_vip_only:
                    # Just to ensure we stay on target
                    self.bot.hunter_locked_target = self.destination
                self.no_log_until = now + 30

        return WorkerResult.RUNNING

    def get_pokeball_count(self):
        return sum([inventory.items().get(ball.value).count for ball in [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]])

    def set_target(self):
        self.search_points = self.get_search_points(self.destination["s2_cell_id"])
        self.walker = PolylineWalker(self.bot, self.search_points[0][0], self.search_points[0][1])
        self.search_cell_id = self.destination["s2_cell_id"]
        self.search_points = self.search_points[1:] + self.search_points[:1]

        if "fort_id" in self.destination:
            # The Pokemon is hding at a POkestop, so move to that Pokestop!
            # Get forts
            forts = self.bot.get_forts(order_by_distance=True)
            for fort in forts:
                if fort['id'] == self.destination['fort_id']:
                    # Found our fort!
                    lat = fort['latitude']
                    lng = fort['longitude']
                    details = fort_details(self.bot, fort['id'], lat, lng)
                    fort_name = details.get('name', 'Unknown')
                    self.logger.info("%s is hiding at %s, going there first!" % (self.destination["name"], fort_name))
                    self.walker = PolylineWalker(self.bot, lat, lng)

    def pokemon_slots_left(self):
        left = self.max_pokemon_storage - inventory.Pokemons.get_space_used()
        return left

    def get_nearby_pokemons(self):
        radius = self.config_max_distance

        pokemons = [p for p in self.bot.cell["nearby_pokemons"] if self.get_distance(self.bot.start_position, p) <= radius]

        for pokemon in pokemons:
            pokemon["distance"] = self.get_distance(self.bot.position, pokemon)
            pokemon["name"] = inventory.pokemons().name_for(pokemon["pokemon_id"])
            pokemon["candies"] = inventory.candies().get(pokemon["pokemon_id"]).quantity
            # Pokemon also has a fort_id of the PokeStop the Pokemon is hiding at.
            # We should set our first destination at that Pokestop.

        pokemons.sort(key=lambda p: p["distance"])

        return pokemons

    def _is_vip_pokemon(self, pokemon):
        # having just a name present in the list makes them vip
        # Not seen pokemons also will become vip if it's not disabled in config
        if self.bot.config.vips.get(pokemon["name"]) == {} or (self.config_treat_unseen_as_vip and not inventory.pokedex().seen(pokemon["pokemon_id"])):
            return True
        # If we must treat the family of the Pokemon as a VIP, also return true!
        if self.config_treat_family_of_vip_as_vip and self._is_family_of_vip(pokemon):
            return True

    def _is_family_of_vip(self, pokemon):
        for fid in self.get_family_ids(pokemon):
            name = inventory.pokemons().name_for(fid)
            if self.bot.config.vips.get(name) == {}:
                return True
        # No, not a family member of the VIP
        return False

    def _is_needed_pokedex(self, pokemon):
        candies = inventory.candies().get(pokemon["pokemon_id"]).quantity
        if candies > 150:
            # We have enough candies, pass on hunting this Pokemon
            return False

        # get family ids, gets ALL ids, also for previous evo!
        # We could see a Ivysaur on the map, and need a Bulbasaur
        # Then we have no need for a Ivysaur. If we see a Bulbasaur and need
        # a Ivysaur, then we DO need this pokemon.
        got_current_evo = False
        ids = []
        for fid in self.get_family_ids(pokemon):
            if got_current_evo:
                ids += [fid]
            else:
                if fid == pokemon["pokemon_id"]:
                    ids += [fid]
                    got_current_evo = True
        # Check if we need this, or a next EVO in the Pokedex
        if any(not inventory.pokedex().seen(fid) for fid in ids):
            return True

    def get_worth_pokemons(self, pokemons, closest_first=False):
        if self.config_hunt_all:
            worth_pokemons = pokemons
        else:
            worth_pokemons = []

            if self.config_hunt_vip:
                worth_pokemons += [p for p in pokemons if p["name"] in self.bot.config.vips]

            if self.config_target_family_of_vip or self.config_treat_family_of_vip_as_vip:
                worth_pokemons += [p for p in pokemons if (p not in worth_pokemons) and self._is_family_of_vip(p)]

            if self.config_hunt_pokedex:
                worth_pokemons += [p for p in pokemons if (p not in worth_pokemons) and self._is_needed_pokedex(p)]

        if closest_first:
            worth_pokemons.sort(key=lambda p: p["distance"])
        else:
            worth_pokemons.sort(key=lambda p: inventory.candies().get(p["pokemon_id"]).quantity)

        return worth_pokemons

    def get_family_ids(self, pokemon):
        family_id = inventory.pokemons().data_for(pokemon["pokemon_id"]).first_evolution_id
        ids = [family_id]
        ids += inventory.pokemons().data_for(family_id).next_evolutions_all[:]
        # ids have now all family ids
        return ids

    def get_distance(self, location, pokemon):
        return great_circle(location, (pokemon["latitude"], pokemon["longitude"])).meters

    def get_search_points(self, cell_id):
        points = []

        # For cell level 15
        for c in Cell(CellId(cell_id)).subdivide():
            for cc in c.subdivide():
                latlng = LatLng.from_point(cc.get_center())
                point = (latlng.lat().degrees, latlng.lng().degrees)
                points.append(point)

        points[0], points[1] = points[1], points[0]
        points[14], points[15] = points[15], points[14]
        point = points.pop(2)
        points.insert(7, point)
        point = points.pop(13)
        points.insert(8, point)

        closest = min(points, key=lambda p: great_circle(self.bot.position, p).meters)
        index = points.index(closest)

        return points[index:] + points[:index]

    def destination_caught(self):
        if self.destination is None:
            return False

        with self.bot.database as conn:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(pokemon) FROM catch_log where pokemon = '{}' and  datetime(dated, 'localtime') > Datetime('{}')".format(self.destination["name"], self.hunt_started_at.strftime("%Y-%m-%d %H:%M:%S")))
        # Now check if there is 1 or more caught
        amount = c.fetchone()[0]
        caught = amount > 0
        if caught:
            self.logger.info("We caught {} {}(s) since {}".format(amount, self.destination["name"], self.hunt_started_at.strftime("%Y-%m-%d %H:%M:%S")))

        return caught

    def destination_vanished(self):
        if self.destination is None:
            return False

        with self.bot.database as conn:
            c = conn.cursor()
            c.execute(
                "SELECT COUNT(pokemon) FROM vanish_log where pokemon = '{}' and  datetime(dated, 'localtime') > Datetime('{}')".format(self.destination["name"], self.hunt_started_at.strftime("%Y-%m-%d %H:%M:%S")))
        # Now check if there is 1 or more caught
        amount = c.fetchone()[0]
        vanished = amount > 0
        if vanished:
            self.logger.info("We lost {} {}(s) since {}".format(amount, self.destination["name"], self.hunt_started_at.strftime("%Y-%m-%d %H:%M:%S")))

        return vanished
