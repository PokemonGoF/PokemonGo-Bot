from utils import distance, format_dist, i2f
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult

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

        if dist > 10:
            if self.bot.softbanned == False:
                logger.log('Moving towards fort {}, {} left'.format(fortID, format_dist(dist, unit)))

            step_walker = StepWalker(
                self.bot,
                self.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        if self.bot.softbanned == False:
            logger.log('Arrived at Pokestop')

        return WorkerResult.SUCCESS

