import ctypes
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException


class UpdateLiveInventory(BaseTask):
    """
    Periodically displays the user inventory in the terminal.

    Example config :
    {
        "type": "UpdateLiveInventory",
        "config": {
          "enabled": true,
          "min_interval": 120,
          "show_all_multiple_lines": false,
          "items": ["space_info", "pokeballs", "greatballs", "ultraballs", "razzberries", "luckyegg"]
        }
    }

    min_interval : The minimum interval at which the stats are displayed,
                   in seconds (defaults to 120 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    show_all_multiple_lines : Logs all items on inventory using multiple lines.
                              Ignores configuration of 'items' 
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
        self.show_all_multiple_lines = self.config.get('show_all_multiple_lines', False)
        self.displayed_items = self.config.get('items', [])

        if self.show_all_multiple_lines:
            self.bot.event_manager.register_event('show_inventory')
        else:
            self.bot.event_manager.register_event('show_inventory', parameters=('items',))


    def work(self):
        """
        Displays the items if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self.should_print():
            return WorkerResult.SUCCESS
        self.inventory = inventory.items()
        if self.show_all_multiple_lines:
            self.print_all()
            return WorkerResult.SUCCESS
        line = self.get_inventory_line()
        if not line:
            return WorkerResult.SUCCESS
        self.print_inv(line)
        return WorkerResult.SUCCESS

    def should_print(self):
        """
        Returns a value indicating whether the items should be displayed.
        :return: True if the stats should be displayed; otherwise, False.
        :rtype: bool
        """
        return self.next_update is None or datetime.now() >= self.next_update

    def compute_next_update(self):
        """
        Computes the next update datetime based on the minimum update interval.
        :return: Nothing.
        :rtype: None
        """
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def print_inv(self, items):
        """
        Logs the items into the terminal using an event.
        :param items: The items to display.
        :type items: string
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
            'show_inventory',
            formatted="{items}",
            data={
                'items': items
            }
        )
        self.compute_next_update()


    def get_inventory_line(self):
        """
        Generates a items string according to the configuration.
        :return: A string containing items and their count, ready to be displayed.
        :rtype: string
        """
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
            """
            Fetches a item string from the available items dictionary.
            :param item: The item name.
            :type item: string
            :return: The generated item string.
            :rtype: string
            :raise: ConfigException: When the provided item string isn't in the available items
            dictionary.
            """
            if item not in available_items:
                raise ConfigException("item '{}' isn't available for displaying".format(item))
            return available_items[item]

        line = ' | '.join(map(get_item, self.displayed_items))
        return line

    def print_all(self):
        """
        Logs the items into the terminal using an event.
        It logs using multiple lines and logs all items.
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
                'show_inventory',
                formatted='Items: {items_count}/{item_bag}',
                data={
                    'items_count': self.inventory.get_space_used(),
                    'item_bag': self.inventory.get_space_used() + self.inventory.get_space_left()
                }
            )

        self.emit_event(
                'show_inventory',
                formatted='PokeBalls: {pokeballs} | GreatBalls: {greatballs} | UltraBalls: {ultraballs} | MasterBalls: {masterballs}',
                data={
                    'pokeballs': str(self.inventory.get(1).count),
                    'greatballs': str(self.inventory.get(2).count),
                    'ultraballs': str(self.inventory.get(3).count),
                    'masterballs': str(self.inventory.get(4).count)
                }
            )

        self.emit_event(
                'show_inventory',
                formatted='RazzBerries: {razzberries} | BlukBerries: {blukberries} | NanabBerries: {nanabberries}',
                data={
                    'razzberries': self.inventory.get(701).count,
                    'blukberries': self.inventory.get(702).count,
                    'nanabberries': self.inventory.get(703).count
                }
            )

        self.emit_event(
                'show_inventory',
                formatted='LuckyEgg: {luckyegg} | Incubator: {incubator} | TroyDisk: {troydisk}',
                data={
                    'luckyegg': self.inventory.get(301).count,
                    'incubator': self.inventory.get(902).count,
                    'troydisk': self.inventory.get(501).count
                }
            )

        self.emit_event(
                'show_inventory',
                formatted='Potion: {potion} | SuperPotion: {superpotion} | HyperPotion: {hyperpotion} | MaxPotion: {maxpotion}',
                data={
                    'potion': self.inventory.get(101).count,
                    'superpotion': self.inventory.get(102).count,
                    'hyperpotion': self.inventory.get(103).count,
                    'maxpotion': self.inventory.get(104).count
                }
            )

        self.emit_event(
                'show_inventory',
                formatted='Incense: {incense} | IncenseSpicy: {incensespicy} | IncenseCool: {incensecool}',
                data={
                    'incense': self.inventory.get(401).count,
                    'incensespicy': self.inventory.get(402).count,
                    'incensecool': self.inventory.get(403).count
                }
            )
           
        self.emit_event(
                'show_inventory',
                formatted='Revive: {revive} | MaxRevive: {maxrevive}',
                data={
                    'revive': self.inventory.get(201).count,
                    'maxrevive': self.inventory.get(202).count
                }
           )

        self.compute_next_update()
