from pokemongo_bot import logger


class RecycleItems(object):

    def __init__(self, bot, config):
        self.bot = bot

    def work(self):
        self.bot.latest_inventory = None
        item_count_dict = self.bot.item_inventory_count('all')

        for item_id, bag_count in item_count_dict.iteritems():
            item_name = self.bot.item_list[str(item_id)]
            id_filter = self.bot.config.item_filter.get(item_name, 0)
            if id_filter is not 0:
                id_filter_keep = id_filter.get('keep', 20)
            else:
                id_filter = self.bot.config.item_filter.get(str(item_id), 0)
                if id_filter is not 0:
                    id_filter_keep = id_filter.get('keep', 20)

            bag_count = self.bot.item_inventory_count(item_id)
            if (item_name in self.bot.config.item_filter or str(item_id) in self.bot.config.item_filter) and bag_count > id_filter_keep:
                items_recycle_count = bag_count - id_filter_keep
                response_dict_recycle = self.send_recycle_item_request(item_id=item_id, count=items_recycle_count)
                result = response_dict_recycle.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

                if result == 1: # Request success
                    message_template = "-- Discarded {}x {} (keeps only {} maximum) "
                    message = message_template.format(str(items_recycle_count), item_name, str(id_filter_keep))
                    logger.log(message, 'green')
                else:
                    logger.log("-- Failed to discard " + item_name, 'red')

    def send_recycle_item_request(self, item_id, count):
        self.bot.api.recycle_inventory_item(item_id=item_id, count=count)
        inventory_req = self.bot.api.call()

        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return inventory_req
