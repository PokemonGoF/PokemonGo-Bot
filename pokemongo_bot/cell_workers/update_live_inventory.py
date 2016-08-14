import ctypes
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException


class UpdateLiveInventory(BaseTask):
    """
    Periodically displays the user inventory in the terminal.

    Fetching some stats requires making API calls. If you're concerned about the amount of calls
    your bot is making, don't enable this worker.

    Example config :
    {
        "type": "UpdateLiveInventory",
        "config": {
          "enabled": true,
          "min_interval": 120,
          "items": ["space_info", "pokeballs", "greatballs", "ultraballs", "razzberries", "luckyegg"]
        }
    }

    min_interval : The minimum interval at which the stats are displayed,
                   in seconds (defaults to 120 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    items : An array of items to display and their display order (implicitly),
            see available items below (defaults to []).

    Available items :
        'space_info': not an item but shows inventory bag space (i.e. 'Items: 140/350')
        'pokeballs'
        'greatballs'
        'ultraballs'
        'masterballs'
        'razzberries'
        'blukberries'
        'nanabberries'
        'luckyegg'
        'incubator'
        'troydisk'
        'potion'
        'superpotion'
        'hyperpotion'
        'maxpotion'
        'incense'
        'incensespicy'
        'incensecool'
        'revive'
        'maxrevive'
    """

    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.next_update = None
        self.min_interval = self.config.get('min_interval', 120)
        self.displayed_items = self.config.get('items', [])

        self.bot.event_manager.register_event('show_inventory', parameters=('items',))

    def work(self):
        if not self.should_print():
            return WorkerResult.SUCCESS
        line = self.get_inventory_line()
        if not line:
            return WorkerResult.SUCCESS
        self.print_inv(line)
        return WorkerResult.SUCCESS

    def should_print(self):
        return self.next_update is None or datetime.now() >= self.next_update

    def compute_next_update(self):
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def print_inv(self, items):
        self.emit_event(
            'show_inventory',
            formatted="{items}",
            data={
                'items': items
            }
        )
        self.compute_next_update()


    def get_inventory_line(self):
        self.inventory = inventory.items()

        available_items = {
            'space_info': 'Items: {:,}/{:,}'.format(self.inventory.get_space_used(),
                                                    self.inventory.get_space_used() + self.inventory.get_space_left()),
            'pokeballs': 'Pokeballs: {:,}'.format(self.inventory.get(1).count),
            'greatballs': 'GreatBalls: {:,}'.format(self.inventory.get(2).count),
            'ultraballs': 'UltraBalls: {:,}'.format(self.inventory.get(3).count),
            'masterballs': 'MasterBalls: {:,}'.format(self.inventory.get(4).count),
            'razzberries': 'RazzBerries: {:,}'.format(self.inventory.get(701).count),
            'blukberries': 'BlukBerries: {:,}'.format(self.inventory.get(702).count),
            'nanabberries': 'NanabBerries: {:,}'.format(self.inventory.get(703).count),
            'luckyegg': 'LuckyEgg: {:,}'.format(self.inventory.get(301).count),
            'incubator': 'Incubator: {:,}'.format(self.inventory.get(902).count),
            'troydisk': 'TroyDisk: {:,}'.format(self.inventory.get(501).count),
            'potion': 'Potion: {:,}'.format(self.inventory.get(101).count),
            'superpotion': 'SuperPotion: {:,}'.format(self.inventory.get(102).count),
            'hyperpotion': 'HyperPotion: {:,}'.format(self.inventory.get(103).count),
            'maxpotion': 'MaxPotion: {:,}'.format(self.inventory.get(104).count),
            'incense': 'Incense: {:,}'.format(self.inventory.get(401).count),
            'incensespicy': 'IncenseSpicy: {:,}'.format(self.inventory.get(402).count),
            'incensecool': 'IncenseCool: {:,}'.format(self.inventory.get(403).count),
            'revive': 'Revive: {:,}'.format(self.inventory.get(201).count),
            'maxrevive': 'MaxRevive: {:,}'.format(self.inventory.get(202).count)
        }

        def get_item(item):
            if item not in available_items:
                raise ConfigException("item '{}' isn't available for displaying".format(item))
            return available_items[item]

        line = ' | '.join(map(get_item, self.displayed_items))

        return line
