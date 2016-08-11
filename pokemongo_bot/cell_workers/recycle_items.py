import json
import os
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.tree_config_builder import ConfigException


class RecycleItems(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.min_empty_space = self.config.get('min_empty_space', None)
        self.item_filter = self.config.get('item_filter', {})
        self._validate_item_filter()

    def _validate_item_filter(self):
        item_list = json.load(open(os.path.join(_base_dir, 'data', 'items.json')))
        for config_item_name, bag_count in self.item_filter.iteritems():
            if config_item_name == 'All Balls':
                continue
            if config_item_name == 'All Potions':
                continue
            if config_item_name not in item_list.viewvalues():
                if config_item_name not in item_list:
                    raise ConfigException(
                        "item {} does not exist, spelling mistake? (check for valid item names in data/items.json)".format(
                            config_item_name))

    def work(self):
        items_in_bag = self.bot.get_inventory_count('item')
        total_bag_space = self.bot.player_data['max_item_storage']
        free_bag_space = total_bag_space - items_in_bag

        if self.min_empty_space is not None:
            if free_bag_space >= self.min_empty_space and items_in_bag < total_bag_space:
                    self.emit_event(
                        'item_discard_skipped',
                        formatted="Skipping Recycling of Items. {space} space left in bag.",
                        data={
                            'space': free_bag_space
                        }
                    )
                    return

        self.bot.latest_inventory = None
        item_count_dict = self.bot.item_inventory_count('all')

        # build item filter dynamicly if we have total limit
        if "All Balls" in self.item_filter:
            all_balls_limit = self.item_filter.get("All Balls").get("keep", 50)
            pokeball_count = item_count_dict.get(1, 0)
            greatball_count = item_count_dict.get(2, 0)
            ultraball_count = item_count_dict.get(3, 0)
            masterball_count = item_count_dict.get(4, 0)

            if ( pokeball_count + greatball_count + ultraball_count + masterball_count) > all_balls_limit:
                if ( greatball_count + ultraball_count + masterball_count ) > all_balls_limit:
                    self.item_filter["Pokeball"] = {"keep":0}
                    self.item_filter[1] = {"keep":0}
                    if ( ultraball_count + masterball_count ) > all_balls_limit:
                        self.item_filter["Greatball"] = {"keep":0}
                        self.item_filter[2] = {"keep":0}
                        if masterball_count > all_balls_limit:
                            self.item_filter["Ultraball"] = {"keep":0}
                            self.item_filter[3] = {"keep":0}
                            self.item_filter["Masterball"] = {"keep":all_balls_limit}
                            self.item_filter[4] = {"keep":all_balls_limit}
                        else:
                            self.item_filter["Ultraball"] = {"keep":all_balls_limit - masterball_count}
                            self.item_filter[3] = {"keep":all_balls_limit - masterball_count}
                    else:
                        self.item_filter["Greatball"] = {"keep":all_balls_limit - ultraball_count - masterball_count}
                        self.item_filter[2] = {"keep":all_balls_limit - ultraball_count - masterball_count}
                else:
                    self.item_filter["Pokeball"] = {"keep":all_balls_limit - greatball_count - ultraball_count - masterball_count}
                    self.item_filter[1] = {"keep":all_balls_limit - greatball_count - ultraball_count - masterball_count}

        if "All Portions" in self.item_filter:
            all_portions_limit = self.item_filter.get("All Portions").get("keep", 50)
            portion_count = item_count_dict.get(101, 0)
            super_count = item_count_dict.get(102, 0)
            hyper_count = item_count_dict.get(103, 0)
            max_count = item_count_dict.get(104, 0)
            if ( portion_count + super_count + hyper_count + max_count) > all_portions_limit:
                if ( super_count + hyper_count + max_count ) > all_portions_limit:
                    self.item_filter["Portion"] = {"keep":0}
                    self.item_filter[101] = {"keep":0}
                    if ( hyper_count + max_count ) > all_portions_limit:
                        self.item_filter["Super Portion"] = {"keep":0}
                        self.item_filter[102] = {"keep":0}
                        if max_count > all_portions_limit:
                            self.item_filter["Hyper Portion"] = {"keep":0}
                            self.item_filter[103] = {"keep":0}
                            self.item_filter["Max Portion"] = {"keep":all_portions_limit}
                            self.item_filter[104] = {"keep":all_portions_limit}
                        else:
                            self.item_filter["Hyper Portion"] = {"keep":all_portions_limit - max_count}
                            self.item_filter[103] = {"keep":all_protions_limit - max_count}
                    else:
                        self.item_filter["Super Portion"] = {"keep":all_portions_limit - hyper_count - max_count}
                        self.item_filter[102] = {"keep":all_protions_limit - hyper_count - max_count}
                else:
                    self.item_filter["Portion"] = {"keep":all_portions_limit - super_count - hyper_count - max_count}
                    self.item_filter[101] = {"keep":all_portions_limit - super_count - hyper_count - max_count}

        for item_id, bag_count in item_count_dict.iteritems():
            item_name = self.bot.item_list[str(item_id)]
            id_filter = self.item_filter.get(item_name, 0)
            id_filter_keep = 0
            if id_filter is not 0:
                id_filter_keep = id_filter.get('keep', 20)
            else:
                id_filter = self.item_filter.get(str(item_id), 0)
                if id_filter is not 0:
                    id_filter_keep = id_filter.get('keep', 20)

            bag_count = self.bot.item_inventory_count(item_id)
            if (item_name in self.item_filter or str(item_id) in self.item_filter) and bag_count > id_filter_keep:
                items_recycle_count = bag_count - id_filter_keep
                response_dict_recycle = self.send_recycle_item_request(item_id=item_id, count=items_recycle_count)
                result = response_dict_recycle.get('responses', {}).get('RECYCLE_INVENTORY_ITEM', {}).get('result', 0)

                if result == 1: # Request success
                    self.emit_event(
                        'item_discarded',
                        formatted='Discarded {amount}x {item} (maximum {maximum}).',
                        data={
                            'amount': str(items_recycle_count),
                            'item': item_name,
                            'maximum': str(id_filter_keep)
                        }
                    )
                else:
                    self.emit_event(
                        'item_discard_fail',
                        formatted="Failed to discard {item}",
                        data={
                            'item': item_name
                        }
                    )

    def send_recycle_item_request(self, item_id, count):
        # Example of good request response
        # {'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return self.bot.api.recycle_inventory_item(
            item_id=item_id,
            count=count
        )
