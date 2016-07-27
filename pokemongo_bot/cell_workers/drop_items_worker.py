import random

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot import logger

class DropItemsWorker(object):
    def __init__(self, bot, storage_trigger):
        self.bot = bot
        self.api = bot.api
        self.items_count = self.bot.get_inventory_count('item')
        self.items = self.bot.current_inventory()
        self.storage_trigger = storage_trigger

    def work(self):
        try:
            self.api.get_player()
            response_dict = self.api.call()
            max_storage = response_dict['responses']['GET_PLAYER']['player_data']['max_item_storage']
        except:
            return None

        if self.items_count/max_storage > self.storage_trigger:
            items_to_remove = []
            if self.items[Item.ITEM_MASTER_BALL.value] > 45:
                how_many = self.items[Item.ITEM_MASTER_BALL.value] - 45
                items_to_remove.append([Item.ITEM_MASTER_BALL.value, how_many, '{} Master Ball'.format(how_many)])
                self.items[Item.ITEM_MASTER_BALL.value] = self.items[Item.ITEM_MASTER_BALL.value] - how_many
                if self.items[Item.ITEM_ULTRA_BALL.value]>30:
                    how_many = self.items[Item.ITEM_ULTRA_BALL.value] - 30
                    items_to_remove.append([Item.ITEM_ULTRA_BALL.value, how_many, '{} Ultra Ball'.format(how_many)])
                    self.items[Item.ITEM_ULTRA_BALL.value] = self.items[Item.ITEM_ULTRA_BALL.value] - (how_many)
                if self.items[Item.ITEM_GREAT_BALL.value]:
                    how_many = self.items[Item.ITEM_GREAT_BALL.value]
                    items_to_remove.append([Item.ITEM_GREAT_BALL.value, how_many, '{} Great Ball'.format(how_many)])
                    self.items[Item.ITEM_GREAT_BALL.value] = 0
                if self.items[Item.ITEM_POKE_BALL.value]:
                    how_many = self.items[Item.ITEM_POKE_BALL.value]
                    items_to_remove.append([Item.ITEM_POKE_BALL.value, how_many, '{} Poke Ball'.format(how_many)])
                    self.items[Item.ITEM_POKE_BALL.value] = 0
            if self.items[Item.ITEM_ULTRA_BALL.value] > 45:
                how_many = self.items[Item.ITEM_ULTRA_BALL.value] - 45
                items_to_remove.append([Item.ITEM_ULTRA_BALL.value, how_many, '{} Ultra Ball'.format(how_many)])
                self.items[Item.ITEM_ULTRA_BALL.value] = self.items[Item.ITEM_ULTRA_BALL.value] - (how_many)
                if self.items[Item.ITEM_GREAT_BALL.value]>30:
                    how_many = self.items[Item.ITEM_GREAT_BALL.value] - 30
                    items_to_remove.append([Item.ITEM_GREAT_BALL.value, how_many, '{} Great Ball'.format(how_many)])
                    self.items[Item.ITEM_GREAT_BALL.value] = self.items[Item.ITEM_GREAT_BALL.value] - (how_many)
                if self.items[Item.ITEM_POKE_BALL.value]:
                    how_many = self.items[Item.ITEM_POKE_BALL.value]
                    items_to_remove.append([Item.ITEM_POKE_BALL.value, how_many, '{} Poke Ball'.format(how_many)])
                    self.items[Item.ITEM_POKE_BALL.value] = 0
            if self.items[Item.ITEM_GREAT_BALL.value] > 45:
                how_many = self.items[Item.ITEM_GREAT_BALL.value] - 45
                items_to_remove.append([Item.ITEM_GREAT_BALL.value, how_many, '{} Great Ball'.format(how_many)])
                self.items[Item.ITEM_GREAT_BALL.value] = self.items[Item.ITEM_GREAT_BALL.value] - (how_many)
                if self.items[Item.ITEM_POKE_BALL.value]>30:
                    how_many = self.items[Item.ITEM_POKE_BALL.value] - 30
                    items_to_remove.append([Item.ITEM_POKE_BALL.value, how_many, '{} Poke Ball'.format(how_many)])
                    self.items[Item.ITEM_POKE_BALL.value] = self.items[Item.ITEM_POKE_BALL.value] - (how_many)
            if self.items[Item.ITEM_POKE_BALL.value] > 45:
                how_many = self.items[Item.ITEM_POKE_BALL.value] - 45
                items_to_remove.append([Item.ITEM_POKE_BALL.value, how_many, '{} Poke Ball'.format(how_many)])
                self.items[Item.ITEM_POKE_BALL.value] = self.items[Item.ITEM_POKE_BALL.value] - (how_many)

            if self.items[Item.ITEM_MAX_POTION.value] > 25:
                how_many = self.items[Item.ITEM_MAX_POTION.value] - 25
                items_to_remove.append([Item.ITEM_MAX_POTION.value, how_many, '{} Max Potion'.format(how_many)])
                self.items[Item.ITEM_MAX_POTION.value] = self.items[Item.ITEM_MAX_POTION.value] - (how_many)
                if self.items[Item.ITEM_HYPER_POTION.value]>20:
                    how_many = self.items[Item.ITEM_HYPER_POTION.value] - 20
                    items_to_remove.append([Item.ITEM_HYPER_POTION.value, how_many, '{} Hyper Potion'.format(how_many)])
                    self.items[Item.ITEM_HYPER_POTION.value] = self.items[Item.ITEM_HYPER_POTION.value] - (how_many)
                if self.items[Item.ITEM_SUPER_POTION.value]:
                    how_many = self.items[Item.ITEM_SUPER_POTION.value]
                    items_to_remove.append([Item.ITEM_SUPER_POTION.value, how_many, '{} Super Potion'.format(how_many)])
                    self.items[Item.ITEM_SUPER_POTION.value] = 0
                if self.items[Item.ITEM_POTION.value]:
                    how_many = self.items[Item.ITEM_POTION.value]
                    items_to_remove.append([Item.ITEM_POTION.value, how_many, '{} Potion'.format(how_many)])
                    self.items[Item.ITEM_POTION.value] = 0
            if self.items[Item.ITEM_HYPER_POTION.value] > 25:
                how_many = self.items[Item.ITEM_HYPER_POTION.value] - 25
                items_to_remove.append([Item.ITEM_HYPER_POTION.value, how_many, '{} Hyper Potion'.format(how_many)])
                self.items[Item.ITEM_HYPER_POTION.value] = self.items[Item.ITEM_HYPER_POTION.value] - (how_many)
                if self.items[Item.ITEM_SUPER_POTION.value]>20:
                    how_many = self.items[Item.ITEM_SUPER_POTION.value] - 20
                    items_to_remove.append([Item.ITEM_SUPER_POTION.value, how_many, '{} Super Potion'.format(how_many)])
                    self.items[Item.ITEM_SUPER_POTION.value] = self.items[Item.ITEM_SUPER_POTION.value] - (how_many)
                if self.items[Item.ITEM_POTION.value]:
                    how_many = self.items[Item.ITEM_POTION.value]
                    items_to_remove.append([Item.ITEM_POTION.value, how_many, '{} Potion'.format(how_many)])
                    self.items[Item.ITEM_POTION.value] = 0
            if self.items[Item.ITEM_SUPER_POTION.value] > 25:
                how_many = self.items[Item.ITEM_SUPER_POTION.value] - 25
                items_to_remove.append([Item.ITEM_SUPER_POTION.value, how_many, '{} Super Potion'.format(how_many)])
                self.items[Item.ITEM_SUPER_POTION.value] = self.items[Item.ITEM_SUPER_POTION.value] - (how_many)
                if self.items[Item.ITEM_POTION.value]>20:
                    how_many = self.items[Item.ITEM_POTION.value] - 20
                    items_to_remove.append([Item.ITEM_POTION.value, how_many, '{} Potion'.format(how_many)])
                    self.items[Item.ITEM_POTION.value] = self.items[Item.ITEM_POTION.value] - (how_many)
            if self.items[Item.ITEM_POTION.value] > 25:
                how_many = self.items[Item.ITEM_POTION.value] - 25
                items_to_remove.append([Item.ITEM_POTION.value, how_many, '{} Potion'.format(how_many)])
                self.items[Item.ITEM_POTION.value] = self.items[Item.ITEM_POTION.value] - (how_many)

            if self.items[Item.ITEM_MAX_REVIVE.value] > 25:
                how_many = self.items[Item.ITEM_MAX_REVIVE.value] - 25
                items_to_remove.append([Item.ITEM_MAX_REVIVE.value, how_many, '{} Max Revive'.format(how_many)])
                self.items[Item.ITEM_MAX_REVIVE.value] = self.items[Item.ITEM_MAX_REVIVE.value] - (how_many)
                if self.items[Item.ITEM_REVIVE.value]>20:
                    how_many = self.items[Item.ITEM_REVIVE.value] - 20
                    items_to_remove.append([Item.ITEM_REVIVE.value, how_many, '{} Revive'.format(how_many)])
                    self.items[Item.ITEM_REVIVE.value] = self.items[Item.ITEM_REVIVE.value] - (how_many)
            if self.items[Item.ITEM_REVIVE.value] > 25:
                how_many = self.items[Item.ITEM_REVIVE.value] - 25
                items_to_remove.append([Item.ITEM_REVIVE.value, how_many, '{} Revive'.format(how_many)])
                self.items[Item.ITEM_REVIVE.value] = self.items[Item.ITEM_REVIVE.value] - (how_many)

            if items_to_remove:
                logger.log('Start to drop items', 'yellow')
                for item in items_to_remove:
                    response_drop = self.bot.drop_item(item_id=item[0], count=item[1])
                    if response_drop and 'responses' in response_drop and \
                        'RECYCLE_INVENTORY_ITEM' in response_drop['responses'] and \
                            'result' in response_drop['responses']['RECYCLE_INVENTORY_ITEM']:
                        result_drop = response_drop['responses']['RECYCLE_INVENTORY_ITEM']['result']
                        if result_drop is 1: # Request success
                            logger.log("-- Recycled " + item[2] + "!", 'green')
                        else:
                            logger.log("-- Recycling " + item[2] + "has failed!", 'red')
                        sleep(random.random()*2)
                logger.log('Complete!', 'yellow')
        return None
