import json
import datetime
import os.path

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger


class InventoryActionsWorker(object):

    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api
        self.inventory_options_file = 'data/inventory_options'

    def work(self):
        if self.config.use_lucky_egg and (self.config.mode == "all" or
                                          self.config.mode == "poke"):
            self._use_lucky_eggs()

    def _use_lucky_eggs(self):
        lucky_egg_file = 'data/last-lucky-egg-use-{0}.json'.format(self.config.username)
        if os.path.isfile(lucky_egg_file):
            with open('data/last-lucky-egg-use-%s.json' %
                    (self.config.username)) as f:
                last_use_json = json.load(f)
                self.last_lucky_egg_use = datetime.datetime.strptime(
                    last_use_json['last_use'], '%Y-%m-%d %H:%M:%S.%f')
        else:
            # First time we let the last lucky egg use to minus 30 minutes to
            # use lucky egg
            self.last_lucky_egg_use = datetime.datetime.now() - datetime.timedelta(minutes=30)

        last_use_delta = datetime.datetime.today() - self.last_lucky_egg_use
        last_use_in_minutes = last_use_delta.seconds / 60
        if last_use_in_minutes >= 30:
            logger.log(
                '[x] {0} minutes since last lucky egg used'.format(
                last_use_in_minutes))
            logger.log(
                '[x] Using lucky egg!')
            with open(lucky_egg_file, 'w') as f:
                data = {"last_use": str(datetime.datetime.now())}
                json.dump(data, f)

        return
