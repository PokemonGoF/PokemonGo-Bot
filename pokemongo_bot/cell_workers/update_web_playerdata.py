import json
import os
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.base_dir import _base_dir


class UpdateWebPlayerdata(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        pass

    def work(self):
        self.bot.metrics.capture_stats()
        self.update_player_stats(self.bot.metrics.player_stats)
                
    def update_player_stats(self,player_data):
        web_inventory = os.path.join(_base_dir, "web", "inventory-%s.json" % self.bot.config.username)

        try:
            with open(web_inventory, "r") as infile:
                json_stats = json.load(infile)
        except (IOError, ValueError):
            # Unable to read json from web inventory
            # File may be corrupt. Create a new one.
            self.bot.logger.info('[x] Error while opening inventory file for read: %s' % e, 'red')
            json_stats = []
        except:
            raise FileIOException("Unexpected error loading information from json.")

        json_stats = [x for x in json_stats if not x.get("inventory_item_data", {}).get("player_stats", None)]
        
        json_stats.append({"inventory_item_data": {"player_stats": player_data}})

        try:
            with open(web_inventory, "w") as outfile:
                json.dump(json_stats, outfile)
        except (IOError, ValueError):
            self.bot.logger.info('[x] Error while opening inventory file for write: %s' % e, 'red')
            pass
        except:
            raise FileIOException("Unexpected error writing to {}".web_inventory)

