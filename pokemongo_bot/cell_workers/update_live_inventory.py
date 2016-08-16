import ctypes
import logging
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
        self.logger = logging.getLogger(type(self).__name__)

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
            self.print_inv(self.get_inventory_line(True),  True)
            return WorkerResult.SUCCESS

        line = self.get_inventory_line(False)
        if not line:
            return WorkerResult.SUCCESS

        self.print_inv(line, False)
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

    def print_inv(self, items, is_debug):
        """
        Logs the items into the terminal using an event.
        :param items: The items to display.
        :type items: string
        :param is_debug: If True emits event at debug level.
        :type is_debug: boolean
        :return: Nothing.
        :rtype: None
        """
        if not is_debug:
            self.emit_event(
                'show_inventory',
                formatted="{items}",
                data={
                    'items': items
                }
            )
        else:
            self.emit_event(
                'show_inventory',
                sender=self,
                level='debug',
                formatted="{items}",
                data={
                    'items': items
                }
            )

        self.compute_next_update()


    def get_inventory_line(self, is_debug):
        """
        Generates a items string according to the configuration.
        :param is_debug: If True returns a string with all items.
        :type is_debug: boolean
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

        if is_debug:
            temp = []
            for key, value in available_items.iteritems():
                temp.append(value)
            return ' | '.join(temp)

        line = ' | '.join(map(get_item, self.displayed_items))
        return line

    def print_all(self):
        """
        Logs the items into the terminal using self.logger.
        It logs using multiple lines and logs all items.
        :return: Nothing.
        :rtype: None
        """
        self.logger.info(
            'Items: {}/{}'.format(
                self.inventory.get_space_used(),
                self.inventory.get_space_used() + self.inventory.get_space_left()
                )
            )

        self.logger.info(
            'PokeBalls: {} | GreatBalls: {} | UltraBalls: {} | MasterBalls: {}'.format(
                self.inventory.get(1).count,
                self.inventory.get(2).count,
                self.inventory.get(3).count,
                self.inventory.get(4).count
                )
            )

        self.logger.info(
            'RazzBerries: {} | BlukBerries: {} | NanabBerries: {}'.format(
                self.inventory.get(701).count,
                self.inventory.get(702).count,
                self.inventory.get(703).count
                )
            )

        self.logger.info(
            'LuckyEgg: {} | Incubator: {} | TroyDisk: {}'.format(
                self.inventory.get(301).count,
                self.inventory.get(902).count,
                self.inventory.get(501).count
                )
            )

        self.logger.info(
            'Potion: {} | SuperPotion: {} | HyperPotion: {} | MaxPotion: {}'.format(
                self.inventory.get(101).count,
                self.inventory.get(102).count,
                self.inventory.get(103).count,
                self.inventory.get(104).count
                )
            )

        self.logger.info(
            'Incense: {} | IncenseSpicy: {} | IncenseCool: {}'.format(
                self.inventory.get(401).count,
                self.inventory.get(402).count,
                self.inventory.get(403).count
                )
            )

        self.logger.info(
            'Revive: {} | MaxRevive: {}'.format(
                self.inventory.get(201).count,
                self.inventory.get(202).count
                )
            )

        self.compute_next_update()
