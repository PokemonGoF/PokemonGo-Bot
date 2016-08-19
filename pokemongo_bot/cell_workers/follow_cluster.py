from pokemongo_bot.walkers.step_walker import StepWalker
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.cell_workers.utils import find_biggest_cluster
from pokemongo_bot.base_task import BaseTask
from random import uniform

class FollowCluster(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.is_at_destination = False
        self.announced = False
        self.dest = None
        self._process_config()

    def _process_config(self):
        self.lured = self.config.get("lured", True)
        self.radius = self.config.get("radius", 50)

    def work(self):
        forts = self.bot.get_forts()
        log_lure_avail_str = ''
        log_lured_str = ''
        if self.lured:
            lured_forts = [x for x in forts if 'active_fort_modifier' in x]
            if len(lured_forts) > 0:
                log_lured_str = 'lured '
                self.dest = find_biggest_cluster(self.radius, lured_forts, '9QM=')
            else:
                log_lure_avail_str = 'No lured pokestops in vicinity. Search for normal ones instead. '
                self.dest = find_biggest_cluster(self.radius, forts)
        else:
            self.dest = find_biggest_cluster(self.radius, forts)

        if self.dest is not None:

            lat = self.dest['latitude']
            lng = self.dest['longitude']
            cnt = self.dest['num_points']

            if not self.is_at_destination:
                msg = log_lure_avail_str + (
                    "Move to cluster: {num_points} {forts} "
                    "pokestops will be in range of {radius}. Walking {distance}m."
                )
                self.emit_event(
                    'found_cluster',
                    formatted=msg,
                    data={
                        'num_points': cnt,
                        'forts': log_lured_str,
                        'radius': str(self.radius),
                        'distance': str(round(distance(self.bot.position[0], self.bot.position[1], lat, lng), 2))
                    }
                )

                self.announced = False

                if self.bot.config.walk_max > 0:
                    step_walker = StepWalker(
                        self.bot,
                        lat,
                        lng
                    )

                    self.is_at_destination = False
                    if step_walker.step():
                        self.is_at_destination = True
                else:
                    alt = uniform(self.bot.config.alt_min, self.bot.config.alt_max)
                    self.bot.api.set_position(lat, lng, alt)

            elif not self.announced:
                self.emit_event(
                    'arrived_at_cluster',
                    formatted="Arrived at cluster. {num_points} {forts} pokestops are in a range of {radius}m radius.",
                    data={
                        'num_points': cnt,
                        'forts': log_lured_str,
                        'radius': self.radius
                    }
                )
                self.announced = True
        else:
            lat = self.bot.position[0]
            lng = self.bot.position[1]

        return [lat, lng]
