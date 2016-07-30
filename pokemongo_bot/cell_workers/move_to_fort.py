from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from utils import distance, format_dist, fort_details


class MoveToFort(object):

    def __init__(self, bot):
        self.bot = bot
        self.initialized = False
        self.nearest_fort = None
        self.step_walker = None

    def should_run(self):
        return (self.bot.config.forts_spin and \
         self.bot.config.forts_move_to_spin and \
         self.bot.has_space_for_loot()) or self.bot.softban

    def navigate_to_fort(self):
        self.nearest_fort = self.get_nearest_fort()
        self.step_walker = StepWalker(
            self.bot,
            self.bot.config.walk,
            self.nearest_fort['latitude'],
            self.nearest_fort['longitude']
        )
        
    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        if not self.initialized:
            self.navigate_to_fort()
            self.initialized = True

        if self.nearest_fort is None:
            return WorkerResult.SUCCESS

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            self.nearest_fort['latitude'],
            self.nearest_fort['longitude']
        )

        if dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            lat = self.nearest_fort['latitude']
            lng = self.nearest_fort['longitude']
            fort_id = self.nearest_fort['id']
            details = fort_details(self.bot, fort_id, lat, lng)
            fort_name = details.get('name', 'Unknown').encode('utf8', 'replace')
            unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

            logger.log('Moving towards fort {}, {} left'.format(fort_name, format_dist(dist, unit)))
            if not self.step_walker.step():
                return WorkerResult.RUNNING

        logger.log('Arrived at pokestop.')
        self.navigate_to_fort()
        return WorkerResult.SUCCESS

    def get_nearest_fort(self):
        forts = self.bot.get_forts(order_by_distance=True)

        # Remove stops that are still on timeout
        forts = filter(lambda x: x["id"] not in self.bot.fort_timeouts, forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.bot.config.forts_avoid_circles:
            forts = filter(lambda x: x["id"] not in self.bot.recent_forts, forts)

        if len(forts) > 0:
            return forts[0]
        else:
            return None
