from pgoapi.utilities import f2i

from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.cell_workers import MoveToFort
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.worker_result import WorkerResult


class HandleSoftBan(BaseTask):
    def work(self):
        if not self.should_run():
            return

        forts = self.bot.get_forts(order_by_distance=True)

        if len(forts) == 0:
            return

        fort_distance = distance(
            self.bot.position[0],
            self.bot.position[1],
            forts[0]['latitude'],
            forts[0]['longitude'],
        )

        if fort_distance > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            MoveToFort(self.bot).work()
            self.bot.recent_forts = self.bot.recent_forts[0:-1]
            if forts[0]['id'] in self.bot.fort_timeouts:
                del self.bot.fort_timeouts[forts[0]['id']]
            return WorkerResult.RUNNING
        else:
            self.bot.event_manager.emit(
                'softban_fix',
                sender=self,
                level='info',
                formatted='Fixing softban.'
            )
            for i in xrange(50):
                self.spin_fort(forts[0])
            self.bot.softban = False
            self.bot.event_manager.emit(
                'softban_fix_done',
                sender=self,
                level='info',
                formatted='Softban should be fixed'
            )

    def spin_fort(self, fort):
        self.bot.api.fort_search(
            fort_id=fort['id'],
            fort_latitude=fort['latitude'],
            fort_longitude=fort['longitude'],
            player_latitude=f2i(self.bot.position[0]),
            player_longitude=f2i(self.bot.position[1])
        )
        self.bot.api.call()
        self.bot.event_handler.emit(
            'spun_fort',
            sender=self,
            level='debug',
            formatted="Spun fort {fort_id}",
            data={
                'fort_id': fort_id,
                'lat': fort['latitude'],
                'lng': fort['longitude']
            }
        )

    def should_run(self):
        return self.bot.softban
