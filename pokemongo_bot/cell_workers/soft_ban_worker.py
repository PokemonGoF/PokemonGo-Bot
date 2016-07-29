# -*- coding: utf-8 -*-

from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers import SeenFortWorker
from pokemongo_bot.cell_workers import MoveToFortWorker


class SoftBanWorker(object):
    def __init__(self, bot):
        self.running = False
        self.bot = bot
    def work(self):
       if self.bot.softbanned == True:
           nearest_fort = self.nearest_pokestop()
           MoveToFortWorker(nearest_fort, self.bot).work()
           SeenFortWorker(nearest_fort, self.bot).work()

           if self.bot.softbanned == True:
               return WorkerResult.RUNNING
 
    def nearest_pokestop(self):
        if 'forts' in self.bot.cell:
            forts = [fort
                for fort in self.bot.cell['forts']
                if 'latitude' in fort and 'type' in fort]
            forts.sort(key=lambda x: distance(self.bot.position[
                0], self.bot.position[1], x['latitude'], x['longitude']))
            return forts[0]

        return None
