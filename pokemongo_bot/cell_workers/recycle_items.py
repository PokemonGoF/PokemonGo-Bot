from pokemongo_bot import logger
from pokemongo_bot.cell_workers.base_task import BaseTask

class RecycleItems(BaseTask):
    def work(self):
        self.bot.latest_inventory = None
        item_count_dict = self.bot.item_inventory_count('all')

        for item_id, bag_count in item_count_dict.iteritems():
            item_name = self.get_item_name(item_id)
            amount_to_keep = self.get_amount_to_keep(item_id)
            bag_count = self.bot.item_inventory_count(item_id)

            if (item_name in self.bot.config.item_filter or str(item_id) in self.bot.config.item_filter) and bag_count > amount_to_keep:
                items_recycle_count = bag_count - amount_to_keep
                self.recycle(item_id, items_recycle_count)

        self.recycle_pokeballs()

    def get_item_name(self, item_id):
        return self.bot.item_list[str(item_id)]

    def get_amount_to_keep(self, item_id):
            item_name = self.get_item_name(item_id)
            id_filter = self.bot.config.item_filter.get(item_name, 0)
            if id_filter is not 0:
                id_filter_keep = id_filter.get('keep', 20)
            else:
                id_filter = self.bot.config.item_filter.get(str(item_id), 0)
                if id_filter is not 0:
                    id_filter_keep = id_filter.get('keep', 20)
            return id_filter_keep

    def recycle(self, item_id, recycle_count, show_amount=True):
        item_name = self.get_item_name(item_id)
        response_dict_recycle = self.send_recycle_item_request(item_id=item_id, count=recycle_count)
        result = response_dict_recycle.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

        if result == 1: # Request success
            message = "-- Discarded {}x {} "
            message = message.format(str(recycle_count),
                                     item_name)
            if show_amount:
                message += "(keeps only {} maximum) "
                message = message.format(str(self.get_amount_to_keep(item_id)))
            logger.log(message, 'green')
        else:
            logger.log("-- Failed to discard " + item_name, 'red')

    def send_recycle_item_request(self, item_id, count):
        self.bot.api.recycle_inventory_item(item_id=item_id, count=count)
        inventory_req = self.bot.api.call()

        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return inventory_req

    def recycle_pokeballs(self):
        number_of_balls_to_keep_logged = False
        number_of_balls_to_keep = self.get_amount_to_keep(5)
        total_amount_of_balls = 0

        for ball_id in [4, 3, 2, 1]:
            bag_count = self.bot.item_inventory_count(ball_id)
            if bag_count:
                total_amount_of_balls += bag_count
                if total_amount_of_balls > number_of_balls_to_keep:
                    if not number_of_balls_to_keep_logged:
                        logger.log('Keeping {} balls in total'.format(str(number_of_balls_to_keep)), 'green')
                        number_of_balls_to_keep_logged = True
                    recycle_amount = total_amount_of_balls - number_of_balls_to_keep
                    number_of_balls_to_keep -= recycle_amount
                    self.recycle(ball_id, recycle_amount, show_amount=False)
