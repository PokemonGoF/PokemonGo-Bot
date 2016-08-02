# -*- coding: utf-8 -*-

import gpxpy
import gpxpy.gpx
import json
import pokemongo_bot.logger as logger
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.cell_workers.utils import distance, i2f, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.step_walker import StepWalker
from pgoapi.utilities import f2i
import googlemaps


class FollowHumanPath(BaseTask):
    def get_gmap_directions(self, origin, destination):
        tmp = googlemaps.directions.directions(self.bot.gmap_client, origin, destination, mode="walking", optimize_waypoints=True)
        tmp = googlemaps.convert.decode_polyline(tmp[0]['overview_polyline']['points'])
        return tmp

    def initialize(self):
        self.ptr = 0
        self._process_config()
        self.points = self.load_path()

    def _process_config(self):
        self.path_file = self.config.get("path_file", None)
        self.path_mode = self.config.get("path_mode", "linear")

    def load_path(self):
        if self.path_file is None:
            raise RuntimeError('You need to specify a path file (json or gpx)')

        path = []
        if self.path_file.endswith('.json'):
            path = self.load_json()
        elif self.path_file.endswith('.gpx'):
            path = self.load_gpx()
        new_path = []
        for index, point in enumerate(path):
            if not index + 1 >= len(path):
                new_path.extend(self.get_gmap_directions(path[index], path[index + 1]))
        return new_path

    def load_json(self):
        with open(self.path_file) as data_file:
            points=json.load(data_file)
        # Replace Verbal Location with lat&lng.
        logger.log("Resolving Navigation Paths (GeoLocating Strings)")
        for index, point in enumerate(points):
            if self.bot.config.debug:
                logger.log("Resolving Point {} - {}".format(index, point))
            point_tuple = self.bot.get_pos_by_name(point['location'])
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

    def work(self):
        point = self.points[self.ptr]
        lat = float(point['lat'])
        lng = float(point['lng'])

        if self.bot.config.walk > 0:
            step_walker = StepWalker(
                self.bot,
                self.bot.config.walk,
                lat,
                lng
            )

            is_at_destination = False
            if step_walker.step():
                is_at_destination = True

        else:
            self.bot.api.set_position(lat, lng)

        dist = distance(
            self.bot.api._position_lat,
            self.bot.api._position_lng,
            lat,
            lng
        )

        if dist <= 1 or (self.bot.config.walk > 0 and is_at_destination):
            if (self.ptr + 1) == len(self.points):
                self.ptr = 0
                if self.path_mode == 'linear':
                    self.points = list(reversed(self.points))
            else:
                self.ptr += 1

        return [lat, lng]
