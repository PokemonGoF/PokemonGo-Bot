from pokemongo_bot import logger
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers import MoveToFortWorker, SeenFortWorker
from utils import distance

class SpinNearestFortWorker(object):

    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

        self.cell = bot.cell
        self.fort_timeouts = bot.fort_timeouts
        self.position = bot.position
        self.recent_forts = bot.recent_forts

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        nearest_fort = self.get_nearest_fort()

        if nearest_fort:
            # Move to and spin the nearest stop.
            if MoveToFortWorker(nearest_fort, self.bot).work() == WorkerResult.RUNNING:
                return WorkerResult.RUNNING
            if SeenFortWorker(nearest_fort, self.bot).work() == WorkerResult.RUNNING:
                return WorkerResult.RUNNING

        return WorkerResult.SUCCESS

    def should_run(self):
        number_of_things_gained_by_stop = 5

        enough_space = self.bot.get_inventory_count('item') < self.bot._player['max_item_storage'] - number_of_things_gained_by_stop

        return self.config.spin_forts and enough_space

    def get_nearest_fort(self):
        forts = self.bot.get_forts()

        # Remove stops that are still on timeout
        forts = filter(lambda x: x["id"] not in self.fort_timeouts, forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.config.avoid_circles:
            forts = filter(lambda x: x["id"] not in self.recent_forts, forts)

        if len(forts) > 0:
            return forts[0]
        else:
            return None
