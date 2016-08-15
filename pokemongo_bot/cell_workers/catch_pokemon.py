# -*- coding: utf-8 -*-
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.cell_workers import CatchVisiblePokemon, CatchLuredPokemon


class CatchPokemon(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.catch_workers = []
        if self.config['catch_visible_pokemon']:
            self.catch_workers.append(CatchVisiblePokemon(self.bot, self.config))
        if self.config['catch_lured_pokemon']:
            self.catch_workers.append(CatchLuredPokemon(self.bot, self.config))

    def work(self):
        for cw in self.catch_workers:
            if cw.work() == WorkerResult.RUNNING:
                return WorkerResult.RUNNING
        return WorkerResult.SUCCESS
