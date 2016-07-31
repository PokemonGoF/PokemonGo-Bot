from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.cell_workers import find_biggest_cluster
from pokemongo_bot.cell_workers.utils import distance


class FollowCluster(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.is_at_destination = False
        self.announced = False
        self.dest = None

    def work(self):
        worker = [x for x in self.bot.workers if type(x) == find_biggest_cluster.FindBiggestCluster][0]
        self.radius = worker.radius

        if worker.dest is not None:
            self.dest = worker.dest

        if self.dest is not None:

            lat = self.dest['latitude']
            lng = self.dest['longitude']
            cnt = self.dest['num_forts']

            if not self.is_at_destination:
                log_str = 'Move to destiny. ' + str(cnt) + ' pokestops will in range of ' \
                          + str(self.radius) + 'm. Arrive in ' \
                          + str(distance(self.bot.position[0], self.bot.position[1], lat, lng)) + 'm.'
                logger.log(log_str)
                self.announced = False

                if self.bot.config.walk > 0:
                    step_walker = StepWalker(
                        self.bot,
                        self.bot.config.walk,
                        lat,
                        lng
                    )

                    self.is_at_destination = False
                    if step_walker.step():
                        self.is_at_destination = True
                else:
                    self.bot.api.set_position(lat, lng)

            elif not self.announced:
                log_str = 'Arrived at destiny. ' + str(cnt) + ' pokestops are in range of ' \
                         + str(self.radius) + 'm.'
                logger.log(log_str)
                self.announced = True
        else:
            lat = self.bot.position[0]
            lng = self.bot.position[1]

        return [lat, lng]


