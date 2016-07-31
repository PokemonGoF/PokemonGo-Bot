from pokemongo_bot import logger
from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.cell_workers.utils import distance
from pokemongo_bot.cell_workers.utils import find_biggest_cluster


class FollowCluster(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.is_at_destination = False
        self.announced = False
        self.dest = None
        self.config = config
        self._process_config()

    def _process_config(self):
        self.radius = self.config.get("radius", 50)

    def work(self):
        forts = self.bot.get_forts()
        self.dest = find_biggest_cluster(self.radius, forts)

        if self.dest is not None:

            lat = self.dest['latitude']
            lng = self.dest['longitude']
            cnt = self.dest['num_points']

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


