import json

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger

class EggIncubationWorker(object):
    last_km_walked = 0

    def __init__(self, bot):
        self.bot = bot
        self.available_incubators = []
        self.used_incubators = []
        self.ready_eggs = []
        self.incubating_eggs = []
        self.km_walked = 0
        self.remaining_km = []
        EggIncubationWorker.last_km_walked

    def work(self):
        check_incubation = False
        self._check_inventory() # get km, incubators, and incubating pkmn
        self._calculate_remaining_km()
        if len(self.remaining_km) and min(self.remaining_km)<=0:
            logger.log('[#] Checking for hatched eggs...')
            check_incubation = self._check_hatched_eggs()
            sleep(10)
            self.bot.latest_inventory = None
            self._check_inventory() # incubators don't release til after check hatched eggs call
        if len(self.available_incubators) and len(self.ready_eggs):
            logger.log('[#] Applying incubators to eggs...')
            self._incubate_eggs()
            self._calculate_remaining_km() # get updated min km target
        if len(self.used_incubators) and (self.km_walked!=EggIncubationWorker.last_km_walked or check_incubation):
            logger.log('[#] Next egg hatches in {:.2n} km.'.format(min([km if km>=0 else 0 for km in self.remaining_km])),'yellow')
            EggIncubationWorker.last_km_walked=self.km_walked

    def _calculate_remaining_km(self):
        self.remaining_km = [(lambda x: x.get("target_km_walked",10000)-self.km_walked)(x) for x in self.used_incubators]

    def _check_hatched_eggs(self):
        hatch_success = False
        self.bot.api.get_hatched_eggs()
        response_dict = self.bot.api.call()
        logger.log('[d] Get hatched eggs call result: {}'.format(response_dict))
        try:
            hatched_results = response_dict['responses']['GET_HATCHED_EGGS']
            if 'pokemon_id' in hatched_results:
                hatch_success = True
                pokemon = self.bot.pokemon_list[hatched_results['pokemon_id']]['Name']
                xp = hatched_results['experience_awarded']
                candy = hatched_results['candy_awarded']
                ziggy = hatched_results['stardust_awarded']
                logger.log('[#] Congratulations! You\'re the proud trainer of a new {}!'.format(pokemon),'green')
                logger.log('[#] Acquired {} xp, {} candies, and {} stardust from hatch.'.format(xp,candy,ziggy),'green')
            elif 'Protobuf' in hatched_results:
                logger.log('[#] Something probably hatched, but we couldn\'t tell what. Update your protos!','yellow')    
                hatch_success = True
            else:
                logger.log('[#] No hatched eggs this time')
        except Exception as e:
            hatch_success = True 
            logger.log('[#] Hatched eggs check call failed!','red')
        return hatch_success

    def _check_inventory(self):
        response_dict = self.bot.get_inventory()
        incubator_list = []
        egg_list = []
        try:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                if 'inventory_item_data' in item:
                    item = item['inventory_item_data']
                    if 'egg_incubators' in item:
                        incubators = item['egg_incubators']
                        if isinstance(incubators, list):
                            #new protos
                            for inc in incubators:
                                incubator_list.append(inc['egg_incubator'])
                        else:
                            #old protos
                            incubator_list.append(incubators['egg_incubator'])
                    if 'pokemon_data' in item:
                        pokemon = item['pokemon_data']
                        if 'is_egg' in pokemon and pokemon['is_egg']:
                            egg_list.append(pokemon['id'])
                    if 'player_stats' in item:
                        self.km_walked = item['player_stats']['km_walked']
            if len(incubator_list)>0:
                for inc in incubator_list:
                    if 'pokemon_id' in inc:
                        self.incubating_eggs.append(inc['pokemon_id'])
                        self.used_incubators.append(inc)
                    elif inc['uses_remaining']>0:
                        self.available_incubators.append(inc['id'])
            if len(egg_list)>0:
                self.ready_eggs = [egg for egg in egg_list if egg not in self.incubating_eggs]
        except KeyError, NoneType:
            return

    def _incubate_eggs(self):
        api_responses=["Incubator unset",
                       "Incubator applied",
                       "Incubator not found",
                       "Egg not found",
                       "Provided pokemon isn't an egg",
                       "Incubator already in use",
                       "Egg already incubating",
                       "Incubator has no uses remaining"]
        applied = 0
        result = 6
        logger.log('[#] {} incubators available, {} eggs ready.'.format(len(self.available_incubators),len(self.ready_eggs)))
        for incubator in self.available_incubators:
            while len(self.ready_eggs)>0 and result==6:
                egg = self.ready_eggs.pop()
                if self.bot.config.debug:
                    logger.log('[d] trying to apply incubator {} to pokemon {}'.format(incubator, egg),'yellow')
                self.bot.api.use_item_egg_incubator(item_id=incubator,pokemon_id=egg)
                response_dict = self.bot.api.call()
                if 'result' in response_dict['responses']['USE_ITEM_EGG_INCUBATOR']:
                    result = response_dict['responses']['USE_ITEM_EGG_INCUBATOR']['result']
                if result == 1:
                    applied+=1
                    self.incubating_eggs.append(egg)
                else:
                    self.ready_eggs.append(egg)
                if self.bot.config.debug:
                    logger.log('[d] {}'.format(api_responses[result]))
                else:
                    result=6
        logger.log('[#] {} incubators applied. {} eggs now incubating, in total.'.format(applied,len(self.incubating_eggs)),'green')
