# -*- coding: utf-8 -*-

import gpxpy
import gpxpy.gpx
import json
import time
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.utils import distance, i2f, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.walkers.walker_factory import walker_factory
from pokemongo_bot.worker_result import WorkerResult
from pgoapi.utilities import f2i
from random import uniform
from utils import getSeconds
from datetime import datetime as dt, timedelta

STATUS_MOVING = 0
STATUS_LOITERING = 1
STATUS_FINISHED = 2
 
class FollowPath(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self._process_config()
        self.points = self.load_path()
        self.status = STATUS_MOVING
        self.loiter_end_time = 0

        if self.path_start_mode == 'closest':
            self.ptr = self.find_closest_point_idx(self.points)

        else:
            self.ptr = 0

    def _process_config(self):
        self.path_file = self.config.get("path_file", None)
        self.path_mode = self.config.get("path_mode", "linear")
        self.path_start_mode = self.config.get("path_start_mode", "first")
        self.number_lap_max = self.config.get("number_lap", -1) # if < 0, then the number is inf.
        self.timer_restart_min = getSeconds(self.config.get("timer_restart_min", "00:20:00"))
        self.timer_restart_max = getSeconds(self.config.get("timer_restart_max", "02:00:00"))
        self.walker = self.config.get('walker', 'StepWalker')

        if self.timer_restart_min > self.timer_restart_max:
            raise ValueError('path timer_restart_min is bigger than path timer_restart_max') #TODO there must be a more elegant way to do it...
        
        #var not related to configs
        self.number_lap = 0
        
    def load_path(self):
        if self.path_file is None:
            raise RuntimeError('You need to specify a path file (json or gpx)')

        if self.path_file.endswith('.json'):
            return self.load_json()
        elif self.path_file.endswith('.gpx'):
            return self.load_gpx()

    def load_json(self):
        with open(self.path_file) as data_file:
            points=json.load(data_file)
        # Replace Verbal Location with lat&lng.
        for _, point in enumerate(points):
            point_tuple = self.bot.get_pos_by_name(point['location'])
            self.emit_event(
                'location_found',
                level='debug',
                formatted="Location found: {location} {position}",
                data={
                    'location': point,
                    'position': point_tuple
                }
            )
            # Keep point['location']
            point["lat"] = float(point_tuple[0])
            point["lng"] = float(point_tuple[1])
            point["alt"] = float(point_tuple[2])
        return points

    def load_gpx(self):
        gpx_file = open(self.path_file, 'r')
        gpx = gpxpy.parse(gpx_file)

        if len(gpx.tracks) == 0:
            raise RuntimeError('GPX file does not contain a track')

        points = []
        track = gpx.tracks[0]
        for segment in track.segments:
            for point in segment.points:
                points.append({"lat": point.latitude, "lng": point.longitude,
                    "alt": point.elevation, "location": point.name})

        return points

    def find_closest_point_idx(self, points):
        return_idx = 0
        min_distance = float("inf");
        for index in range(len(points)):
            point = points[index]
            botlat = self.bot.api._position_lat
            botlng = self.bot.api._position_lng
            lat = point['lat']
            lng = point['lng']

            dist = distance(
                botlat,
                botlng,
                lat,
                lng
            )

            if dist < min_distance:
                min_distance = dist
                return_idx = index

        return return_idx

    def endLaps(self):
        duration = int(uniform(self.timer_restart_min, self.timer_restart_max))
        resume = dt.now() + timedelta(seconds=duration)
        
        self.emit_event(
            'path_lap_end',
            formatted="Great job, lot of calories burned! Taking a break now for {duration}, will resume at {resume}.",
            data={
                'duration': str(timedelta(seconds=duration)),
                'resume': resume.strftime("%H:%M:%S")
            }
        )
        
        self.number_lap = 0 # at the end of the break, start again
        sleep(duration)
        self.bot.login()

    def work(self):
        # If done or loitering allow the next task to run
        if self.status == STATUS_FINISHED:
            return WorkerResult.SUCCESS

        if self.status == STATUS_LOITERING and time.time() < self.loiter_end_time:
            return WorkerResult.SUCCESS

        last_lat = self.bot.api._position_lat
        last_lng = self.bot.api._position_lng
        last_alt = self.bot.api._position_alt

        point = self.points[self.ptr]
        lat = point['lat']
        lng = point['lng']

        if 'alt' in point:
            alt = float(point['alt'])
        else:
            alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)

        if self.bot.config.walk_max > 0:
            step_walker = walker_factory(self.walker,
                self.bot,
                lat,
                lng,
                alt
            )

            is_at_destination = False
            if step_walker.step():
                is_at_destination = True

        else:
            self.bot.api.set_position(lat, lng, alt)

        dist = distance(
            last_lat,
            last_lng,
            lat,
            lng
        )

        self.emit_event(
            'position_update',
            formatted="Walking from {last_position} to {current_position}, distance left: ({distance} {distance_unit}) ..",
            data={
                'last_position': (last_lat, last_lng, last_alt),
                'current_position': (lat, lng, alt),
                'distance': dist,
                'distance_unit': 'm'
            }
        )
        
        if dist <= 1 or (self.bot.config.walk_min > 0 and is_at_destination) or (self.status == STATUS_LOITERING and time.time() >= self.loiter_end_time):
            if "loiter" in point and self.status != STATUS_LOITERING: 
                print("Loitering {} seconds".format(point["loiter"]))
                self.status = STATUS_LOITERING
                self.loiter_end_time = time.time() + point["loiter"]
                return WorkerResult.SUCCESS
            if (self.ptr + 1) == len(self.points):
                if self.path_mode == 'single':
                    self.status = STATUS_FINISHED
                    return WorkerResult.SUCCESS
                self.ptr = 0
                if self.path_mode == 'linear':
                    self.points = list(reversed(self.points))
                if self.number_lap_max >= 0:
                    self.number_lap+=1
                    self.emit_event(
                        'path_lap_update',
                        formatted="number lap : {number_lap} / {number_lap_max}",
                        data={
                            'number_lap': str(self.number_lap),
                            'number_lap_max': str(self.number_lap_max)
                        }
                    )
                    if self.number_lap >= self.number_lap_max:
                        self.endLaps()
            else:
                self.ptr += 1
        
        self.status = STATUS_MOVING
        return WorkerResult.RUNNING
