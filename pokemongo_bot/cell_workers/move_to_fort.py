from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.base_task import BaseTask
from utils import distance, format_dist


class MoveToFort(BaseTask):

    def initialize(self):
        self.lure_distance = 0
        self.lure_attraction = self.config.get("lure_attraction", True)
        self.lure_max_distance = self.config.get("lure_max_distance", 2000)

    def is_attracted(self):
        return (self.lure_distance > 0)

    def work(self, *args, **kwargs):
        nearest_fort = self.get_nearest_fort()

        if nearest_fort is None:
            logger.log("can't find a nearby fort to walk to", 'yellow')
            return WorkerResult.SUCCESS

        lat = nearest_fort['latitude']
        lng = nearest_fort['longitude']
        fortID = nearest_fort['id']

        unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            lat,
            lng
        )

        if dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            if self.is_attracted() > 0:
                add_str = ' (attraction of lure {})'.format(format_dist(self.lure_distance, unit))
            else:
                add_str = ''

            logger.log('Moving towards fort {}, {} left{}'.format(fortID, format_dist(dist, unit), add_str))

            step_walker = StepWalker(
                self.bot,
                self.bot.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('Arrived at pokestop: {}'.format(fortID))

        return WorkerResult.SUCCESS

    def _get_nearest_fort_on_lure_way(self, forts):

        if not self.lure_attraction:
            return None, 0

        lures = filter(lambda x: True if x.get('lure_info', None) != None else False, forts)

        if (len(lures)):
            dist_lure_me = distance(self.bot.position[0], self.bot.position[1],
                                    lures[0]['latitude'],lures[0]['longitude'])
        else:
            dist_lure_me = 0

        if dist_lure_me > 0 and dist_lure_me < self.lure_max_distance:

            self.lure_distance = dist_lure_me

            for fort in forts:
                dist_lure_fort = distance(
                    fort['latitude'],
                    fort['longitude'],
                    lures[0]['latitude'],
                    lures[0]['longitude'])
                dist_fort_me = distance(
                    fort['latitude'],
                    fort['longitude'],
                    self.bot.position[0],
                    self.bot.position[1])

                if dist_lure_fort < dist_lure_me and dist_lure_me > dist_fort_me:
                    return fort, dist_lure_me

                if dist_fort_me > dist_lure_me:
                    break

            return lures[0], dist_lure_me

        else:
            return None, 0

    def get_nearest_fort(self):
        forts = self.bot.get_forts(order_by_distance=True)

        # Remove stops that are still on timeout
        forts = filter(lambda x: x["id"] not in self.bot.fort_timeouts, forts)

        forts = filter(lambda x: 'cooldown_complete_timestamp_ms' not in x, forts)

        next_attracted_pts, lure_distance = self._get_nearest_fort_on_lure_way(forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.bot.config.forts_avoid_circles:
            forts = filter(lambda x: x["id"] not in self.bot.recent_forts, forts)

        self.lure_distance = lure_distance

        if (lure_distance > 0):
            return next_attracted_pts

        if len(forts) > 0:
            return forts[0]
        else:
            return None
