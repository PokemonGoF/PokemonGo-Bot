import ctypes
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult


class UpdateLiveInventory(BaseTask):
    """
    Periodically displays the user inventory in the terminal.

    Fetching some stats requires making API calls. If you're concerned about the amount of calls
    your bot is making, don't enable this worker.

    Example config :
    {
        "type": "UpdateLiveInventory",
        "config": {
          "min_interval": 120
        }
    }

    min_interval : The minimum interval at which the stats are displayed,
                   in seconds (defaults to 120 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    """

    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.next_update = None
        self.min_interval = self.config.get('min_interval', 120)

        self.bot.event_manager.register_event('show_inventory')

    def work(self):
        """
        Displays the inventory if the minimum interval was already achieved.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self.should_print():
            return WorkerResult.SUCCESS
        self.print_inv()
        return WorkerResult.SUCCESS

    def should_print(self):
        """
        Returns a value indicating whether the stats should be displayed.
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

    def print_inv(self):
        """
        Updates the inventory.
        Logs the inventory into the terminal using an event.
        :return: Nothing.
        :rtype: None
        """
        self.inventory = inventory.items()

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
        