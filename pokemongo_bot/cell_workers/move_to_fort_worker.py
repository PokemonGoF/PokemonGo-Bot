from utils import distance, format_dist, i2f
from pokemongo_bot.constants import Constants
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult

class MoveToFortWorker(object):

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config
        self.fort_timeouts = bot.fort_timeouts
        self.recent_forts = bot.recent_forts
        self.navigator = bot.navigator
        self.position = bot.position

    def should_run(self):
        return self.config.forts_spin and self.bot.has_space_for_loot()

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        nearest_fort = self.get_nearest_fort()

        if nearest_fort == None:
            return WorkerResult.SUCCESS

        lat = nearest_fort['latitude']
        lng = nearest_fort['longitude']
        fortID = nearest_fort['id']
        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(
            self.position[0],
            self.position[1],
            lat,
            lng
        )

        if dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            logger.log('Moving towards fort {}, {} left'.format(fortID, format_dist(dist, unit)))

            step_walker = StepWalker(
                self.bot,
                self.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('Arrived at pokestop.')
        return WorkerResult.SUCCESS

    def get_nearest_fort(self):
        forts = self.bot.get_forts()

        # Remove stops that are still on timeout
        forts = filter(lambda x: x["id"] not in self.fort_timeouts, forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.config.forts_avoid_circles:
            forts = filter(lambda x: x["id"] not in self.recent_forts, forts)

        if len(forts) > 0:
            return forts[0]
        else:
            return None
