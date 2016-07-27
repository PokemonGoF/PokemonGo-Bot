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
        self._step_walker = None

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']
        fortID = self.fort['id']
        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(self.position[0], self.position[1], lat, lng)

        # print('Found fort {} at distance {}m'.format(fortID, dist))
        logger.log('Found fort {} at distance {}'.format(
            fortID, format_dist(dist, unit)))

        if dist > 10:
            logger.log('Need to move closer to Pokestop')
            position = (lat, lng, 0.0)

            if self.config.walk > 0:
                if self._step_walker == None:
                    self._step_walker = StepWalker(
                        self.bot,
                        self.config.walk,
                        self.api._position_lat,
                        self.api._position_lng,
                        position[0],
                        position[1]
                    )


                if self._step_walker.step():
                    return WorkerResult.SUCCESS
                else:
                    return WorkerResult.RUNNING

            else:
                self.api.set_position(*position)

            self.api.player_update(latitude=lat, longitude=lng)
            response_dict = self.api.call()
            logger.log('Arrived at Pokestop')
            sleep(2)
            return WorkerResult.SUCCESS

        return None
