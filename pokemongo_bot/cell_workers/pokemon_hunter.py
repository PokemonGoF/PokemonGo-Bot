# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from geopy.distance import great_circle
from s2sphere import Cell, CellId, LatLng

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.item_list import Item
from pokemongo_bot.walkers.polyline_walker import PolylineWalker
from pokemongo_bot.walkers.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult


class PokemonHunter(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(PokemonHunter, self).__init__(bot, config)

    def initialize(self):
        self.destination = None
        self.walker = None
        self.search_cell_id = None
        self.search_points = []
        self.lost_counter = 0
        self.no_log_until = 0

        self.config_max_distance = self.config.get("max_distance", 2000)
        self.config_hunt_all = self.config.get("hunt_all", False)
        self.config_hunt_vip = self.config.get("hunt_vip", True)
        self.config_hunt_pokedex = self.config.get("hunt_pokedex", True)
        # Lock on Target; ignore all other Pokémon until we found our target.
        self.config_lock_on_target = self.config.get("lock_on_target", False)
        self.bot.hunter_locked_target = None

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        if self.bot.catch_disabled:
            if not hasattr(self.bot,"hunter_disabled_global_warning") or \
                        (hasattr(self.bot,"hunter_disabled_global_warning") and not self.bot.hunter_disabled_global_warning):
                self.logger.info("All catching tasks are currently disabled until {}. Pokemon Hunter will resume when catching tasks are re-enabled".format(self.bot.catch_resume_at.strftime("%H:%M:%S")))
            self.bot.hunter_disabled_global_warning = True
            return WorkerResult.SUCCESS
        else:
            self.bot.hunter_disabled_global_warning = False

        if self.get_pokeball_count() <= 0:
            self.destination = None
            self.last_cell_id = None
            return WorkerResult.SUCCESS

        now = time.time()
        pokemons = self.get_nearby_pokemons()

        if self.destination is None:
            worth_pokemons = self.get_worth_pokemons(pokemons)

            if len(worth_pokemons) > 0:
                self.destination = worth_pokemons[0]
                self.lost_counter = 0

                self.logger.info("New destination at %(distance).2f meters: %(name)s", self.destination)
                self.no_log_until = now + 60
                if self.config_lock_on_target:
                    self.bot.hunter_locked_target = self.destination

                if self.destination["s2_cell_id"] != self.search_cell_id:
                    self.search_points = self.get_search_points(self.destination["s2_cell_id"])
                    self.walker = PolylineWalker(self.bot, self.search_points[0][0], self.search_points[0][1])
                    self.search_cell_id = self.destination["s2_cell_id"]
                    self.search_points = self.search_points[1:] + self.search_points[:1]
            else:
                if self.no_log_until < now:
                    self.logger.info("There is no nearby pokemon worth hunting down [%s]", ", ".join(p["name"] for p in pokemons))
                    self.no_log_until = now + 120

                self.last_cell_id = None

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
            else:
                self.logger.info("Now searching for %(name)s", self.destination)

                self.walker = StepWalker(self.bot, self.search_points[0][0], self.search_points[0][1])
                self.search_points = self.search_points[1:] + self.search_points[:1]
        elif self.no_log_until < now:
            distance = great_circle(self.bot.position, (self.walker.dest_lat, self.walker.dest_lng)).meters
            self.logger.info("Moving to destination at %s meters: %s", round(distance, 2), self.destination["name"])
            if self.config_lock_on_target:
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

        pokemons.sort(key=lambda p: p["distance"])

        return pokemons

    def get_worth_pokemons(self, pokemons):
        if self.config_hunt_all:
            worth_pokemons = pokemons
        else:
            worth_pokemons = []

            if self.config_hunt_vip:
                worth_pokemons += [p for p in pokemons if p["name"] in self.bot.config.vips]

            if self.config_hunt_pokedex:
                worth_pokemons += [p for p in pokemons if (p not in worth_pokemons) and any(not inventory.pokedex().seen(fid) for fid in self.get_family_ids(p))]

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
