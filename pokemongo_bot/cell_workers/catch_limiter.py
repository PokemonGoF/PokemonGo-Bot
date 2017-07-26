# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.item_list import Item
from pokemongo_bot.worker_result import WorkerResult


class CatchLimiter(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(CatchLimiter, self).__init__(bot, config)
        self.bot = bot
        self.config = config
        self.enabled = self.config.get("enabled", False)
        self.min_balls = self.config.get("min_balls", 20)
        self.resume_at_balls = self.config.get("resume_balls", 100)
        self.duration = self.config.get("duration", 15)
        self.no_log_until = datetime.now()
        self.min_ultraball_to_keep = 0
        for catch_cfg in self.bot.config.raw_tasks:
            if "type" in catch_cfg:
                if catch_cfg["type"] == "CatchPokemon":
                    self.min_ultraball_to_keep = catch_cfg["config"]["min_ultraball_to_keep"]
                    self.daily_catch_limit = catch_cfg["config"]["daily_catch_limit"]
                    self.exit_on_limit_reached = catch_cfg["config"]["exit_on_limit_reached"]

        if not hasattr(self.bot, "catch_resume_at"):
            self.bot.catch_resume_at = None
        if not hasattr(self.bot, "catch_limit_reached"):
            self.bot.catch_limit_reached = False
        if not hasattr(self.bot, "warned_about_catch_limit"):
            self.bot.warned_about_catch_limit = False

    def work(self):
        if not self.enabled:
            return WorkerResult.SUCCESS

        now = datetime.now()

        # check catch limits
        with self.bot.database as conn:
            c = conn.cursor()
            c.execute(
                "SELECT DISTINCT COUNT(encounter_id) FROM catch_log WHERE dated >= datetime('now','-1 day')")

        result = c.fetchone()

        # check catch limits before catch

        if result[0] >= self.daily_catch_limit:
            if hasattr(
                    self.bot,
                    "warned_about_catch_limit") and not self.bot.warned_about_catch_limit:
                self.emit_event(
                    'catch_limit',
                    formatted='WARNING! You have reached (%s / %s) your daily catch limit. Disabling catching for an hour!' %
                    (result[0],
                     self.daily_catch_limit))
                self.bot.warned_about_catch_limit = True
                self.bot.catch_limit_reached = True
                self.bot.catch_resume_at = now + timedelta(minutes=60)
                self.bot.catch_disabled = True
            if self.exit_on_limit_reached:
                sys.exit(2)

            return WorkerResult.SUCCESS

        elif result[0] <= (self.daily_catch_limit - 20):
            if self.bot.catch_limit_reached:
                self.emit_event(
                    'catch_limit_off',
                    formatted="Resume time hasn't passed yet, but catch limit passing ({} / {}}). Re-enabling catch tasks.".format(
                        result[0],
                        self.daily_catch_limit))
                self.bot.catch_disabled = False
                self.bot.catch_limit_reached = False
                self.bot.catch_resume_at = now
            self.bot.warned_about_catch_limit = False

        elif self.bot.catch_resume_at is not None:
            # Lets check if the resume time has passed and the limit is okay
            if now >= self.bot.catch_resume_at and result[0] < self.daily_catch_limit:
                self.emit_event(
                    'catch_limit_off',
                    formatted="Resume time has passed and catch limit passing ({} / {}}). Re-enabling catch tasks.".format(
                        result[0],
                        self.daily_catch_limit))
                self.bot.catch_disabled = False
                self.bot.catch_limit_reached = False
                self.bot.catch_resume_at = now

        if self.bot.catch_limit_reached:
            if self.no_log_until <= now:
                self.logger.info(
                    "All catch tasks disabled until %s beacuse we hit the daily catch limit (%s >= %s)" %
                    (self.bot.catch_resume_at.strftime("%H:%M:%S"), result[0], self.daily_catch_limit))
                self.no_log_until = now + timedelta(minutes=2)
            return WorkerResult.SUCCESS

        # Back to the balls
        balls_on_hand = self.get_pokeball_count() - self.min_ultraball_to_keep

        # If resume time has passed, resume catching tasks
        if self.bot.catch_disabled and not self.bot.catch_limit_reached and now >= self.bot.catch_resume_at:
            if balls_on_hand > self.min_balls:
                self.emit_event(
                    'catch_limit_off',
                    formatted="Resume time has passed and balls on hand ({}) exceeds threshold {}. Re-enabling catch tasks.".format(
                        balls_on_hand,
                        self.min_balls))
                self.bot.catch_disabled = False

        # If balls_on_hand is more than resume_at_balls,
        # resume catch tasks, if not softbanned
        if (
                self.bot.softban is False and
                self.bot.catch_disabled and
                balls_on_hand >= self.resume_at_balls
        ):
            self.emit_event(
                'catch_limit_off',
                formatted="Resume time hasn't passed yet, but balls on hand ({}) exceeds threshold {}. Re-enabling catch tasks.".format(
                    balls_on_hand,
                    self.resume_at_balls))
            self.bot.catch_disabled = False

        # If balls_on_hand less than threshold,
        # pause catching tasks for duration minutes
        if not self.bot.catch_disabled and balls_on_hand <= self.min_balls:
            self.bot.catch_resume_at = now + timedelta(minutes=self.duration)
            self.no_log_until = now + timedelta(minutes=2)
            self.bot.catch_disabled = True
            self.emit_event(
                'catch_limit_on',
                formatted=(
                    "Balls on hand ({}) has reached threshold {}."
                    " Disabling catch tasks until {} or balls on hand > threshold (whichever is later).").format(
                    balls_on_hand,
                    self.min_balls,
                    self.bot.catch_resume_at.strftime("%H:%M:%S")))

        if self.bot.catch_disabled and self.no_log_until <= now:
            if now >= self.bot.catch_resume_at:
                self.logger.info(
                    "All catch tasks disabled until balls on hand (%s) > threshold." %
                    balls_on_hand)
            else:
                self.logger.info(
                    "All catch tasks disabled until %s or balls on hand (%s) >= %s" %
                    (self.bot.catch_resume_at.strftime("%H:%M:%S"),
                     balls_on_hand,
                     self.resume_at_balls))
            self.no_log_until = now + timedelta(minutes=2)

        return WorkerResult.SUCCESS

    def get_pokeball_count(self):
        return sum([inventory.items().get(ball.value).count for ball in [
            Item.ITEM_POKE_BALL,
            Item.ITEM_GREAT_BALL,
            Item.ITEM_ULTRA_BALL]
        ])
