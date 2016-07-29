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
	self.progress_scale = 3;

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']
        fortID = self.fort['id']
        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(self.position[0], self.position[1], lat, lng)

        global original_dist
        try:
            if not original_dist > 0:
                original_dist = dist
        except NameError:
            original_dist = dist

        progress = (((original_dist - dist) / original_dist)*100)
        progressbar = "[" + ("|" * int(progress//self.progress_scale)).ljust(int(100/self.progress_scale)) + "]"


        if dist > 10:
            logger.log('Moving towards fort {}, {} left {} {}%'.format(fortID, format_dist(dist, unit),progressbar, int(progress)))

            step_walker = StepWalker(
                self.bot,
                self.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('Arrived at Pokestop')
	original_dist = 0
        return WorkerResult.SUCCESS
