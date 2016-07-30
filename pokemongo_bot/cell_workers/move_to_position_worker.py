from utils import distance, format_dist, i2f
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult

class MoveToPositionWorker(object):

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config
        self.navigator = bot.navigator
        self.position = bot.position
        self.location = self.bot.cached_destination

    def should_run(self):
        return bool(self.location)

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        if not self.location:
            return

        lat = self.location[0]
        lng = self.location[1]

        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(self.position[0], self.position[1], lat, lng)

        # print('Found fort {} at distance {}m'.format(fortID, dist))

        if dist > 5:
            logger.log('[x] Moving Closer to Destination {}, {} left'.format(self.location, format_dist(dist, unit)))

            step_walker = StepWalker(
                self.bot,
                self.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('[o] Arrived at Destination')
        self.bot.cached_destination = None
        return WorkerResult.SUCCESS