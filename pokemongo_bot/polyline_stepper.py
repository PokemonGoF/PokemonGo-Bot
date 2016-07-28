# -*- coding: utf-8 -*-
from math import ceil

import logger
from human_behaviour import sleep
from walkers.polyline_walker import PolylineWalker


class PolylineStepper(Stepper):

    def _walk_to(self, speed, lat, lng, alt):
        origin = ','.join([str(self.api._position_lat), str(self.api._position_lng)])
        destination = ','.join([str(lat), str(lng)])
        polyline_walker = PolylineWalker(origin, destination, speed)
        proposed_origin = polyline_walker.points[0]
        proposed_destination = polyline_walker.points[-1]
        proposed_lat = proposed_origin[0]
        proposed_lng = proposed_origin[1]
        if proposed_lat != lat and proposed_lng != lng:
            logger.log('[#] Using _old_walk_to to go to the proposed_origin: {}'
                       .format(proposed_origin))
            self._old_walk_to(speed, proposed_lat, proposed_lng, alt)
        if proposed_origin != proposed_destination:
            duration = polyline_walker.get_total_distance() / speed
            logger.log('[#] Using PolylineWalker from {} to {} for approx. {} seconds.'
                       .format(proposed_origin, proposed_destination, ceil(duration)))
            while proposed_destination != polyline_walker.get_pos()[0]:
                cLat, cLng = polyline_walker.get_pos()[0]
                self.api.set_position(cLat, cLng, alt)
                self.bot.heartbeat()
                self._work_at_position(self.api._position_lat, self.api._position_lng, alt, False)
                sleep(1)  # sleep one second plus a random delta
        if proposed_lat != self.api._position_lat and proposed_lng != self.api._position_lng:
            logger.log('[#] Using _old_walk_to to go from the proposed destination : {} to {}'
                       .format(proposed_destination, (lat, lng)))

            self._old_walk_to(speed, lat, lng, alt)

    def _old_walk_to(self, speed, lat, lng, alt):
        return super(PolylineStepper, self)._walk_to(speed, lat, lng, alt)
