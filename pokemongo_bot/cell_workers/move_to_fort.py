from pokemongo_bot import logger
from pokemongo_bot.constants import Constants
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers.base_task import BaseTask
from utils import distance, format_dist, fort_details


class MoveToFort(BaseTask):
    def should_run(self):
        has_space_for_loot = self.bot.has_space_for_loot()
        if not has_space_for_loot:
            logger.log("Not moving to any forts as there aren't enough space. You might want to change your config to recycle more items if this message appears consistently.", 'yellow')
        return has_space_for_loot or self.bot.softban

    def work(self):
        if not self.should_run():
            return WorkerResult.SUCCESS

        nearest_fort = self.get_nearest_fort()

        if nearest_fort is None:
            return WorkerResult.SUCCESS

        lat = nearest_fort['latitude']
        lng = nearest_fort['longitude']
        fortID = nearest_fort['id']
        details = fort_details(self.bot, fortID, lat, lng)
        fort_name = details.get('name', 'Unknown').encode('utf8', 'replace')

        unit = self.bot.config.distance_unit  # Unit to use when printing formatted distance

        dist = distance(
            self.bot.position[0],
            self.bot.position[1],
            lat,
            lng
        )

        if dist > Constants.MAX_DISTANCE_FORT_IS_REACHABLE:
            logger.log('Moving towards fort {}, {} left'.format(fort_name, format_dist(dist, unit)))

            step_walker = StepWalker(
                self.bot,
                self.bot.config.walk,
                lat,
                lng
            )

            if not step_walker.step():
                return WorkerResult.RUNNING

        logger.log('Arrived at pokestop.')
        return WorkerResult.SUCCESS

    def get_nearest_fort(self):
        forts = self.bot.get_forts(order_by_distance=True)

        # Remove stops that are still on timeout
        forts = filter(lambda x: x["id"] not in self.bot.fort_timeouts, forts)

        # Remove all forts which were spun in the last ticks to avoid circles if set
        if self.bot.config.forts_avoid_circles:
            forts = filter(lambda x: x["id"] not in self.bot.recent_forts, forts)

        if len(forts) > 0:
            return forts[0]
        else:
            return None
