# -*- coding: utf-8 -*-
from polyline_walker import PolylineWalker
from stepper import Stepper
from human_behaviour import sleep, random_lat_long_delta


class PolylineStepper(Stepper):

    def _walk_to(self, speed, lat, lng, alt):
        origin = ','.join([str(self.api._position_lat), str(self.api._position_lng)])
        destination = ','.join([str(lat), str(lng)])
        polyline_walker = PolylineWalker(origin, destination, self.speed)
        proposed_origin = polyline_walker.points[0]
        proposed_destination = polyline_walker.points[-1]
        proposed_lat = proposed_origin[0]
        proposed_lng = proposed_origin[1]
        if proposed_lat != lat and proposed_lng != lng:
            self._old_walk_to(speed, proposed_lat, proposed_lng, alt)
        while proposed_destination != polyline_walker.get_pos()[0]:
            cLat, cLng = polyline_walker.get_pos()[0]
            self.api.set_position(cLat, cLng, alt)
            self.bot.heartbeat()
            self._work_at_position(i2f(self.api._position_lat), i2f(self.api._position_lng), alt, False)
            sleep(1)  # sleep one second plus a random delta
        if proposed_lat != self.api._position_lat and proposed_lng != self.api._position_lng:
            self._old_walk_to(speed, lat, lng, alt)

    def _old_walk_to(self, speed, lat, lng, alt):
        dist = distance(
            i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps
        logger.log('[#] Walking from ' + str((i2f(self.api._position_lat), i2f(
            self.api._position_lng))) + " to " + str(str((lat, lng))) +
                   " for approx. " + str(format_time(ceil(steps))))
        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + \
                    dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + \
                    dLng + random_lat_long_delta()
                self.api.set_position(cLat, cLng, alt)
                self.bot.heartbeat()
                sleep(1)  # sleep one second plus a random delta
                self._work_at_position(
                    i2f(self.api._position_lat), i2f(self.api._position_lng),
                    alt, False)

            self.api.set_position(lat, lng, alt)
            self.bot.heartbeat()
            logger.log("[#] Finished walking")

