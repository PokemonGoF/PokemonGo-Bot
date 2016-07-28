from utils import distance, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger


class IncubateEggsWorker(object):
    def __init__(self, bot):
        self.api = bot.api
        self.config = bot.config
        self.bot = bot
        # self.position = bot.position

    def work(self):
        if not self.config.hatch_eggs:
            return

        response_dict = self.bot.get_inventory()
        inv = {}
        incubators = []
        eggs = []

        try:
            inv = reduce(dict.__getitem__, [
                "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for inv_data in inv:
                inv_data = inv_data.get("inventory_item_data", {})

                if "egg_incubators" in inv_data:
                    for incubator in inv_data.get("egg_incubators", {}).get("egg_incubator", []):
                        if "pokemon_id" not in incubator:
                            incubators.append({"id":incubator.get("id", -1), "used":False})

                if "pokemon_data" in inv_data:
                    pokemon = inv_data.get("pokemon_data", {})
                    if pokemon.get("is_egg", False) and "egg_incubator_id" not in pokemon:
                        eggs.append({"id": pokemon.get("id", -1), "km": pokemon.get("egg_km_walked_target", -1), "used": False})

            sorting = self.config.longer_eggs_first
            eggs.sort(key=lambda x: x.get("km"), reverse=sorting)

            for incubator in incubators:
                if incubator["used"]:
                    continue

                for egg in eggs:
                    if egg["used"] or egg["km"] == -1:
                        continue

                    self.api.use_item_egg_incubator(item_id=incubator["id"], pokemon_id=egg["id"])
                    ret = self.api.call()
                    if ret:
                        code = ret.get("responses", {}).get("USE_ITEM_EGG_INCUBATOR", {}).get("result", 0)
                        if code == 1:
                            logger.log('Successfully incubated a ' + str(egg["km"]) + "km egg", 'green')
                            egg["used"] = True
                            incubator["used"] = True
                            break
                        elif code == 5 or code == 7:
                            incubator["used"] = True
                            break
                        elif code == 6:
                            egg["used"] = True

