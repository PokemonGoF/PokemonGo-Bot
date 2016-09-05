# -*- coding: utf-8 -*-

import math

from random import uniform
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.human_behaviour import sleep, random_alt_delta
from geopy.distance import VincentyDistance
from geopy import Point

class StepWalker(object):

    def __init__(self, bot, dest_lat, dest_lng, dest_alt=None, fixed_speed=None, precision=50):
        self.bot = bot
        self.api = bot.api
        self.precision = precision

        self.initLat, self.initLng = self.bot.position[0:2]

        self.dist = distance(
            self.initLat,
            self.initLng,
            dest_lat,
            dest_lng
        )
        
        if dest_alt == None:
            self.alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
        else:
            self.alt = dest_alt
            
        if fixed_speed != None:
            # PolylineWalker uses a fixed speed!
            self.speed = fixed_speed
        else:
            self.speed = uniform(self.bot.config.walk_min, self.bot.config.walk_max)

        if len(self.bot.position) == 3:
            self.initAlt = self.bot.position[2]
        else:
            self.initAlt = self.alt

        self.destLat = dest_lat
        self.destLng = dest_lng

        if self.speed == 0:
            raise Exception("Walking speed cannot be 0, change your walking speed higher than 1!")
        else:
            self.steps = (self.dist + 0.0) / (self.speed + 0.0)

        if self.dist < self.speed or int(self.steps) <= 1:
            self.dLat = 0
            self.dLng = 0
        else:
            self.dLat = (dest_lat - self.initLat) / int(self.steps)
            self.dLng = (dest_lng - self.initLng) / int(self.steps)
            
        self.bearing = self._calc_bearing(self.initLat, self.initLng, self.destLat, self.destLng)

    def step(self):
        if (self.dLat == 0 and self.dLng == 0) or self.dist < self.speed:
            self.api.set_position(self.destLat, self.destLng, self.alt)
            self.bot.event_manager.emit(
                'position_update',
                sender=self,
                level='debug',
                data={
                    'current_position': (self.destLat, self.destLng),
                    'last_position': (self.initLat, self.initLng),
                    'distance': '',
                    'distance_unit': ''
                }
            )
            self.bot.heartbeat()
            # This step is implicitlly teleporting...
            # and since now we have variable speeds it can be quite often that self.dist < self.speed
            # especially for the polyline
            # need to speed one even when teleporting small distances
            sleep(1)  # sleep one second plus a random delta
            return True


        self._new_position = self._get_next_pos(self.initLat, self.initLng, self.bearing, self.speed, self.precision)
        cAlt = self.initAlt + random_alt_delta()

        self.api.set_position(self._new_position[0], self._new_position[1], cAlt)
        self.bot.event_manager.emit(
            'position_update',
            sender=self,
            level='debug',
            data={
                'current_position': (self._new_position[0], self._new_position[1], cAlt),
                'last_position': (self.initLat, self.initLng, self.initAlt),
                'distance': '',
                'distance_unit': ''
            }
        )
        self.bot.heartbeat()

        sleep(1)  # sleep one second plus a random delta
        # self._work_at_position(
        #     self.initLat, self.initLng,
        #     alt, False)

    def _calc_bearing(self, start_lat, start_lng, dest_lat, dest_lng):
        """
        Calculates the bearing between two points.
    
        The formulae used is the following:
            θ = atan2(sin(Δlong).cos(lat2),
                      cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
    
        :Parameters:
          - `start_lat in decimal degrees
          - `start_lng in decimal degrees
          - `dest_lat in decimal degrees
          - `dest_lng in decimal degrees
    
        :Returns:
          The bearing in degrees
    
        :Returns Type:
          float
        """
    
        lat1 = math.radians(start_lat)
        lat2 = math.radians(dest_lat)
    
        diffLong = math.radians(dest_lng - start_lng)
    
        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                * math.cos(lat2) * math.cos(diffLong))
    
        initial_bearing = math.atan2(x, y)
    
        # Now we have the initial bearing but math.atan2 return values
        # from -180° to + 180° which is not what we want for a compass bearing
        # The solution is to normalize the initial bearing as shown below
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
    
        return compass_bearing
        
    def _get_next_pos(self, lat, lon, bearing, speed, precision):
        origin = Point(lat, lon)
        if speed == 0.0:
            return lat, lon
        if speed == float("inf"):
            return self.destLat, self.destLng
        else:
            offset_angle = (1/self.speed)*(precision/1.74)
            lat, lon, _ = VincentyDistance(kilometers=speed*1e-3).destination(origin, bearing + uniform(-offset_angle, offset_angle))
            return lat, lon
