# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from datetime import datetime, timedelta
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot import inventory
from pokemongo_bot.item_list import Item

class CatchLimiter(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(CatchLimiter, self).__init__(bot, config)
        self.bot = bot
        self.config = config
        self.enabled = self.config.get("enabled",False)
        self.min_balls = self.config.get("min_balls",20)
        self.duration = self.config.get("duration",15)
        if not hasattr(self.bot, "catch_resume_at"): self.bot.catch_resume_at = None

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        now = datetime.now()
        balls_on_hand = self.get_pokeball_count()
        
        # If resume time has passed, resume catching tasks
        if self.bot.catch_disabled and now >= self.bot.catch_resume_at:
            if balls_on_hand > self.min_balls:
                self.emit_event(
                    'catch_limit_off',
                    formatted="Resume time has passed and balls on hand ({}) exceeds threshold {}. Re-enabling catch tasks.".
                        format(balls_on_hand,self.min_balls)
                )
                self.bot.catch_disabled = False

        # If balls_on_hand less than threshold, pause catching tasks for duration minutes
        if not self.bot.catch_disabled and balls_on_hand <= self.min_balls:
            self.bot.catch_resume_at = now + timedelta(minutes = self.duration)
            self.bot.catch_disabled = True
            self.emit_event(
                'catch_limit_on',
                formatted="Balls on hand ({}) has reached threshold {}. Disabling catch tasks until {} or balls on hand > threshold (whichever is later).".
                    format(balls_on_hand, self.min_balls, self.bot.catch_resume_at.strftime("%H:%M:%S"))
            )
            
        return WorkerResult.SUCCESS

    def get_pokeball_count(self):
        return sum([inventory.items().get(ball.value).count for ball in [Item.ITEM_POKE_BALL, Item.ITEM_GREAT_BALL, Item.ITEM_ULTRA_BALL]])
