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

import random
from random import uniform

class PokemonHunter(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(PokemonHunter, self).__init__(bot, config)

    def initialize(self):
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
        # Lock on Target; ignore all other Pokémon until we found our target.
        self.config_lock_on_target = self.config.get("lock_on_target", False)
        # Lock only VIP Pokemon (unseen / VIP)
        self.config_lock_vip_only = self.config.get("lock_vip_only", True)
        # If we are camping forts, disable hunting (see CampFort)
        self.config_disabled_while_camping = self.config.get("disabled_while_camping", True)
        # Hunt unseens as VIP?
        self.config_treat_unseen_as_vip = self.config.get("treat_unseen_as_vip", True)
        self.bot.hunter_locked_target = None

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

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

        if self.bot.catch_disabled:
            if not hasattr(self.bot,"hunter_disabled_global_warning") or \
                        (hasattr(self.bot,"hunter_disabled_global_warning") and not self.bot.hunter_disabled_global_warning):
                self.logger.info("All catching tasks are currently disabled until {}. Pokemon Hunter will resume when catching tasks are re-enabled".format(self.bot.catch_resume_at.strftime("%H:%M:%S")))
            self.bot.hunter_disabled_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.hunter_disabled_global_warning = False

        if self.bot.softban:
            if not hasattr(self.bot, "softban_global_warning") or \
                        (hasattr(self.bot, "softban_global_warning") and not self.bot.softban_global_warning):
                self.logger.info("Possible softban! Not trying to catch Pokemon.")
            self.bot.softban_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.softban_global_warning = False

        if self.get_pokeball_count() <= 0:
            self.destination = None
            self.last_cell_id = None
            return WorkerResult.SUCCESS

        if self.destination is not None:
            if self.destination_caught():
                self.logger.info("We found a %(name)s while hunting. Aborting the current search.", self.destination)
                self.destination = None
                wait = uniform(120, 600)
                self.no_hunt_until = time.time() + wait
                self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
                return WorkerResult.SUCCESS

        now = time.time()
        pokemons = self.get_nearby_pokemons()
        pokemons = filter(lambda x: x["pokemon_id"] not in self.recent_tries, pokemons)

        if self.destination is None:
            worth_pokemons = self.get_worth_pokemons(pokemons)

            if len(worth_pokemons) > 0:
                # Pick a random target from the list
                random.shuffle(worth_pokemons)
                # Prevents the bot from looping the same Pokemon
                self.destination = worth_pokemons[0]
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

                if self.destination["s2_cell_id"] != self.search_cell_id:
                    self.search_points = self.get_search_points(self.destination["s2_cell_id"])
                    self.walker = PolylineWalker(self.bot, self.search_points[0][0], self.search_points[0][1])
                    self.search_cell_id = self.destination["s2_cell_id"]
                    self.search_points = self.search_points[1:] + self.search_points[:1]
            else:
                if self.no_log_until < now:
                    # Show like "Pidgey (12), Zubat(2)"
                    names = Counter((p["name"] for p in pokemons))
                    sorted(names) # unicode object, no lower? , key=str.lower)

                    self.logger.info("There is no nearby pokemon worth hunting down [%s]", ", ".join('{}({})'.format(key, val) for key, val in names.items()))
                    self.no_log_until = now + 120
                    self.destination = None
                    wait = uniform(120, 600)
                    self.no_hunt_until = now + wait
                    self.logger.info("Will look again around {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))

                self.last_cell_id = None

                return WorkerResult.SUCCESS

        if self.config_lock_on_target and not self.config_lock_vip_only:
            if self.bot.hunter_locked_target == None:
                self.logger.info("We found a %(name)s while hunting. Aborting the current search.", self.destination)
                self.destination = None
                wait = uniform(120, 600)
                self.no_hunt_until = now + wait
                self.logger.info("Hunting on cooldown until {}.".format((datetime.now() + timedelta(seconds=wait)).strftime("%H:%M:%S")))
                return WorkerResult.SUCCESS

        if any(self.destination["encounter_id"] == p["encounter_id"] for p in self.bot.cell["catchable_pokemons"] + self.bot.cell["wild_pokemons"]):
            self.destination = None
        elif self.walker.step():
            if not any(self.destination["encounter_id"] == p["encounter_id"] for p in pokemons):
                self.lost_counter += 1
            else:
                self.lost_counter = 0

            if self.lost_counter >= 3:
                self.logger.info("I haven't found %(name)s", self.destination)
                self.bot.hunter_locked_target = None
                self.destination = None
                wait = uniform(120, 600)
                self.no_hunt_until = now + wait
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
                self.bot.hunter_locked_target = None
                self.destination = None
                wait = uniform(120, 600)
                self.no_hunt_until = now + wait
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

    def get_nearby_pokemons(self):
        radius = self.config_max_distance

        pokemons = [p for p in self.bot.cell["nearby_pokemons"] if self.get_distance(self.bot.start_position, p) <= radius]

        for pokemon in pokemons:
            pokemon["distance"] = self.get_distance(self.bot.position, p)
            pokemon["name"] = inventory.pokemons().name_for(pokemon["pokemon_id"])
            pokemon["candies"] = inventory.candies().get(pokemon["pokemon_id"]).quantity

        pokemons.sort(key=lambda p: p["distance"])

        return pokemons

    def _is_vip_pokemon(self, pokemon):
        # having just a name present in the list makes them vip
        # Not seen pokemons also will become vip if it's not disabled in config
        if self.bot.config.vips.get(pokemon["name"]) == {} or (self.config_treat_unseen_as_vip and not inventory.pokedex().seen(pokemon["pokemon_id"])):
            return True

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

    def get_worth_pokemons(self, pokemons):
        if self.config_hunt_all:
            worth_pokemons = pokemons
        else:
            worth_pokemons = []

            if self.config_hunt_vip:
                worth_pokemons += [p for p in pokemons if p["name"] in self.bot.config.vips]

            if self.config_hunt_pokedex:
                worth_pokemons += [p for p in pokemons if (p not in worth_pokemons) and self._is_needed_pokedex(p)]

        worth_pokemons.sort(key=lambda p: inventory.candies().get(p["pokemon_id"]).quantity)

        return worth_pokemons

    def get_family_ids(self, pokemon):
        family_id = inventory.pokemons().data_for(pokemon["pokemon_id"]).first_evolution_id
        ids = [family_id]
        ids += inventory.pokemons().data_for(family_id).next_evolutions_all[:]

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
        # self.logger.info("Searching for a {} since {}".format(self.destination["name"], self.hunt_started_at.strftime("%Y-%m-%d %H:%M:%S")))

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
