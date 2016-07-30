from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from utils import distance, format_dist


class MoveToPositionWorker(object):

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    def should_run(self):
        return bool(self.bot.cached_destination)

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        if not self.bot.cached_destination:
            return

        lat = self.bot.cached_destination[0]
        lng = self.bot.cached_destination[1]

        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(self.bot.position[0], self.bot.position[1], lat, lng)

        # print('Found fort {} at distance {}m'.format(fortID, dist))

        if dist > Constants.MAX_DISTANCE_DEST_ACCURACY:
            logger.log('[x] Moving Closer to Destination {}, {} left'.format(self.bot.cached_destination, format_dist(dist, unit)))

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