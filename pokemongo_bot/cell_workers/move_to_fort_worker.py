from utils import distance, format_dist, i2f
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker

class MoveToFortWorker(object):

    def __init__(self, fort, bot):
        self.bot = bot
        self.fort = fort
        self.api = bot.api
        self.config = bot.config
        self.navigator = bot.navigator
        self.position = bot.position

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']
        fortID = self.fort['id']
        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(self.position[0], self.position[1], lat, lng)

        # print('Found fort {} at distance {}m'.format(fortID, dist))
        logger.log('[x] Found fort {} at distance {}'.format(
            fortID, format_dist(dist, unit)))

        if dist > 10:
            logger.log('[x] Need to move closer to Pokestop')

            if self.config.walk > 0:
                step_walker = StepWalker(
                    self.bot,
                    self.config.walk,
                    self.api._position_lat,
                    self.api._position_lng,
                    position[0],
                    position[1]
                )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('[o] Arrived at Pokestop')
        return WorkerResult.SUCCESS
