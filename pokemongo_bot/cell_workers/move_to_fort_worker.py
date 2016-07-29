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
        # print('Found fort {} at distance {}m'.format(fortID, dist))
        if fortID not in self.bot.lastFort:
            self.bot.lastFort = {fortID:dist}
            logger.log('Found fort {} at distance {}'.format(
                fortID, format_dist(dist, unit)))
            if dist > 10:
                logger.log('Need to move closer to Pokestop')
        else:
            changed = self.bot.lastFort[fortID] - dist
            if changed >= 10:
                logger.log("We are now {} away from fort {}".format(
                    format_dist(dist,unit),fortID))
                self.bot.lastFort[fortID] = dist
        if dist > 10:
            step_walker = StepWalker(
                self.bot,
                self.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('Arrived at Pokestop')
        return WorkerResult.SUCCESS
