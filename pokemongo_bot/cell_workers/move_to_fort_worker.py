from utils import distance, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class MoveToFortWorker(object):
    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.config = bot.config
        self.stepper = bot.stepper
        self.position = bot.position

    def work(self):
        lat = self.fort['latitude']
        lng = self.fort['longitude']
        fortID = self.fort['id']
        unit = self.config['location']['distance_unit']

        dist = distance(self.position[0], self.position[1], lat, lng)

        logger.log('[#] Found fort {} at distance {}'.format(fortID, format_dist(dist, unit)))

        if dist > 10:
            logger.log('[#] Need to move closer to Pokestop')
            position = (lat, lng, 0.0)

            if self.config['bot']['speed'] > 0:
                self.stepper._walk_to(self.config['bot']['speed'], *position)
            else:
                self.api.set_position(*position)

            self.api.player_update(latitude=lat, longitude=lng)
            response_dict = self.api.call()
            logger.log('[#] Arrived at Pokestop')
            sleep(2)
            return response_dict

        return None
