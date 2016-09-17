import unittest
from datetime import timedelta, datetime
from time import sleep

from mock import patch, MagicMock

from pokemongo_bot.cell_workers import MoveToFort
from tests import FakeBot


class LogDelayTestCase(unittest.TestCase):

    config = {
          "enabled": 'true',
          "lure_attraction": 'true',
          "lure_max_distance": 2000,
          "walker": "StepWalker",
          "log_interval": 3
      }

    def setUp(self):
        self.bot = FakeBot()
        self.bot.event_manager = MagicMock()
        self.worker = MoveToFort(self.bot, self.config)

    def test_read_correct_delay_config(self):
        self.worker.config['log_interval'] = 3
        self.assertEqual(self.config.get('log_interval'), 3)

    def test_log_with_no_delay(self):
        self.worker.config['log_interval'] = 3
        # All those call should not happen cause without any delay between each other
        self.worker.emit_event('moving_to_fort', formatted="just an example")
        self.worker.emit_event('moving_to_fort', formatted="just an example")

        # Let's try to subtract 2 of 3 sec and see if event_manager.emit() get no call at all
        self.worker.last_log_time -= 2
        self.worker.emit_event('moving_to_fort', formatted="just an example")
        self.worker.emit_event('moving_to_fort', formatted="just an example")

        self.assertEqual(self.bot.event_manager.emit.call_count, 0)
        assert not self.bot.event_manager.emit.called

    def test_correct_delay_wait(self):

        self.worker.config['log_interval'] = 2

        # to avoid use sleep() function here, we subtract expected log_interval to last_log_time
        self.worker.last_log_time -= self.worker.config['log_interval']

        for number_of_checks in range(10):
            self.worker.emit_event('moving_to_fort', formatted="just an example")
            self.worker.last_log_time -= 2

        self.assertEqual(self.bot.event_manager.emit.call_count, 10)

        # i think should be better assert in this way, but can't get it working
        # assert self.bot.event_manager.emit.assert_any_call('moving_to_fort',
        #                                                    sender=None,
        #                                                    level='info',
        #                                                    formatted="just an example",data={})

