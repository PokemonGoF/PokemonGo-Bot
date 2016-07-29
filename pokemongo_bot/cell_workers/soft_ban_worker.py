from pgoapi.utilities import f2i

from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.cell_workers import MoveToFortWorker, SeenFortWorker
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.worker_result import WorkerResult

class SoftBanWorker(object):

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config

    def work(self):
        if not self.should_run():
            return

        forts = self.bot.get_forts(order_by_distance=True)

        if len(forts) == 0:
            logger.log('Found no forts to reset softban, skipping...', 'red')
            return
        logger.log('Got softban, fixing...', 'yellow')

        fort_distance = distance(
            self.bot.position[0],
            self.bot.position[1],
            forts[0]['latitude'],
            forts[0]['longitude'],
        )

        if fort_distance > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            MoveToFortWorker(self.bot).work()
            self.bot.recent_forts = self.bot.recent_forts[0:-1]
            if forts[0]['id'] in self.bot.fort_timeouts:
                del self.bot.fort_timeouts[forts[0]['id']]
            return WorkerResult.RUNNING
        else:
            logger.log('Starting 50 spins...')
            for i in xrange(50):
                if (i + 1) % 10 == 0:
                    logger.log('Spin #{}'.format(str(i+1)))
                self.spin_fort(forts[0])
            self.softban = False
            logger.log('Softban should be fixed.')

    def spin_fort(self, fort):
        self.api.fort_search(
            fort_id=fort['id'],
            fort_latitude=fort['latitude'],
            fort_longitude=fort['longitude'],
            player_latitude=f2i(self.bot.position[0]),
            player_longitude=f2i(self.bot.position[1])
        )
        self.api.call()

    def should_run(self):
        return self.bot.config.softban_fix and self.bot.softban
