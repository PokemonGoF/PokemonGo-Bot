import json
import time
import math
from utils import distance, format_dist, i2f, coord2merc, merc2coord
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult

class HuntNearbyPokemon(BaseTask):
    def initialize(self):
        self.detect_radius = self.config.get("detect_radius", 50)
        self.search_radius = self.config.get("search_radius", 200)
        self.start_count_pokemon = self.config.get("start_count_pokemon", 4)
        self.start_vip = self.config.get("start_vip", True)
        self.start_min_anyball = self.config.get("start_min_anyball", 40)
        self.stop_min_anyball = self.config.get("stop_min_anyball", 20)
        self.stop_max_time = self.config.get("stop_max_time", 60) * 60
        self.show_radar = self.config.get("show_radar", True)
        self.fix_speed = self.config.get("fix_speed", True)
        self.ptr = 0
        self.direction = 1
        self.start_search = 0
        self.last_step_time = 0

    def work(self):

        radar_change = False

        if self.bot.last_cell == None or (len(self.bot.cell['nearby_pokemons']) != len(self.bot.last_cell['nearby_pokemons'])):
            radar_change = True
        else:
            for i in range(len(self.bot.cell['nearby_pokemons'])):
                if (self.bot.cell['nearby_pokemons'][i]['encounter_id'] != self.bot.last_cell['nearby_pokemons'][i]['encounter_id']):
                    radar_change = True
                    break

        if 'nearby_pokemons' in self.bot.cell and len(self.bot.cell['nearby_pokemons']) > 0:
            strpoke = ""
            if self.show_radar and radar_change:
                for poke in self.bot.cell['nearby_pokemons']:
                    pokemon_num = int(poke['pokemon_id']) - 1
                    pokemon_name = self.bot.pokemon_list[int(pokemon_num)]['Name']
                    strpoke = strpoke + "{}:{} / ".format(pokemon_name, str(poke['encounter_id'])[:3])
                logger.log(' Radar : {}'.format(strpoke))

        items_stock = self.bot.current_inventory()
        anyball_count = items_stock[1] + items_stock[2] + items_stock[3]
        free_pokemon_slot = self.bot._player['max_pokemon_storage'] - self.bot.get_inventory_count('pokemon')

        if self.start_search > 0:
            if anyball_count <= self.stop_min_anyball:
                logger.log("No enought balls, stopping search :/")
                self._end_search()
            elif ((time.time() - self.start_search) < self.stop_max_time):
                #logger.log("Searching at {},{}".format(self.bot.position[0], self.bot.position[1]))
                if self._continue_search():
                    return WorkerResult.RUNNING
                else:
                    self._end_search()
            elif (free_pokemon_slot < 1):
                logger.log("Not enought space for new pokemon :(")
                self._end_search()
            else:
                self._end_search()
        elif 'nearby_pokemons' in self.bot.cell and anyball_count >= self.start_min_anyball and free_pokemon_slot > 0 and self._should_hunt(self.bot.cell['nearby_pokemons']):
           #logger.log("start search pokemon !")
           self._start_search()
           return WorkerResult.RUNNING

        return WorkerResult.RUNNING if self.start_search > 0 else WorkerResult.SUCCESS

    def _start_search(self):
        self.points = self.generate_path(self.bot.position[0], self.bot.position[1], self.detect_radius * 2, self.search_radius)
        self.ptr = 0
        self.direction = 1
        self.start_search = time.time()

    def _continue_search(self):
        point = self.points[self.ptr]
        # steroid if needed
        if not self.fix_speed or self.last_step_time == 0:
            fix_speed = self.bot.config.walk
        else:
            #trick/ugly, need fix StepWalker
            fix_speed = min(40, self.bot.config.walk * min(10, max(1, time.time() - self.last_step_time)))
            #logger.log("fixed speed={} (time={})".format(fix_speed, time.time() - self.last_step_time))

        step_walker = StepWalker(
            self.bot,
            fix_speed,
            point['lat'],
            point['lng']
        )

        dist = distance(
            self.bot.api._position_lat,
            self.bot.api._position_lng,
            point['lat'],
            point['lng']
        )

        if step_walker.step():
            step_walker = None

        self.last_step_time = time.time()
        if distance(
                    self.bot.api._position_lat,
                    self.bot.api._position_lng,
                    point['lat'],
                    point['lng']
                ) <= 1 or (self.bot.config.walk > 0 and step_walker == None):
            if self.ptr + self.direction >= len(self.points) or self.ptr + self.direction <= -1:
                return False
            if len(self.points) != 1:
                self.ptr += self.direction
                dest = self.points[self.ptr]
                logger.log(" [{}/{} ({}min)] Search from {} to {}".format(self.ptr, len(self.points),
                                                        int((time.time() - self.start_search) / 60),
                                                        str((self.bot.api._position_lat,self.bot.api._position_lng)),
                                                        str((dest['lat'],dest['lng']))))
        return True

    def _end_search(self):
        logger.log("[{}/{}] Stop hunting ({}min)".format(self.ptr, len(self.points), int((time.time() - self.start_search) / 60)))
        self.start_search = 0
        self.last_step_time = 0

    def _should_hunt(self, nearby):
        vip_detected = False
        if self.start_vip:
            for poke in nearby:
                pokemon_num = int(poke['pokemon_id']) - 1
                pokemon_name = self.bot.pokemon_list[int(pokemon_num)]['Name']
                if self.check_vip_pokemon(pokemon_name):
                    logger.log(" VIP pokemon detected \o/ ({})".format(pokemon_name))
                    vip_detected = True

        if len(nearby) >= self.start_count_pokemon:
            return True

        return vip_detected

    # for real spiral :)
    def magic_x(self, x):
        return 5 * x * math.cos(x)

    def magic_y(self, y):
        return 5 * y * math.sin(y)

    # stupid path
    def generate_path(self, starting_lat, starting_lng, start_step, search_range):
        current_step = start_step
        mlat,mlon = coord2merc(starting_lat, starting_lng)
        cycle = int(search_range / start_step * 2)
        coords = [{'lat': starting_lat, 'lng': starting_lng}]
        for i in range(1, cycle):
            #logger.log("step {}! {}".format(i, current_step))
            mlat = mlat + current_step
            lat, lng = merc2coord((mlat, mlon))
            coords.append({'lat': lat, 'lng': lng})

            mlon = mlon - current_step
            lat, lng = merc2coord((mlat, mlon))
            coords.append({'lat': lat, 'lng': lng})

            mlat = mlat - (current_step + start_step)
            lat, lng = merc2coord((mlat, mlon))
            coords.append({'lat': lat, 'lng': lng})

            mlon = mlon + (current_step + start_step)
            lat, lng = merc2coord((mlat, mlon))
            coords.append({'lat': lat, 'lng': lng})

            mlat, mlon = coord2merc(lat, lng)
            current_step = current_step + (start_step * 2)
        return coords

    def check_vip_pokemon(self,pokemon):
        vip_name = self.bot.config.vips.get(pokemon)
        if vip_name == {}:
            return True
