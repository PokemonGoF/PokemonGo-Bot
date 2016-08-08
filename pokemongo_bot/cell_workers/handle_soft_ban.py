from random import randint

from pgoapi.utilities import f2i

from pokemongo_bot.constants import Constants
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.cell_workers import MoveToFort
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.worker_result import WorkerResult


class HandleSoftBan(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

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
            MoveToFort(self.bot, config=None).work()
            self.bot.recent_forts = self.bot.recent_forts[0:-1]
            if forts[0]['id'] in self.bot.fort_timeouts:
                del self.bot.fort_timeouts[forts[0]['id']]
            return WorkerResult.RUNNING
        else:
            spins = randint(50,60)
            self.emit_event(
                'softban_fix',
                formatted='Fixing softban.'
            )
            for i in xrange(spins):
                self.spin_fort(forts[0])
            self.bot.softban = False
            self.emit_event(
                'softban_fix_done',
                formatted='Softban should be fixed'
            )

    def spin_fort(self, fort):
        fort_id = fort['id']
        latitude = fort['latitude']
        longitude = fort['longitude']
        self.bot.api.fort_search(
            fort_id=fort_id,
            fort_latitude=latitude,
            fort_longitude=longitude,
            player_latitude=f2i(self.bot.position[0]),
            player_longitude=f2i(self.bot.position[1])
        )
        self.emit_event(
            'spun_fort',
            level='debug',
            formatted="Spun fort {fort_id}",
            data={
                'fort_id': fort_id,
                'latitude': latitude,
                'longitude': longitude
            }
        )

    def should_run(self):
        return self.bot.softban
