# -*- coding: utf-8 -*-
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers import CatchVisiblePokemon, CatchLuredPokemon
from pokemongo_bot.item_list import Item
from pokemongo_bot import inventory


class CatchPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.catch_workers = []
        if self.config.get('catch_visible_pokemon', True):
            self.catch_workers.append(CatchVisiblePokemon(self.bot, self.config))
        if self.config.get('catch_lured_pokemon', True):
            self.catch_workers.append(CatchLuredPokemon(self.bot, self.config))

    def work(self):

        if sum([inventory.items().get(ball.value).count for ball in 
            [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]]) <= 0:
            return WorkerResult.ERROR

        for cw in self.catch_workers:
            if cw.work() == WorkerResult.RUNNING:
                return WorkerResult.RUNNING
        return WorkerResult.SUCCESS
