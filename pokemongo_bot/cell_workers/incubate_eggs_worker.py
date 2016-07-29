from utils import distance, format_dist
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class IncubateEggsWorker(object):
    last_km_walked = 0

    def __init__(self, bot):
        self.bot = bot
        self.ready_incubators = []
        self.used_incubators = []
        self.eggs = []
        self.km_walked = 0

    def work(self):
        if not self.bot.config.hatch_eggs:
            return

        try:
            self._check_inventory()
        except:
            return
            
        if self.used_incubators and IncubateEggsWorker.last_km_walked!=self.km_walked:
            self.used_incubators.sort(key=lambda x: x.get("km"), reverse=True)
            km_left = self.used_incubators[0]['km']-self.km_walked
            if km_left<=0:
                self._hatch_eggs()
            else:
                logger.log('[x] Next egg incubates in {:.2f} km'.format(km_left),'yellow')
            IncubateEggsWorker.last_km_walked = self.km_walked
        
        sorting = self.bot.config.longer_eggs_first
        self.eggs.sort(key=lambda x: x.get("km"))
        
        if self.ready_incubators:
            self._apply_incubators()

    def _apply_incubators(self):
        for incubator in self.ready_incubators:
            for egg in self.eggs:
                if egg["used"] or egg["km"] == -1:
                    continue                
                if self.bot.config.debug:    
                    logger.log('[x] Attempting to apply incubator {} to egg {}'.format(incubator['id'],egg['id']))
                self.bot.api.use_item_egg_incubator(item_id=incubator["id"], pokemon_id=egg["id"])
                ret = self.bot.api.call()
                if ret:
                    code = ret.get("responses", {}).get("USE_ITEM_EGG_INCUBATOR", {}).get("result", 0)
                    if code == 1:
                        logger.log('[x] Now incubating a ' + str(egg["km"]) + "km egg", 'green')
                        egg["used"] = True
                        incubator["used"] = True
                        break
                    elif code == 5 or code == 7:
                        if self.bot.config.debug:
                            logger.log('[x] Incubator already in use')
                        incubator["used"] = True
                        break
                    elif code == 6:
                        if self.bot.config.debug:
                            logger.log('[x] Egg already incubating')
                        egg["used"] = True

    def _check_inventory(self):
        inv = {}
        response_dict = self.bot.get_inventory()
        inv = reduce(dict.__getitem__, ["responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        for inv_data in inv:
            inv_data = inv_data.get("inventory_item_data", {})
            if "egg_incubators" in inv_data:
                incubators = inv_data.get("egg_incubators", {}).get("egg_incubator",[])
                if isinstance(incubators, basestring): # checking for old response
                    incubators = [incubators]
                for incubator in incubators:
                    if 'pokemon_id' in incubator:
                        self.used_incubators.append({"id":incubator.get('id', -1), "km":incubator.get('target_km_walked', 9001)})
                    else:
                        self.ready_incubators.append({"id":incubator.get('id',-1)})
                continue
            if "pokemon_data" in inv_data:
                pokemon = inv_data.get("pokemon_data", {})
                if pokemon.get("is_egg", False) and "egg_incubator_id" not in pokemon:
                    self.eggs.append({"id": pokemon.get("id", -1), "km": pokemon.get("egg_km_walked_target", -1), "used": False})
                continue
            if "player_stats" in inv_data:
                self.km_walked = inv_data.get("player_stats", {}).get("km_walked", 0)

    def _hatch_eggs(self):
        self.bot.api.get_hatched_eggs()
        response_dict = self.bot.api.call()
        try:
            result = reduce(dict.__getitem__, ["responses", "GET_HATCHED_EGGS"], response_dict)
        except KeyError:
            pass
        else:
            if 'pokemon_id' in result:
                pokemon_ids = [id for id in result['pokemon_id']]
            stardust = result.get('stardust_awarded', 0)
            candy = result.get('candy_awarded', 0)
            xp = result.get('experience_awarded', 0)
            logger.log("[!] Eggs hatched! Received:", 'green')
            logger.log("[!] XP: {}".format(xp),'green')
            logger.log("[!] Stardust: {}".format(stardust),'green')
            logger.log("[!] Candy: {}".format(candy),'green')
        sleep(4.20)
        self.bot.latest_inventory = None
        try:
            self._check_inventory()
        except:
            pass # just proceed with what we have