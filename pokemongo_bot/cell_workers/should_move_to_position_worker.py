from pokemongo_bot import logger
from pokemongo_bot.worker_result import WorkerResult
from utils import distance
import json

class ShouldMoveToPositionWorker(object):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.cached_destination = self.bot.cached_destination

    def work(self):

        self.should_run()

        return WorkerResult.SUCCESS

    def should_run(self):
        if bool(self.cached_destination):
            return True
        self.get_json()

    def get_json(self):
        try:
            with open("configs/destination.json", 'r+') as f:
                try:
                    location_json = json.load(f)
                except ValueError:
                    logger.log("Invalid json file")
                    return

                try:
                    location = location_json['destination']
                except KeyError:
                    logger.log("Failed to Parse destination location")
                    return

                if location:
                    location = (self.bot.get_pos_by_name(location.replace(" ", "")))
                    # location_str = location.encode('utf-8')
                    logger.log("[!] Move To Position Directive Detected")
                    location_json['destination'] = ""
                    f.seek(0)
                    try:
                        json.dump(location_json, f)
                    except IOError:
                        logger.log("Failed to empty the destination file")
                        return
                    except:
                        logger.log("Unknown Error occurred attempting to empty the destination file")
                    f.truncate()
                    self.bot.cached_destination = location
                    logger.log("[V] Succesfully Parsed Destination, Moving to {}".format(location))
                    return
                return
        except IOError:
            return
