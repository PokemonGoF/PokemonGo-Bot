# -*- coding: utf-8 -*-

import gpxpy
import gpxpy.gpx
import json
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers.utils import distance, i2f, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.step_walker import StepWalker
from pgoapi.utilities import f2i


class FollowPath(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self._process_config()
        self.points = self.load_path()

        if self.path_start_mode == 'closest':
            self.ptr = self.find_closest_point_idx(self.points)

        else:
            self.ptr = 0

    def _process_config(self):
        self.path_file = self.config.get("path_file", None)
        self.path_mode = self.config.get("path_mode", "linear")
        self.path_start_mode = self.config.get("path_start_mode", "first")

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
        for index, point in enumerate(points):
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
            points[index] = self.lat_lng_tuple_to_dict(point_tuple)
        return points

    def lat_lng_tuple_to_dict(self, tpl):
        return {'lat': tpl[0], 'lng': tpl[1]}

    def load_gpx(self):
        gpx_file = open(self.path_file, 'r')
        gpx = gpxpy.parse(gpx_file)

        if len(gpx.tracks) == 0:
            raise RuntimeError('GPX file does not cotain a track')

        points = []
        track = gpx.tracks[0]
        for segment in track.segments:
            for point in segment.points:
                points.append({"lat": point.latitude, "lng": point.longitude})

        return points

    def find_closest_point_idx(self, points):

        return_idx = 0
        min_distance = float("inf");
        for index in range(len(points)):
            point = points[index]
            botlat = self.bot.api._position_lat
            botlng = self.bot.api._position_lng
            lat = float(point['lat'])
            lng = float(point['lng'])

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

    def work(self):
        last_lat = self.bot.api._position_lat
        last_lng = self.bot.api._position_lng

        point = self.points[self.ptr]
        lat = float(point['lat'])
        lng = float(point['lng'])

        if self.bot.config.walk_max > 0:
            step_walker = StepWalker(
                self.bot,
                lat,
                lng
            )

            is_at_destination = False
            if step_walker.step():
                is_at_destination = True

        else:
            self.bot.api.set_position(lat, lng, 0)

        dist = distance(
            last_lat,
            last_lng,
            lat,
            lng
        )

        if dist <= 1 or (self.bot.config.walk_min > 0 and is_at_destination):
            if (self.ptr + 1) == len(self.points):
                self.ptr = 0
                if self.path_mode == 'linear':
                    self.points = list(reversed(self.points))
            else:
                self.ptr += 1

        self.emit_event(
            'position_update',
            formatted="Walking from {last_position} to {current_position} ({distance} {distance_unit})",
            data={
                'last_position': (last_lat, last_lng, 0),
                'current_position': (lat, lng, 0),
                'distance': dist,
                'distance_unit': 'm'
            }
        )
        return [lat, lng]
